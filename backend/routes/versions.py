import datetime
import difflib
import mimetypes
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import FileResponse
from backend.database import get_db_connection
from backend.auth import get_current_user, check_folder_permission
from backend.models import DiffRequest
from backend.audit_helper import log_audit
from backend.storage import read_binary_file

router = APIRouter(prefix="/api/v1/versions", tags=["Control de Versiones"])

@router.get("/file/{file_id}")
def get_version_history(file_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, folder_id, current_version_id, name FROM files WHERE id = ?", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso denegado")

    versions = conn.execute('''
        SELECT v.id, v.file_id, v.version_number, v.author_id, v.created_at,
               v.comment, v.file_size, v.mime_type, v.content_hash,
               v.review_status, v.reviewed_at, v.review_notes,
               u.full_name as author_name, u.username as author_username,
               ur.full_name as reviewer_name,
               (v.id = f.current_version_id) as is_current
        FROM versions v
        JOIN files f ON v.file_id = f.id
        LEFT JOIN users u ON v.author_id = u.id
        LEFT JOIN users ur ON v.reviewed_by_user_id = ur.id
        WHERE v.file_id = ?
        ORDER BY v.version_number DESC
    ''', (file_id,)).fetchall()
    conn.close()

    return [dict(v) for v in versions]

@router.get("/{version_id}/download")
def download_specific_version(version_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    v = conn.execute('''
        SELECT v.*, f.name as file_name, f.folder_id
        FROM versions v
        JOIN files f ON v.file_id = f.id
        WHERE v.id = ?
    ''', (version_id,)).fetchone()
    conn.close()

    if not v:
        raise HTTPException(status_code=404, detail="Versión no encontrada")

    if not check_folder_permission(current_user, v["folder_id"], "Lectura"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="DESCARGAR_VERSION",
        target_type="VERSION",
        target_id=version_id,
        target_name=f"{v['file_name']} (v{v['version_number']})",
        details=f"Descarga histórica de versión v{v['version_number']}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return FileResponse(
        path=v["storage_path"],
        filename=f"v{v['version_number']}_{v['file_name']}",
        media_type=v["mime_type"] or "application/octet-stream"
    )

@router.post("/{version_id}/restore")
def restore_version(version_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "Lector":
        raise HTTPException(status_code=403, detail="Los usuarios Lectores no pueden restaurar versiones")

    conn = get_db_connection()
    target_v = conn.execute('''
        SELECT v.*, f.id as file_id, f.folder_id, f.name as file_name, f.is_locked, f.locked_by_user_id
        FROM versions v
        JOIN files f ON v.file_id = f.id
        WHERE v.id = ?
    ''', (version_id,)).fetchone()

    if not target_v:
        conn.close()
        raise HTTPException(status_code=404, detail="Versión objetivo no encontrada")

    if not check_folder_permission(current_user, target_v["folder_id"], "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso de edición insuficiente en la carpeta")

    if target_v["is_locked"] and target_v["locked_by_user_id"] != current_user["id"] and current_user["role"] != "Administrador":
        conn.close()
        raise HTTPException(status_code=423, detail="El archivo está bloqueado para edición por otro usuario")

    # In accordance with Requirement RF-07 and Acceptance Scenario 4:
    # "Un usuario restaura la versión 2: se crea una versión N+1 con ese contenido y las versiones anteriores permanecen intactas."
    cursor = conn.cursor()
    latest_v = cursor.execute("SELECT MAX(version_number) FROM versions WHERE file_id = ?", (target_v["file_id"],)).fetchone()[0]
    new_v_num = latest_v + 1
    now = datetime.datetime.now().isoformat()
    restore_comment = f"Restauración a partir del contenido de la versión v{target_v['version_number']}"

    cursor.execute('''
        INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Sin revisión')
    ''', (
        target_v["file_id"],
        new_v_num,
        current_user["id"],
        now,
        restore_comment,
        target_v["file_size"],
        target_v["mime_type"],
        target_v["content_hash"],
        target_v["storage_path"],
        target_v["content_text"]
    ))
    new_version_id = cursor.lastrowid

    cursor.execute('''
        UPDATE files 
        SET current_version_id = ?, updated_at = ?, is_locked = 0, locked_by_user_id = NULL, locked_at = NULL
        WHERE id = ?
    ''', (new_version_id, now, target_v["file_id"]))

    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="RESTAURAR_VERSION",
        target_type="ARCHIVO",
        target_id=target_v["file_id"],
        target_name=target_v["file_name"],
        details=f"Versión v{target_v['version_number']} restaurada como nueva versión vigente v{new_v_num}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {
        "message": f"Versión v{target_v['version_number']} restaurada exitosamente como versión vigente v{new_v_num}",
        "new_version_number": new_v_num,
        "new_version_id": new_version_id
    }

@router.post("/diff")
def compare_versions(data: DiffRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    va = conn.execute('''
        SELECT v.*, u.full_name as author_name, f.name as file_name
        FROM versions v
        JOIN files f ON v.file_id = f.id
        LEFT JOIN users u ON v.author_id = u.id
        WHERE v.id = ?
    ''', (data.version_a_id,)).fetchone()

    vb = conn.execute('''
        SELECT v.*, u.full_name as author_name, f.name as file_name
        FROM versions v
        JOIN files f ON v.file_id = f.id
        LEFT JOIN users u ON v.author_id = u.id
        WHERE v.id = ?
    ''', (data.version_b_id,)).fetchone()
    conn.close()

    if not va or not vb:
        raise HTTPException(status_code=404, detail="Una o ambas versiones no existen")

    # Metadata comparison
    metadata_diff = {
        "file_name": va["file_name"],
        "version_a": {
            "id": va["id"],
            "version_number": va["version_number"],
            "author": va["author_name"],
            "created_at": va["created_at"],
            "comment": va["comment"],
            "file_size": va["file_size"],
            "content_hash": va["content_hash"],
            "review_status": va["review_status"]
        },
        "version_b": {
            "id": vb["id"],
            "version_number": vb["version_number"],
            "author": vb["author_name"],
            "created_at": vb["created_at"],
            "comment": vb["comment"],
            "file_size": vb["file_size"],
            "content_hash": vb["content_hash"],
            "review_status": vb["review_status"]
        },
        "size_difference": vb["file_size"] - va["file_size"],
        "is_content_identical": (va["content_hash"] == vb["content_hash"])
    }

    # Text diff if content_text is available
    text_diff_lines = []
    text_a = va["content_text"] or ""
    text_b = vb["content_text"] or ""
    
    if text_a or text_b:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = difflib.unified_diff(
            lines_a, lines_b,
            fromfile=f"Versión v{va['version_number']}",
            tofile=f"Versión v{vb['version_number']}",
            lineterm=""
        )
        text_diff_lines = list(diff)

    return {
        "metadata": metadata_diff,
        "is_text": bool(text_a or text_b),
        "text_diff": text_diff_lines,
        "text_a": text_a,
        "text_b": text_b
    }
