FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV API_REST_PORT=5010

ENV SECRET_KEY=secret_key
ENV FLASK_RUN_PORT=5010

CMD ["python", "app.py"]
