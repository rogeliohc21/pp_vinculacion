"""
Configuración general de la aplicación
Carga variables de entorno y define constantes
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic"""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "vinculacion_inteligente"
    
    # Seguridad JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Cifrado
    encryption_key: str
    
    # Servidor
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = True
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8501"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    # Límits específicos por endpoint (formato accepted por slowapi/limits, e.g. "5/minute")
    auth_register_limit: str = "5/minute"
    auth_login_limit: str = "10/minute"
    upload_limit: str = "5/minute"
    # Redis (opcional) - usado por el rate limiter en despliegue multi-proceso
    # Dejar vacío para usar almacenamiento en memoria (útil en tests/local)
    redis_url: str = ""
    
    # Archivos
    max_file_size_mb: int = 10
    upload_dir: str = "./uploads"
    allowed_file_extensions: str = ".pdf,.docx,.doc"
    
    # Logs
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # Email (opcional)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    
    # Universidad
    university_name: str = "Universidad Nacional Rosario Castellanos"
    university_email: str = "vinculacion@unrc.edu.mx"
    
    # IA
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    matching_threshold: float = 0.80
    
    # Entorno
    environment: str = "development"
    testing: bool = False  # Bandera para modo testing
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convierte string de orígenes permitidos en lista"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convierte string de extensiones permitidas en lista"""
        return [ext.strip() for ext in self.allowed_file_extensions.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convierte MB a bytes"""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación (singleton)
    lru_cache asegura que solo se cree una instancia
    """
    return Settings()


# Constantes de la aplicación
class AppConstants:
    """Constantes usadas en toda la aplicación"""
    
    # Roles de usuario
    ROLE_STUDENT = "estudiante"
    ROLE_COMPANY = "empresa"
    ROLE_ADMIN = "admin"
    
    ROLES = [ROLE_STUDENT, ROLE_COMPANY, ROLE_ADMIN]
    
    # Permisos por rol
    PERMISSIONS = {
        ROLE_STUDENT: [
            "read_own_profile",
            "update_own_profile",
            "upload_cv",
            "message_admin",
            "view_own_matches"
        ],
        ROLE_COMPANY: [
            "read_candidates",
            "create_vacancy",
            "update_own_vacancy",
            "view_matches",
            "request_contact"
        ],
        ROLE_ADMIN: [
            "read_all",
            "write_all",
            "delete_all",
            "view_analytics",
            "approve_requests",
            "manage_users",
            "view_audit_logs"
        ]
    }
    
    # Estados de vacantes
    VACANCY_STATUS_ACTIVE = "activa"
    VACANCY_STATUS_CLOSED = "cerrada"
    VACANCY_STATUS_DRAFT = "borrador"
    
    # Estados de solicitudes de contacto
    CONTACT_REQUEST_PENDING = "pendiente"
    CONTACT_REQUEST_APPROVED = "aprobada"
    CONTACT_REQUEST_REJECTED = "rechazada"
    
    # Niveles de experiencia
    EXPERIENCE_LEVELS = [
        "Sin experiencia",
        "Menos de 1 año",
        "1-2 años",
        "2-3 años",
        "3-5 años",
        "Más de 5 años"
    ]
    
    # Niveles de idiomas
    LANGUAGE_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2", "Nativo"]
    
    # Carreras disponibles (ajustar según tu universidad)
    CARRERAS = [
        "Ingeniería en Sistemas Computacionales",
        "Ingeniería Industrial",
        "Ingeniería Mecánica",
        "Ingeniería Eléctrica",
        "Licenciatura en Administración",
        "Licenciatura en Contaduría",
        "Arquitectura",
        "Diseño Gráfico"
    ]
    
    # Tipos de contrato
    CONTRACT_TYPES = [
        "Tiempo completo",
        "Medio tiempo",
        "Por proyecto",
        "Prácticas profesionales",
        "Becario"
    ]
    
    # Modalidades de trabajo
    WORK_MODALITIES = [
        "Presencial",
        "Remoto",
        "Híbrido"
    ]


# Configuración de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "DEBUG",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    },
}


# Exportar configuración
settings = get_settings()
constants = AppConstants()
