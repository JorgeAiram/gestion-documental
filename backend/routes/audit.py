from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.database import get_db_connection
from backend.auth import get_current_user, require_role

router = APIRouter(prefix="/api/v1/audit", tags=["Bitácora de Auditoría"])

@router.get("")
def get_audit_log(
    action: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_role("Administrador"))
):
    conn = get_db_connection()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if action:
        query += " AND action = ?"
        params.append(action)

    if username:
        query += " AND username LIKE ?"
        params.append(f"%{username}%")

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    logs = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(log) for log in logs]
