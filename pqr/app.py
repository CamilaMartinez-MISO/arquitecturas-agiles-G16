from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource

from modelos import db

from api import api_pqr

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


db.create_all()

api.add_resource(api_pqr.ApiPqr, '/pqrs')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')