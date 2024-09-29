FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV VALIDATOR_URL=validator:5010
ENV PQR_SERVICE_URL=pqr:5000

CMD ["python", "app.py"]
