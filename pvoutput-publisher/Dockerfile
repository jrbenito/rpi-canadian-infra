FROM python:3-alpine

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

VOLUME ["/app/config"]

CMD ["python", "./app.py"]