import flask
from flask_restful import Resource, reqparse, request
import datetime

from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, move_to_empty_storage

db = CreateApi.create_db_connection()


class Rejection(Resource):
    def get(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            message = []
            query = "Select REJECTIONDATE,BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,TAGSTATUS,LASTDATE,LASTUSER from rejection where "
            COUNT = int(request.args.get('COUNT'))
            COLUMN = request.args.get('COLUMN')
            VALUE = request.args.get('VALUE')
            if COUNT >= 1:
                COLUMN = COLUMN.split(',')
                VALUE = VALUE.split(',')
                for i in range(0, COUNT):
                    if i == COUNT - 1:
                        if COLUMN[COUNT - 1] == "REJECTIONDATE":
                            query = query + COLUMN[COUNT - 1] + ' >= \'' + str(
                                datetime.datetime.strptime(VALUE[COUNT - 1], '%m/%d/%y')) + '\' AND ' + COLUMN[
                                        COUNT - 1] + ' < \'' + str(
                                datetime.datetime.strptime(VALUE[COUNT - 1], '%m/%d/%y') + datetime.timedelta(
                                    days=1)) + '\''
                        else:
                            query = query + COLUMN[COUNT - 1] + ' LIKE \'%' + VALUE[COUNT - 1] + '%\''
                        break
                    else:
                        if COLUMN[i] == "REJECTIONDATE":
                            query = query + COLUMN[i] + ' >= \'' + str(
                                datetime.datetime.strptime(VALUE[i], '%m/%d/%y')) + '\' AND ' + COLUMN[
                                        i] + ' < \'' + str(
                                datetime.datetime.strptime(VALUE[i], '%m/%d/%y') + datetime.timedelta(
                                    days=1)) + '\' AND '
                        else:
                            query = query + COLUMN[i] + ' LIKE \'%' + VALUE[i] + '%\' AND '
            else:
                query = query + COLUMN + ' 1'
            cursor = db.cursor()
            row_count = cursor.execute(query)
            row = cursor.fetchall()
            for i in range(0, row_count):
                message.append({
                    "REJECTIONDATE": row[i][0],
                    "BARCODE": row[i][1],
                    "TAG": row[i][2],
                    "SHIPMENTDATE": row[i][3],
                    "PROJECTID": row[i][4],
                    "PROJECTNAME": row[i][5],
                    "NBP": row[i][6],
                    "ASTRO": row[i][7],
                    "KEYMARK": row[i][8],
                    "DESCRIPTION": row[i][9],
                    "FINISHID": row[i][10],
                    "FINISHNAME": row[i][11],
                    "LENGTH": row[i][12],
                    "QTY": row[i][13],
                    "LBFT": row[i][14],
                    "NETWEIGHT": row[i][15],
                    "NOREX": row[i][16],
                    "LOCATION": row[i][17],
                    "LOCATIONGRID": row[i][18],
                    "MODEL": row[i][19],
                    "EASCO": row[i][20],
                    "EXTRUDER": row[i][20],
                    "TAGSTATUS": row[i][21],
                    "LASTDATE": row[i][22],
                    "LASTUSER": row[i][23]
                })
            return flask.jsonify(message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500

    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            message = []
            parser = reqparse.RequestParser()
            parser.add_argument('BARCODE')
            parser.add_argument('QTY')
            args = parser.parse_args()
            cursor = db.cursor()
            row_count = cursor.execute(
                'select * from inventorystorage where BARCODE=%s', args['BARCODE'])
            row = cursor.fetchone()
            if int(row[12]) == int(args['QTY']):
                if cursor.execute(
                        "Update inventorystorage set TAG = 0, SHIPMENTDATE = '1990-01-01', PROJECTID = '', PROJECTNAME = '', NBP = 0, ASTRO = '', KEYMARK = '', DESCRIPTION = '', FINISHID = '', FINISHNAME = '', LENGTH=0, QTY = 0, LBFT = 0, NETWEIGHT = 0, NOREX='REJECTION', LOCATION = 'REJECTION', LOCATIONGRID = '', MODEL = '', EASCO = '', EXTRUDER = '', NAtoLOC = 0, TAGSTATUS = 0,  LASTDATE= %s, LASTUSER= %s,TICKET = 0 WHERE BARCODE=%s",
                        (datetime.datetime.now(), access_token['UserName'], args['BARCODE'])) > 0:
                    if cursor.execute(
                            "INSERT into rejection(REJECTIONDATE,BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,TAGSTATUS,LASTDATE,LASTUSER) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (
                                    datetime.datetime.now(), row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                                    row[7],
                                    row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16],
                                    row[17],
                                    row[18], row[19], row[20], row[22], datetime.datetime.now(),
                                    access_token['UserName'])) > 0:
                        if Log.register(request.headers.get('Authorization'), 'Reject item ' + args['BARCODE'], True):
                            new_barcode = args['BARCODE']
                            db.commit()
                        else:
                            return {"message": "Try again"}, 500
                    else:
                        return {"message": "Try again"}, 500
                else:
                    return {"message": "Try again"}, 500
            elif int(row[12]) > int(args['QTY']) > 0:
                NQTY = int(row[12]) - int(args['QTY'])
                if cursor.execute(
                        "Update inventorystorage set QTY = %s WHERE BARCODE =%s", (NQTY, args['BARCODE'])) > 0:
                    if cursor.execute('select MAX(BARCODE) from inventorystorage') > 0:
                        new_barcode = int(cursor.fetchone()[0]) + 1
                        if cursor.execute(
                                "INSERT INTO inventorystorage (BARCODE ,NOREX, LOCATION,TAG, SHIPMENTDATE , PROJECTID , PROJECTNAME , NBP , ASTRO , KEYMARK , DESCRIPTION , FINISHID , FINISHNAME , LENGTH,QTY , LBFT , NETWEIGHT , LOCATIONGRID , MODEL , EASCO , EXTRUDER , NAtoLOC , TAGSTATUS ,  LASTDATE, LASTUSER,TICKET) VALUES (%s,'REJECTION','REJECTION',0,'1990-01-01','','',0,'','','','','',0,0,0,0,'','','','',0,0,%s,%s,0)",
                                (new_barcode, datetime.datetime.now(), access_token['UserName'])) > 0:
                            if cursor.execute(
                                    "INSERT into rejection(REJECTIONDATE,BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,TAGSTATUS,LASTDATE,LASTUSER) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                    (
                                            datetime.datetime.now(), new_barcode, row[1], row[2], row[3], row[4],
                                            row[5], row[6], row[7], row[8], row[9], row[10], row[11], args['QTY'],
                                            row[13], row[14], row[15], row[16], row[17],
                                            row[18], row[19], row[20], row[22], datetime.datetime.now(),
                                            access_token['UserName'])) > 0:
                                if Log.register(request.headers.get('Authorization'), 'Reject item ' + str(new_barcode),
                                                True):
                                    db.commit()
                                else:
                                    db.rollback()
                                    return {"message": "Try again"}, 500
                            else:
                                return {"message": "Try again"}, 500
                        else:
                            return {"message": "Try again"}, 500
                    else:
                        return {"message": "Try again"}, 500
                else:
                    return {"message": "invalid Qty"}, 500
            else:
                return {"message": "invalid Qty"}, 500
            cursor.execute(
                'SELECT REJECTIONDATE,BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER FROM rejection WHERE BARCODE = %s',
                new_barcode)
            res = cursor.fetchone()
            return flask.jsonify({
                "REJECTIONDATE": res[0],
                "BARCODE": res[1],
                "TAG": res[2],
                "SHIPMENTDATE": res[3],
                "PROJECTID": res[4],
                "PROJECTNAME": res[5],
                "NBP": res[6],
                "ASTRO": res[7],
                "KEYMARK": res[8],
                "DESCRIPTION": res[9],
                "FINISHID": res[10],
                "FINISHNAME": res[11],
                "LENGTH": res[12],
                "QTY": res[13],
                "LBFT": res[14],
                "NETWEIGHT": res[15],
                "NOREX": res[16],
                "LOCATION": res[17],
                "LOCATIONGRID": res[18],
                "MODEL": res[19],
                "EASCO": res[20],
                "EXTRUDER": res[21]
            })
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return ({'message': str(e)}), 500
