import datetime
import os
import mimetypes
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse, Response
from backend.database import get_db_connection
from backend.auth import get_current_user, check_folder_permission
from backend.storage import store_binary_file, extract_text_content, verify_file_integrity
from backend.models import FileRename, FileMove
from backend.audit_helper import log_audit
from backend.config import MAX_UPLOAD_SIZE_BYTES

router = APIRouter(prefix="/api/v1/files", tags=["Archivos"])

@router.get("")
def list_files(
    folder_id: Optional[int] = None,
    search: Optional[str] = None,
    extension: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    content_query: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    query = '''
        SELECT f.id, f.folder_id, f.name, f.extension, f.current_version_id,
               f.is_locked, f.locked_by_user_id, f.locked_at, f.tags, f.category,
               f.created_at, f.updated_at,
               u_creator.full_name as created_by_name,
               u_locker.full_name as locked_by_name,
               v.version_number, v.file_size, v.comment, v.content_hash, v.review_status,
               fo.name as folder_name
        FROM files f
        LEFT JOIN users u_creator ON f.created_by_user_id = u_creator.id
        LEFT JOIN users u_locker ON f.locked_by_user_id = u_locker.id
        LEFT JOIN versions v ON f.current_version_id = v.id
        LEFT JOIN folders fo ON f.folder_id = fo.id
        WHERE f.is_in_trash = 0
    '''
    params = []

    if folder_id is not None and not search and not tag and not content_query:
        query += " AND f.folder_id = ?"
        params.append(folder_id)

    if search:
        query += " AND (f.name LIKE ? OR f.tags LIKE ? OR f.category LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])

    if extension:
        query += " AND LOWER(f.extension) = LOWER(?)"
        params.append(extension.strip().lstrip('.'))

    if author:
        query += " AND (u_creator.username LIKE ? OR u_creator.full_name LIKE ?)"
        params.extend([f"%{author}%", f"%{author}%"])

    if tag:
        query += " AND f.tags LIKE ?"
        params.append(f"%{tag.strip()}%")

    if content_query:
        query += " AND v.content_text LIKE ?"
        params.append(f"%{content_query.strip()}%")

    query += " ORDER BY f.updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        # Check folder read permission
        if check_folder_permission(current_user, r["folder_id"], "Lectura"):
            result.append(dict(r))
    return result

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    comment: str = Form("Versión inicial"),
    tags: Optional[str] = Form(""),
    category: Optional[str] = Form("General"),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == "Lector":
        raise HTTPException(status_code=403, detail="Los usuarios con rol Lector no tienen permisos para subir archivos")

    if not check_folder_permission(current_user, folder_id, "Edicion"):
        raise HTTPException(status_code=403, detail="No tienes permisos de edición en esta carpeta")

    filename = file.filename
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"El archivo excede el tamaño máximo permitido de 500 MB")

    content_hash, file_size, storage_path = store_binary_file(file_bytes)
    content_text = extract_text_content(filename, file_bytes)
    mime = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    now = datetime.datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if file with same name already exists in this folder
    existing_file = cursor.execute(
        "SELECT id, is_locked, locked_by_user_id FROM files WHERE folder_id IS ? AND name = ? AND is_in_trash = 0",
        (folder_id, filename)
    ).fetchone()

    client_ip = request.client.host if request and request.client else "127.0.0.1"

    if existing_file:
        file_id = existing_file["id"]
        # Check lock
        if existing_file["is_locked"] and existing_file["locked_by_user_id"] != current_user["id"]:
            locker = conn.execute("SELECT full_name FROM users WHERE id = ?", (existing_file["locked_by_user_id"],)).fetchone()
            locker_name = locker["full_name"] if locker else "otro usuario"
            conn.close()
            raise HTTPException(
                status_code=423,
                detail=f"El archivo está bloqueado para edición por {locker_name}. No se puede sobrescribir hasta que sea liberado."
            )

        # Get latest version number
        latest_v = cursor.execute(
            "SELECT MAX(version_number) FROM versions WHERE file_id = ?",
            (file_id,)
        ).fetchone()[0] or 1
        new_v_num = latest_v + 1

        # Atomic Insert of new Version (Immutable)
        cursor.execute('''
            INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Sin revisión')
        ''', (file_id, new_v_num, current_user["id"], now, comment.strip(), file_size, mime, content_hash, storage_path, content_text))
        new_version_id = cursor.lastrowid

        # Update file pointer to current version & release lock automatically!
        cursor.execute('''
            UPDATE files 
            SET current_version_id = ?, is_locked = 0, locked_by_user_id = NULL, locked_at = NULL, updated_at = ?
            WHERE id = ?
        ''', (new_version_id, now, file_id))

        conn.commit()
        conn.close()

        log_audit(
            username=current_user["username"],
            action="NUEVA_VERSION",
            target_type="ARCHIVO",
            target_id=file_id,
            target_name=filename,
            details=f"Nueva versión {new_v_num} creada. Comentario: {comment.strip()}. Bloqueo liberado.",
            user_id=current_user["id"],
            ip_address=client_ip
        )

        return {
            "file_id": file_id,
            "version_id": new_version_id,
            "version_number": new_v_num,
            "message": f"Nueva versión {new_v_num} subida con éxito y archivo desbloqueado.",
            "name": filename
        }

    else:
        # Create brand new file
        cursor.execute('''
            INSERT INTO files (folder_id, name, extension, current_version_id, is_locked, tags, category, created_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, NULL, 0, ?, ?, ?, ?, ?)
        ''', (folder_id, filename, ext, tags.strip() if tags else '', category.strip() if category else 'General', current_user["id"], now, now))
        file_id = cursor.lastrowid

        # Insert Version 1
        cursor.execute('''
            INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, 'Sin revisión')
        ''', (file_id, current_user["id"], now, comment.strip(), file_size, mime, content_hash, storage_path, content_text))
        v1_id = cursor.lastrowid

        # Link pointer
        cursor.execute("UPDATE files SET current_version_id = ? WHERE id = ?", (v1_id, file_id))
        conn.commit()
        conn.close()

        log_audit(
            username=current_user["username"],
            action="SUBIR_ARCHIVO",
            target_type="ARCHIVO",
            target_id=file_id,
            target_name=filename,
            details=f"Archivo creado con versión 1. Tamaño: {file_size} bytes. SHA-256: {content_hash}",
            user_id=current_user["id"],
            ip_address=client_ip
        )

        return {
            "file_id": file_id,
            "version_id": v1_id,
            "version_number": 1,
            "message": "Archivo y versión 1 registrados exitosamente",
            "name": filename
        }

