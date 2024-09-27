import logging
import os

import jwt
import requests
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

API_REST_PORT = int(os.getenv("API_REST_PORT", 5000))
VALIDATOR_URL = os.getenv("VALIDATOR_URL", "validator:5010")
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")


def create_app(config_name):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pqr.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


app = create_app("default")
app_context = app.app_context()
app_context.push()


@app.route("/api/pqrs", methods=["POST"])
def access_resource():
    token = request.headers.get("Authorization").split(" ")[1]  # Extraer el token
    logging.info(f"http://{VALIDATOR_URL}/validate_permission")
    try:
        # Verificar el token con el autorizador
        response = requests.get(
            f"http://{VALIDATOR_URL}/validate_permission",
            json={"resource": "/pqrs", "method": "POST"},
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
        )
        logging.info(response)
        if response.status_code == 200:
            # El acceso está permitido, redirigir a microservicio
            return jsonify({"message": "Acceso permitido a los recursos."}), 200
        else:
            return jsonify({"message": "Acceso denegado"}), 403
    except Exception as e:
        logging.info(e)
        return jsonify({"message": "Token inválido o expirado"}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
