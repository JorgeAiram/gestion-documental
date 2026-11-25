import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from backend.database import get_db_connection, hash_password
from backend.auth import get_current_user, require_role
from backend.models import UserCreate, UserUpdate
from backend.audit_helper import log_audit

router = APIRouter(prefix="/api/v1/users", tags=["Usuarios"])

@router.get("")
def list_users(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, username, email, full_name, role, is_active, created_at FROM users ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, request: Request, current_user: dict = Depends(require_role("Administrador"))):
    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (data.username, data.email)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este nombre de usuario o correo electrónico"
        )
    
    now = datetime.datetime.now().isoformat()
    pwd_hash = hash_password(data.password)
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, email, full_name, password_hash, role, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
    ''', (data.username, data.email, data.full_name, pwd_hash, data.role, now))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="CREAR_USUARIO",
        target_type="USUARIO",
        target_id=new_id,
        target_name=data.username,
        details=f"Creación de usuario con rol {data.role}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"id": new_id, "username": data.username, "full_name": data.full_name, "role": data.role}

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, request: Request, current_user: dict = Depends(require_role("Administrador"))):
    conn = get_db_connection()
    user = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    updates = []
    params = []
    if data.full_name is not None:
        updates.append("full_name = ?")
        params.append(data.full_name)
    if data.email is not None:
        updates.append("email = ?")
        params.append(data.email)
    if data.role is not None:
        updates.append("role = ?")
        params.append(data.role)
    if data.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if data.is_active else 0)
    if data.password:
        updates.append("password_hash = ?")
        params.append(hash_password(data.password))

    if updates:
        params.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="EDITAR_USUARIO",
        target_type="USUARIO",
        target_id=user_id,
        target_name=user["username"],
        details=f"Actualización de campos del usuario ID {user_id}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Usuario actualizado correctamente"}

@router.delete("/{user_id}")
def delete_user(user_id: int, request: Request, current_user: dict = Depends(require_role("Administrador"))):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta de administrador")

    conn = get_db_connection()
    user = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Soft delete or deactivate to preserve history integrity
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="DESACTIVAR_USUARIO",
        target_type="USUARIO",
        target_id=user_id,
        target_name=user["username"],
        details="Usuario desactivado del sistema",
        user_id=current_user["id"],
        ip_address=client_ip
    )
    return {"message": "Usuario desactivado correctamente"}
