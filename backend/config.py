import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
BACKUP_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "dms.db"

# Ensure essential directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Security and limits
SECRET_KEY = os.environ.get("DMS_SECRET_KEY", "super-secret-key-gestion-documental-2026-secure-token")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours
MAX_UPLOAD_SIZE_MB = 500
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
LOCK_TIMEOUT_HOURS = 24
TRASH_RETENTION_DAYS = 30
