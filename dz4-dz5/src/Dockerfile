FROM python:3.11.9-slim

WORKDIR /app
COPY . /app

RUN apt-get update &&  apt-get install libpq-dev gcc -y && rm -rf /var/lib/apt/lists/*
RUN pip3 install -r requirements.txt
ENV FLASK_APP=app.py
ENV PROMETHEUS_MULTIPROC_DIR /tmp
ENV prometheus_multiproc_dir /tmp

CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]