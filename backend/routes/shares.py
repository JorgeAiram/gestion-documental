import datetime
import secrets
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from backend.database import get_db_connection
from backend.auth import get_current_user, check_folder_permission
from backend.models import ShareCreate
from backend.audit_helper import log_audit

router = APIRouter(prefix="/api/v1/shares", tags=["Enlaces Compartidos"])

@router.post("")
def create_share_link(data: ShareCreate, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id FROM files WHERE id = ? AND is_in_trash = 0", (data.file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso denegado")

    token = secrets.token_urlsafe(32)
    now = datetime.datetime.now()
    expires_at = (now + datetime.timedelta(hours=data.expires_in_hours)).isoformat()

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shared_links (file_id, token, created_by_user_id, expires_at, created_at, access_count)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (data.file_id, token, current_user["id"], expires_at, now.isoformat()))
    share_id = cursor.lastrowid
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="GENERAR_ENLACE",
        target_type="ARCHIVO",
        target_id=data.file_id,
        target_name=f["name"],
        details=f"Enlace de consulta temporal generado con vencimiento {expires_at}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {
        "share_id": share_id,
        "token": token,
        "expires_at": expires_at,
        "share_url": f"/share/{token}"
    }

@router.get("/public/{token}/download")
def download_shared_file(token: str, request: Request):
    conn = get_db_connection()
    share = conn.execute('''
        SELECT s.*, f.name as file_name, v.storage_path, v.mime_type
        FROM shared_links s
        JOIN files f ON s.file_id = f.id
        JOIN versions v ON f.current_version_id = v.id
        WHERE s.token = ?
    ''', (token,)).fetchone()

    if not share:
        conn.close()
        raise HTTPException(status_code=404, detail="Enlace no válido o inexistente")

    now = datetime.datetime.now().isoformat()
    if share["expires_at"] < now:
        conn.close()
        raise HTTPException(status_code=410, detail="Este enlace de consulta ha vencido")

    # Increment counter
    conn.execute("UPDATE shared_links SET access_count = access_count + 1 WHERE id = ?", (share["id"],))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username="INVITADO_ENLACE",
        action="DESCARGA_PUBLICA",
        target_type="ARCHIVO",
        target_id=share["file_id"],
        target_name=share["file_name"],
        details=f"Descarga mediante enlace compartido público token {token[:8]}...",
        ip_address=client_ip
    )

    return FileResponse(
        path=share["storage_path"],
        filename=share["file_name"],
        media_type=share["mime_type"] or "application/octet-stream"
    )
