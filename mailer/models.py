from django.db import models

# Create your models here.
class EmailLog (models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    
    email_body = models.TextField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", 'pending'),
            ("SUCCESS", 'success'),
            ("FAILED", 'failed'),
        ],
        default='PENDING'
    )
    
    task_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    follow_up_at = models.DateTimeField(blank=True, null=True)
    follow_up_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ("email", "company")

    def __str__ (self):
        return f"{self.email} - {self.status}"