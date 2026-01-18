import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()

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

def send_mail(to_email, name, company, attachment_path):
    msg = EmailMessage()
    msg['Subject'] = 'Application for Software Development Engineer Internship | Arjun Tomar'
    msg['From'] = os.getenv('EMAIL_USER')
    msg['To'] = to_email
    
    msg.set_content(MAIL_CONTENT.format(name=name, company=company))
    
    with open(attachment_path, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype='application',
            subtype='pdf',
            filename='Arjun_Tomar_ML_Resume.pdf'
        )
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        server.send_message(msg)
    
    return MAIL_CONTENT.format(name=name, company=company)