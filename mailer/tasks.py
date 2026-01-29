from celery import shared_task
from django.utils import timezone
from django.conf import settings

from imapclient import IMAPClient
import pyzmail

from .mailer import send_mail
from .models import EmailLog
from .utils import enforce_domain_rate_limit, classify_smtp_error, classify_bounce_severity
from .utils import extract_bounce_reason, extract_recipient_from_dsn

import os
import re
from datetime import timedelta

FOLLOW_UP_MAIL = """
Hi Arjun!

This is Arjun from your past. Your mail was sent at {person_email} and now it's time to follow up with
{person_name}.

Click on the following button to send a Follow Up email.
"""

@shared_task(bind=True)
def send_email_task(self, log_id):
    log = EmailLog.objects.filter(id=log_id, status="PENDING").first()
    
    if not log:
        return
    
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
        send_mail(
            to_email=os.getenv('EMAIL_USER') or "EMAIL_USER not set",
            subject=f"Follow Up Due with {log.name}",
            body=FOLLOW_UP_MAIL.format(person_email=log.email, person_name=log.name)
        )
        
        log.follow_up_done = True
        log.save()

@shared_task
def check_bounces():
    IMAP_HOST = os.getenv("IMAP_HOST")
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASS = os.getenv('EMAIL_PASS')
    
    with IMAPClient(IMAP_HOST) as client:
        client.login(EMAIL_USER, EMAIL_PASS)
        client.select_folder('INBOX')
        
        messages = client.search(["FROM", "mailer-daemon"])
        
        for uid in messages:
            raw = client.fetch([uid], ["RFC822"])[uid]["RFC822"]
            msg = pyzmail.PyzMessage.factory(raw)
            
            subject = msg.get_subject() or ""
            body = ""
            
            if msg.text_part:
                body = msg.text_part.get_payload().decode(
                    msg.text_part.charset or "utf-8",
                    errors="ignore"
                )
            
            # Original Recipient
            recipient = extract_recipient_from_dsn(body)
            reason = extract_bounce_reason(body)
            severity = classify_bounce_severity(reason)
            
            if not recipient:
                continue
            
            log = EmailLog.objects.filter(
                email__iexact=recipient,
                status='SUCCESS'
            ).order_by("-created_at").first()
            
            if not log:
                continue
            
            log.failure_reason = f'{severity} bounce: {reason}'
            if severity == 'SOFT':
                log.status = 'PENDING'
                log.follow_up_at = timezone.now() + timedelta(hours=24)
            else:
                log.status = 'FAILED'
            log.save()
            
            client.add_flags(uid, ["\\Seen"])
