from celery import shared_task
from django.utils import timezone
from django.conf import settings

from imapclient import IMAPClient
import pyzmail

from .mailer import send_mail
from .models import EmailLog
from .utils import enforce_domain_rate_limit, classify_smtp_error, classify_bounce_severity
from .utils import extract_bounce_reason, extract_recipient_from_dsn, is_suppressed, suppress_email
from .smtp_store import get_smtp_credentials


import os
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
    
    if (is_suppressed(log.email)):
        log.status = 'FAILED'
        log.failure_reason = 'Email Suppressed due to prior hard bounce'
        log.save()
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
        log.status = "FAILED"
        log.failure_reason = classify_smtp_error(e)
        log.save()
        return

@shared_task
def check_followups():
    creds = get_smtp_credentials()
    if not creds:
        return
    
    logs = EmailLog.objects.filter(
        follow_up_at__lte = timezone.now(),
        follow_up_done = False,
        status = "SUCCESS"
    )
    
    
    for log in logs:        
        send_mail(
            to_email=creds['email'],
            subject=f"Follow Up Due with {log.name}",
            body=FOLLOW_UP_MAIL.format(
                person_email=log.email,
                person_name=log.name
            )
        )
        
        log.follow_up_done = True
        log.save()

@shared_task
def check_bounces():
    creds = get_smtp_credentials()
    if not creds:
        return

    EMAIL_USER = creds["email"]
    EMAIL_PASS = creds["password"]
    IMAP_HOST = os.getenv("IMAP_HOST")
    
    with IMAPClient(IMAP_HOST) as client:
        client.login(EMAIL_USER, EMAIL_PASS)
        client.select_folder('INBOX')
        
        messages = client.search([
            "OR",
            "FROM", "mailer-daemon",
            "FROM", "postmaster",
            "SUBJECT", "Delivery Status Notification",
        ])
        
        for uid in messages:
            response = client.fetch([uid], ['BODY[]'])
            raw = response[uid][b'BODY[]']
            msg = pyzmail.PyzMessage.factory(raw)
            
            subject = msg.get_subject() or ""
            content_type = msg.get('content-type', '').lower()
            
            if (
                'delivery-status' not in content_type
                and 'delivery incomplete' not in subject.lower()
                and 'undeliverable' not in subject.lower()
            ):
                continue
            
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
            
            if severity == 'HARD':
                log.status = 'FAILED'
                log.failure_reason = f'HARD Bounce: {reason}'
                log.save()
                suppress_email(log.email, reason)
            
            if severity == 'SOFT':
                log.retry_count += 1
                
                if log.retry_count <=3:
                    log.status = 'PENDING'
                    log.next_retry_at = timezone.now() + timedelta(hours=24)
                    log.failure_reason = f'SOFT Bounce: {reason}'
                else:
                    log.status = 'FAILED'
                    log.failure_reason = f'SOFT Bounce retry limit exceeded (3): {reason}'
                log.save()

            client.add_flags(uid, ["\\Seen"])

@shared_task
def retry_pending_emails():
    now = timezone.now()
    
    logs = EmailLog.objects.filter(
        status = 'PENDING',
        next_retry_at__lte = now
    )
    
    for log in logs:
        send_email_task.delay(log.id)