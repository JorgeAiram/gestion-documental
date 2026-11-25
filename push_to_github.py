import sys
import getpass
from pathlib import Path
from dulwich import porcelain
from dulwich.repo import Repo

PROJECT_DIR = Path(__file__).resolve().parent

def push_to_github():
    print("=" * 60)
    print("  SUBIDA DEL CÓDIGO A GITHUB (DOCUCONTROL v1.0)")
    print("=" * 60)
    
    repo_url = input("Ingresa la URL de tu repositorio en GitHub (ej: https://github.com/usuario/gestion-documental.git): ").strip()
    if not repo_url:
        print("Operación cancelada. No se ingresó URL.")
        return

    token = getpass.getpass("Ingresa tu GitHub Personal Access Token (con permisos de 'repo'): ").strip()
    if not token:
        print("Operación cancelada. Se requiere un token de acceso.")
        return

    # Format authenticated URL
    if repo_url.startswith("https://"):
        clean_url = repo_url[8:]
        auth_url = f"https://oauth2:{token}@{clean_url}"
    else:
        auth_url = repo_url

    print("\nConectando con GitHub y subiendo ramas...")
    try:
        porcelain.push(str(PROJECT_DIR), auth_url, b"refs/heads/master:refs/heads/main")
        print("\n[ÉXITO] ¡Código subido correctamente a GitHub en la rama 'main'!")
    except Exception as e:
        print(f"\n[ERROR] No se pudo completar la subida: {e}")
        print("\nAlternativa manual:")
        print(f"1. git remote add origin {repo_url}")
        print("2. git branch -M main")
        print("3. git push -u origin main")

if __name__ == "__main__":
    push_to_github()
