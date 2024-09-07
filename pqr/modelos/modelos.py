from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class PQR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime)
    descripcion = db.Column(db.String(255))
    estado = db.Column(db.String(50))

class PQRSchema():
    class Meta:
        fields = ("id", "fecha_creacion", "descripcion", "estado")


