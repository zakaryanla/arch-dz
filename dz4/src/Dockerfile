FROM python:3.11.9-slim

WORKDIR /app

COPY . /app
RUN apt-get update &&  apt-get install libpq-dev gcc -y && rm -rf /var/lib/apt/lists/*
RUN pip3 install -r requirements.txt
ENV FLASK_APP=api.py

ENTRYPOINT ["python3"]
CMD ["api.py"]