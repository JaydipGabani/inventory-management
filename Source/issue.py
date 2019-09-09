import flask
from flask_restful import Resource, request
from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, edittag_json_response_array

db = CreateApi.create_db_connection()


class Issue(Resource):
    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            args = flask.request.get_json()
            cursor = db.cursor()
            cursor.execute('SELECT LOCATIONGRID FROM inventorystorage WHERE BARCODE = %s', (args['BARCODE']))
            loc = cursor.fetchone()
            if loc[0] == 'NA':
                status = cursor.execute('UPDATE inventorystorage SET LOCATIONGRID = %s, NAtoLOC = 1 WHERE BARCODE = %s',
                                        (args['LOCATIONGRID'], args['BARCODE']))
            else:
                status = cursor.execute('UPDATE inventorystorage SET LOCATIONGRID = %s WHERE BARCODE = %s',
                                        (args['LOCATIONGRID'], args['BARCODE']))
            if status > 0:
                if Log.register(request.headers.get('Authorization'),
                                'Issue item %s from loc %s to loc %s' % (args['BARCODE'], loc[0], args['LOCATIONGRID']),
                                True):
                    db.commit()
                    return flask.jsonify(edittag_json_response_array(cursor, args['BARCODE']))
                else:
                    return {'message': 'Try again'}, 500
            else:
                return {'message': 'Try again'}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)