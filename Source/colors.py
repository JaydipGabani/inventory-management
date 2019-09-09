import flask
import datetime
from flask_restful import Resource, request
from pymysql import InterfaceError
from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator

db = CreateApi.create_db_connection()


class Colors(Resource):
    def get(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            data = request.args
            cursor = db.cursor()
            if data['FINISHID'] == "" and data['FINISHNAME'] == "":
                cursor.execute('SELECT FINISHID, FINISHNAME FROM colors ORDER BY FINISHNAME')
            elif data['FINISHNAME'] == "":
                cursor.execute('SELECT FINISHID, FINISHNAME FROM colors WHERE FINISHID LIKE %s ORDER BY FINISHNAME',
                               (data['FINISHID'] + '%'))
            elif data['FINISHID'] == "":
                cursor.execute('SELECT FINISHID, FINISHNAME FROM colors WHERE FINISHNAME LIKE %s ORDER BY FINISHNAME',
                               (data['FINISHNAME'] + '%'))
            else:
                cursor.execute(
                    'SELECT FINISHID, FINISHNAME FROM colors WHERE FINISHNAME LIKE %s AND FINISHID LIKE %s ORDER BY FINISHNAME',
                    ((data['FINISHNAME'] + '%'), (data['FINISHID'] + '%')))
            colors = cursor.fetchall()
            res = []
            for color in colors:
                res.append({
                    "FINISHID": color[0],
                    "FINISHNAME": color[1]
                })
            return flask.jsonify(res)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500

    def post(self):
        data = {}
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            data = request.get_json()
            cursor = db.cursor()
            if cursor.execute(
                    "insert into colors (FINISHID,FINISHNAME,LASTDATE,LASTUSER) values(%s,%s,%s,%s)",
                    (data['FINISHID'], data['FINISHNAME'], datetime.datetime.now(), access_token['UserName'])) > 0:
                if Log.register(request.headers.get('Authorization'),
                                'New Color added with FID:%s, FNAME:%s ' % (data['FINISHID'], data['FINISHNAME']),
                                True):
                    db.commit()
                    return ({
                        'FINISHID': data['FINISHID'],
                        'FINISHNAME': data['FINISHNAME']
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
                message = {'message': "Color %s already exists." % data['FINISHID']}
            else:
                message = {"message": str(e)}
            db.rollback()
            return message, 500

    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            data = request.get_json()
            cursor = db.cursor()
            values = []
            cursor.execute('UPDATE colors SET FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID = %s',
                           (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName'], data['FINISHID']))
            if cursor.execute('SELECT PROJECTID FROM projects WHERE FINISHID = %s', data['FINISHID']) != 0:
                projects = cursor.fetchall()
                for project in projects:
                    values.append('"' + project[0] + '"')
                values = '(' + ','.join(values) + ')'
                cursor.execute(
                    'update projects set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
                cursor.execute(
                    'update inventorystorage set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE" AND PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
                cursor.execute(
                    'update bufferpurchasingmanifest set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE" AND PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
                cursor.execute(
                    'update purchasingmanifest set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE" AND PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
                cursor.execute(
                    'update warehousemanifest set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE" AND PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
                cursor.execute(
                    'update rejection set FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE" AND PROJECTID IN ' + values,
                    (data['FINISHNAME'], datetime.datetime.now(), access_token['UserName']))
            if Log.register(request.headers.get('Authorization'),
                            'FINISH ID %s updated with FNAME:%s and it updated projects: %s' % (
                                    data['FINISHID'], data['FINISHNAME'], values),
                            True):
                db.commit()
            return flask.jsonify(data)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            db.rollback()
            return {"message": str(e)}, 500
