"""
Modelo de Match
Resultado del matching entre estudiante y vacante
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId  # ← IMPORTAR en lugar de definir


class MatchDesglose(BaseModel):
    """Desglose detallado del matching"""
    habilidades_tecnicas: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de habilidades técnicas (0-1)"
    )
    habilidades_blandas: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de habilidades blandas (0-1)"
    )
    idiomas: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de idiomas (0-1)"
    )
    experiencia: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de experiencia (0-1)"
    )
    carrera: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de carrera (0-1)"
    )
    semestre: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de semestre (0-1)"
    )
    modalidad: float = Field(
        ...,
        ge=0,
        le=1,
        description="Score de modalidad de trabajo (0-1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "habilidades_tecnicas": 0.95,
                "habilidades_blandas": 0.85,
                "idiomas": 0.90,
                "experiencia": 0.75,
                "carrera": 1.0,
                "semestre": 1.0,
                "modalidad": 1.0
            }
        }


class MatchCreate(BaseModel):
    """Modelo para crear un match"""
    vacancy_id: str
    student_matricula: str
    porcentaje_match: float = Field(..., ge=0, le=100)
    desglose: MatchDesglose


class MatchInDB(MatchCreate):
    """Modelo de match en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    vacancy_id: PyObjectId
    student_matricula: str  # Solo matrícula, NO ObjectId para privacidad
    
    # Matching
    porcentaje_match: float = Field(..., ge=0, le=100)
    desglose: MatchDesglose
    
    # Similitud de embeddings (IA)
    embedding_similarity: Optional[float] = None
    
    # Fechas
    fecha_match: datetime = Field(default_factory=datetime.utcnow)
    
    # Estado
    visto_por_empresa: bool = False
    fecha_visto: Optional[datetime] = None
    
    # Para gráfica de araña
    radar_chart_data: Optional[Dict[str, float]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class MatchResponse(BaseModel):
    """Respuesta de match para la empresa"""
    id: str = Field(alias="_id")
    student_matricula: str  # Solo matrícula (anónimo)
    porcentaje_match: float
    desglose: MatchDesglose
    fecha_match: datetime
    
    # Datos anónimos del estudiante
    carrera: str
    semestre: int
    habilidades_tecnicas: List[str]
    habilidades_blandas: List[str]
    idiomas: List[Dict[str, str]]
    tiene_experiencia: bool
    modalidad_preferida: str
    
    # Gráfica de araña (para visualización)
    radar_chart_data: Dict[str, float]
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "student_matricula": "A01234567",
                "porcentaje_match": 87.5,
                "desglose": {
                    "habilidades_tecnicas": 0.95,
                    "habilidades_blandas": 0.85,
                    "idiomas": 0.90,
                    "experiencia": 0.75,
                    "carrera": 1.0,
                    "semestre": 1.0,
                    "modalidad": 1.0
                },
                "fecha_match": "2025-10-16T10:30:00",
                "carrera": "Ingeniería en Sistemas",
                "semestre": 8,
                "habilidades_tecnicas": ["Python", "React", "FastAPI"],
                "habilidades_blandas": ["Trabajo en equipo", "Comunicación"],
                "idiomas": [{"idioma": "Inglés", "nivel": "B2"}],
                "tiene_experiencia": True,
                "modalidad_preferida": "Híbrido",
                "radar_chart_data": {
                    "Habilidades Técnicas": 95,
                    "Habilidades Blandas": 85,
                    "Idiomas": 90,
                    "Experiencia": 75,
                    "Carrera": 100,
                    "Semestre": 100,
                    "Modalidad": 100
                }
            }
        }


class MatchListResponse(BaseModel):
    """Lista de matches para una vacante"""
    vacancy_id: str
    vacancy_titulo: str
    total_matches: int
    matches: List[MatchResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "vacancy_id": "507f1f77bcf86cd799439011",
                "vacancy_titulo": "Desarrollador Full Stack Junior",
                "total_matches": 15,
                "matches": []
            }
        }


class RadarChartData(BaseModel):
    """Datos para gráfica de araña (Spider/Radar Chart)"""
    categories: List[str] = [
        "Habilidades Técnicas",
        "Habilidades Blandas",
        "Idiomas",
        "Experiencia",
        "Carrera",
        "Semestre",
        "Modalidad"
    ]
    valores_requeridos: List[float]  # Lo que pide la vacante (100%)
    valores_candidato: List[float]   # Lo que tiene el candidato
    
    class Config:
        json_schema_extra = {
            "example": {
                "categories": [
                    "Habilidades Técnicas",
                    "Habilidades Blandas",
                    "Idiomas",
                    "Experiencia",
                    "Carrera",
                    "Semestre",
                    "Modalidad"
                ],
                "valores_requeridos": [100, 100, 100, 100, 100, 100, 100],
                "valores_candidato": [95, 85, 90, 75, 100, 100, 100]
            }
        }