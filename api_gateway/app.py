import os

import jwt
import requests
from flask import Flask, jsonify, request

API_REST_PORT = int(os.getenv("API_REST_PORT", 5000))
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")


def create_app(config_name):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pqr.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


app = create_app("default")
app_context = app.app_context()
app_context.push()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