@router.get("/{file_id}")
def get_file_detail(file_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute('''
        SELECT f.*, u.full_name as created_by_name,
               ul.full_name as locked_by_name, ul.username as locked_by_username,
               v.version_number, v.file_size, v.mime_type, v.content_hash, v.comment, v.created_at as version_created_at,
               fo.name as folder_name
        FROM files f
        LEFT JOIN users u ON f.created_by_user_id = u.id
        LEFT JOIN users ul ON f.locked_by_user_id = ul.id
        LEFT JOIN versions v ON f.current_version_id = v.id
        LEFT JOIN folders fo ON f.folder_id = fo.id
        WHERE f.id = ?
    ''', (file_id,)).fetchone()
    conn.close()

    if not f:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este archivo")

    return dict(f)

@router.get("/{file_id}/download")
def download_current_file(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute('''
        SELECT f.id, f.name, f.folder_id, v.storage_path, v.mime_type, v.content_hash, v.version_number
        FROM files f
        JOIN versions v ON f.current_version_id = v.id
        WHERE f.id = ? AND f.is_in_trash = 0
    ''', (file_id,)).fetchone()
    conn.close()

    if not f:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        raise HTTPException(status_code=403, detail="Permiso denegado")

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="DESCARGAR_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details=f"Descarga de la versión vigente v{f['version_number']}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return FileResponse(
        path=f["storage_path"],
        filename=f["name"],
        media_type=f["mime_type"] or "application/octet-stream"
    )

@router.post("/{file_id}/lock")
def lock_file(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "Lector":
        raise HTTPException(status_code=403, detail="Un usuario Lector no puede bloquear archivos para edición")

    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id, is_locked, locked_by_user_id FROM files WHERE id = ? AND is_in_trash = 0", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permisos insuficientes para editar en esta carpeta")

    if f["is_locked"]:
        if f["locked_by_user_id"] == current_user["id"]:
            conn.close()
            return {"message": "Ya tienes este archivo bloqueado", "is_locked": True}
        
        locker = conn.execute("SELECT full_name FROM users WHERE id = ?", (f["locked_by_user_id"],)).fetchone()
        locker_name = locker["full_name"] if locker else "otro usuario"
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=f"El archivo ya se encuentra bloqueado por {locker_name}. No puedes editarlo simultáneamente."
        )

    now = datetime.datetime.now().isoformat()
    conn.execute("UPDATE files SET is_locked = 1, locked_by_user_id = ?, locked_at = ? WHERE id = ?", (current_user["id"], now, file_id))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="BLOQUEAR_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details="Archivo bloqueado para edición exclusiva",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo bloqueado exitosamente para tu edición", "is_locked": True}

