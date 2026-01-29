from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone, html
from django.views.decorators.http import require_POST


from .forms import UploadFileForm
from .parser import parse_file
from .mailer import MAIL_CONTENT
from .tasks import send_email_task
from .utils import has_mx_record
from .models import EmailLog, SuppressedEmail

import textwrap
import tempfile
import os
from datetime import timedelta
import json

def upload_file(request):
    parsed_data = None
    error = None
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data['file']
            ext = os.path.splitext(uploaded.name)[1]
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
            
            try:
                parsed_data = parse_file(tmp.name)
            except Exception as e:
                error = str(e)
        
    else:
        form = UploadFileForm()
        
    return render(request, "upload.html", {
        "form": form,
        "parsed_data": parsed_data,
        "error": error
    })

def preview_email(request):
    prefixes = set()
    
    for key in request.POST:
        if key.endswith('[selected]'):
            prefixes.add(key.replace('[selected]', ''))

    people = []
    for prefix in list(prefixes):
        people.append({
            "name": request.POST.get(f"{prefix}[name]"),
            "email": request.POST.get(f"{prefix}[email]"),
            "company": request.POST.get(f"{prefix}[company]"),
        })

    return render(request, "preview.html", {
        "people": people,
        "template": MAIL_CONTENT
    })

def send_emails(request):
    if request.method != "POST":
        return redirect("/")
    
    raw_body = request.POST.get("email_body", "")
    email_body_template = textwrap.dedent(raw_body).strip()

    if not email_body_template:
        messages.error(request, "Email content is empty.")
        return redirect("preview_email")
    
    sent_count = 0
    
    for key in request.POST:
        if not key.endswith('[selected]'):
            continue
        
        prefix = key.replace('[selected]', '')
        
        email=request.POST.get(f"{prefix}[email]")
        name=request.POST.get(f"{prefix}[name]")
        company=request.POST.get(f"{prefix}[company]")
        
        name = name if name and str(name).lower() != "nan" else "Hiring Manager"
        company = company if company and str(company).lower() != "nan" else "your company"
        
        # Prevents Duplicates
        if EmailLog.objects.filter(
            email=email,
            company=company,
            status='SUCCESS'
        ).exists():
            continue
        
        # Logging Emails
        try:
            personalized_body = email_body_template.format(
                name=name,
                company=company
            )
        except KeyError as e:
            messages.error(request, f"Invalid placeholder: {e}")
            return redirect("preview_email")
        
        # Validating Email Address
        if not has_mx_record(email):
            EmailLog.objects.create(
                email=email,
                name=name,
                company=company,
                email_body=personalized_body,
                status="FAILED",
                failure_reason="No MX Record found for domain"
            )
            continue
        
        log = EmailLog.objects.create(
            email=email,
            name=name,
            company=company,
            email_body=personalized_body,
            status="PENDING"
        )
        
        try:
            result = send_email_task.delay(log.id)
            log.task_id = result.id
            log.save()
            
            sent_count += 1
            
        except Exception as e:
            log.status = "FAILED"
            log.save()
            print("Celery enque failed:", e)

    messages.success(
        request,
        f"{sent_count} emails queued successfully."
    )
    return redirect("dashboard")

def dashboard(request):
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    
    base_qs = EmailLog.objects.all()
    
    if query:
        base_qs = base_qs.filter(
            Q(email__icontains = query) |
            Q(company__icontains=query)
        )
    
    suppressed = set(SuppressedEmail.objects.values_list('email', flat=True))
    
    paginator = Paginator(base_qs.order_by("-created_at"), 25)
    page_obj = paginator.get_page(page_number)
    
    due_followups = EmailLog.objects.filter(
        follow_up_at__isnull=False,
        follow_up_done=False,
        follow_up_at__lte=timezone.now()
    )
    
    context = {
        "emails": page_obj,
        "query": query,
        "due_followups": due_followups,
        "suppressed_emails": suppressed,
        "total_emails": base_qs.count(),
        "success_count": base_qs.filter(status="SUCCESS").count(),
        "failed_count": base_qs.filter(status="FAILED").count(),
        "pending_count": base_qs.filter(status="PENDING").count(),
    }
    
    return render(request, "dashboard.html", context)

def dashboard_data(request):
    emails = EmailLog.objects.all()
    logs = emails.order_by("-created_at")[:200]
    
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "email": log.email,
            "company": log.company,
            "status": log.status,
            "created_at": log.created_at.strftime("%d-%m-%Y %H:%M:%S"),
            "sent_at": log.sent_at.strftime("%d-%m-%Y %H:%M:%S") if log.sent_at else None,
        })
    
    return JsonResponse({"logs": data})

@require_POST
def retry_email(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    
    if log.status != "FAILED" or "HARD bounce" in (log.failure_reason or ""):
        messages.error(request, "This email cannot be retried.")
        return redirect("dashboard")
    
    log.status = "PENDING"
    log.save()
    
    send_email_task.delay(log.id)
    
    return redirect("dashboard")

def status_page(request):
    logs = EmailLog.objects.order_by("-created_at")[:100]
    return render (request, "status.html", {"logs":logs})

def email_detail(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    suppression = SuppressedEmail.objects.filter(email=log.email).first()
    
    return JsonResponse({
        "email": log.email,
        "company": log.company,
        "status": log.status,
        "created_at": log.created_at.strftime("%d-%m-%Y %H:%M:%S"),
        "sent_at": log.sent_at.strftime("%d-%m-%Y %H:%M:%S") if log.sent_at else None,
        "failure_reason": log.failure_reason,
        "content_url": f"/emails/{log.id}/content/",
        "suppressed": bool(suppression),
        "suppression_reason": suppression.reason if suppression else None,
    })

def email_content(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    return HttpResponse(
        f"<pre>{html.escape(log.email_body)}</pre>",
        content_type="text/html"
    )

def schedule_followup(request, log_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid Request"}, status = 400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    days = int(data.get("days", 0))
    
    log = EmailLog.objects.get(id=log_id)
    
    if log.status != "SUCCESS":
        return JsonResponse(
            {"error": "Follow-ups can only be scheduled for delivered emails"},
            status=400
        )
    
    log.follow_up_at = timezone.now() + timedelta(days=days)
    log.follow_up_done = False
    log.save()
    
    return JsonResponse({"status": "ok"})