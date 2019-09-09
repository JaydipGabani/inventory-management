import dateparser
import flask
from flask_restful import Resource, request
from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from customErrors import ProjectNotFound, InvalidProjectUpdate
from helper.helper import authenticator, update_project

db = CreateApi.create_db_connection()


class Browse(Resource):
    def post(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            Data = flask.request.get_json()
            s = "SELECT BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,LASTDATE,LASTUSER,TICKET from inventorystorage "
            query = []
            values = []
            result = []
            if Data['PageNo'] == 1:
                Data['PageNo'] = 0
            else:
                Data['PageNo'] = (Data['PageNo'] - 1) * 100
            cursor = db.cursor()
            if (Data['BARCODE'] != ""):
                query.append("BARCODE LIKE %s")
                values.append("%" + str(Data['BARCODE'] + "%"))
            if (Data['TAG'] != ""):
                query.append("TAG LIKE %s")
                values.append("%" + str(Data['TAG']) + "%")
            if (Data['SHIPMENTDATE'] != ""):
                query.append("SHIPMENTDATE LIKE %s")
                values.append("%" + str(dateparser.parse(Data['SHIPMENTDATE']).date()) + "%")
            if (Data['PROJECTID'] != ""):
                query.append("PROJECTID LIKE %s")
                values.append(str("%" + Data['PROJECTID'] + "%"))
            if (Data['PROJECTNAME'] != ""):
                query.append("PROJECTNAME LIKE %s")
                values.append(str("%" + Data['PROJECTNAME'] + "%"))
            if (Data['NBP'] != ""):
                query.append("NBP LIKE %s")
                values.append("%" + str(Data['NBP']) + "%")
            if (Data['ASTRO'] != ""):
                query.append("ASTRO LIKE %s")
                values.append(str("%" + Data['ASTRO'] + "%"))
            if (Data['KEYMARK'] != ""):
                query.append("KEYMARK LIKE %s")
                values.append("%" + str(Data['KEYMARK']) + "%")
            if (Data['DESCRIPTION'] != ""):
                query.append("DESCRIPTION LIKE %s")
                values.append("%" + str(Data['DESCRIPTION']) + "%")
            if (Data['FINISHID'] != ""):
                query.append("FINISHID LIKE %s")
                values.append("%" + str(Data['FINISHID']) + "%")
            if (Data['FINISHNAME'] != ""):
                query.append("FINISHNAME LIKE %s")
                values.append("%" + str(Data['FINISHNAME']) + "%")
            if (Data['LENGTH'] != ""):
                query.append("LENGTH LIKE %s")
                values.append(str(Data['LENGTH']))
            if (Data['QTY'] != ""):
                query.append("QTY LIKE %s")
                values.append(str(Data['QTY']))
            if (Data['LBFT'] != ""):
                query.append("LBFT LIKE %s")
                values.append(str(Data['LBFT']))
            if (Data['NETWEIGHT'] != ""):
                query.append("%" + "NETWEIGHT LIKE %s" + "%")
                values.append("%" + str(Data['NETWEIGHT']) + "%")
            if (Data['NOREX'] != ""):
                query.append("NOREX LIKE %s")
                values.append("%" + str(Data['NOREX']) + "%")
            if (Data['LOCATION'] != ""):
                query.append("LOCATION LIKE %s")
                values.append("%" + str(Data['LOCATION']) + "%")
            if (Data['LOCATIONGRID'] != ""):
                query.append("LOCATIONGRID LIKE %s")
                values.append("%" + str(Data['LOCATIONGRID']) + "%")
            if (Data['MODEL'] != ""):
                query.append("MODEL LIKE %s")
                values.append("%" + str(Data['MODEL']) + "%")
            if (Data['EASCO'] != ""):
                query.append("EASCO LIKE %s")
                values.append("%" + str(Data['EASCO']) + "%")
            if (Data['EXTRUDER'] != ""):
                query.append("EXTRUDER LIKE %s")
                values.append("%" + str(Data['EXTRUDER']) + "%")
            if (Data['NAtoLOC'] != ""):
                query.append("NAtoLOC LIKE %s")
                values.append("%" + str(Data['NAtoLOC']) + "%")
            if (Data['TAGSTATUS'] != ""):
                query.append("TAGSTATUS LIKE %s")
                values.append("%" + str(Data['TAGSTATUS']) + "%")
            if (len(query) != 0):
                query = ' and '.join([str(x) for x in query])
                # values = ', '.join([str(x) for x in values])
                s = s + "where " + query + " ORDER BY BARCODE LIMIT 100 OFFSET " + str(Data['PageNo'])
            else:
                s = s + " ORDER BY BARCODE LIMIT 100 OFFSET " + str(Data['PageNo'])
            row_count = cursor.execute(s, (values))
            row = cursor.fetchall()
            if (row_count > 0):
                for i in range(0, row_count):
                    cursor.execute(
                        "SELECT IMAGE from rawvalues where NOREX = %s and LOCATION = %s", (row[i][15], row[i][16]))
                    value = cursor.fetchone()
                    m = {
                        "BARCODE": row[i][0],
                        "TAG": row[i][1],
                        "SHIPMENTDATE": row[i][2],
                        "PROJECTID": row[i][3],
                        "PROJECTNAME": row[i][4],
                        "NBP": row[i][5],
                        "ASTRO": row[i][6],
                        "KEYMARK": row[i][7],
                        "DESCRIPTION": row[i][8],
                        "FINISHID": row[i][9],
                        "FINISHNAME": row[i][10],
                        "LENGTH": row[i][11],
                        "QTY": row[i][12],
                        "LBFT": row[i][13],
                        "NETWEIGHT": row[i][14],
                        "NOREX": row[i][15],
                        "LOCATION": row[i][16],
                        "LOCATIONGRID": row[i][17],
                        "MODEL": row[i][18],
                        "EASCO": row[i][19],
                        "EXTRUDER": row[i][20],
                        "NAtoLOC": row[i][21],
                        "TAGSTATUS": row[i][22],
                        "LASTDATE": row[i][23],
                        "LASTUSER": row[i][24],
                        "TICKET": row[i][25],
                        "IMAGE": value[0]
                    }
                    result.append(m)
            else:
                return {"message": "No results found!"}, 404
            return (flask.jsonify(result))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def put(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            cursor = db.cursor()
            data = flask.request.get_json()
            if data['status'] == 'NAtoLOC' or data['status'] == 'TAGSTATUS':
                for i in data['data']:
                    cursor.execute('UPDATE inventorystorage SET ' + data['status'] + ' = 0 WHERE BARCODE = %s', i)
            elif data['status'] == 'PROJECT':
                for i in data['data']:
                    update_project(cursor, data['PROJECTID'], 'inventorystorage', 'BARCODE', i,
                                   access_token['UserName'], access_token['Role'])
                Log.register(request.headers.get('Authorization'),
                             'Projectid:%s assigned to barcodes %s' % (
                             data['PROJECTID'], ','.join([str(x) for x in data['data']])),
                             True)
            db.commit()
            return 'success'
        except InvalidProjectUpdate as e:
            return {'message': str(e)}, 500
        except ProjectNotFound as e:
            db.rollback()
            return {'message': str(e)}, 404
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            db.rollback()
            return {"message": str(e)}, 500

    def delete(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            Data = flask.request.get_json()
            s = "SELECT BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,NAtoLOC,TAGSTATUS,LASTDATE,LASTUSER,TICKET from inventorystorage "
            query = []
            values = []
            result = []
            cursor = db.cursor()
            if (Data['BARCODE'] != ""):
                query.append("BARCODE LIKE %s")
                values.append("%" + str(Data['BARCODE'] + "%"))
            if (Data['TAG'] != ""):
                query.append("TAG LIKE %s")
                values.append("%" + str(Data['TAG']) + "%")
            if (Data['SHIPMENTDATE'] != ""):
                query.append("SHIPMENTDATE LIKE %s")
                values.append("%" + str(dateparser.parse(Data['SHIPMENTDATE']).date()) + "%")
            if (Data['PROJECTID'] != ""):
                query.append("PROJECTID LIKE %s")
                values.append(str("%" + Data['PROJECTID'] + "%"))
            if (Data['PROJECTNAME'] != ""):
                query.append("PROJECTNAME LIKE %s")
                values.append(str("%" + Data['PROJECTNAME'] + "%"))
            if (Data['NBP'] != ""):
                query.append("NBP LIKE %s")
                values.append("%" + str(Data['NBP']) + "%")
            if (Data['ASTRO'] != ""):
                query.append("ASTRO LIKE %s")
                values.append(str("%" + Data['ASTRO'] + "%"))
            if (Data['KEYMARK'] != ""):
                query.append("KEYMARK LIKE %s")
                values.append("%" + str(Data['KEYMARK']) + "%")
            if (Data['DESCRIPTION'] != ""):
                query.append("DESCRIPTION LIKE %s")
                values.append("%" + str(Data['DESCRIPTION']) + "%")
            if (Data['FINISHID'] != ""):
                query.append("FINISHID LIKE %s")
                values.append("%" + str(Data['FINISHID']) + "%")
            if (Data['FINISHNAME'] != ""):
                query.append("FINISHNAME LIKE %s")
                values.append("%" + str(Data['FINISHNAME']) + "%")
            if (Data['LENGTH'] != ""):
                query.append("LENGTH LIKE %s")
                values.append("%" + str(Data['LENGTH']) + "%")
            if (Data['QTY'] != ""):
                query.append("QTY LIKE %s")
                values.append("%" + str(Data['QTY']) + "%")
            if (Data['LBFT'] != ""):
                query.append("LBFT LIKE %s")
                values.append("%" + str(Data['LBFT']) + "%")
            if (Data['NETWEIGHT'] != ""):
                query.append("%" + "NETWEIGHT LIKE %s" + "%")
                values.append("%" + str(Data['NETWEIGHT']) + "%")
            if (Data['NOREX'] != ""):
                query.append("NOREX LIKE %s")
                values.append("%" + str(Data['NOREX']) + "%")
            if (Data['LOCATION'] != ""):
                query.append("LOCATION LIKE %s")
                values.append("%" + str(Data['LOCATION']) + "%")
            if (Data['LOCATIONGRID'] != ""):
                query.append("LOCATIONGRID LIKE %s")
                values.append("%" + str(Data['LOCATIONGRID']) + "%")
            if (Data['MODEL'] != ""):
                query.append("MODEL LIKE %s")
                values.append("%" + str(Data['MODEL']) + "%")
            if (Data['EASCO'] != ""):
                query.append("EASCO LIKE %s")
                values.append("%" + str(Data['EASCO']) + "%")
            if (Data['EXTRUDER'] != ""):
                query.append("EXTRUDER LIKE %s")
                values.append("%" + str(Data['EXTRUDER']) + "%")
            if (Data['NAtoLOC'] != ""):
                query.append("NAtoLOC LIKE %s")
                values.append("%" + str(Data['NAtoLOC']) + "%")
            if (Data['TAGSTATUS'] != ""):
                query.append("TAGSTATUS LIKE %s")
                values.append("%" + str(Data['TAGSTATUS']) + "%")
            if (len(query) != 0):
                query = ' and '.join([str(x) for x in query])
                # values = ', '.join([str(x) for x in values])
                s = s + "where " + query
            row_count = cursor.execute(s, (values))
            row = cursor.fetchall()
            if (row_count > 0):
                for i in range(0, row_count):
                    m = {
                        "BARCODE": row[i][0],
                        "TAG": row[i][1],
                        "SHIPMENTDATE": row[i][2],
                        "PROJECTID": row[i][3],
                        "PROJECTNAME": row[i][4],
                        "NBP": row[i][5],
                        "ASTRO": row[i][6],
                        "KEYMARK": row[i][7],
                        "DESCRIPTION": row[i][8],
                        "FINISHID": row[i][9],
                        "FINISHNAME": row[i][10],
                        "LENGTH": row[i][11],
                        "QTY": row[i][12],
                        "LBFT": row[i][13],
                        "NETWEIGHT": row[i][14],
                        "NOREX": row[i][15],
                        "LOCATION": row[i][16],
                        "LOCATIONGRID": row[i][17],
                        "MODEL": row[i][18],
                        "EASCO": row[i][19],
                        "EXTRUDER": row[i][20],
                        "NAtoLOC": row[i][21],
                        "TAGSTATUS": row[i][22],
                        "LASTDATE": row[i][23],
                        "LASTUSER": row[i][24],
                        "TICKET": row[i][25]
                    }
                    result.append(m)
            else:
                return {"message": "No results found!"}, 404
            return (flask.jsonify(result))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)
