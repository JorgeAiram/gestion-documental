import base64
import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from backend.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import get_db_connection

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = int(time.time()) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    header_json = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(',', ':')).encode('utf-8')
    
    encoded_header = base64.urlsafe_b64encode(header_json).rstrip(b'=').decode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(payload_json).rstrip(b'=').decode('utf-8')
    
    signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_signature = parts
        
        # Verify signature
        signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(encoded_signature + '=='[:(4 - len(encoded_signature) % 4) % 4])
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + '=='[:(4 - len(encoded_payload) % 4) % 4])
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if "exp" in payload and payload["exp"] < time.time():
            return None
            
        return payload
    except Exception:
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación no proporcionadas o formato inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o token inválido. Por favor inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    conn = get_db_connection()
    user = conn.execute("SELECT id, username, email, full_name, role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado",
        )
    
    return dict(user)

def require_role(*roles):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user["role"] not in roles and current_user["role"] != "Administrador":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Se requiere uno de los siguientes roles: {', '.join(roles)}",
            )
        return current_user
    return role_checker

def check_folder_permission(user: Dict[str, Any], folder_id: Optional[int], required_level: str) -> bool:
    """
    Check if user has required level in folder ('Lectura', 'Edicion', 'Administracion').
    Administrador role has full access everywhere.
    """
    if user["role"] == "Administrador":
        return True
    if folder_id is None:
        # Root folder: all authenticated users can view, but only Admin/Editor can create folders
        if required_level == "Lectura":
            return True
        return user["role"] in ["Administrador", "Editor"]

    hierarchy = ["Lectura", "Edicion", "Administracion"]
    req_idx = hierarchy.index(required_level)

    conn = get_db_connection()
    # Check direct user permission or role permission
    perms = conn.execute('''
        SELECT access_level FROM permissions 
        WHERE folder_id = ? AND (user_id = ? OR role = ?)
    ''', (folder_id, user["id"], user["role"])).fetchall()
    conn.close()

    if not perms:
        # Default behavior:
        # Lector can read everything by default unless restricted
        if user["role"] == "Lector" and required_level == "Lectura":
            return True
        # Editor can read and edit by default
        if user["role"] == "Editor" and req_idx <= 1:
            return True
        # Revisor can read and comment by default
        if user["role"] == "Revisor" and req_idx <= 0:
            return True
        return False

    max_idx = -1
    for p in perms:
        lvl = p["access_level"]
        if lvl in hierarchy:
            max_idx = max(max_idx, hierarchy.index(lvl))
            
    return max_idx >= req_idx
