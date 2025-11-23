"""
Punto de entrada principal de la API
FastAPI application con todos los routers configurados
"""
from app.routers import auth, students, companies, vacancies, matching, contact_requests
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime
import os

from app.config import settings


# Validación de settings críticos en entornos de producción
def _validate_critical_settings():
    """Evitar que la aplicación arranque en producción sin secrets esenciales.

    Esta validación es intencionalmente estricta solo cuando
    settings.environment == 'production'. En desarrollo permite valores
    por defecto para facilitar pruebas locales.
    """
    try:
        env = settings.environment
    except Exception:
        env = None

    if env and env.lower() == "production":
        missing = []
        if not getattr(settings, "secret_key", None):
            missing.append("SECRET_KEY")
        if not getattr(settings, "encryption_key", None):
            missing.append("ENCRYPTION_KEY")

        if missing:
            logger.critical(
                "Missing critical environment variables for production: %s. "
                "Copy .env.example to .env and set them, or set variables in the environment.",
                ", ".join(missing),
            )
            raise RuntimeError(
                f"Missing critical environment variables: {', '.join(missing)}"
            )


# Ejecutar validación temprana
_validate_critical_settings()
from app.database import db

# Importar routers
from app.routers import auth, students, companies, vacancies, matching

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando aplicación...")
    logger.info(f"Entorno: {settings.environment}")
    logger.info(f"Universidad: {settings.university_name}")
    
    # Conectar a MongoDB solo si no estamos en modo test
    if not settings.testing:
        await db.connect_db()
    
    # Crear directorios necesarios
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.upload_dir, "cvs"), exist_ok=True)
    os.makedirs(os.path.join(settings.upload_dir, "logos"), exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("✓ Aplicación lista para recibir peticiones")
    
    yield
    
    # Shutdown - cerrar BD solo si no estamos en modo test
    logger.info("🛑 Cerrando aplicación...")
    if not settings.testing:
        await db.close_db()
    logger.info("✓ Aplicación cerrada correctamente")


# Crear instancia de FastAPI
app = FastAPI(
    title="API de Vinculación Inteligente",
    description="""
    API para conectar estudiantes con oportunidades laborales usando IA
    
    ## Características principales:
    
    * **Matching inteligente con IA** - Algoritmo que calcula compatibilidad entre estudiantes y vacantes
    * **Análisis automático de CVs** - Extracción de habilidades y experiencia
    * **Sistema de autenticación seguro** - OAuth2 + JWT + MFA
    * **Protección de datos** - Cumplimiento con LFPDPPP
    * **Dashboard de KPIs** - Métricas y análisis para toma de decisiones
    * **Gráficas de compatibilidad** - Visualización de matching en gráfica de araña
    * **Anonimización de datos** - Solo matrícula visible hasta aprobación
    
    ## Roles:
    
    * **Estudiante** - Crea perfil, sube CV, recibe notificaciones
    * **Empresa** - Publica vacantes, busca candidatos, solicita contacto
    * **Administrador** - Gestiona usuarios, aprueba solicitudes, visualiza KPIs
    """,
    version="1.0.0",
    contact={
        "name": settings.university_name,
        "email": settings.university_email,
    },
    lifespan=lifespan
)

# Inicializar rate limiter (slowapi)
from app.limiter import init_limiter
init_limiter(app)

# ============= MIDDLEWARES =============

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

# Middleware de seguridad - Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Agregar headers de seguridad a todas las respuestas"""
    response = await call_next(request)
    
    # Headers de seguridad según OWASP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registrar información de cada petición"""
    start_time = time.time()
    
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"→ {request.method} {request.url.path} - IP: {client_host}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"← {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Middleware de validación de tamaño
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limitar tamaño de peticiones"""
    content_length = request.headers.get("content-length")
    
    if content_length:
        content_length = int(content_length)
        max_size = settings.max_file_size_bytes * 2
        
        if content_length > max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": f"Request demasiado grande. Máximo: {settings.max_file_size_mb * 2}MB"
                }
            )
    
    return await call_next(request)

# ============= EXCEPTION HANDLERS =============

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejar errores de validación"""
    logger.warning(f"Error de validación en {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejar excepciones generales"""
    logger.error(f"Error en {request.url.path}: {str(exc)}", exc_info=True)
    
    if settings.environment == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )

# ============= ENDPOINTS BÁSICOS =============

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz - Información de la API"""
    return {
        "message": "API de Vinculación Inteligente",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "university": settings.university_name,
        "docs": "/docs",
        "features": [
            "Matching con IA",
            "Gestión de perfiles",
            "Sistema de vacantes",
            "Autenticación segura",
            "Dashboard de KPIs"
        ]
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Health check - Verificar estado del sistema"""
    try:
        await db.client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }

@app.get("/api/info", tags=["General"])
async def api_info():
    """Información detallada de la API"""
    return {
        "name": "API de Vinculación Inteligente",
        "version": "1.0.0",
        "description": "Sistema para conectar estudiantes con oportunidades laborales usando IA",
        "university": settings.university_name,
        "contact": settings.university_email,
        "features": [
            "Matching inteligente con IA (80%+ compatibilidad)",
            "Análisis automático de CVs",
            "Sistema de autenticación seguro (OAuth2 + MFA)",
            "Protección de datos (LFPDPPP)",
            "Dashboard de KPIs y OKRs",
            "Gráficas de compatibilidad (Spider Chart)",
            "Anonimización de datos estudiantiles"
        ],
        "security": {
            "authentication": "OAuth2 + JWT + MFA",
            "encryption": "TLS 1.3 + AES-256",
            "compliance": ["OWASP Top 10", "ISO 27001", "LFPDPPP"],
            "levels": 5
        },
        "roles": ["estudiante", "empresa", "admin"],
        "endpoints": {
            "auth": "/api/auth",
            "students": "/api/students",
            "companies": "/api/companies",
            "vacancies": "/api/vacancies",
            "matching": "/api/matching"
        }
    }

# ============= REGISTRAR ROUTERS =============

# Autenticación
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Autenticación"]
)

