import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from backend.database import get_db_connection
from backend.auth import get_current_user, require_role, check_folder_permission
from backend.models import ReviewCreate
from backend.audit_helper import log_audit, create_notification

router = APIRouter(prefix="/api/v1/reviews", tags=["Revisión Opcional"])

@router.post("/version/{version_id}/request")
def request_optional_review(version_id: int, reviewer_id: int, current_user: dict = Depends(get_current_user)):
    """
    RF-16: Revisión opcional. Un editor pide a un revisor que verifique una versión.
    Nunca es requisito previo ni bloquea la consulta o descarga.
    """
    conn = get_db_connection()
    v = conn.execute('''
        SELECT v.id, v.version_number, v.file_id, f.name as file_name, f.folder_id
        FROM versions v
        JOIN files f ON v.file_id = f.id
        WHERE v.id = ?
    ''', (version_id,)).fetchone()

    if not v:
        conn.close()
        raise HTTPException(status_code=404, detail="Versión no encontrada")

    if not check_folder_permission(current_user, v["folder_id"], "Edicion"):
        conn.close()
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

    # Update version status to 'Pendiente'
    conn.execute("UPDATE versions SET review_status = 'Pendiente' WHERE id = ?", (version_id,))
    conn.commit()
    conn.close()

    create_notification(
        recipient_id=reviewer_id,
        title=f"Solicitud de revisión opcional",
        message=f"{current_user['full_name']} te solicita revisar la versión v{v['version_number']} de '{v['file_name']}'.",
        sender_id=current_user["id"],
        link=f"/files/{v['file_id']}"
    )

    return {"message": "Solicitud de revisión enviada al revisor"}

@router.post("/version/{version_id}")
def submit_review(version_id: int, data: ReviewCreate, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Revisor marks the version as 'Revisado' or 'Con observaciones' with notes.
    """
    if current_user["role"] not in ["Revisor", "Administrador"]:
        raise HTTPException(status_code=403, detail="Solo usuarios con rol Revisor o Administrador pueden registrar revisiones")

    if data.status not in ["Revisado", "Con observaciones"]:
        raise HTTPException(status_code=400, detail="El estado debe ser 'Revisado' o 'Con observaciones'")

    conn = get_db_connection()
    v = conn.execute('''
        SELECT v.id, v.version_number, v.file_id, v.author_id, f.name as file_name
        FROM versions v
        JOIN files f ON v.file_id = f.id
        WHERE v.id = ?
    ''', (version_id,)).fetchone()

    if not v:
        conn.close()
        raise HTTPException(status_code=404, detail="Versión no encontrada")

    now = datetime.datetime.now().isoformat()
    conn.execute('''
        UPDATE versions
        SET review_status = ?, reviewed_by_user_id = ?, reviewed_at = ?, review_notes = ?
        WHERE id = ?
    ''', (data.status, current_user["id"], now, data.notes or "", version_id))
    conn.commit()

    # Notify author
    if v["author_id"] != current_user["id"]:
        create_notification(
            recipient_id=v["author_id"],
            title=f"Versión v{v['version_number']} {data.status}",
            message=f"{current_user['full_name']} marcó la versión como '{data.status}'. Observaciones: {data.notes or 'Ninguna'}",
            sender_id=current_user["id"],
            link=f"/files/{v['file_id']}"
        )

    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="REVISION_VERSION",
        target_type="VERSION",
        target_id=version_id,
        target_name=f"{v['file_name']} (v{v['version_number']})",
        details=f"Estado de revisión: {data.status}. Notas: {data.notes}",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {"message": f"Revisión registrada como '{data.status}'"}
