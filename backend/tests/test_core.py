import pytest
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, get_db_connection, DB_PATH
from backend.config import STORAGE_DIR

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    # Ensure fresh test database
    init_db()
    yield

def get_auth_token(username="admin", password="admin123"):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_login_success():
    token = get_auth_token("admin", "admin123")
    assert token is not None

def test_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401

def test_list_folders():
    token = get_auth_token("admin", "admin123")
    response = client.get("/api/v1/folders", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) >= 5

def test_version_control_and_immutability():
    token = get_auth_token("carlos.editor", "editor123")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload initial file
    content_v1 = b"Contenido version 1 para prueba unitaria"
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("test_doc.txt", content_v1, "text/plain")},
        data={"folder_id": 1, "comment": "Subida v1 inicial", "tags": "test,unitario"},
        headers=headers
    )
    assert response.status_code == 200
    file_id = response.json()["file_id"]
    assert response.json()["version_number"] == 1

    # 2. Upload version 2 of the same file
    content_v2 = b"Contenido version 2 modificado y mejorado"
    response2 = client.post(
        "/api/v1/files/upload",
        files={"file": ("test_doc.txt", content_v2, "text/plain")},
        data={"folder_id": 1, "comment": "Actualizacion a v2 con cambios"},
        headers=headers
    )
    assert response2.status_code == 200
    assert response2.json()["version_number"] == 2

    # 3. Check history: both versions must exist (immutability)
    history_res = client.get(f"/api/v1/versions/file/{file_id}", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["version_number"] == 2  # Current
    assert history[1]["version_number"] == 1  # Previous

    # 4. Test version restoration: restoring v1 must create v3 (Scenario 4 of acceptance criteria)
    v1_id = history[1]["id"]
    restore_res = client.post(f"/api/v1/versions/{v1_id}/restore", headers=headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["new_version_number"] == 3

    # Check updated history has 3 versions intact
    history_res2 = client.get(f"/api/v1/versions/file/{file_id}", headers=headers)
    assert len(history_res2.json()) == 3

def test_file_locking_mechanics():
    editor_token = get_auth_token("carlos.editor", "editor123")
    revisor_token = get_auth_token("elena.revisora", "revisora123")

    # 1. Carlos uploads a file
    res = client.post(
        "/api/v1/files/upload",
        files={"file": ("contrato_confidencial.txt", b"Texto de contrato", "text/plain")},
        data={"folder_id": 1, "comment": "Borrador de contrato"},
        headers={"Authorization": f"Bearer {editor_token}"}
    )
    file_id = res.json()["file_id"]

    # 2. Carlos locks the file for exclusive editing
    lock_res = client.post(f"/api/v1/files/{file_id}/lock", headers={"Authorization": f"Bearer {editor_token}"})
    assert lock_res.status_code == 200

    # 3. Another user attempts to upload a new version: must be rejected with 423 Locked!
    collision_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("contrato_confidencial.txt", b"Intento de sobreescritura", "text/plain")},
        data={"folder_id": 1, "comment": "Sobreescribiendo sin permiso"},
        headers={"Authorization": f"Bearer {revisor_token}"}
    )
    assert collision_res.status_code == 423
    assert "bloqueado" in collision_res.json()["detail"].lower()

    # 4. Carlos uploads new version -> Lock automatically released!
    success_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("contrato_confidencial.txt", b"Texto oficial actualizado", "text/plain")},
        data={"folder_id": 1, "comment": "Version final por el autor"},
        headers={"Authorization": f"Bearer {editor_token}"}
    )
    assert success_res.status_code == 200

    # Check file is now unlocked
    detail_res = client.get(f"/api/v1/files/{file_id}", headers={"Authorization": f"Bearer {editor_token}"})
    assert detail_res.json()["is_locked"] == 0

def test_reader_role_restrictions():
    # Lector cannot upload or delete
    lector_token = get_auth_token("mario.lector", "lector123")
    headers = {"Authorization": f"Bearer {lector_token}"}

    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("intento_lector.txt", b"No autorizado", "text/plain")},
        data={"folder_id": 1, "comment": "Intento"},
        headers=headers
    )
    assert upload_res.status_code == 403

def test_trash_and_recovery():
    token = get_auth_token("admin", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload file
    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("archivo_papelera.txt", b"Para borrar", "text/plain")},
        data={"folder_id": 1, "comment": "Para borrar"},
        headers=headers
    )
    file_id = upload_res.json()["file_id"]

    # Send to trash
    trash_res = client.post(f"/api/v1/files/{file_id}/trash", headers=headers)
    assert trash_res.status_code == 200

    # Verify in trash list
    list_res = client.get("/api/v1/files/trash/list", headers=headers)
    assert any(item["id"] == file_id for item in list_res.json())

    # Restore from trash
    restore_res = client.post(f"/api/v1/files/trash/{file_id}/restore", headers=headers)
    assert restore_res.status_code == 200

    # Verify back in active files
    active_res = client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert active_res.status_code == 200
    assert active_res.json()["is_in_trash"] == 0

def test_audit_log_registered():
    admin_token = get_auth_token("admin", "admin123")
    audit_res = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    actions = [log["action"] for log in logs]
    assert "LOGIN_EXITOSO" in actions