# Estudiantes
app.include_router(
    students.router,
    prefix="/api/students",
    tags=["Estudiantes"]
)

# Empresas
app.include_router(
    companies.router,
    prefix="/api/companies",
    tags=["Empresas"]
)

# Vacantes
app.include_router(
    vacancies.router,
    prefix="/api/vacancies",
    tags=["Vacantes"]
)

# Matching con IA
app.include_router(
    matching.router,
    prefix="/api/matching",
    tags=["Matching IA"]
)

# Solicitudes de Contacto
app.include_router(
    contact_requests.router,
    prefix="/api/contact-requests",
    tags=["Solicitudes de Contacto"]
)

# ============= ENDPOINTS DE DESARROLLO =============

@app.get("/api/routes", tags=["Desarrollo"])
async def list_routes():
    """
    Listar todas las rutas disponibles (solo en desarrollo)
    """
    if settings.environment == "production":
        return {"message": "Not available in production"}
    
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    
    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x["path"])
    }

# ============= MENSAJE DE INICIO =============

@app.on_event("startup")
async def startup_message():
    """Mensaje al iniciar la aplicación"""
    logger.info("=" * 60)
    logger.info("🎓 API de Vinculación Inteligente")
    logger.info(f"🏫 Universidad: {settings.university_name}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"📡 Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"📚 Docs: http://localhost:{settings.api_port}/docs")
    logger.info("=" * 60)

# ============= forzar ==============

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="📘 Documentación API Vinculación Inteligente"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    try:
        return get_openapi(
            title="API Vinculación Inteligente",
            version="1.0.0",
            description="Documentación generada manualmente para resolver conflicto Swagger UI",
            routes=app.routes
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



# ============= EJECUTAR APLICACIÓN =============

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Iniciando servidor en {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower()
    )
