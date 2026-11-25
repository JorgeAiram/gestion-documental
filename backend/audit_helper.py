import datetime
from typing import Optional
from backend.database import get_db_connection

def log_audit(
    username: str,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    target_name: Optional[str] = None,
    details: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: str = "127.0.0.1"
):
    try:
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            INSERT INTO audit_log (user_id, username, action, target_type, target_id, target_name, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, action, target_type, target_id, target_name, details, ip_address, now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit: {e}")

def create_notification(
    recipient_id: int,
    title: str,
    message: str,
    sender_id: Optional[int] = None,
    link: Optional[str] = None
):
    try:
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            INSERT INTO notifications (recipient_id, sender_id, title, message, link, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (recipient_id, sender_id, title, message, link, now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating notification: {e}")
