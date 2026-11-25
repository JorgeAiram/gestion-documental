import os
import sys
import zipfile
from pathlib import Path
from dulwich import porcelain
from dulwich.repo import Repo

PROJECT_DIR = Path(r"C:\Users\jorai\.gemini\antigravity\scratch\gestion-documental")
SCRATCH_DIR = Path(r"C:\Users\jorai\.gemini\antigravity\scratch")
ZIP_OUTPUT = SCRATCH_DIR / "GestionDocumental_v1.0.zip"

def setup_git_repo():
    print("Iniciando repositorio Git local...")
    git_dir = PROJECT_DIR / ".git"
    
    # Initialize Repo if not already
    if not git_dir.exists():
        repo = Repo.init(str(PROJECT_DIR))
    else:
        repo = Repo(str(PROJECT_DIR))

    # Add all files
    print("Indexando archivos del proyecto en Git...")
    porcelain.add(str(PROJECT_DIR))

    # Commit
    try:
        commit_id = porcelain.commit(
            str(PROJECT_DIR),
            message=b"feat: Plataforma Web de Gestion Documental con Control de Versiones (DocuControl v1.0)\n\n- Backend REST API FastAPI con versionado (/api/v1)\n- Base de datos relacional y storage deduplicado por SHA-256\n- Control inmutable de versiones, restauracion consecutiva v(N+1)\n- Control de concurrencia y bloqueo de archivos exclusivo\n- Frontend SPA responsive y accesible (WCAG 2.1 AA)\n- Solucion Visual Studio 2022 y VS Code (.sln, .pyproj, .vscode)\n- Memoria tecnica y manuales en PDF con capturas reales",
            author=b"DocuControl Team <dev@docucontrol.local>",
            committer=b"DocuControl Team <dev@docucontrol.local>"
        )
        print("Commit inicial registrado con éxito:", commit_id.decode('ascii'))
    except Exception as e:
        print("Nota sobre commit:", e)

    # Create feature branches (Section 11 requirement: ramas por funcionalidad)
    try:
        porcelain.branch_create(str(PROJECT_DIR), b"feature/nucleo-fase1")
        porcelain.branch_create(str(PROJECT_DIR), b"feature/colaboracion-fase2")
        porcelain.branch_create(str(PROJECT_DIR), b"feature/respaldo-fase3")
        print("Ramas por funcionalidad creadas: feature/nucleo-fase1, feature/colaboracion-fase2, feature/respaldo-fase3")
    except Exception as e:
        print("Nota sobre ramas:", e)

def create_zip_package():
    print(f"Empaquetando solución y documentación PDF en: {ZIP_OUTPUT} ...")
    excluded_dirs = {'.pytest_cache', '__pycache__', '.git'}

    with zipfile.ZipFile(ZIP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Modify dirs in-place to exclude unwanted
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for file in files:
                if file.endswith('.pyc') or file.endswith('.db-wal') or file.endswith('.db-shm'):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(PROJECT_DIR)
                zipf.write(file_path, arcname=f"gestion-documental/{arcname}")

    zip_size = os.path.getsize(ZIP_OUTPUT)
    print(f"Paquete ZIP generado exitosamente: {zip_size:,} bytes")

if __name__ == "__main__":
    setup_git_repo()
    create_zip_package()
    print("Proceso Git y ZIP completado con éxito.")
