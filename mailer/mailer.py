import smtplib
from email.message import EmailMessage
from .smtp_store import get_smtp_credentials

MAIL_CONTENT="""
Dear {name},

I hope you are doing well.

I am writing to inquire about the availability of Summer Internship opportunities at {company} in technical roles, particularly in Software Development/Engineering and machine learning–related domains.

I am currently pursuing my Bachelor’s degree in Engineering from Pimpri Chinchwad University, Pune and have a strong interest in building scalable software systems as well as applying machine learning techniques to solve real-world problems and deploy applications. I have hands-on experience with programming, data handling, problem-solving, and core computer science fundamentals, along with foundational experience in machine learning concepts, model development, and Python-based ML libraries with advanced Agentic AI and RAG-based pipeline deployment.

I have attached my resume for your reference and would be happy to provide any additional information if required.

Thank you for your time and consideration. I look forward to hearing from you.

Warm regards,
Arjun Tomar
B.Tech - CSE AI/ML (III Year)
Pimpri Chinchwad University, Pune
www.linkedin.com/in/arjunstomar
www.github.com/arjun16-t
"""

def send_mail(to_email, subject, body, attachment_path=None):
    creds = get_smtp_credentials()
    if not creds:
        raise RuntimeError("SMTP credentials not configured")
    
    smtp_email = creds["email"]
    smtp_password = creds["password"]
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_email
    msg['To'] = to_email
    
    msg.set_content(body)
    
    if attachment_path:
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='pdf',
                filename='Arjun_Tomar_ML_Resume.pdf'
            )
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(smtp_email, smtp_password)
        server.send_message(msg)