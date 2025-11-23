"""
Helpers de autenticación (hashing, tokens y dependencia get_current_user).
Separamos esta lógica desde los routers para mejorar organización y testabilidad.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import logging
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.config import settings
from app.database import get_users_collection
from app.models.user import UserInDB, TokenData

logger = logging.getLogger(__name__)

# Configuración específica de bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    bcrypt__default_rounds=12,
    deprecated="auto"
)

# OAuth2 scheme usado en la aplicación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña: bcrypt(password[:72])"""
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password: str) -> str:
    """Generar hash de contraseña: bcrypt(password[:72])"""
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT de acceso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crear token JWT de refresco"""
    # Generate a unique token id (jti) so we can persist / revoke refresh tokens
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    iat = datetime.utcnow()
    expire = iat + timedelta(days=settings.refresh_token_expire_days)
    # include standard claims
    to_encode.update({"exp": expire, "iat": iat, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    # return both token and its jti so callers can persist metadata
    return encoded_jwt, jti


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Dependencia para obtener el usuario actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    users = await get_users_collection()
    user = await users.find_one({"username": username})

    if user is None:
        raise credentials_exception

    # Normalizar a modelo pydantic
    return UserInDB(**user)
