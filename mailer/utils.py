import time
import random
from django.core.cache import cache

DOMAIN_DELAY = random.randint(10, 70)   # seconds

def enforce_domain_rate_limit(email):
    domain = email.split('@')[-1]
    key = f"domain_last_sent:{domain}"
    
    last_sent = cache.get(key)
    now = time.time()
    
    if last_sent and now - last_sent < DOMAIN_DELAY:
        sleep_time = DOMAIN_DELAY - (now - last_sent)
        time.sleep(sleep_time)
    
    cache.set(key, time.time(), timeout=DOMAIN_DELAY)