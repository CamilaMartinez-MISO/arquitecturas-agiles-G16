FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV INSTANCE_ID=1

CMD ["python", "app.py"]
