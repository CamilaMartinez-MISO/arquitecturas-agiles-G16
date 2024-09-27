import os

import jwt
from jwt import InvalidTokenError
from flask import Flask, jsonify, request

API_REST_PORT = int(os.getenv("API_REST_PORT", 5010))
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

app = Flask(__name__)

app_context = app.app_context()
app_context.push()

allowed_resources = {"methods": ["GET", "POST"], "endpoints": ["/pqr", "/settlement"]}


@app.route("/validate_permission", methods=["GET"])
def validate_permission():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'message': 'Token no enviado en la solicitud'}), 401

    token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if len(payload) > 0 : 
            print(f'Payload: {payload}')
            permiso_str = payload['permisos'][0]
            metodo, ruta = permiso_str.split()
            if metodo in allowed_resources['methods'] and ruta in allowed_resources['endpoints']:
                print("Acceso permitido.")
                return jsonify({'message': 'Acceso concedido'}), 200
            return jsonify({'message': 'No se tiene permiso a los recursos solicitados'}), 401

        return jsonify({'message': 'No se adjuntaron permisos en la solicitud'}), 401
    except InvalidTokenError:
        return jsonify({'message': 'Token invalido!'}), 401
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
