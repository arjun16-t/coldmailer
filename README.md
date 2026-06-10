# 🚀 ColdMailer

ColdMailer is a production-oriented cold email automation system built with Django, Celery, Redis, and PostgreSQL.

The project focuses on scalable backend architecture, asynchronous processing, distributed services, and real-world deployment practices rather than just local development.

---

# ✨ Features

- 📄 Upload resumes for personalized cold email generation
- ⚡ Asynchronous email processing using Celery workers
- 🔁 Automatic retry system for failed emails
- 🧹 Scheduled background jobs using Celery Beat
- 🗂️ Temporary centralized file storage
- 🧠 Designed for multi-service deployment environments
- 📊 Email logging and status tracking
- ☁️ Cloud deployment ready

---

# 🏗️ Architecture

```mermaid
flowchart LR
    U[User / Browser]
    W[Django Web App]
    DB[(PostgreSQL)]
    R[(Redis Broker)]
    CW[Celery Worker]
    CB[Celery Beat]
    FS[(Central File Storage)]
    SMTP[SMTP Provider]

    U -->|Upload resume & inputs| W

    W -->|Store resume temporarily| FS
    W -->|Enqueue async task| R
    W -->|Create email logs| DB

    R -->|Dispatch task| CW
    CW -->|Read resume| FS
    CW -->|Send email| SMTP
    CW -->|Update logs/status| DB

    CB -->|Schedule retries & cleanup| R
```

---

# 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Backend | Django |
| Language | Python |
| Database | PostgreSQL |
| Queue/Broker | Redis |
| Async Workers | Celery |
| Scheduler | Celery Beat |
| Deployment | Railway |
| Static Files | WhiteNoise |

---

# 📂 Project Structure

```bash
coldmailer/
│
├── coldmailer/          # Django project settings
├── mailer/              # Main application logic
├── templates/           # HTML templates
├── static/              # CSS and JS
├── attachments/         # Local development uploads
├── manage.py
└── requirements.txt
```

---

# ⚙️ Environment Variables

Create a `.env` file in the root directory.

```env
SECRET_KEY=your_secret_key

DEBUG=True

DATABASE_URL=postgresql://username:password@localhost:5432/coldmailer

REDIS_URL=redis://127.0.0.1:6379/0

SMTP_ENCRYPTION_KEY=your_encryption_key
```

---

# 🚀 Local Setup

## 1. Clone Repository

```bash
git clone https://github.com/your-username/coldmailer.git
cd coldmailer
```

---

## 2. Create Virtual Environment

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🧰 Install & Start Redis

## Ubuntu

```bash
sudo apt update
sudo apt install redis-server
```

Start Redis:

```bash
sudo systemctl start redis-server
```

Verify Redis:

```bash
redis-cli ping
```

Expected output:

```bash
PONG
```

---

# 🗄️ Setup PostgreSQL

Install PostgreSQL and create a database.

Example:

```sql
CREATE DATABASE coldmailer;
```

Update your `DATABASE_URL` accordingly.

---

# 🧱 Run Database Migrations

```bash
python manage.py migrate
```

---

# 📦 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

# ▶️ Running the Project

## Start Django Server

```bash
python manage.py runserver
```

---

## Start Celery Worker

```bash
celery -A coldmailer worker --loglevel=info
```

---

## Start Celery Beat

```bash
celery -A coldmailer beat --loglevel=info
```

---

# 🌐 Production Deployment (Railway)

The project is designed to run as multiple services:

- Django Web Service
- Celery Worker
- Celery Beat Scheduler
- Redis
- PostgreSQL

---

# 🚀 Railway Start Command

```bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn coldmailer.wsgi:application --bind 0.0.0.0:$PORT
```

---

# 📌 Important Production Notes

- Do not use SQLite in production
- Redis is required for Celery
- PostgreSQL is required for persistent data
- Temporary files should use centralized/shared storage
- Services are stateless and distributed

---

# 📈 Future Improvements

- 🤖 AI-generated personalized emails
- 📊 Analytics dashboard
- 📄 Resume parser
- 🎯 ATS optimization
- 📬 Campaign tracking
- 📑 Email templates

---

# 🧠 What This Project Demonstrates

This project focuses on:

- Distributed backend systems
- Production deployment
- Asynchronous task queues
- Service-oriented architecture
- Fault tolerance
- Scalability considerations

---

# 👨‍💻 Author

## Arjun Tomar

---

# ⭐ Final Note

ColdMailer was built as a backend engineering project to explore how production systems behave beyond local development.

The focus was not only on features, but also on reliability, architecture, deployment, and scalability.
