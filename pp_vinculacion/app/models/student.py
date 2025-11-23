"""
Modelo de Estudiante
Define el perfil completo de un estudiante
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.base import PyObjectId


#class PyObjectId(ObjectId):
#    @classmethod
#    def __get_validators__(cls):
#        yield cls.validate

#    @classmethod
#    def validate(cls, v):
#        if not ObjectId.is_valid(v):
#            raise ValueError("Invalid ObjectId")
#        return ObjectId(v)

#    @classmethod
#    def __get_pydantic_json_schema__(cls, field_schema):
#        field_schema.update(type="string")


class Idioma(BaseModel):
    """Idioma y nivel"""
    idioma: str = Field(..., description="Nombre del idioma")
    nivel: str = Field(..., description="Basico, Intermedio, Avanzado, Nativo")
    porcentaje: str = Field(..., description="Indica el porcentaje")
    class Config:
        json_schema_extra = {
            "example": {
                "idioma": "Inglés",
                "nivel": "Basico",
                "porcentaje": "30%"
            }
        }


class Experiencia(BaseModel):
    """Experiencia laboral"""
    empresa: str
    puesto: str
    descripcion: Optional[str] = None
    fecha_inicio: str  # Formato: "YYYY-MM"
    fecha_fin: Optional[str] = None  # None si es trabajo actual
    es_actual: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa": "Tech Company SA",
                "puesto": "Desarrollador Junior",
                "descripcion": "Desarrollo de aplicaciones web",
                "fecha_inicio": "2023-06",
                "fecha_fin": "2024-12",
                "es_actual": False
            }
        }


class Proyecto(BaseModel):
    """Proyecto personal o académico"""
    nombre: str
    descripcion: str
    tecnologias: List[str] = []
    url: Optional[str] = None
    fecha: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Sistema de Inventario",
                "descripcion": "Aplicación web para gestión de inventarios",
                "tecnologias": ["Python", "FastAPI", "React"],
                "url": "https://github.com/user/proyecto"
            }
        }


class Certificacion(BaseModel):
    """Certificación o curso"""
    nombre: str
    institucion: str
    fecha_obtencion: Optional[str] = None
    url_credencial: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Python for Data Science",
                "institucion": "Coursera",
                "fecha_obtencion": "2024-08"
            }
        }


class StudentProfile(BaseModel):
    """Perfil completo del estudiante"""
    # Datos básicos
    matricula: str = Field(..., description="Matrícula del estudiante")
    nombre_completo: str
    carrera: str
    semestre: int = Field(..., ge=1, le=8, description="Semestre actual (1-8)")
    promedio: Optional[float] = Field(None, ge=0, le=10)
    
    # Información de contacto (cifrada en BD)
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    disponibilidad: str = Field(
        default="Tiempo completo",
        description="Tiempo completo, Medio tiempo, Por proyecto, Prácticas"
    )
    
    # Habilidades
    habilidades_tecnicas: List[str] = Field(default_factory=list)
    habilidades_blandas: List[str] = Field(default_factory=list)
    idiomas: List[Idioma] = Field(default_factory=list)
    
    # Experiencia
    experiencia_laboral: List[Experiencia] = Field(default_factory=list)
    proyectos: List[Proyecto] = Field(default_factory=list)
    certificaciones: List[Certificacion] = Field(default_factory=list)
    
    # CV
    cv_filename: Optional[str] = None
    cv_upload_date: Optional[datetime] = None
    
    # Preferencias
    areas_interes: List[str] = Field(default_factory=list)
    modalidad_preferida: str = Field(
        default="Híbrido",
        description="Presencial, Remoto, Híbrido"
    )
    salario_esperado: Optional[float] = None
    
    # Perfil público (lo que ven las empresas antes de solicitar contacto)
    descripcion_breve: Optional[str] = Field(
        None,
        max_length=500,
        description="Breve descripción profesional"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "matricula": "A01234567",
                "nombre_completo": "Juan Pérez García",
                "carrera": "Ingeniería en Sistemas Computacionales",
                "semestre": 8,
                "promedio": 8.5,
                "telefono": "5512345678",
                "ciudad": "Ciudad de México",
                "disponibilidad": "Tiempo completo",
                "habilidades_tecnicas": ["Python", "JavaScript", "React", "FastAPI", "MongoDB"],
                "habilidades_blandas": ["Trabajo en equipo", "Comunicación", "Liderazgo"],
                "idiomas": [
                    {"idioma": "Español", "nivel": "Nativo"},
                    {"idioma": "Inglés", "nivel": "Basico", "porcentaje": "30%"}
                ],
                "areas_interes": ["Desarrollo Web", "Inteligencia Artificial", "Ciberseguridad"],
                "modalidad_preferida": "Híbrido",
                "descripcion_breve": "Estudiante apasionado por el desarrollo de software"
            }
        }


class StudentInDB(StudentProfile):
    """Modelo de estudiante en base de datos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId  # Referencia al User
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Embeddings para matching (generados por IA)
    profile_embedding: Optional[List[float]] = None
    
    # Estado
    perfil_completo: bool = False
    visible_empresas: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StudentUpdate(BaseModel):
    """Modelo para actualizar perfil de estudiante"""
    nombre_completo: Optional[str] = None
    semestre: Optional[int] = Field(None, ge=1, le=12)
    promedio: Optional[float] = Field(None, ge=0, le=10)
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    disponibilidad: Optional[str] = None
    habilidades_tecnicas: Optional[List[str]] = None
    habilidades_blandas: Optional[List[str]] = None
    idiomas: Optional[List[Idioma]] = None
    experiencia_laboral: Optional[List[Experiencia]] = None
    proyectos: Optional[List[Proyecto]] = None
    certificaciones: Optional[List[Certificacion]] = None
    areas_interes: Optional[List[str]] = None
    modalidad_preferida: Optional[str] = None
    salario_esperado: Optional[float] = None
    descripcion_breve: Optional[str] = None
    visible_empresas: Optional[bool] = None


class StudentPublicProfile(BaseModel):
    """Perfil público del estudiante (lo que ven las empresas SIN contacto)"""
    matricula: str  # Solo matrícula, NO nombre
    carrera: str
    semestre: int
    habilidades_tecnicas: List[str]
    habilidades_blandas: List[str]
    idiomas: List[Idioma]
    areas_interes: List[str]
    modalidad_preferida: str
    descripcion_breve: Optional[str]
    tiene_experiencia: bool
    num_proyectos: int
    num_certificaciones: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "matricula": "A01234567",
                "carrera": "Ingeniería en Sistemas",
                "semestre": 8,
                "habilidades_tecnicas": ["Python", "React"],
                "habilidades_blandas": ["Trabajo en equipo"],
                "idiomas": [{"idioma": "Inglés", "nivel": "B2"}],
                "areas_interes": ["Desarrollo Web"],
                "modalidad_preferida": "Híbrido",
                "tiene_experiencia": True,
                "num_proyectos": 3,
                "num_certificaciones": 2
            }
        }