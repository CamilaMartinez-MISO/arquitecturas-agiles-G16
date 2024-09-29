import logging
import os

import jwt
from flask import Flask, jsonify, request
from jwt import InvalidTokenError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

API_REST_PORT = int(os.getenv("API_REST_PORT", 5010))
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

app = Flask(__name__)


@app.route("/validate_permission", methods=["GET"])
def validate_permission():
    token_header = request.headers.get("Authorization")
    if not token_header or not token_header.startswith("Bearer "):
        return jsonify({"message": "Token no enviado en la solicitud"}), 401

    token = token_header.split(" ")[1]
    body = request.get_json()
    if not body:
        return jsonify({"message": "Solicitud inválida, falta cuerpo JSON"}), 400

    resource = body.get("resource")
    method = body.get("method")
    if not resource or not method:
        return jsonify({"message": "Solicitud inválida, faltan campos"}), 400

    logging.info(f"Validating token for resource: {resource}, method: {method}")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        permisos = payload.get("permisos", [])
        if permisos:
            for permiso_str in permisos:
                method_allowed, resource_allowed = permiso_str.split()
                if resource == resource_allowed and method == method_allowed:
                    logging.info("Acceso permitido.")
                    return jsonify({"message": "Acceso permitido"}), 200
            return jsonify({"message": "No se tiene permiso a los recursos solicitados"}), 403
        else:
            return jsonify({"message": "No se adjuntaron permisos en la solicitud"}), 403
    except InvalidTokenError:
        return jsonify({"message": "Token inválido!"}), 401
    except Exception as e:
        logging.error(f"Error processing token: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
