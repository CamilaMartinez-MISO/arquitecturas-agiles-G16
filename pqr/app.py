import os
from flask import Flask
import threading

from flask_restful import Api

from modelos import db
from api import api_pqr
from health_check import health_check

API_REST_PORT = int(os.getenv("API_REST_PORT", 5000))

def create_app(config_name):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pqr.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

app = create_app('default')
app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

api = Api(app)

api.add_resource(api_pqr.ApiPqr, '/pqrs')

if __name__ == '__main__':
    rabbitmq_thread = threading.Thread(target=health_check.HealthCheck.init, daemon=True)
    rabbitmq_thread.start()

    app.run(host='0.0.0.0', port=API_REST_PORT, debug=False)