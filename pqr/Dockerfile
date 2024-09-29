FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV INSTANCE_ID=1
ENV RABBITMQ_HOST=rabbitmq
ENV RABBITMQ_USER=guest
ENV RABBITMQ_PASSWORD=guest

CMD ["python", "app.py"]
