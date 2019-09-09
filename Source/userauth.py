from flask import request
from flask_restful import Resource, reqparse
from flask_jwt import jwt
from pymysql import InterfaceError

from Config.api import CreateApi

db = CreateApi.create_db_connection()


class UserAuth(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('UserName', required=True, help='UserName is Required')
            parser.add_argument('Password', required=True, help='Password is Required')
            args = parser.parse_args()
            cursor = db.cursor()
            row_count = cursor.execute(
                'select Role from users where UserName=\'' + args['UserName'] + '\'' + 'and Password=\'' + args[
                    'Password'] + '\'')
            row = cursor.fetchone()
            if row_count > 0:
                payload = {
                    'UserName': args['UserName'],
                    'Password': args['Password'],
                    'Role': row[0]
                }
                access_token = jwt.encode(payload, 'secret', algorithm='HS256')
                print(access_token)
                message = {
                    'AuthToken': str(access_token),
                    'Role': payload['Role'],
                    'Request': 'Successful'
                }
            else:
                message = {
                    'AuthToken': 'Null',
                    'Request': 'Wrong Details'
                }
            return (message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def put(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('oldPassword', required=True, help='oldPassword is Required')
            parser.add_argument('newPassword', required=True, help='newPassword is Required')
            args = parser.parse_args()
            x = request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            cursor = db.cursor()
            cursor.execute('SELECT Password FROM users WHERE UserName = %s', (access_token['UserName']))
            pwd = cursor.fetchone()
            if (pwd[0] == args['oldPassword']):
                try:
                    cursor.execute('UPDATE users SET Password = %s WHERE UserName = %s',
                                   (args['newPassword'], access_token['UserName']))
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": "Please try again!"}, 500
                db.commit()
                return {"message": "Password changed successfully"}
            else:
                return {"message": "Password does not match"}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)