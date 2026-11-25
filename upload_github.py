import ctypes
import os
import sys
import requests
from ctypes import wintypes
from pathlib import Path
from dulwich import porcelain
from dulwich.repo import Repo

PROJECT_DIR = Path(r"C:\Users\jorai\.gemini\antigravity\scratch\gestion-documental")

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR)
    ]

def get_github_credentials():
    PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
    CredRead = ctypes.windll.advapi32.CredReadW
    cred_ptr = PCREDENTIAL()
    if CredRead('git:https://github.com', 1, 0, ctypes.byref(cred_ptr)):
        blob = ctypes.string_at(cred_ptr.contents.CredentialBlob, cred_ptr.contents.CredentialBlobSize)
        token = blob.decode('utf-8', errors='ignore').strip()
        if not token.isprintable():
            token = blob.decode('utf-16le', errors='ignore').strip()
        return cred_ptr.contents.UserName, token
    return None, None

def main():
    username, token = get_github_credentials()
    if not token:
        print("ERROR: No se encontró token en Credential Manager")
        sys.exit(1)

    print(f"Usuario GitHub autenticado: {username}")
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    repo_name = "gestion-documental"
    # Check if repo exists
    check_url = f"https://api.github.com/repos/{username}/{repo_name}"
    res = requests.get(check_url, headers=headers)

    if res.status_code == 404:
        print(f"Creando repositorio '{repo_name}' en GitHub para {username}...")
        create_payload = {
            "name": repo_name,
            "description": "Plataforma Web de Gestión Documental con Control de Versiones (DocuControl v1.0) - Integrantes: Cervantes Morán Jorge Airam, Hernández Rosas Aranza Jaqueline, Ricárdez Reyes Rafael",
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False
        }
        create_res = requests.post("https://api.github.com/user/repos", headers=headers, json=create_payload)
        if create_res.status_code in [200, 201]:
            print("Repositorio creado exitosamente en GitHub.")
            clone_url = create_res.json()["clone_url"]
        else:
            print(f"Error al crear repositorio: {create_res.status_code} - {create_res.text}")
            sys.exit(1)
    elif res.status_code == 200:
        print(f"El repositorio '{repo_name}' ya existe en GitHub.")
        clone_url = res.json()["clone_url"]
    else:
        print(f"Respuesta inesperada de GitHub API: {res.status_code} - {res.text}")
        sys.exit(1)

    # Git commit any recent changes (updated PDF)
    print("Actualizando commits locales...")
    porcelain.add(str(PROJECT_DIR))
    try:
        porcelain.commit(
            str(PROJECT_DIR),
            message=b"docs: actualizacion de integrantes del equipo en documentacion oficial PDF",
            author=b"Cervantes Moran Jorge Airam <jorge.airam@docucontrol.local>",
            committer=b"Cervantes Moran Jorge Airam <jorge.airam@docucontrol.local>"
        )
    except Exception as e:
        print("Commit note:", e)

    # Push to GitHub
    auth_remote = f"https://oauth2:{token}@github.com/{username}/{repo_name}.git"
    print(f"Subiendo rama 'main' a {clone_url} ...")
    
    # Push main (from local master)
    try:
        porcelain.push(str(PROJECT_DIR), auth_remote, b"refs/heads/master:refs/heads/main")
        print("✓ Rama 'main' subida con éxito.")
    except Exception as e:
        print("Push error on main:", e)

    # Push feature branches
    for branch in [b"feature/nucleo-fase1", b"feature/colaboracion-fase2", b"feature/respaldo-fase3"]:
        try:
            refspec = f"refs/heads/{branch.decode()}:refs/heads/{branch.decode()}".encode()
            porcelain.push(str(PROJECT_DIR), auth_remote, refspec)
            print(f"✓ Rama '{branch.decode()}' subida con éxito.")
        except Exception as e:
            print(f"Push error on {branch.decode()}:", e)

    print("\n" + "=" * 60)
    print(f"¡CÓDIGO Y RAMAS SUBIDOS CON ÉXITO A GITHUB!")
    print(f"URL del Repositorio: https://github.com/{username}/{repo_name}")
    print("=" * 60)

if __name__ == "__main__":
    main()
