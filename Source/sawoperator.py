import flask
from flask_restful import Resource, request
from pymysql import InterfaceError
from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, move_to_empty_storage

db = CreateApi.create_db_connection()


class Sawoperator(Resource):
    def get(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            cursor = db.cursor()
            if cursor.execute('SELECT QTY,NOREX,LOCATION from inventorystorage WHERE BARCODE = %s',
                              (request.args.get('BARCODE'))) == 0:
                return {"message": "No such Barcode exists"}, 404
            else:
                data = cursor.fetchone()
                if cursor.execute(
                        "SELECT IMAGE from rawvalues where NOREX = %s and LOCATION = %s", (data[1], data[2])) > 0:
                    value = cursor.fetchone()
                    return (flask.jsonify({"QTY": data[0],
                                           "IMAGE": value[0]}))
                else:
                    return {"message": "No such Image exists"}, 404
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500

    def put(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            Data = flask.request.get_json()
            cursor = db.cursor()
            cursor.execute("select QTY from inventorystorage where BARCODE = %s", (Data['BARCODE']))
            prev_qty = cursor.fetchone()
            if prev_qty[0] - Data['QTY'] >= 0:
                if cursor.execute(
                        'UPDATE inventorystorage set TAGSTATUS = 1, QTY = QTY - %s where BARCODE = %s',
                        (Data['QTY'], Data['BARCODE'])) == 0:
                    db.rollback()
                    return {'message': 'Error - Could not find the BARCODE'}, 404
                row_count = cursor.execute("select QTY from inventorystorage where BARCODE = %s", (Data['BARCODE']))
                if row_count > 0:
                    row = cursor.fetchone()
                    if row[0] == 0:
                        count = move_to_empty_storage(cursor, Data['BARCODE'], access_token['UserName'])
                        if count > 0:
                            if Log.register(request.headers.get('Authorization'),
                                            'Completed cutting all the items of barcode:%s and moved to empty storage' %
                                                    Data['BARCODE'],
                                            True):
                                db.commit()
                        else:
                            return {'message': 'please try again'}, 404
                    else:
                        if Log.register(request.headers.get('Authorization'),
                                        'Operated on %s items of Barcode %s, remaining Quantity is %s ' % (
                                                Data['QTY'], str(Data['BARCODE']), row[0]),
                                        True):
                            db.commit()
                return "success"
            else:
                return "contact superior", 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return {"message": str(e)}, 500
