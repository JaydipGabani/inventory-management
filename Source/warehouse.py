import dateparser
import flask
from flask_restful import Resource, reqparse, request
from flask_jwt import jwt
import time, datetime

from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from Source.email import Email
from helper.helper import authenticator, tag_inc

db = CreateApi.create_db_connection()


class Warehouse(Resource):
    def get(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            message = []
            Date = request.args['date']
            cursor = db.cursor()
            if (Date == ''):
                if cursor.execute(
                        "SELECT distinct UPLOADDATE FROM warehousemanifest") == 0:
                    return {"message": "no manifest available"}, 404
                else:
                    row = cursor.fetchall()
                    for i in range(0, len(row)):
                        message.append(row[i][0])
            else:
                Date = str(dateparser.parse(Date))
                if cursor.execute(
                        'SELECT NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LASTDATE,LASTUSER FROM warehousemanifest where UPLOADDATE = %s',
                        Date) == 0:
                    return {'message': 'press Refresh'}
                else:
                    row = cursor.fetchall()
                    for i in range(0, len(row)):
                        message.append({
                            "NO": row[i][0],
                            "UPLOADDATE": row[i][1],
                            "SHIPMENTDATE": row[i][2],
                            "EXTRUDER": row[i][3],
                            "PROJECTID": row[i][4],
                            "PROJECTNAME": row[i][5],
                            "NBP": row[i][6],
                            "BL": row[i][7],
                            "MANIFEST": row[i][8],
                            "TICKET": row[i][9],
                            "SO": row[i][10],
                            "ITEM": row[i][11],
                            "ASTRO": row[i][12],
                            "KEYMARK": row[i][13],
                            "DESCRIPTION": row[i][14],
                            "FINISHID": row[i][15],
                            "FINISHNAME": row[i][16],
                            "LENGTH": row[i][17],
                            "QTY": row[i][18],
                            "LBFT": row[i][19],
                            "NETWEIGHT": row[i][20],
                            "NOREX": row[i][21],
                            "LOCATION": row[i][22],
                            "LASTDATE": row[i][23],
                            "LASTUSER": row[i][24]
                        })
            return flask.jsonify(message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return {'message': 'try again'}, 500

    def post(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            Data = flask.request.get_json()
            cursor = db.cursor()
            message = []
            reportArr = []
            if (Data['status'] == 'print'):
                for i in range(0, len(Data['data'])):
                    row_cnt = cursor.execute(
                        'SELECT SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION FROM warehousemanifest where NO = %s',
                        Data['data'][i]['NO'])
                    r = cursor.fetchone()
                    model_count = cursor.execute(
                        'SELECT MODEL,EASCO,IMAGE from rawvalues where NOREX = %s and LOCATION = %s', (r[19], r[20]))
                    c = cursor.fetchone()
                    if (model_count > 0):
                        max_barcode = cursor.execute("SELECT MAX(BARCODE) from inventorystorage")
                        b = cursor.fetchone()
                        if b[0] == None:
                            bar = 0
                        else:
                            bar = int(b[0])
                        if Data['data'][i]['actualQty'] and (r[16] - Data['data'][i]['actualQty']) != 0:
                            reportOb = list(r)
                            reportOb.append(Data['data'][i]['actualQty'])
                            reportOb.append(r[16] - Data['data'][i]['actualQty'])
                            reportArr.append(reportOb)
                            newQty = Data['data'][i]['actualQty']
                        else:
                            newQty = r[16]
                        cursor.execute(
                            "INSERT into inventorystorage(BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,LASTDATE,LASTUSER,TICKET) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            ((bar + 1), (bar + tag_inc), r[0], r[2], r[3], r[4], r[10], r[11], r[12], r[13], r[14],
                             r[15],
                             newQty,
                             r[17], r[18], r[19], r[20], 'NA', c[0], c[1], r[1], 0, 0, datetime.datetime.now(),
                             access_token['UserName'], r[7]))
                        cursor.execute("DELETE from warehousemanifest where NO = %s", (Data['data'][i]['NO']))
                        row_count = cursor.execute(
                            "SELECT * FROM inventorystorage where BARCODE = %s", (int(bar + 1)))
                        row = cursor.fetchone()
                        if (row_count > 0):
                            message.append({
                                "BARCODE": row[0],
                                "TAG": row[1],
                                "SHIPMENTDATE": row[2],
                                "PROJECTID": row[3],
                                "PROJECTNAME": row[4],
                                "NBP": row[5],
                                "ASTRO": row[6],
                                "KEYMARK": row[7],
                                "DESCRIPTION": row[8],
                                "FINISHID": row[9],
                                "FINISHNAME": row[10],
                                "LENGTH": row[11],
                                "QTY": row[12],
                                "LBFT": row[13],
                                "NETWEIGHT": row[14],
                                "NOREX": row[15],
                                "LOCATION": row[16],
                                "LOCATIONGRID": row[17],
                                "MODEL": row[18],
                                "EASCO": row[19],
                                "EXTRUDER": row[20],
                                "NAtoLOC": row[21],
                                "TAGSTATUS": row[22],
                                "LASTDATE": row[23],
                                "LASTUSER": row[24],
                                "TICKET": row[25],
                                "IMAGE": c[2]
                            })
                        else:
                            message = 'ERROR: No MODEL found for given NOREX + LOCATION'
                if (reportArr != []):
                    Email.email('Exception in Quantity', reportArr, access_token['UserName'],
                                ['swadasmaunil@gmail.com'],
                                'exceptionInQty')
                l = Log
                x = l.register(request.headers.get('Authorization'), 'Warehouse- Print', True)
                if x == True:
                    db.commit()
                return flask.jsonify(message)
            else:
                message = 'ERROR: You have not sent data properly in request, Either send "print" OR "reject" in status field'
                return (flask.jsonify(message))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def delete(self):
        cursor = db.cursor()
        Data = request.get_json()
        message = []
        print(Data['DATE'])
        if cursor.execute("DELETE FROM warehousemanifest WHERE UPLOADDATE  = %s", dateparser.parse(Data['DATE'])) != 0:
            if cursor.execute(
                    "SELECT distinct UPLOADDATE FROM warehousemanifest") == 0:
                return []
            else:
                row = cursor.fetchall()
                for i in range(0, len(row)):
                    message.append(row[i][0])
                return flask.jsonify(message)
        else:
            return {"message": "please try again after refreshing list"}
