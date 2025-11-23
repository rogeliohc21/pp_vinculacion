from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
import logging

logger = logging.getLogger(__name__)


# Crear instancia del limitador; si se proporciona `settings.redis_url` se
# usará Redis como backend (storage_uri), en caso contrario usar en-memory.
if getattr(settings, "redis_url", ""):
    logger.info("Inicializando rate limiter con Redis: %s", settings.redis_url)
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
else:
    limiter = Limiter(key_func=get_remote_address)


def init_limiter(app):
    """Inicializa middleware y manejador de errores de rate limiting en la app.

    Nota: los routers suelen importar `limiter` en tiempo de importación para
    aplicar los decoradores `@limiter.limit(...)`. Por eso la configuración
    (usar Redis o no) se aplica en el momento en que se importa este módulo.
    Esta función solo registra el middleware y el manejador 429 en la app.
    """
    # Registrar en el estado de la app para que routers puedan acceder si es necesario
    app.state.limiter = limiter

    # Agregar middleware de slowapi
    app.add_middleware(SlowAPIMiddleware)

    # Registrar manejador de excepción 429
    app.add_exception_handler(429, _rate_limit_exceeded_handler)

    logger.info("Rate limiter inicializado")
