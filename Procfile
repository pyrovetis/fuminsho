web: gunicorn -b 0.0.0.0:8000 -w 2 --log-file - --log-level debug fuminsho.wsgi
worker: python manage.py runscript main