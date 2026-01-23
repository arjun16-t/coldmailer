from django.urls import path
from .views import upload_file, preview_email, send_emails, dashboard, schedule_followup
from .views import retry_email, status_page, dashboard_data, email_detail, email_content

urlpatterns = [
    path("", upload_file, name="upload"),
    path("preview/", preview_email, name="preview_email"),
    path("send/", send_emails, name="send_emails"),         # POST only
    
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/data/", dashboard_data, name="dashboard_data"),
    
    path("email/<int:log_id>/", email_detail, name="email_detail"),
    path("emails/<int:log_id>/content/", email_content),
    path("followup/<int:log_id>/", schedule_followup, name="schedule_followup"),

    path("retry/<int:log_id>/", retry_email, name="retry_email"),
    path("status/", status_page, name="status"),
]