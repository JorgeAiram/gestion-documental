from fastapi import APIRouter, HTTPException, Depends, Request, status
from backend.database import get_db_connection, verify_password
from backend.auth import create_access_token, get_current_user
from backend.models import LoginRequest, TokenResponse
from backend.audit_helper import log_audit
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest, request: Request):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, email, full_name, password_hash, role, is_active FROM users WHERE username = ?",
        (creds.username,)
    ).fetchone()
    conn.close()

    client_ip = request.client.host if request.client else "127.0.0.1"

    if not user or not verify_password(creds.password, user["password_hash"]):
        log_audit(
            username=creds.username,
            action="LOGIN_FALLIDO",
            target_type="USUARIO",
            details="Intento de acceso con credenciales incorrectas",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo. Contacte al administrador.",
        )

    token = create_access_token({
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"]
    })

    log_audit(
        username=user["username"],
        action="LOGIN_EXITOSO",
        target_type="USUARIO",
        target_id=user["id"],
        target_name=user["full_name"],
        details=f"Inicio de sesión exitoso con rol {user['role']}",
        user_id=user["id"],
        ip_address=client_ip
    )

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(request: Request, current_user: dict = Depends(get_current_user)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit(
        username=current_user["username"],
        action="LOGOUT",
        target_type="USUARIO",
        target_id=current_user["id"],
        target_name=current_user["full_name"],
        details="Cierre de sesión seguro",
        user_id=current_user["id"],
        ip_address=client_ip
    )
    return {"message": "Sesión cerrada correctamente"}
