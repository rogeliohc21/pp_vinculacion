"""
Configuración y conexión a MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging
from app.config import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Database:
    """Manejador de conexión a MongoDB"""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """Conectar a MongoDB"""
        try:
            safe_uri = urlparse(settings.mongodb_url)
            host = safe_uri.hostname or "localhost"
            logger.info(f"Conectando a MongoDB en host: {host}")
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                tlsAllowInvalidCertificates=True  # Solo para desarrollo
            )
            cls.database = cls.client[settings.database_name]
            
            # Verificar conexión
            await cls.client.admin.command('ping')
            logger.info(f"✓ Conectado exitosamente a MongoDB - Base de datos: {settings.database_name}")
            
            # Crear índices
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"✗ Error al conectar a MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Cerrar conexión a MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("✓ Conexión a MongoDB cerrada")
    
    @classmethod
    async def create_indexes(cls):
        """Crear índices en las colecciones para mejor rendimiento"""
        try:
            # Índices para colección de usuarios
            await cls.database.users.create_index("email", unique=True)
            await cls.database.users.create_index("username", unique=True)
            await cls.database.users.create_index("role")
            
            # Índices para colección de estudiantes
            await cls.database.students.create_index("matricula", unique=True)
            await cls.database.students.create_index("user_id")
            await cls.database.students.create_index("carrera")
            await cls.database.students.create_index("semestre")
            
            # Índices para colección de empresas
            await cls.database.companies.create_index("user_id")
            await cls.database.companies.create_index("rfc", unique=True)
            
            # Índices para colección de vacantes
            await cls.database.vacancies.create_index("company_id")
            await cls.database.vacancies.create_index("estado")
            await cls.database.vacancies.create_index("fecha_publicacion")
            
            # Índices para colección de matches
            await cls.database.matches.create_index([
                ("vacancy_id", 1),
                ("student_matricula", 1)
            ], unique=True)
            await cls.database.matches.create_index("porcentaje_match")
            
            # Índices para colección de solicitudes de contacto
            await cls.database.contact_requests.create_index("vacancy_id")
            await cls.database.contact_requests.create_index("student_matricula")
            await cls.database.contact_requests.create_index("estado")
            
            # Índices para colección de mensajes
            await cls.database.messages.create_index("student_id")
            await cls.database.messages.create_index("fecha_envio")
            await cls.database.messages.create_index("leido")
            
            # Índices para colección de audit logs
            await cls.database.audit_logs.create_index("user_id")
            await cls.database.audit_logs.create_index("timestamp")
            await cls.database.audit_logs.create_index("event_type")
            
            # Índices para colección de alertas de seguridad
            await cls.database.security_alerts.create_index("timestamp")
            await cls.database.security_alerts.create_index("status")
            await cls.database.security_alerts.create_index("severity")

            # Índices para colección de refresh tokens
            # Usado para persistir y revocar refresh tokens (jti)
            await cls.database.refresh_tokens.create_index("jti", unique=True)
            await cls.database.refresh_tokens.create_index("user_id")
            
            logger.info("✓ Índices de MongoDB creados exitosamente")
            
        except Exception as e:
            logger.warning(f"Advertencia al crear índices: {e}")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Obtener instancia de la base de datos"""
        if cls.database is None:
            raise Exception("Database no está conectada. Ejecuta connect_db() primero.")
        return cls.database


# Instancia global de la base de datos
db = Database()


# Funciones helper para obtener colecciones
async def get_collection(collection_name: str):
    """Obtener una colección de MongoDB"""
    database = db.get_database()
    return database[collection_name]


# Colecciones específicas
async def get_users_collection():
    """Colección de usuarios"""
    return await get_collection("users")


async def get_students_collection():
    """Colección de estudiantes"""
    return await get_collection("students")


async def get_companies_collection():
    """Colección de empresas"""
    return await get_collection("companies")


async def get_vacancies_collection():
    """Colección de vacantes"""
    return await get_collection("vacancies")


async def get_matches_collection():
    """Colección de matches"""
    return await get_collection("matches")


async def get_contact_requests_collection():
    """Colección de solicitudes de contacto"""
    return await get_collection("contact_requests")


async def get_messages_collection():
    """Colección de mensajes estudiante-admin"""
    return await get_collection("messages")


async def get_audit_logs_collection():
    """Colección de logs de auditoría"""
    return await get_collection("audit_logs")


async def get_security_alerts_collection():
    """Colección de alertas de seguridad"""
    return await get_collection("security_alerts")


async def get_refresh_tokens_collection():
    """Colección para persistir refresh tokens (jti + metadata)"""
    return await get_collection("refresh_tokens")