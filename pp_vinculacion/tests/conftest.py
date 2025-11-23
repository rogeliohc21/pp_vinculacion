# conftest.py
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

from app.main import app
from app.database import db
from app.config import settings


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Tell anyio to use the asyncio backend."""
    return "asyncio"


@pytest.fixture(scope="session")
def set_test_db_name():
    """Set database name to a test DB and enable testing mode for the whole session."""
    settings.database_name = "test_db"
    settings.testing = True  # Activar modo testing


@pytest_asyncio.fixture
async def async_client(set_test_db_name) -> AsyncGenerator[AsyncClient, None]:
    """Create an AsyncClient that uses the app's lifespan so DB connects
    inside the same event loop. Clear collections before yielding to tests.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Connect DB in the same loop as the client to avoid cross-loop futures
        await db.connect_db()
        database = db.get_database()
        # Ensure a clean DB for each test
        for collection in await database.list_collection_names():
            await database[collection].delete_many({})
        try:
            yield ac
        finally:
            # Close DB connection after the test
            await db.close_db()


@pytest_asyncio.fixture
async def get_test_db(async_client):
    """Get test database client. Depends on async_client to ensure DB is connected."""
    return db.client[settings.database_name]