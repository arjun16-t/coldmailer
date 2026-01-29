from cryptography.fernet import Fernet
from django.conf import settings
from .redis_client import redis_client

fernet = Fernet(settings.SMTP_ENCRYPTION_KEY.encode())

SMTP_KEY = "smtp:credentials"

def set_smtp_credentials(email: str, password: str):
    encrypted = fernet.encrypt(password.encode()).decode()
    redis_client.hset(SMTP_KEY, mapping={
        "email": email,
        "password": encrypted
    })

def get_smtp_credentials():
    data = redis_client.hgetall(SMTP_KEY)
    if not data:
        return None

    return {
        "email": data["email"],
        "password": fernet.decrypt(data["password"].encode()).decode()
    }

def smtp_configured() -> bool:
    return redis_client.exists(SMTP_KEY) == 1

def clear_smtp_credentials():
    redis_client.delete(SMTP_KEY)
