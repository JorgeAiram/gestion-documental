from typing import Optional, List
from pydantic import BaseModel, Field

# Auth models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "Editor"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

# Folder models
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None

class PermissionCreate(BaseModel):
    folder_id: int
    user_id: Optional[int] = None
    role: Optional[str] = None
    access_level: str  # 'Lectura', 'Edicion', 'Administracion'

# File models
class FileRename(BaseModel):
    new_name: str

class FileMove(BaseModel):
    target_folder_id: Optional[int] = None

class FileLock(BaseModel):
    reason: Optional[str] = "En edición por el usuario"

class FileCommentCreate(BaseModel):
    text: str
    version_id: Optional[int] = None

class ReviewCreate(BaseModel):
    status: str  # 'Revisado', 'Con observaciones'
    notes: Optional[str] = ""

class ShareCreate(BaseModel):
    file_id: int
    expires_in_hours: int = 72

class DiffRequest(BaseModel):
    version_a_id: int
    version_b_id: int
