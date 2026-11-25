import datetime
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from backend.database import get_db_connection
from backend.auth import get_current_user, check_folder_permission
from backend.models import FileCommentCreate
from backend.audit_helper import log_audit, create_notification

router = APIRouter(prefix="/api/v1/comments", tags=["Comentarios y Menciones"])

@router.get("/file/{file_id}")
def get_file_comments(file_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT folder_id FROM files WHERE id = ?", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso denegado")

    comments = conn.execute('''
        SELECT c.id, c.file_id, c.version_id, c.text, c.created_at,
               u.id as author_id, u.full_name as author_name, u.username as author_username, u.role as author_role,
               v.version_number
        FROM comments c
        JOIN users u ON c.author_id = u.id
        LEFT JOIN versions v ON c.version_id = v.id
        WHERE c.file_id = ?
        ORDER BY c.created_at ASC
    ''', (file_id,)).fetchall()
    conn.close()

    return [dict(c) for c in comments]

@router.post("/file/{file_id}")
def add_comment(file_id: int, data: FileCommentCreate, request: Request, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    f = conn.execute("SELECT id, name, folder_id, created_by_user_id FROM files WHERE id = ?", (file_id,)).fetchone()
    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    if not check_folder_permission(current_user, f["folder_id"], "Lectura"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permiso denegado")

    now = datetime.datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO comments (file_id, version_id, author_id, text, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (file_id, data.version_id, current_user["id"], data.text.strip(), now))
    comment_id = cursor.lastrowid
    conn.commit()

    # Detect user mentions: e.g. @username or @carlos.editor
    mentions = re.findall(r"@([a-zA-Z0-9_\.]+)", data.text)
    for mentioned_username in set(mentions):
        u = conn.execute("SELECT id FROM users WHERE username = ?", (mentioned_username,)).fetchone()
        if u and u["id"] != current_user["id"]:
            create_notification(
                recipient_id=u["id"],
                title=f"Mención de {current_user['full_name']}",
                message=f"Te mencionó en un comentario de '{f['name']}': \"{data.text[:80]}...\"",
                sender_id=current_user["id"],
                link=f"/files/{file_id}"
            )

    # Notify file owner if different from commenter
    if f["created_by_user_id"] != current_user["id"]:
        create_notification(
            recipient_id=f["created_by_user_id"],
            title=f"Nuevo comentario en '{f['name']}'",
            message=f"{current_user['full_name']} comentó: \"{data.text[:80]}...\"",
            sender_id=current_user["id"],
            link=f"/files/{file_id}"
        )

    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="COMENTAR_ARCHIVO",
        target_type="ARCHIVO",
        target_id=file_id,
        target_name=f["name"],
        details=f"Comentario agregado: {data.text[:100]}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"id": comment_id, "message": "Comentario registrado con éxito"}
