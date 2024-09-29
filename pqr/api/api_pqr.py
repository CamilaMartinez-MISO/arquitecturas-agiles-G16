import random

from flask import jsonify
from flask_restful import Resource

pqrs = [
    {"name": "PQR 1", "Category": "Service A", "Priority": 1},
    {"name": "PQR 2", "Category": "Service B", "Priority": 2},
    {"name": "PQR 3", "Category": "Service C", "Priority": 1},
    {"name": "PQR 4", "Category": "Service D", "Priority": 5},
    {"name": "PQR 5", "Category": "Service E", "Priority": 4},
]


class ApiPqr(Resource):
    def get(self):
        if random.choice([True, False]):
            return {"message": "Service unavailable"}, 503
        return jsonify(pqrs)
