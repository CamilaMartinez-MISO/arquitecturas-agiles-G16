FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV VALIDATOR_URL=validator:5010

CMD ["python", "app.py"]
