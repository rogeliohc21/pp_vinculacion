"""
Modelo de Message
Mensajes entre estudiantes y administradores
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId  # ← IMPORTAR en lugar de definir


class MessageCreate(BaseModel):
    """Modelo para crear un mensaje"""
    asunto: str = Field(..., max_length=200)
    mensaje: str = Field(..., max_length=2000)
    categoria: str = Field(
        default="general",
        description="general, perfil, cv, vacante, otro"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "asunto": "Ayuda con mi perfil",
                "mensaje": "Necesito ayuda para completar mi perfil profesional. ¿Qué información es más importante?",
                "categoria": "perfil"
            }
        }


class MessageInDB(MessageCreate):
    """Modelo de mensaje en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    student_id: PyObjectId  # Estudiante que envía
    student_matricula: str  # Para búsquedas rápidas
    
    # Estado
    leido: bool = False
    fecha_envio: datetime = Field(default_factory=datetime.utcnow)
    fecha_leido: Optional[datetime] = None
    
    # Respuesta
    respondido: bool = False
    fecha_respuesta: Optional[datetime] = None
    respondido_por: Optional[PyObjectId] = None  # ID del admin
    respuesta: Optional[str] = None
    
    # Prioridad (establecida por admin)
    prioridad: str = Field(
        default="normal",
        description="baja, normal, alta, urgente"
    )
    
    # Estado del ticket
    estado: str = Field(
        default="abierto",
        description="abierto, en_proceso, resuelto, cerrado"
    )
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class MessageResponse(BaseModel):
    """Respuesta de mensaje"""
    id: str = Field(alias="_id")
    asunto: str
    mensaje: str
    categoria: str
    fecha_envio: datetime
    leido: bool
    respondido: bool
    respuesta: Optional[str]
    fecha_respuesta: Optional[datetime]
    estado: str
    prioridad: str
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "asunto": "Ayuda con mi perfil",
                "mensaje": "Necesito ayuda para completar mi perfil...",
                "categoria": "perfil",
                "fecha_envio": "2025-10-16T10:30:00",
                "leido": True,
                "respondido": True,
                "respuesta": "Hola, para completar tu perfil te recomiendo...",
                "fecha_respuesta": "2025-10-16T14:20:00",
                "estado": "resuelto",
                "prioridad": "normal"
            }
        }


class MessageAdminResponse(BaseModel):
    """Modelo para que admin responda mensaje"""
    respuesta: str = Field(..., max_length=2000)
    estado: Optional[str] = Field(None, description="en_proceso, resuelto, cerrado")
    prioridad: Optional[str] = Field(None, description="baja, normal, alta, urgente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "Hola, gracias por tu mensaje. Para mejorar tu perfil...",
                "estado": "resuelto",
                "prioridad": "normal"
            }
        }


class MessageUpdate(BaseModel):
    """Actualizar mensaje (admin)"""
    leido: Optional[bool] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None


class MessageList(BaseModel):
    """Lista de mensajes"""
    total: int
    sin_leer: int
    sin_responder: int
    mensajes: list
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 45,
                "sin_leer": 12,
                "sin_responder": 8,
                "mensajes": []
            }
        }


class MessageStats(BaseModel):
    """Estadísticas de mensajes (para admin)"""
    total_mensajes: int
    mensajes_sin_leer: int
    mensajes_sin_responder: int
    mensajes_abiertos: int
    mensajes_resueltos: int
    mensajes_urgentes: int
    tiempo_promedio_respuesta_horas: Optional[float] = None
    categorias_mas_comunes: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_mensajes": 150,
                "mensajes_sin_leer": 15,
                "mensajes_sin_responder": 10,
                "mensajes_abiertos": 20,
                "mensajes_resueltos": 100,
                "mensajes_urgentes": 3,
                "tiempo_promedio_respuesta_horas": 4.5,
                "categorias_mas_comunes": {
                    "perfil": 45,
                    "cv": 30,
                    "vacante": 25,
                    "general": 50
                }
            }
        }