"""
Modelo de Empresa
Define el perfil de una empresa
"""
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId


class CompanyProfile(BaseModel):
    """Perfil de la empresa"""
    # Información básica
    nombre_empresa: str = Field(..., description="Razón social de la empresa")
    rfc: str = Field(..., description="RFC de la empresa")
    giro: str = Field(..., description="Sector o industria")
    tamano: str = Field(
        ...,
        description="Micro, Pequeña, Mediana, Grande, Corporativo"
    )
    
    # Información de contacto
    email_contacto: EmailStr
    telefono: str
    sitio_web: Optional[HttpUrl] = None
    
    # Ubicación
    direccion: str
    ciudad: str
    estado: str
    codigo_postal: str
    
    # Descripción
    descripcion: str = Field(..., max_length=1000)
    
    # Redes sociales
    linkedin: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    
    # Beneficios que ofrece
    beneficios: List[str] = Field(default_factory=list)
    
    # Logo (URL o path)
    logo_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre_empresa": "Tech Solutions SA de CV",
                "rfc": "TSO123456ABC",
                "giro": "Tecnología de la Información",
                "tamano": "Mediana",
                "email_contacto": "rh@techsolutions.com",
                "telefono": "5555551234",
                "sitio_web": "https://www.techsolutions.com",
                "direccion": "Av. Principal 123",
                "ciudad": "Ciudad de México",
                "estado": "CDMX",
                "codigo_postal": "01000",
                "descripcion": "Empresa líder en desarrollo de software",
                "beneficios": ["Seguro médico", "Home office", "Bonos"],
                "linkedin": "https://linkedin.com/company/techsolutions"
            }
        }


# Alias para compatibilidad con routers
CompanyCreate = CompanyProfile


class CompanyInDB(CompanyProfile):
    """Modelo de empresa en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId  # Referencia al User
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Estado
    verificada: bool = False  # Admin verifica que es empresa legítima
    activa: bool = True
    fecha_verificacion: Optional[datetime] = None
    
    # Estadísticas
    num_vacantes_publicadas: int = 0
    num_candidatos_contactados: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CompanyUpdate(BaseModel):
    """Modelo para actualizar perfil de empresa"""
    nombre_empresa: Optional[str] = None
    giro: Optional[str] = None
    tamano: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = None
    sitio_web: Optional[HttpUrl] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    descripcion: Optional[str] = None
    beneficios: Optional[List[str]] = None
    linkedin: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    logo_url: Optional[str] = None


class CompanyResponse(BaseModel):
    """Respuesta de empresa (para API)"""
    id: str = Field(alias="_id")
    nombre_empresa: str
    rfc: str
    giro: str
    tamano: str
    email_contacto: EmailStr
    telefono: str
    ciudad: str
    estado: str
    codigo_postal: str
    direccion: str
    descripcion: str
    sitio_web: Optional[HttpUrl] = None
    logo_url: Optional[str] = None
    beneficios: List[str]
    verificada: bool
    fecha_verificacion: Optional[datetime] = None
    created_at: datetime
    num_vacantes_publicadas: int = 0
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "nombre_empresa": "Tech Solutions SA",
                "rfc": "TSO123456ABC",
                "giro": "Tecnología",
                "tamano": "Mediana",
                "email_contacto": "rh@techsolutions.com",
                "telefono": "5555551234",
                "ciudad": "Ciudad de México",
                "estado": "CDMX",
                "codigo_postal": "01000",
                "direccion": "Av. Principal 123",
                "descripcion": "Empresa líder en desarrollo de software",
                "sitio_web": "https://www.techsolutions.com",
                "logo_url": None,
                "beneficios": ["Seguro médico", "Home office"],
                "verificada": True,
                "fecha_verificacion": "2025-10-16T10:00:00",
                "created_at": "2025-10-01T08:00:00",
                "num_vacantes_publicadas": 5
            }
        }


class CompanyPublicProfile(BaseModel):
    """Perfil público de la empresa (lo que ven los estudiantes)"""
    nombre_empresa: str
    giro: str
    tamano: str
    ciudad: str
    estado: str
    descripcion: str
    sitio_web: Optional[HttpUrl]
    beneficios: List[str]
    logo_url: Optional[str]
    verificada: bool
    num_vacantes_activas: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre_empresa": "Tech Solutions SA",
                "giro": "Tecnología",
                "tamano": "Mediana",
                "ciudad": "Ciudad de México",
                "estado": "CDMX",
                "descripcion": "Empresa líder en desarrollo de software",
                "sitio_web": "https://www.techsolutions.com",
                "beneficios": ["Seguro médico", "Home office"],
                "verificada": True,
                "num_vacantes_activas": 5
            }
        }