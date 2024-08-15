FROM python:3.11.9-slim

WORKDIR /app

COPY . /app
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["api.py"]
