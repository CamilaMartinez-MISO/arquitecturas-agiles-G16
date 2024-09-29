import logging
import os

import requests
from flask import Flask, jsonify, request, Response

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

API_REST_PORT = int(os.getenv("API_REST_PORT", 5000))
VALIDATOR_URL = os.getenv("VALIDATOR_URL", "validator:5010")
PQR_SERVICE_URL = os.getenv("PQR_SERVICE_URL", "pqr:5000")
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pqr.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


app = create_app()
app_context = app.app_context()
app_context.push()


def get_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None


@app.route("/api/pqrs", methods=["GET", "POST"])
def access_resource():
    token = get_token_from_header()
    if not token:
        return jsonify({"message": "Token no proporcionado o inválido"}), 401

    logging.info(f"Validating token with validator service at http://{VALIDATOR_URL}/validate_permission")
    try:
        # Verify the token with the validator
        response = requests.get(
            f"http://{VALIDATOR_URL}/validate_permission",
            json={"resource": "/pqrs", "method": request.method},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=5,
        )
        logging.info(f"Validator response status code: {response.status_code}")

        if response.status_code == 200:
            # Access is permitted, proxy the request to the PQR service
            return proxy_request_to_pqr()
        else:
            return jsonify({"message": "Acceso denegado"}), 403
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to validator service: {e}")
        return jsonify({"message": "Error en el servicio de validación"}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"message": "Error interno del servidor"}), 500


def proxy_request_to_pqr():
    try:
        pqr_url = f"http://{PQR_SERVICE_URL}/pqrs"
        logging.info(f"Proxying request to PQR service at {pqr_url}")
        if request.method == "GET":
            pqr_response = requests.get(pqr_url, timeout=5)
        elif request.method == "POST":
            pqr_response = requests.post(pqr_url, json=request.get_json(), timeout=5)
        else:
            return jsonify({"message": "Método no soportado"}), 405

        return Response(
            pqr_response.content,
            status=pqr_response.status_code,
            content_type=pqr_response.headers.get("Content-Type", "application/json"),
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to PQR service: {e}")
        return jsonify({"message": "Error en el servicio PQR"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