@router.post("/{file_id}/unlock")
def unlock_file(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, is_locked, locked_by_user_id FROM files WHERE id = ?", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not f["is_locked"]:
        conn.close()
        return {"message": "El archivo no estaba bloqueado", "is_locked": False}

    # Only owner of lock or Administrador can unlock
    is_admin = (current_user["role"] == "Administrador")
    if f["locked_by_user_id"] != current_user["id"] and not is_admin:
        conn.close()
        raise HTTPException(status_code=403, detail="Solo el usuario que bloqueó el archivo o un Administrador pueden desbloquearlo")

    conn.execute("UPDATE files SET is_locked = 0, locked_by_user_id = NULL, locked_at = NULL WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    action = "DESBLOQUEO_FORZADO" if (is_admin and f["locked_by_user_id"] != current_user["id"]) else "DESBLOQUEAR_ARCHIVO"
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action=action,
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details=f"Desbloqueo realizado por {current_user['username']} ({current_user['role']})",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo desbloqueado exitosamente", "is_locked": False}

@router.put("/{file_id}/rename")
def rename_file(file_id: int, data: FileRename, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id, is_locked, locked_by_user_id FROM files WHERE id = ? AND is_in_trash = 0", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso denegado")

    if f["is_locked"] and f["locked_by_user_id"] != current_user["id"] and current_user["role"] != "Administrador":
        conn.close()
        raise HTTPException(status_code=423, detail="No puedes renombrar un archivo bloqueado por otro usuario")

    new_name = data.new_name.strip()
    ext = new_name.split('.')[-1].lower() if '.' in new_name else f["extension"]
    conn.execute("UPDATE files SET name = ?, extension = ? WHERE id = ?", (new_name, ext, file_id))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="RENOMBRAR_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=new_name,
        details=f"Nombre anterior: {f['name']} -> Nuevo: {new_name}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo renombrado exitosamente", "new_name": new_name}

@router.put("/{file_id}/move")
def move_file(file_id: int, data: FileMove, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id, is_locked, locked_by_user_id FROM files WHERE id = ? AND is_in_trash = 0", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Edicion") or not check_folder_permission(current_user, data.target_folder_id, "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso de edición insuficiente en carpeta origen o destino")

    conn.execute("UPDATE files SET folder_id = ? WHERE id = ?", (data.target_folder_id, file_id))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="MOVER_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details=f"Movido a la carpeta ID {data.target_folder_id}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo movido exitosamente"}

# Trash bin (Papelera)
@router.post("/{file_id}/trash")
def move_to_trash(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id, is_locked, locked_by_user_id FROM files WHERE id = ? AND is_in_trash = 0", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar archivos en esta carpeta")

    if f["is_locked"] and f["locked_by_user_id"] != current_user["id"] and current_user["role"] != "Administrador":
        conn.close()
        raise HTTPException(status_code=423, detail="El archivo está bloqueado para edición por otro usuario")

    now = datetime.datetime.now().isoformat()
    conn.execute("UPDATE files SET is_in_trash = 1, trashed_at = ?, is_locked = 0 WHERE id = ?", (now, file_id))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="ENVIAR_PAPELERA",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details="Archivo movido a la papelera de reciclaje",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo movido a la papelera", "id": file_id}

@router.get("/trash/list")
def list_trash(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT f.id, f.name, f.extension, f.trashed_at, fo.name as original_folder_name,
               u.full_name as author_name, v.file_size, v.version_number
        FROM files f
        LEFT JOIN folders fo ON f.folder_id = fo.id
        LEFT JOIN users u ON f.created_by_user_id = u.id
        LEFT JOIN versions v ON f.current_version_id = v.id
        WHERE f.is_in_trash = 1
        ORDER BY f.trashed_at DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/trash/{file_id}/restore")
def restore_from_trash(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id FROM files WHERE id = ? AND is_in_trash = 1", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado en papelera")

    conn.execute("UPDATE files SET is_in_trash = 0, trashed_at = NULL WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="RESTAURAR_PAPELERA",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details="Archivo recuperado con todo su historial desde la papelera",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo restaurado de la papelera con éxito"}

@router.delete("/trash/{file_id}/purge")
def purge_file(file_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Administrador":
        raise HTTPException(status_code=403, detail="Solo un Administrador puede depurar permanentemente archivos de la papelera")

    conn = get_db_connection()
    f = conn.execute("SELECT id, name FROM files WHERE id = ? AND is_in_trash = 1", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="DEPURAR_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details="Eliminación permanente del archivo y su historial de versiones",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Archivo eliminado permanentemente"}
