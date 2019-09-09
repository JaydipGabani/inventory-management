import flask

from flask_restful import Resource, reqparse, request
from flask_jwt import jwt, logger
import datetime

from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, update_project_tuple

db = CreateApi.create_db_connection()


class Project(Resource):
    def get(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            message = []
            COUNT = int(request.args.get('COUNT'))
            COLUMN = request.args.get('COLUMN')
            VALUE = request.args.get('VALUE')
            print(request.args.get('ACTIVE'))
            if request.args.get('ACTIVE') == 'true':
                query = "Select DISTINCT PROJECTID, PROJECTNAME, FINISHID, FINISHNAME " \
                        "from inventorystorage " \
                        "where FINISHID != '' AND "
            else:
                query = "Select PROJECTID, PROJECTNAME, FINISHID, FINISHNAME from projects where "
            print(query)
            if COUNT >= 1:
                COLUMN = COLUMN.split(',')
                VALUE = VALUE.split(',')
                for i in range(0, COUNT):
                    if i == COUNT - 1:
                        query = query + COLUMN[COUNT - 1] + ' LIKE \'%' + VALUE[COUNT - 1] + '%\''
                        break
                    query = query + COLUMN[i] + ' LIKE \'%' + VALUE[i] + '%\' AND '
            else:
                query = query + COLUMN + ' 1'
            cursor = db.cursor()
            row_count = cursor.execute(query)
            if row_count == 0:
                return {"message": "project not found"}, 400
            row = cursor.fetchall()
            for i in range(0, row_count):
                message.append({
                    "PROJECTID": row[i][0],
                    "PROJECTNAME": row[i][1],
                    "FINISHID": row[i][2],
                    "FINISHNAME": row[i][3]
                })
            return flask.jsonify(message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500

    def post(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            parser = reqparse.RequestParser()
            parser.add_argument('PROJECTID')
            parser.add_argument('PROJECTNAME')
            parser.add_argument('FINISHID')
            parser.add_argument('FINISHNAME')
            args = parser.parse_args()
            cursor = db.cursor()
            row_count = cursor.execute(
                "insert into projects (PROJECTID,PROJECTNAME,FINISHID,FINISHNAME,LASTDATE,LASTUSER) values(%s,%s,%s,%s,%s,%s)",
                (args['PROJECTID'], args['PROJECTNAME'], args['FINISHID'], args['FINISHNAME'],
                 datetime.datetime.now(),
                 access_token['UserName']))
            if row_count > 0:
                if Log.register(request.headers.get('Authorization'),
                                'New Project added with PID:%s ,PNAME:%s, FID:%s ,FNAME:%s' % (
                                        args['PROJECTID'], args['PROJECTNAME'], args['FINISHID'], args['FINISHNAME']),
                                True):
                    db.commit()
                    return ({
                        'PROJECTID': args['PROJECTID'],
                        'PROJECTNAME': args['PROJECTNAME'],
                        'FINISHID': args['FINISHID'],
                        'FINISHNAME': args['FINISHNAME']
                    })
                else:
                    db.rollback()
                    return ({'message': 'Error - Try Again'}), 500
            else:
                db.rollback()
                return ({'message': 'Error - Try Again'}), 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            if "Duplicate entry" in str(e):
                message = {'message': "Project %s already exists." % args['PROJECTID']}
            else:
                message = {"message": str(e)}
            db.rollback()
            return message, 500

    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))

            parser = reqparse.RequestParser()
            parser.add_argument('PROJECTID')
            parser.add_argument('PROJECTNAME')
            parser.add_argument('FINISHID')
            parser.add_argument('FINISHNAME')
            args = parser.parse_args()
            cursor = db.cursor()
            if args['PROJECTID'] == '9999':
                return {"message": "stock cannot be edited"}, 500
            update_project_tuple(cursor, args, access_token['UserName'])
            if Log.register(request.headers.get('Authorization'),
                            'Project %s updated with values PNAME:%s, FID:%s ,FNAME:%s' % (
                                    args['PROJECTID'], args['PROJECTNAME'], args['FINISHID'], args['FINISHNAME']),
                            True):
                db.commit()
                return {
                    'PROJECTID': args['PROJECTID'],
                    'PROJECTNAME': args['PROJECTNAME'],
                    'FINISHID': args['FINISHID'],
                    'FINISHNAME': args['FINISHNAME']
                }
            else:
                db.rollback()
                return {'Message': 'Try again'}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500
