import os
import threading

from flask import Flask
from flask_restful import Api

from api.api_pqr import ApiPqr
from health_check.health_check import HealthCheck
from modelos.modelos import db

API_REST_PORT = int(os.getenv("API_REST_PORT", 5000))


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pqr.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app


app = create_app()
app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

api = Api(app)
api.add_resource(ApiPqr, '/pqrs')

if __name__ == '__main__':
    threading.Thread(target=HealthCheck.init, daemon=True).start()
    app.run(host='0.0.0.0', port=API_REST_PORT, debug=False)
