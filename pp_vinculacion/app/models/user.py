"""
Modelo de Usuario
Define la estructura del usuario base para autenticación
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId  # ← IMPORTAR en lugar de definir


class UserBase(BaseModel):
    """Campos base del usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(..., description="estudiante, empresa, o admin")
    is_active: bool = True
    email_verified: bool = False


class UserCreate(UserBase):
    """Modelo para crear usuario (con contraseña)"""
    password: str = Field(..., min_length=8, max_length=128)  # aumentamos a 128 chars para dar más flexibilidad


class UserLogin(BaseModel):
    """Modelo para login"""
    username: str
    password: str


class UserInDB(UserBase):
    """Modelo de usuario en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    mfa_secret: Optional[str] = None  # Para autenticación de dos factores
    mfa_enabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "email": "estudiante@universidad.edu.mx",
                "username": "juan_perez",
                "role": "estudiante",
                "is_active": True
            }
        }


class UserResponse(UserBase):
    """Modelo de respuesta (sin contraseña)"""
    id: str = Field(alias="_id")
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "estudiante@universidad.edu.mx",
                "username": "juan_perez",
                "role": "estudiante",
                "is_active": True,
                "created_at": "2025-10-16T10:30:00"
            }
        }


class Token(BaseModel):
    """Modelo de token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos dentro del token"""
    username: Optional[str] = None
    role: Optional[str] = None