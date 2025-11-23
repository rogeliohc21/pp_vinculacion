""""
Modelo de Vacante
Define las ofertas laborales de las empresas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId  # ← IMPORTAR en lugar de definir


class IdiomaRequerido(BaseModel):
    """Idioma requerido para la vacante"""
    idioma: str
    nivel_minimo: str  # Basico, Intermedio, Avanzado
    
    class Config:
        json_schema_extra = {
            "example": {
                "idioma": "Inglés",
                "nivel_minimo": "Basico"
            }
        }


class Requisito(BaseModel):
    """Requisito específico"""
    descripcion: str
    es_indispensable: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "descripcion": "Experiencia con APIs REST",
                "es_indispensable": True
            }
        }


class VacancyCreate(BaseModel):
    """Modelo para crear una vacante"""
    # Información básica
    titulo: str = Field(..., description="Título del puesto")
    area: str = Field(..., description="Área o departamento")
    descripcion: str = Field(..., description="Descripción detallada del puesto")
    
    # Requisitos
    carrera_requerida: List[str] = Field(
        default_factory=list,
        description="Carreras aceptadas (vacío = todas)"
    )
    semestre_minimo: Optional[int] = Field(None, ge=1, le=12)
    promedio_minimo: Optional[float] = Field(None, ge=0, le=10)
    
    habilidades_tecnicas_requeridas: List[str] = Field(default_factory=list)
    habilidades_tecnicas_deseables: List[str] = Field(default_factory=list)
    habilidades_blandas_requeridas: List[str] = Field(default_factory=list)
    
    idiomas_requeridos: List[IdiomaRequerido] = Field(default_factory=list)
    
    experiencia_minima: str = Field(
        default="Sin experiencia",
        description="Sin experiencia, Menos de 1 año, 1-2 años, etc."
    )
    
    otros_requisitos: List[Requisito] = Field(default_factory=list)
    
    # Oferta
    tipo_contrato: str = Field(
        ...,
        description="Tiempo completo, Medio tiempo, Por proyecto, Prácticas, Becario"
    )
    modalidad: str = Field(
        ...,
        description="Presencial, Remoto, Híbrido"
    )
    
    salario_minimo: Optional[float] = None
    salario_maximo: Optional[float] = None
    salario_oculto: bool = False  # Si no quiere mostrar salario
    
    # Beneficios específicos del puesto
    beneficios: List[str] = Field(default_factory=list)
    
    # Ubicación (si es presencial o híbrido)
    ubicacion_ciudad: Optional[str] = None
    ubicacion_estado: Optional[str] = None
    
    # Horario
    horario: Optional[str] = None
    
    # Duración (si es temporal)
    duracion_meses: Optional[int] = None
    
    # Fecha límite para aplicar
    fecha_cierre: Optional[datetime] = None
    
    # Responsabilidades
    responsabilidades: List[str] = Field(default_factory=list)
    
    # Número de vacantes
    num_vacantes: int = Field(default=1, ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Desarrollador Full Stack Junior",
                "area": "Desarrollo de Software",
                "descripcion": "Buscamos desarrollador para proyecto de e-commerce",
                "carrera_requerida": ["Ingeniería en Sistemas", "Ingeniería en Software"],
                "semestre_minimo": 7,
                "promedio_minimo": 8.0,
                "habilidades_tecnicas_requeridas": ["Python", "JavaScript", "React"],
                "habilidades_tecnicas_deseables": ["Docker", "AWS"],
                "habilidades_blandas_requeridas": ["Trabajo en equipo", "Comunicación"],
                "idiomas_requeridos": [
                    {"idioma": "Inglés", "nivel_minimo": "Basico"}
                ],
                "experiencia_minima": "Menos de 1 año",
                "tipo_contrato": "Tiempo completo",
                "modalidad": "Híbrido",
                "salario_minimo": 15000,
                "salario_maximo": 20000,
                "beneficios": ["Seguro médico", "Capacitaciones", "Home office"],
                "ubicacion_ciudad": "Ciudad de México",
                "ubicacion_estado": "CDMX",
                "horario": "Lunes a Viernes 9:00-18:00",
                "responsabilidades": [
                    "Desarrollar features del sistema",
                    "Realizar code reviews",
                    "Documentar código"
                ],
                "num_vacantes": 2
            }
        }


class VacancyInDB(VacancyCreate):
    """Modelo de vacante en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    company_id: PyObjectId  # Referencia a la empresa
    
    # Estado
    estado: str = Field(
        default="activa",
        description="activa, cerrada, borrador"
    )
    
    # Fechas
    fecha_publicacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)
    
    # Embeddings para matching (generados por IA)
    vacancy_embedding: Optional[List[float]] = None
    
    # Estadísticas
    num_visualizaciones: int = 0
    num_candidatos_matched: int = 0
    num_solicitudes_contacto: int = 0
    
    # Candidatos que ya han sido contactados (para no volver a mostrarlos)
    candidatos_contactados: List[str] = Field(
        default_factory=list,
        description="Lista de matrículas"
    )
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class VacancyUpdate(BaseModel):
    """Modelo para actualizar vacante"""
    titulo: Optional[str] = None
    area: Optional[str] = None
    descripcion: Optional[str] = None
    habilidades_tecnicas_requeridas: Optional[List[str]] = None
    habilidades_tecnicas_deseables: Optional[List[str]] = None
    habilidades_blandas_requeridas: Optional[List[str]] = None
    tipo_contrato: Optional[str] = None
    modalidad: Optional[str] = None
    salario_minimo: Optional[float] = None
    salario_maximo: Optional[float] = None
    beneficios: Optional[List[str]] = None
    horario: Optional[str] = None
    responsabilidades: Optional[List[str]] = None
    estado: Optional[str] = None


class VacancyPublic(BaseModel):
    """Vacante pública (lo que ven los estudiantes)"""
    id: str = Field(alias="_id")
    titulo: str
    area: str
    descripcion: str
    empresa_nombre: str  # Se obtiene de la empresa
    tipo_contrato: str
    modalidad: str
    salario_visible: bool
    salario_rango: Optional[str] = None  # "15,000 - 20,000"
    beneficios: List[str]
    ubicacion: Optional[str] = None
    habilidades_requeridas: List[str]
    fecha_publicacion: datetime
    num_vacantes: int
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "titulo": "Desarrollador Full Stack Junior",
                "area": "Desarrollo de Software",
                "descripcion": "Buscamos desarrollador...",
                "empresa_nombre": "Tech Solutions SA",
                "tipo_contrato": "Tiempo completo",
                "modalidad": "Híbrido",
                "salario_visible": True,
                "salario_rango": "$15,000 - $20,000",
                "beneficios": ["Seguro médico", "Home office"],
                "ubicacion": "Ciudad de México, CDMX",
                "habilidades_requeridas": ["Python", "React"],
                "fecha_publicacion": "2025-10-16T10:30:00",
                "num_vacantes": 2
            }
        }