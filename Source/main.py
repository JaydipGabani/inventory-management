from flask_restful import Resource,reqparse
from flask_jwt import jwt
from Config.api import CreateApi
from flask import jsonify, request
db=CreateApi.create_db_connection()

class MainHandler(Resource):
    def post(self):
        x= request.headers.get('Authorization')
        try:
            x=x[2:-1]
        except TypeError:
            print(x)
        print(x)
        access_token= jwt.decode(x,'secret',algorithms='HS256',verify=False)
        print(access_token)
        
