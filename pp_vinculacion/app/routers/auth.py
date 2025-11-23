"""
Router de Autenticación
Endpoints para registro, login, y gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import pyotp
import qrcode
import hashlib
from io import BytesIO
import base64
from jose import JWTError, jwt

from app.models.user import (
    UserCreate,
    UserLogin,
    UserInDB,
    UserResponse,
    Token,
    TokenData
)
from app.database import get_users_collection
from app.config import settings
from app.database import get_refresh_tokens_collection

# Importaremos estos cuando creemos el módulo de seguridad
# from app.security.auth import (
#     get_password_hash,
#     verify_password,
#     create_access_token,
#     create_refresh_token,
#     get_current_user
# )

router = APIRouter()


# Mover helpers de autenticación a módulo de seguridad
from app.security.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
)

# Rate limiter
from app.limiter import limiter


# ============= ENDPOINTS =============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: settings.auth_register_limit)
async def register(request: Request, user: UserCreate):
    """
    Registrar nuevo usuario
    
    - **email**: Email válido
    - **username**: Nombre de usuario único (3-50 caracteres)
    - **password**: Contraseña (mínimo 8 caracteres)
    - **role**: estudiante, empresa, o admin
    """
    print(f"\nAttempting to register user: {user.json()}")
    users = await get_users_collection()
    
    # Verificar si el usuario ya existe
    existing_user = await users.find_one({
        "$or": [
            {"email": user.email},
            {"username": user.username}
        ]
    })
    if existing_user:
        print(f"Found existing user: {existing_user}")
    
    if existing_user:
        if existing_user.get("email") == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Validar rol
    valid_roles = ["estudiante", "empresa", "admin"]
    if user.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Crear usuario
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user.password)
    del user_dict["password"]
    user_dict["created_at"] = datetime.utcnow()
    user_dict["mfa_enabled"] = False
    
    result = await users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    return UserResponse(**user_dict)


@router.post("/login", response_model=Token)
@limiter.limit(lambda: settings.auth_login_limit)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login de usuario
    
    Retorna access_token y refresh_token
    """
    users = await get_users_collection()
    
    # Buscar usuario
    user = await users.find_one({"username": form_data.username})
    
    if not user or not verify_password(form_data.password, user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si está activo
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Verificar MFA si está habilitado
    if user.get("mfa_enabled", False):
        # En este caso, retornamos un token temporal que requiere MFA
        # Por ahora lo omitimos para simplificar
        pass
    
    # Crear tokens
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    refresh_token, jti = create_refresh_token(
        data={"sub": user["username"]}
    )

    # Persist refresh token metadata so it can be revoked/rotated
    refresh_tokens = await get_refresh_tokens_collection()
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(days=settings.refresh_token_expire_days)
    try:
        await refresh_tokens.insert_one({
            "jti": jti,
            "user_id": user["_id"],
            "username": user["username"],
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked": False,
        })
    except Exception:
        # If persistence fails, log but continue to return tokens (avoid breaking login flow)
        # The token will be valid until it expires server-side; however, revocation won't work
        pass
    
    # Actualizar último login
    await users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    
    Requiere autenticación
    """
    user_dict = current_user.dict()
    user_dict["_id"] = str(current_user.id)
    return UserResponse(**user_dict)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refrescar access token usando refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if username is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    users = await get_users_collection()
    user = await users.find_one({"username": username})
    
    if user is None:
        raise credentials_exception
    
    # Verify refresh token exists and not revoked
    refresh_tokens = await get_refresh_tokens_collection()
    token_record = await refresh_tokens.find_one({"jti": jti, "revoked": False})
    if not token_record:
        raise credentials_exception

    # Crear nuevos tokens (rotation)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    new_refresh_token, new_jti = create_refresh_token(
        data={"sub": user["username"]}
    )

    # Persist new refresh token and revoke old one
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(days=settings.refresh_token_expire_days)
    try:
        await refresh_tokens.insert_one({
            "jti": new_jti,
            "user_id": user["_id"],
            "username": user["username"],
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked": False,
        })
        await refresh_tokens.update_one({"jti": jti}, {"$set": {"revoked": True}})
    except Exception:
        # If DB operations fail, still continue but revocation/rotation may not be recorded
        pass
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(refresh_token: str):
    """
    Revoke a refresh token (logout).
    The client should send the refresh token to be revoked.
    """
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        jti: str = payload.get("jti")
        if jti is None:
            return {"message": "Invalid token"}
    except JWTError:
        return {"message": "Invalid token"}

    refresh_tokens = await get_refresh_tokens_collection()
    result = await refresh_tokens.update_one({"jti": jti}, {"$set": {"revoked": True}})
    if result.modified_count:
        return {"message": "Refresh token revoked"}
    else:
        return {"message": "Token not found or already revoked"}


@router.post("/setup-mfa")
async def setup_mfa(current_user: UserInDB = Depends(get_current_user)):
    """
    Configurar autenticación de dos factores (MFA)
    
    Retorna QR code para escanear con Google Authenticator
    """
    users = await get_users_collection()
    
    # Generar secreto MFA
    secret = pyotp.random_base32()
    
    # Crear URL para QR
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name=settings.university_name
    )
    
    # Generar QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Guardar secreto (pero no activar aún)
    await users.update_one(
        {"_id": current_user.id},
        {"$set": {"mfa_secret": secret}}
    )
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{img_str}",
        "message": "Scan the QR code with Google Authenticator and verify with /verify-mfa"
    }


@router.post("/verify-mfa")
async def verify_mfa(
    token: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Verificar código MFA y activar
    """
    users = await get_users_collection()
    
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up. Call /setup-mfa first"
        )
    
    # Verificar token
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )
    
    # Activar MFA
    await users.update_one(
        {"_id": current_user.id},
        {"$set": {"mfa_enabled": True}}
    )
    
    return {"message": "MFA enabled successfully"}


@router.post("/disable-mfa")
async def disable_mfa(
    password: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Desactivar MFA (requiere contraseña)
    """
    users = await get_users_collection()
    
    # Verificar contraseña
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Desactivar MFA
    await users.update_one(
        {"_id": current_user.id},
        {"$set": {
            "mfa_enabled": False,
            "mfa_secret": None
        }}
    )
    
    return {"message": "MFA disabled successfully"}


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Cambiar contraseña
    """
    users = await get_users_collection()
    
    # Verificar contraseña actual
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Validar nueva contraseña
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Actualizar contraseña
    new_hashed_password = get_password_hash(new_password)
    await users.update_one(
        {"_id": current_user.id},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    return {"message": "Password changed successfully"}
