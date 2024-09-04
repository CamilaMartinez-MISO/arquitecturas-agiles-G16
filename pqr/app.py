from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from redis import Redis
from rq import Queue
from pqr import create_app


app = create_app('default')
app_context = app.app_context()
app_context.push()

db = SQLAlchemy()
ma = Marshmallow(app)
api = Api(app)

db.init_app(app)

class PQR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime)
    descripcion = db.Column(db.String(255))
    estado = db.Column(db.String(50))

class PQRSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ("id", "fecha_creacion", "descripcion", "estado")

class PQRResource(Resource):
    def get(self):
        pqr = PQR.query.all()
        pqr_schema = PQRSchema(many=True)
        return pqr_schema.dump(pqr)
    
db.create_all()
api.add_resource(PQRResource, '/pqrs')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')