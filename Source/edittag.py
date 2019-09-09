import flask
import datetime
from flask_jwt import jwt
from flask_restful import Resource, request
from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from customErrors import ProjectNotFound, InvalidProjectUpdate
from helper.helper import update_project, calculate_netweight, authenticator, edittag_json_response_array, \
    move_to_empty_storage

db = CreateApi.create_db_connection()


class Edittag(Resource):
    def get(self):
        access_token = authenticator(request.headers.get('Authorization'))
        barcode = request.args.get('BARCODE')
        try:
            cursor = db.cursor()
            return flask.jsonify(edittag_json_response_array(cursor, barcode))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return {'message': str(e)}, 500

    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            Data = flask.request.get_json()
            message = {}
            cursor = db.cursor()
            if Data['status'] == "loc":
                weight_count = cursor.execute(
                    'select LBFT from rawvalues where NOREX = %s and LOCATION = %s', (Data['NOREX'], Data['LOCATION']))
                weight = cursor.fetchone()
                netweight = calculate_netweight(Data['QTY'], weight[0], Data['LENGTH'])
                if int(Data['QTY']) > 0:
                    row_count = cursor.execute(
                        'UPDATE inventorystorage set QTY = %s, LOCATIONGRID = %s, LENGTH = %s, NETWEIGHT = %s, LASTDATE = %s, LASTUSER = %s where BARCODE = %s',
                        (Data['QTY'], Data['LOCATIONGRID'], Data['LENGTH'], netweight, datetime.datetime.now(),
                         access_token['UserName'], Data['BARCODE']))
                    if row_count > 0:
                        if Log.register(request.headers.get('Authorization'), 'Update location of %s' % Data['BARCODE'],
                                        True):
                            db.commit()
                    else:
                        return {'message': 'please try again'}, 404
                elif int(Data['QTY']) == 0:
                    if move_to_empty_storage(cursor, Data['BARCODE'], access_token['UserName']) > 0:
                        if Log.register(request.headers.get('Authorization'), 'Remove item %s' % Data['BARCODE'],
                                        True):
                            db.commit()
                            return {}
                    else:
                        db.rollback()
                        return {'message': 'please try again1'}, 404

                else:
                    return {"message": "Quantity must be possitive"}, 500
            elif Data['status'] == "norex":
                norex_count = cursor.execute("SELECT * from rawvalues where NOREX = %s and LOCATION =%s",
                                             (Data['NOREX'], Data['LOCATION']))
                if norex_count == 0:
                    return {'message': 'Norex not found'}, 404
                norex = cursor.fetchone()
                weight_count = cursor.execute('SELECT QTY,LENGTH from inventorystorage where BARCODE =%s',
                                              (Data['BARCODE']))
                if weight_count == 0:
                    return {'message': 'try again'}, 500
                weight = cursor.fetchone()
                netweight = calculate_netweight(weight[0], weight[1], norex[8])
                print((norex[2], netweight, norex[3], norex[4], norex[6], norex[7], norex[8], datetime.datetime.now(),
                       access_token['UserName'], Data['BARCODE']))
                norex_count = cursor.execute(
                    'UPDATE inventorystorage set NOREX= %s,LOCATION = %s, ASTRO = %s, NETWEIGHT = %s, KEYMARK = %s, EASCO = %s, DESCRIPTION = %s ,MODEL = %s ,LBFT =%s ,LASTDATE= %s ,LASTUSER =%s where BARCODE = %s',
                    (Data['NOREX'], Data['LOCATION'], norex[2], netweight, norex[3], norex[4], norex[6], norex[7],
                     norex[8],
                     datetime.datetime.now(), access_token['UserName'], Data['BARCODE']))
                if norex_count > 0:
                    if Log.register(request.headers.get('Authorization'), 'Update norex of %s' % Data['BARCODE'], True):
                        db.commit()
                else:
                    return {'message': 'please try again'}, 404
            elif Data['status'] == "project":
                update_project(cursor, Data['PROJECTID'], 'inventorystorage', 'BARCODE', Data['BARCODE'],
                               access_token['UserName'],access_token['Role'])
                if Log.register(request.headers.get('Authorization'),
                                'Tag %s project updated to %s ' % (Data['BARCODE'], Data['PROJECTID']),
                                True):
                    db.commit()
            else:
                return {'message': 'try again'}, 500
            return flask.jsonify(edittag_json_response_array(cursor, Data['BARCODE']))
        except InvalidProjectUpdate as e:
            return {'message': str(e)}, 500
        except ProjectNotFound as e:
            return {'message': str(e)}, 404
        except InterfaceError as e:
            CreateApi.reAssignDb()
        except Exception as e:
            return {'message': str(e)}, 500
