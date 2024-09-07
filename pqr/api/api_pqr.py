from flask_restful import Resource

class ApiPqr(Resource):
    def get(self):
        return {"message": "Ok"}, 200
    