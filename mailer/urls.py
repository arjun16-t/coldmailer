from django.urls import path
from .views import (
    smtp_entrypoint,
    reset_smtp,
    upload_file,
    preview_email,
    send_emails,
    dashboard,
    schedule_followup,
    retry_email,
    dashboard_data,
    email_detail,
    email_content,
    suppression_list
)

urlpatterns = [
    path("", smtp_entrypoint, name="smtp_entry"),
    path("upload/", upload_file, name="upload"),
    path("preview/", preview_email, name="preview_email"),
    path("send/", send_emails, name="send_emails"),         # POST only
    path("suppression/", suppression_list, name="suppression_list"),
    path("reset-smtp/", reset_smtp, name="reset_smtp"),

    
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/data/", dashboard_data, name="dashboard_data"),
    
    path("email/<int:log_id>/", email_detail, name="email_detail"),
    path("emails/<int:log_id>/content/", email_content),
    path("followup/<int:log_id>/", schedule_followup, name="schedule_followup"),

    path("retry/<int:log_id>/", retry_email, name="retry_email"),
]