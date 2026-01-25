from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .mailer import send_mail
from .models import EmailLog
from .utils import enforce_domain_rate_limit, classify_smtp_error

import os

FOLLOW_UP_MAIL = """
Hi Arjun!

This is Arjun from your past. Your mail was sent at {person_email} and now it's time to follow up with
{person_name}.

Click on the following button to send a Follow Up email.
"""

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def send_email_task(self, log_id):
    log = EmailLog.objects.filter(id=log_id, status="PENDING").first()
    
    try:
        enforce_domain_rate_limit(log.email)
        
        send_mail(
            to_email=log.email,
            subject="Application for Software Development Engineer Internship | Arjun Tomar",
            body=log.email_body,
            attachment_path=str(
                settings.BASE_DIR / "attachments" / "Arjun_Tomar_ML_Resume.pdf"
            ),
        )
        
        if log:
            log.status = "SUCCESS"
            log.sent_at = timezone.now()
            log.failure_reason = None
            log.save()
        
    except Exception as e:
        if log:
            log.status = "FAILED"
            log.failure_reason = classify_smtp_error(e)
            log.save()
        raise e

@shared_task
def check_followups():
    now = timezone.now()
    
    logs = EmailLog.objects.filter(
        follow_up_at__lte = now,
        follow_up_done = False,
        status = "SUCCESS"
    )
    
    for log in logs:
        if not log:
            raise ValueError("No pending EmailLog found")
        
        send_mail(
            to_email=os.getenv('EMAIL_USER') or "EMAIL_USER not set",
            subject=f"Follow Up Due with {log.name}",
            body=FOLLOW_UP_MAIL.format(person_email=log.email, person_name=log.name)
        )
        
        log.follow_up_done = True
        log.save()