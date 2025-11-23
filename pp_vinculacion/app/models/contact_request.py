"""
Modelo de ContactRequest
Solicitud de contacto de empresa a estudiante
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId  # ← IMPORTAR en lugar de definir


class ContactRequestCreate(BaseModel):
    """Modelo para crear solicitud de contacto"""
    vacancy_id: str
    student_matricula: str
    motivo: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo de la solicitud (opcional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "vacancy_id": "507f1f77bcf86cd799439011",
                "student_matricula": "A01234567",
                "motivo": "El perfil del candidato es ideal para nuestro equipo"
            }
        }


class ContactRequestInDB(ContactRequestCreate):
    """Modelo de solicitud en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vacancy_id: PyObjectId
    company_id: PyObjectId  # Empresa que solicita
    student_matricula: str
    
    # Estado de la solicitud
    estado: str = Field(
        default="pendiente",
        description="pendiente, aprobada, rechazada"
    )
    
    # Fechas
    fecha_solicitud: datetime = Field(default_factory=datetime.utcnow)
    fecha_respuesta: Optional[datetime] = None
    
    # Respuesta del admin
    respondido_por: Optional[PyObjectId] = None  # ID del admin que respondió
    comentario_admin: Optional[str] = None
    
    # Motivo del rechazo (si aplica)
    motivo_rechazo: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ContactRequestUpdate(BaseModel):
    """Modelo para que admin actualice solicitud"""
    estado: str = Field(..., description="aprobada o rechazada")
    comentario_admin: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "estado": "aprobada",
                "comentario_admin": "Empresa verificada, candidato notificado"
            }
        }


class ContactRequestResponse(BaseModel):
    """Respuesta de solicitud de contacto"""
    id: str = Field(alias="_id")
    vacancy_titulo: str
    company_nombre: str
    student_matricula: str
    estado: str
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime]
    motivo: Optional[str]
    comentario_admin: Optional[str]
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "vacancy_titulo": "Desarrollador Full Stack Junior",
                "company_nombre": "Tech Solutions SA",
                "student_matricula": "A01234567",
                "estado": "pendiente",
                "fecha_solicitud": "2025-10-16T10:30:00",
                "fecha_respuesta": None,
                "motivo": "Perfil ideal para el equipo",
                "comentario_admin": None
            }
        }


class StudentContactInfo(BaseModel):
    """Información de contacto del estudiante (SOLO si solicitud aprobada)"""
    matricula: str
    nombre_completo: str
    email: str
    telefono: str
    carrera: str
    semestre: int
    cv_url: Optional[str] = None
    
    # Datos de contacto adicionales
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portafolio: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "matricula": "A01234567",
                "nombre_completo": "Juan Pérez García",
                "email": "juan.perez@universidad.edu.mx",
                "telefono": "5512345678",
                "carrera": "Ingeniería en Sistemas Computacionales",
                "semestre": 8,
                "cv_url": "/uploads/cvs/A01234567.pdf"
            }
        }


class ContactRequestList(BaseModel):
    """Lista de solicitudes de contacto"""
    total: int
    pendientes: int
    aprobadas: int
    rechazadas: int
    solicitudes: list
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 25,
                "pendientes": 10,
                "aprobadas": 12,
                "rechazadas": 3,
                "solicitudes": []
            }
        }