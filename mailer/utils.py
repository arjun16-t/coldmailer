import time
import random
import smtplib
import re
import dns.resolver
from django.core.cache import cache
from django.shortcuts import redirect

from .models import SuppressedEmail
from .smtp_store import smtp_configured

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

def extract_recipient_from_dsn(text):
    patterns = [
        r"Original-Recipient:\s*rfc822;\s*(\S+@\S+)",
        r"Final-Recipient:\s*rfc822;\s*(\S+@\S+)",
        r"for\s+<(\S+@\S+)>",
        r"to\s+<(\S+@\S+)>",
        r"delivering your message to\s+(\S+@\S+)",
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return None

def extract_bounce_reason(text):
    patterns = [
        # HARD BOUNCES
        (r"550 5\.1\.1", "Mailbox does not exist"),
        (r"user unknown", "Mailbox does not exist"),
        (r"no such user", "Mailbox does not exist"),
        (r"address rejected", "Address rejected"),
        (r"mailbox.*not found", "Mailbox not found"),

        # SOFT BOUNCES
        (r"delivery incomplete", "Temporary delivery failure"),
        (r"temporary problem", "Temporary delivery failure"),
        (r"timed out", "Recipient mail server timed out"),
        (r"could not connect", "Could not connect to recipient server"),
        (r"connection refused", "Recipient server refused connection"),
        (r"resources temporarily unavailable", "Recipient server overloaded"),
        (r"try again later", "Temporary server issue"),

        # POLICY / SPAM
        (r"blocked", "Message blocked by recipient server"),
        (r"spam", "Message flagged as spam"),
        (r"policy", "Rejected due to recipient policy"),
    ]

    for pattern, reason in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return reason

    return "Delayed bounce (unclassified)"

def classify_bounce_severity(reason: str) -> str:
    HARD = [
        "Mailbox does not exist",
        "Mailbox not found",
        "Address rejected",
    ]

    for h in HARD:
        if h.lower() in reason.lower():
            return "HARD"

    return "SOFT"

def is_suppressed(email) -> bool:
    return SuppressedEmail.objects.filter(
        email__iexact=email
    ).exists()

def suppress_email(email, reason):
    SuppressedEmail.objects.get_or_create(
        email = email,
        defaults= {"reason":reason}
    )

def require_smtp(view_func):
    def wrapper(request, *args, **kwargs):
        if not smtp_configured():
            return redirect("/")
        return view_func(request, *args, **kwargs)
    return wrapper