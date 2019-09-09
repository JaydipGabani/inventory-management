import datetime

import flask
from flask_jwt import jwt
from flask_restful import Resource, reqparse, request
from pymysql import InterfaceError
from werkzeug.exceptions import BadRequest

from Config.api import CreateApi
from Source.logs import Log

db = CreateApi.create_db_connection()


class Users(Resource):
    def get(self):
        try:
            x = request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            cursor = db.cursor()
            message = []
            row_count = cursor.execute("SELECT UserName,role from users")
            row = cursor.fetchall()
            for item in row:
                message.append({
                    "UserName": item[0],
                    "Role": item[1]
                })
            return flask.jsonify(message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def post(self):
        try:
            x = request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            parser = reqparse.RequestParser()
            parser.add_argument('UserName', required=True, help='UserName is Required')
            parser.add_argument('Role', required=True, help='Role is Required')
            args = parser.parse_args()
            cursor = db.cursor()
            try:
                row_count = cursor.execute(
                    "Insert into users(UserName,Password,Role,LASTDATE,LASTUSER) VALUES (%s,%s,%s,%s,%s)",
                    (args['UserName'], '123456', args['Role'], datetime.datetime.now(), access_token['UserName']))
            except InterfaceError as e:
                CreateApi.reAssignDb()
                print(e)
            except Exception as e:
                print(e.args[1])
                if ("Duplicate entry" in e.args[1]):
                    raise BadRequest("user already exists")
                else:
                    raise BadRequest(str(e.args[1]))
            row = cursor.fetchone()
            l = Log
            x = True
            x = l.register(request.headers.get('Authorization'), 'Add User:%s' % args['UserName'], True)
            if x == True:
                db.commit()
            message = {
                'message': 'adduser',
                'data': {
                    "UserName": args['UserName'],
                    "Role": args['Role']
                }
            }
            return (message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def put(self):
        try:
            x = request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            parser = reqparse.RequestParser()
            parser.add_argument('Role')
            parser.add_argument('UserName')
            args = parser.parse_args()
            cursor = db.cursor()
            row_count = cursor.execute(
                'UPDATE users SET Role = %s ,LASTDATE = %s ,LASTUSER = %s WHERE UserName = %s',
                (args['Role'], datetime.datetime.now(), access_token['UserName'], args['UserName']))
            if row_count > 0:
                l = Log
                x = l.register(request.headers.get('Authorization'),
                               'UPDATE Role: %s of User: %s' % (args['Role'], args['UserName']),
                               True)
                if x == True:
                    db.commit()
                    return ({
                        'message': 'updateuser',
                        'data': {
                            "UserName": args['UserName'],
                            "Role": args['Role']
                        }
                    })
                else:
                    raise BadRequest("Try Again")
            else:
                raise BadRequest("Try Again")
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def delete(self):
        try:
            x = flask.request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            try:
                data = flask.request.get_json()
                cursor = db.cursor()
                cursor.execute(
                    "DELETE from users where UserName = %s ", (data['UserName']))
            except InterfaceError as e:
                CreateApi.reAssignDb()
                print(e)
            except Exception as e:
                raise BadRequest(str(e))
            l=Log
            x = l.register(request.headers.get('Authorization'),
                           'Delete user: %s' % (data['UserName']),
                           True)
            if x == True:
                db.commit()
                return ({
                    'message': 'deleteuser',
                })
            else:
                raise BadRequest("Try Again")
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)