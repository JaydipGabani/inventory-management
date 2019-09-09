import dateparser
import flask
import datetime
from flask_restful import Resource, request
from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator, get_max_project, get_max_norex, get_max_barcode, tag_inc, \
    edittag_json_response_array

db = CreateApi.create_db_connection()


class Util(Resource):
    def get(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            Data = request.args.get('status')
            cursor = db.cursor()
            if Data == "norex":
                return flask.jsonify(get_max_norex(cursor))
            elif Data == "project":
                return flask.jsonify(get_max_project(cursor))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return {"message": str(e)}, 500

    def post(self):
        access_token = authenticator(request.headers.get('Authorization'))
        from pymysql import InterfaceError
        try:
            Data = flask.request.get_json()
            cursor = db.cursor()
            row = cursor.execute(
                "select SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,TICKET from inventorystorage where BARCODE = %s",
                (Data['BARCODE']))
            if row > 0:
                row = cursor.fetchone()
                if int(row[10]) > int(Data['QTY']):
                    max_barcode = get_max_barcode(cursor)
                    cursor.execute(
                        "insert into inventorystorage(BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,LASTDATE,LASTUSER,TICKET) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        ((max_barcode['BARCODE'] + 1), (max_barcode['BARCODE'] + tag_inc), row[0], row[1],
                         row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], Data['QTY'], row[11], row[12],
                         row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20],
                         datetime.datetime.now(), access_token['UserName'], row[21]))
                    print('a')
                    cursor.execute("update inventorystorage SET QTY=%s where BARCODE=%s",
                                   ((row[10] - int(Data['QTY'])), Data['BARCODE']))
                    Log.register(request.headers.get('Authorization'),
                                 "split : barcode %s with %s" % (Data['BARCODE'], max_barcode['BARCODE']),
                                 True)
                    return flask.jsonify(edittag_json_response_array(cursor, (max_barcode['BARCODE'] + 1)))
                else:
                    return {"message": "Quantity you have provided is more than the quantity stored"}, 500
            else:
                return {"message": "barcode %s does not exist" % Data['BARCODE']}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            return {"message": str(e)}, 500


    def put(self):
        try:
            Data = flask.request.get_json()
            message={}
            cursor = db.cursor()
            row = cursor.execute("SELECT SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,LASTDATE,LASTUSER,TICKET FROM inventorystorage where LASTDATE between"+Data['startDate']+"AND"+Data['endDate'])
            rowCount = cursor.fetchall()
            if(rowCount>0):
                for i in range (0,rowCount):
                    model_count = cursor.execute(
                        'SELECT IMAGE from rawvalues where NOREX = %s and LOCATION = %s'+(rowCount[i][13], rowCount[i][14]))
                    model = cursor.one()
                    if (model_count > 0):
                        message.append({
                            "SHIPMENTDATE": row[i][0],
                            "PROJECTID": row[i][1],
                            "PROJECTNAME": row[i][2],
                            "NBP": row[i][3],
                            "ASTRO": row[i][4],
                            "KEYMARK": row[i][5],
                            "DESCRIPTION": row[i][6],
                            "FINISHID": row[i][7],
                            "FINISHNAME": row[i][8],
                            "LENGTH": row[i][9],
                            "QTY": row[i][10],
                            "LBFT": row[i][11],
                            "NETWEIGHT": row[i][12],
                            "NOREX": row[i][13],
                            "LOCATION": row[i][14],
                            "LOCATIONGRID": row[i][15],
                            "MODEL": row[i][16],
                            "EASCO": row[i][17],
                            "EXTRUDER": row[i][18],
                            "NAtoLOC": row[i][19],
                            "TAGSTATUS": row[i][20],
                            "LASTDATE": row[i][21],
                            "LASTUSER": row[i][22],
                            "TICKET": row[i][23],
                            "IMAGE": model[0]
                        })
                        print(message)
                    else:
                        return {"message": "image does not exist"}, 500
            else:
                return {"message": "No record exists"}, 500
        except InterfaceError as e:
             CreateApi.reAssignDb()
             print(e)
        except Exception as e:
            return {"message": str(e)}, 500