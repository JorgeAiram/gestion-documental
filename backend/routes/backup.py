import os
import shutil
import zipfile
import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import FileResponse
from backend.database import get_db_connection, DB_PATH
from backend.auth import require_role
from backend.config import BACKUP_DIR, STORAGE_DIR
from backend.audit_helper import log_audit

router = APIRouter(prefix="/api/v1/backup", tags=["Respaldos y Restauración"])

@router.post("/create")
def create_backup(request: Request, current_user: dict = Depends(require_role("Administrador"))):
    """
    Creates a full backup containing the SQLite database and all binary files.
    RF-21: Respaldo programado / manual y restauración desde interfaz de administración.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"dms_backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename

    # Create backup zip
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Database file (safe checkpoint copy)
        if DB_PATH.exists():
            # Run checkpoint first
            conn = get_db_connection()
            conn.execute("PRAGMA wal_checkpoint(FULL);")
            conn.close()
            zip_file.write(DB_PATH, arcname="database/dms.db")
        
        # 2. Binary Storage files
        for root, _, files in os.walk(STORAGE_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = f"storage/{file}"
                zip_file.write(file_path, arcname=arcname)

    backup_size = os.path.getsize(backup_path)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="CREAR_RESPALDO",
        target_type="SISTEMA",
        target_name=backup_filename,
        details=f"Respaldo completo generado con éxito. Tamaño: {backup_size} bytes",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return {
        "message": "Respaldo generado exitosamente",
        "filename": backup_filename,
        "size_bytes": backup_size,
        "created_at": datetime.datetime.now().isoformat()
    }

@router.get("/list")
def list_backups(current_user: dict = Depends(require_role("Administrador"))):
    backups = []
    for f in BACKUP_DIR.glob("*.zip"):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups

@router.get("/download/{filename}")
def download_backup(filename: str, request: Request, current_user: dict = Depends(require_role("Administrador"))):
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Archivo de respaldo no encontrado")

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="DESCARGAR_RESPALDO",
        target_type="SISTEMA",
        target_name=filename,
        details="Descarga de archivo de respaldo por el Administrador",
        user_id=current_user["id"],
        ip_address=client_ip
    )

    return FileResponse(path=backup_path, filename=filename, media_type="application/zip")

@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: dict = Depends(require_role("Administrador"))
):
    temp_zip = BACKUP_DIR / f"temp_restore_{secrets_token()}.zip"
    try:
        content = await file.read()
        with open(temp_zip, "wb") as f:
            f.write(content)

        # Validate ZIP
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            namelist = zf.namelist()
            if "database/dms.db" not in namelist:
                raise HTTPException(status_code=400, detail="El archivo no es un respaldo válido de la plataforma (falta database/dms.db)")

            # Extract storage files
            for member in namelist:
                if member.startswith("storage/"):
                    zf.extract(member, BACKUP_DIR / "temp_extract")
            
            # Extract db
            zf.extract("database/dms.db", BACKUP_DIR / "temp_extract")

        # Replace storage
        extracted_storage = BACKUP_DIR / "temp_extract" / "storage"
        if extracted_storage.exists():
            for s_file in extracted_storage.glob("*"):
                shutil.copy2(s_file, STORAGE_DIR / s_file.name)

        # Replace database
        extracted_db = BACKUP_DIR / "temp_extract" / "database" / "dms.db"
        if extracted_db.exists():
            shutil.copy2(extracted_db, DB_PATH)

        # Clean temp
        shutil.rmtree(BACKUP_DIR / "temp_extract", ignore_errors=True)
        if temp_zip.exists():
            temp_zip.unlink()

        client_ip = request.client.host if request and request.client else "127.0.0.1"
        log_audit(
            username=current_user["username"],
            action="RESTAURACION_SISTEMA",
            target_type="SISTEMA",
            target_name=file.filename,
            details="Restauración exitosa de base de datos y almacén de archivos",
            user_id=current_user["id"],
            ip_address=client_ip
        )

        return {"message": "Sistema restaurado correctamente a partir del respaldo"}

    except Exception as e:
        if temp_zip.exists():
            temp_zip.unlink()
        shutil.rmtree(BACKUP_DIR / "temp_extract", ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error durante la restauración: {str(e)}")

def secrets_token():
    import secrets
    return secrets.token_hex(4)
