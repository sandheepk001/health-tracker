import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def test_connection():
    try:
        redis_client.ping()
        return True
    except Exception:
        return False