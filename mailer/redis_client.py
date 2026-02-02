import redis
import os
from django.conf import settings

redis_url = os.environ.get('REDIS_URL')

if redis_url:
    # Production (Railway): Use the full URL
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
    # Local Development: Fall back to specific settings or localhost defaults
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', '127.0.0.1'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True
    )
