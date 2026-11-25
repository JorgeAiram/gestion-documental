import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from backend.database import get_db_connection
from backend.auth import get_current_user, check_folder_permission, require_role
from backend.models import FolderCreate, FolderUpdate, PermissionCreate
from backend.audit_helper import log_audit

router = APIRouter(prefix="/api/v1/folders", tags=["Carpetas"])

@router.get("")
def list_folders(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    folders = conn.execute('''
        SELECT f.id, f.name, f.parent_id, f.owner_id, f.created_at, u.full_name as owner_name,
               (SELECT COUNT(*) FROM files WHERE folder_id = f.id AND is_in_trash = 0) as file_count
        FROM folders f
        LEFT JOIN users u ON f.owner_id = u.id
        ORDER BY f.name ASC
    ''').fetchall()
    conn.close()
    
    # Filter folders user has at least read permission
    accessible = []
    for f in folders:
        if check_folder_permission(current_user, f["id"], "Lectura"):
            accessible.append(dict(f))
    return accessible

@router.post("", status_code=status.HTTP_201_CREATED)
def create_folder(data: FolderCreate, request: Request, current_user: dict = Depends(get_current_user)):
    if not check_folder_permission(current_user, data.parent_id, "Edicion"):
        raise HTTPException(status_code=403, detail="No tienes permisos para crear carpetas en esta ubicación")

    now = datetime.datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO folders (name, parent_id, owner_id, created_at)
        VALUES (?, ?, ?, ?)
    ''', (data.name.strip(), data.parent_id, current_user["id"], now))
    folder_id = cursor.lastrowid
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="CREAR_CARPETA",
        target_type="CARPETA",
        target_id=folder_id,
        target_name=data.name,
        details=f"Carpeta creada con padre ID {data.parent_id}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"id": folder_id, "name": data.name, "parent_id": data.parent_id, "created_at": now}

@router.put("/{folder_id}")
def update_folder(folder_id: int, data: FolderUpdate, request: Request, current_user: dict = Depends(get_current_user)):
    if not check_folder_permission(current_user, folder_id, "Edicion"):
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta carpeta")

    conn = get_db_connection()
    folder = conn.execute("SELECT id, name, parent_id FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if not folder:
        conn.close()
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    updates = []
    params = []
    if data.name:
        updates.append("name = ?")
        params.append(data.name.strip())
    if data.parent_id is not None:
        if data.parent_id == folder_id:
            conn.close()
            raise HTTPException(status_code=400, detail="Una carpeta no puede ser su propio padre")
        updates.append("parent_id = ?")
        params.append(data.parent_id if data.parent_id > 0 else None)

    if updates:
        params.append(folder_id)
        conn.execute(f"UPDATE folders SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="EDITAR_CARPETA",
        target_type="CARPETA",
        target_id=folder_id,
        target_name=data.name or folder["name"],
        details="Carpeta renombrada o movida",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Carpeta actualizada correctamente"}

@router.delete("/{folder_id}")
def delete_folder(folder_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    if not check_folder_permission(current_user, folder_id, "Administracion"):
        raise HTTPException(status_code=403, detail="Se requiere permiso de Administración para eliminar una carpeta")

    conn = get_db_connection()
    # Check if folder has active files
    files = conn.execute("SELECT COUNT(*) FROM files WHERE folder_id = ? AND is_in_trash = 0", (folder_id,)).fetchone()[0]
    if files > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="No se puede eliminar una carpeta que contiene archivos activos. Muévelos o elimínalos primero.")

    folder = conn.execute("SELECT id, name FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if not folder:
        conn.close()
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="ELIMINAR_CARPETA",
        target_type="CARPETA",
        target_id=folder_id,
        target_name=folder["name"],
        details="Carpeta eliminada permanentemente",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": "Carpeta eliminada"}

# Permissions for folders
@router.get("/{folder_id}/permissions")
def get_folder_permissions(folder_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    perms = conn.execute('''
        SELECT p.id, p.folder_id, p.user_id, p.role, p.access_level, p.created_at,
               u.username, u.full_name
        FROM permissions p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.folder_id = ?
    ''', (folder_id,)).fetchall()
    conn.close()
    return [dict(p) for p in perms]

@router.post("/{folder_id}/permissions")
def set_folder_permission(folder_id: int, data: PermissionCreate, request: Request, current_user: dict = Depends(require_role("Administrador"))):
    conn = get_db_connection()
    now = datetime.datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO permissions (folder_id, user_id, role, access_level, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (folder_id, data.user_id, data.role, data.access_level, now))
    perm_id = cursor.lastrowid
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="ASIGNAR_PERMISO",
        target_type="CARPETA",
        target_id=folder_id,
        details=f"Permiso {data.access_level} otorgado a user_id={data.user_id} o rol={data.role}",
        user_id=current_user["id"],
        ip_address=client_ip
    )
    return {"id": perm_id, "status": "Permiso asignado"}
