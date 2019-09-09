import flask

from flask_restful import Resource
from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, get_from_buffer_manifest

db = CreateApi.create_db_connection()


class Replacement(Resource):
    def post(self):
        access_token = authenticator(flask.request.headers.get('Authorization'))
        try:
            data = flask.request.get_json()
            cursor = db.cursor()
            rep = data['replacement']
            for i in range(0, len(rep)):
                if (int(rep[i]['rejection'])) > 0:
                    if cursor.execute('DELETE FROM rejection WHERE BARCODE = %s', rep[i]['rejection']) > 0:
                        if cursor.execute('select TICKET from bufferpurchasingmanifest where NO = %s',
                                          rep[i]['replacement']) > 0:
                            ticket = cursor.fetchone()
                            cursor.execute('UPDATE bufferpurchasingmanifest SET REPLACEMENT = 0 WHERE NO = %s',
                                           (rep[i]['replacement']))
                            cursor.execute('UPDATE inventorystorage SET DESCRIPTION = %s WHERE BARCODE = %s',
                                           ("replaced with " + str(ticket[0]), rep[i]['rejection']))
                            if not Log.register(flask.request.headers.get('Authorization'),
                                                "Replace item " + str(rep[i]['replacement']),
                                                True):
                                db.rollback()
                                return {'message': 'try again'}, 500
                        else:
                            db.rollback()
                            return {'message': 'try again'}, 500
                    else:
                        db.rollback()
                        return {'message': 'try again'}, 500
            db.commit()
            return flask.jsonify(get_from_buffer_manifest(cursor, access_token['UserName'], False))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            db.rollback()
            return {'message': 'try again'}, 500
