from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import UploadFileForm
from .parser import parse_file
from .mailer import MAIL_CONTENT
from .tasks import send_email_task

from .models import EmailLog

import tempfile
import os

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
        if EmailLog.objects.filter(email=email, company=company).exists():
            continue
        
        # Logging Emails
        log = EmailLog.objects.create(
            email = email,
            name = name,
            company = company,
            status = "PENDING"
        )
        
        try:
            result = send_email_task.delay(
                email=email,
                name=name,
                company=company,
                attachment_path=str(settings.BASE_DIR / "attachments" / "Arjun_Tomar_ML_Resume.pdf")
            )

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
    
    paginator = Paginator(base_qs.order_by("-created_at"), 25)
    page_obj = paginator.get_page(page_number)
    
    context = {
        "emails": page_obj,
        "query": query,
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


def retry_email(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    
    if log.status != "FAILED":
        return redirect("dashboard")
    
    log.status = "PENDING"
    log.save()
    
    send_email_task.delay(
        email = log.email,
        name = log.name,
        company = log.company,
        attachment_path=str(settings.BASE_DIR / "attachments" / "Arjun_Tomar_ML_Resume.pdf")
    )
    
    return redirect("dashboard")

def status_page(request):
    logs = EmailLog.objects.order_by("-created_at")[:100]
    return render (request, "status.html", {"logs":logs})

def email_detail(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    
    return JsonResponse({
        "email": log.email,
        "company": log.company,
        "status": log.status,
        "created_at": log.created_at.strftime("%d-%m-%Y %H:%M:%S"),
        "sent_at": log.sent_at.strftime("%d-%m-%Y %H:%M:%S") if log.sent_at else None,
        "content_url": f"/emails/{log.id}/content/"
    })

def email_content(request, log_id):
    log = EmailLog.objects.get(id=log_id)
    return HttpResponse(
        f"<pre>{log.email_body}</pre>",
        content_type="text/html"
    )