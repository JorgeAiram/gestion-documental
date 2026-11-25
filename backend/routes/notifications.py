from fastapi import APIRouter, HTTPException, Depends
from backend.database import get_db_connection
from backend.auth import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notificaciones"])

@router.get("")
def list_notifications(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    notes = conn.execute('''
        SELECT n.id, n.title, n.message, n.link, n.is_read, n.created_at,
               u.full_name as sender_name
        FROM notifications n
        LEFT JOIN users u ON n.sender_id = u.id
        WHERE n.recipient_id = ?
        ORDER BY n.created_at DESC
        LIMIT 50
    ''', (current_user["id"],)).fetchall()
    
    unread_count = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0",
        (current_user["id"],)
    ).fetchone()[0]
    conn.close()

    return {
        "notifications": [dict(n) for n in notes],
        "unread_count": unread_count
    }

@router.put("/{notification_id}/read")
def mark_as_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND recipient_id = ?",
        (notification_id, current_user["id"])
    )
    conn.commit()
    conn.close()
    return {"message": "Notificación marcada como leída"}

@router.put("/read-all")
def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE recipient_id = ?",
        (current_user["id"],)
    )
    conn.commit()
    conn.close()
    return {"message": "Todas las notificaciones marcadas como leídas"}
