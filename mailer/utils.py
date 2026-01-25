import time
import random
import smtplib
import dns.resolver
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

def has_mx_record(email):
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except Exception as e:
        return False

def classify_smtp_error(exc: Exception) -> str:
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return "Mailbox does not exist"
    
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return "SMTP Server disconnected unexpectedly"
    
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "SMTP Authentication failed"
    
    if isinstance(exc, smtplib.SMTPDataError):
        return "SMTP Server rejected message content"
    
    if isinstance(exc, smtplib.SMTPException):
        return f"SMTP Error: {str(exc)}"
    
    return f"Unknown Error: {str(exc)}"
