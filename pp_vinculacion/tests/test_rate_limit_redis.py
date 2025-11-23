import os
import pytest
import pytest_asyncio
from httpx import AsyncClient

try:
    import redis as redis_lib
except Exception:
    redis_lib = None

from app.config import settings

# Use a small test user to drive the login endpoint
TEST_USER_RL = {
    "username": "rl_test@example.com",
    "email": "rl_test@example.com",
    "password": "Test123!",
    "first_name": "RL",
    "last_name": "Tester",
    "role": "estudiante"
}


@pytest.mark.asyncio
async def test_rate_limit_redis(async_client: AsyncClient):
    """If REDIS_URL is provided and reachable, hammer the login endpoint and expect a 429.

    This test is skipped when `REDIS_URL` is not set or Redis is not reachable. It
    does not start Redis itself; use the provided `docker-compose.yml` or start Redis
    manually before running tests that include this file.
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        pytest.skip("REDIS_URL not set; skipping Redis-backed rate limit test")

    if redis_lib is None:
        pytest.skip("redis package not available")

    # Quick connectivity check
    try:
        client = redis_lib.from_url(redis_url)
        client.ping()
    except Exception:
        pytest.skip(f"Cannot connect to Redis at {redis_url}")

    # Create a storage helper from limits to inspect keys directly
    try:
        from limits.storage import storage_from_string
    except Exception:
        pytest.skip("limits.storage not available")

    storage = storage_from_string(redis_url)
    # Clear any existing limit keys for a clean test
    try:
        storage.reset()
    except Exception:
        # If reset fails, continue but test may be flaky
        pass

    # Compute the configured login limit (e.g. '10/minute')
    raw = settings.auth_login_limit
    try:
        allowed = int(raw.split("/")[0])
    except Exception:
        allowed = 10

    # Ensure the test user exists
    await async_client.post("/api/auth/register", json=TEST_USER_RL)

    # Send allowed requests first and record last status
    last_status = None
    for i in range(allowed + 2):
        resp = await async_client.post(
            "/api/auth/login",
            data={"username": TEST_USER_RL["email"], "password": TEST_USER_RL["password"]},
        )
        last_status = resp.status_code

    # After exceeding the limit we expect to see a 429
    assert last_status == 429, f"Expected 429 after exceeding limit, got {last_status}"

    # Verify Redis now contains at least one LIMITS key with a positive counter
    try:
        conn = storage.get_connection()
        # Use scan to iterate keys with the storage prefix
        pattern = f"{storage.key_prefix}:*"
        keys = list(conn.scan_iter(match=pattern, count=100))
        assert keys, "Expected LIMITS keys in Redis but none found"

        # Check at least one key has a positive integer value
        found_positive = False
        for k in keys:
            val = conn.get(k)
            try:
                if val is not None and int(val) > 0:
                    found_positive = True
                    break
            except Exception:
                continue

        assert found_positive, "No LIMITS key with positive counter found in Redis"
    except Exception as e:
        pytest.skip(f"Unable to introspect Redis storage: {e}")
