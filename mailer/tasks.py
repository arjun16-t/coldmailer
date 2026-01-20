from celery import shared_task
from django.utils import timezone

from .mailer import send_mail
from .models import EmailLog
from .utils import enforce_domain_rate_limit

import time


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def send_email_task(self, email, name, company, attachment_path):
    log = EmailLog.objects.filter(
        email=email,
        company=company,
        status="PENDING"
    ).first()
    
    try:
        enforce_domain_rate_limit(email)
        
        send_mail(
            to_email=email,
            subject="Application for Software Development Engineer Internship | Arjun Tomar",
            body=log.email_body,
            attachment_path=attachment_path
        )
        
        if log:
            log.status = "SUCCESS"
            log.sent_at = timezone.now()
            log.save()
        
        time.sleep(5)  # rate limiting
    except Exception as e:
        if log:
            log.status = "FAILED"
            log.save()
        raise e