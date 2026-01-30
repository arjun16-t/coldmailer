web: gunicorn coldmailer.wsgi --log-file -
worker: celery -A coldmailer worker --loglevel=info