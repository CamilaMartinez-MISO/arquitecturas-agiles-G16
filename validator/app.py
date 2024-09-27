import os

import jwt
from jwt import InvalidTokenError
from flask import Flask, jsonify, request

API_REST_PORT = int(os.getenv("API_REST_PORT", 5010))
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

app = Flask(__name__)

app_context = app.app_context()
app_context.push()



@app.route("/validate_permission", methods=["GET"])
def validate_permission():
    token = request.headers.get('Authorization')
    body = request.get_data()
    resource = body.resource
    method = body.method

    if not token:
        return jsonify({'message': 'Token no enviado en la solicitud'}), 401

    token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if len(payload) > 0 : 
            print(f'Payload: {payload}')
            permiso_str = payload['permisos'][0]
            method_allowed, resource_allowed = permiso_str.split()

            if resource == resource_allowed and method == method_allowed:
                print("Acceso permitido.")
                return jsonify({'message': 'Acceso permitido'}), 200
            return jsonify({'message': 'No se tiene permiso a los recursos solicitados'}), 401

        return jsonify({'message': 'No se adjuntaron permisos en la solicitud'}), 401
    except InvalidTokenError:
        return jsonify({'message': 'Token invalido!'}), 401
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=API_REST_PORT, debug=False)
