import datetime
import dateparser
import flask

from pymysql import InterfaceError
from werkzeug.exceptions import HTTPException, BadRequest
from flask_restful import Resource, reqparse
from Config.api import CreateApi
from Source.logs import Log
from customErrors import ProjectNotFound, NorexNotFound, ColorNotFound
from helper.helper import update_project, authenticator, get_rawvalues, get_project, calculate_netweight, \
    insert_into_buffer_manifest, get_from_buffer_manifest, get_rejection_for_replacement, get_color

db = CreateApi.create_db_connection()


class Purchase(Resource):
    def post(self):
        try:
            flag = 0
            try:
                data = flask.request.get_json()
            except HTTPException as e:
                raise BadRequest("Bad Request")
            cursor = db.cursor()
            message = []
            response = {}
            replacementProject = []
            replacementNorex = []
            t = str(datetime.datetime.today().now())
            access_token = authenticator(flask.request.headers.get('Authorization'))
            try:
                cursor.execute('DELETE FROM bufferpurchasingmanifest WHERE USER = %s', access_token['UserName'])
            except InterfaceError as e:
                CreateApi.reAssignDb()
                print(e)
            except Exception as e:
                return {"message": str(e)}, 500
            if data['Company'] == "Astro":
                for i in range(0, len(data['Data'])):
                    try:
                        row = get_rawvalues(cursor, 'ASTRO', data['Data'][i]['Die#'])
                        s = data['Data'][i]['NBP PO#'].split('/ID # ')
                        project = get_project(cursor, s[1])
                        if data['Data'][i]['rep'] == "1":
                            replacementNorex.append(row[0])
                            replacementProject.append(s[1])
                        if data['Data'][i]['Finish'] == 'MILL FINISH' or data['Data'][i]['Finish'] == 'CLEAR ANODIZE':
                            finishid = data['Data'][i]['Finish']
                            color = data['Data'][i]['Finish']
                        else:
                            if s[1] == "9999":
                                finishid = get_color(cursor, data['Data'][i]['Finish'])
                                color = data['Data'][i]['Finish']
                            else:
                                finishid = project[1]
                                color = project[2]
                        netwt = calculate_netweight(data['Data'][i]['Length'], data['Data'][i]['Pcs'], row[4])
                        if data['Data'][i]['rep'] == "1" and flag == 0:
                            flag = 1
                        insert_into_buffer_manifest(cursor, t,
                                                    datetime.datetime.strptime(data['Data'][i]['ShipD'],
                                                                               '%m/%d/%y').date(),
                                                    "ASTRO", s[1], project[0], s[0], data['Data'][i]['BL#'],
                                                    data['Data'][i]['Manifest'], data['Data'][i]['Ticket#'],
                                                    data['Data'][i]['SO#'], data['Data'][i]['Item#'],
                                                    data['Data'][i]['Die#'], row[6], row[3], finishid, color,
                                                    data['Data'][i]['Length'], data['Data'][i]['Pcs'], row[4],
                                                    data['Data'][i]['NetWt'], netwt, row[0], row[2], row[1],
                                                    access_token['UserName'], t, access_token['UserName'],
                                                    data['Data'][i]['rep'],data['fileName'])
                    except ColorNotFound as e:
                        return {'message': str(e)}, 404
                    except ProjectNotFound as e:
                        return {'message': str(e)}, 404
                    except NorexNotFound as e:
                        return {'message': str(e)}, 404
                    except InterfaceError as e:
                        CreateApi.reAssignDb()
                        print(e)
                    except Exception as e:
                        return {'message': str(e)}, 500
            elif data['Company'] == "Keymark":
                try:
                    for i in range(0, len(data['Data'])):
                        row = get_rawvalues(cursor, 'KEYMARK', data['Data'][i]['DieNum'])
                        if data['Data'][i]['rep'] == "1":
                            replacementNorex.append(row[0])
                            replacementProject.append(data['Data'][i]['ProjectID'])
                        project = get_project(cursor, data['Data'][i]['ProjectID'])
                        if data['Data'][i]['FinishDescrip'] == 'MILL FINISH' or data['Data'][i][
                            'FinishDescrip'] == 'CLEAR ANODIZE':
                            finishid = data['Data'][i]['FinishDescrip']
                            color = data['Data'][i]['FinishDescrip']
                        else:
                            if data['Data'][i]['ProjectID'] == "9999":
                                finishid = get_color(cursor, data['Data'][i]['FinishDescrip'])
                                color = data['Data'][i]['FinishDescrip']
                            else:
                                finishid = project[1]
                                color = project[2]
                        netwt = calculate_netweight(data['Data'][i]['LengthInches'], data['Data'][i]['Pcs'], row[4])
                        if data['Data'][i]['rep'] == "1" and flag == 0:
                            flag = 1
                        insert_into_buffer_manifest(cursor,
                                                    t, datetime.datetime.strptime(data['Data'][i]['ShipDt'],
                                                                                  '%m/%d/%y').date(), "KEYMARK",
                                                    data['Data'][i]['ProjectID'], project[0], data['Data'][i]['PONum'],
                                                    data['Data'][i]['BLNum'], data['Data'][i]['Manifest'],
                                                    data['Data'][i]['TicketNum'], data['Data'][i]['SONum'],
                                                    data['Data'][i]['SOItemNum'], row[5], data['Data'][i]['DieNum'],
                                                    row[3],
                                                    finishid, color, data['Data'][i]['LengthInches'],
                                                    data['Data'][i]['Pcs'], row[4], data['Data'][i]['NetWt'], netwt,
                                                    row[0],
                                                    row[2], row[1], access_token['UserName'], t,
                                                    access_token['UserName'],
                                                    data['Data'][i]['rep'],data['fileName'])
                except ColorNotFound as e:
                    return {'message': str(e)}, 404
                except ProjectNotFound as e:
                    return {'message': str(e)}, 404
                except NorexNotFound as e:
                    return {'message': str(e)}, 404
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {'message': str(e)}, 500
            else:
                try:
                    for i in range(0, len(data['Data'])):
                        if data['Data'][i]['rep'] == "1":
                            replacementNorex.append(data['Data'][i]['NOREX'])
                            replacementProject.append(data['Data'][i]['ProjectID'])
                        if cursor.execute(
                                'select NOREX,MODEL,LOCATION,DESCRIPTION,LBFT,KEYMARK,ASTRO from rawvalues where NOREX= %s AND LOCATION = %s',
                                (data['Data'][i]['NOREX'], data['Data'][i]['LOCATION'])) == 0:
                            return {"message": "Can not find NOREX: " + data['Data'][i]['NOREX'] + ", LOCATION: " +
                                               data['Data'][i][
                                                   'LOCATION']}, 404
                        row = cursor.fetchone()
                        project = get_project(cursor, data['Data'][i]['ProjectID'])
                        if data['Data'][i]['FinishDescrip'] == 'MILL FINISH' or data['Data'][i][
                            'FinishDescrip'] == 'CLEAR ANODIZE':
                            finishid = data['Data'][i]['FinishDescrip']
                            color = data['Data'][i]['FinishDescrip']
                        else:
                            if data['Data'][i]['ProjectID'] == "9999":
                                finishid = get_color(cursor, data['Data'][i]['FinishDescrip'])
                                color = data['Data'][i]['FinishDescrip']
                            else:
                                finishid = project[1]
                                color = project[2]
                        netwt = calculate_netweight(data['Data'][i]['LengthInches'], data['Data'][i]['Pcs'], row[4])
                        if data['Data'][i]['rep'] == "1" and flag == 0:
                            flag = 1
                        if cursor.execute(
                                'insert into bufferpurchasingmanifest(UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,KEYMARK,ASTRO,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHTexcel,NETWEIGHTnorex,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,REPLACEMENT,FILENAME)'
                                ' values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                (t, datetime.datetime.strptime(data['Data'][i]['ShipDt'], '%m/%d/%y').date(),
                                 data['Company'], data['Data'][i]['ProjectID'], project[0],
                                 data['Data'][i]['PONum'],
                                 data['Data'][i]['BLNum'], data['Data'][i]['Manifest'],
                                 data['Data'][i]['TicketNum'],
                                 data['Data'][i]['SONum'], data['Data'][i]['SOItemNum'], row[5], row[6], row[3],
                                 finishid, color, data['Data'][i]['LengthInches'], data['Data'][i]['Pcs'], row[4],
                                 data['Data'][i]['NetWt'], netwt, row[0], row[2], row[1], access_token['UserName'],
                                 t,
                                 access_token['UserName'], data['Data'][i]['rep'],data['fileName'])) == 0:
                            db.rollback()
                            return {'message': 'try again'}, 500
                except ColorNotFound as e:
                    return {'message': str(e)}, 404
                except ProjectNotFound as e:
                    return {'message': str(e)}, 404
                except NorexNotFound as e:
                    return {'message': str(e)}, 404
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    raise BadRequest(str(e))
            if flag == 0:
                try:
                    response["state"] = "manifestData"
                    response["data"] = get_from_buffer_manifest(cursor, access_token['UserName'], False)
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    raise BadRequest(str(e))
            else:
                response["replacement"] = get_from_buffer_manifest(cursor, access_token['UserName'], True)
                response["rejection"] = get_rejection_for_replacement(cursor, replacementProject, replacementNorex)
                response["state"] = "reject"
            y = Log.register(flask.request.headers.get('Authorization'),
                             "new manifest added of " + data['Company'] + " Extruder(filename:%s)" % data['fileName'],
                             True)
            if y:
                db.commit()
            else:
                return {"message": "Try again"}, 500
            return (flask.jsonify(response))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def get(self):
        access_token = authenticator(flask.request.headers.get('Authorization'))
        parser = reqparse.RequestParser()
        parser.add_argument('date', required=True, help='date is required')
        try:
            args = parser.parse_args()
        except HTTPException as e:
            raise BadRequest("Bad Request")
        cursor = db.cursor()
        if (args['date'] != ''):
            date = str(dateparser.parse(args['date']))
            try:
                if access_token['Role'] == 'admin':
                    row_count = cursor.execute(
                        "SELECT NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER FROM purchasingmanifest WHERE UPLOADDATE =%s",
                        dateparser.parse(date))
                else:
                    row_count = cursor.execute(
                        "SELECT NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER FROM purchasingmanifest WHERE UPLOADDATE =%s AND USER = %s",
                        (dateparser.parse(date), access_token['UserName']))
                row = cursor.fetchall()
                message = []
                for i in range(0, row_count):
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
                        "MODEL": row[i][23],
                        "USER": row[i][24],
                        "LASTDATE": row[i][25],
                        "LASTUSER": row[i][26]
                    })
            except InterfaceError as e:
                CreateApi.reAssignDb()
                print(e)
            except Exception as e:
                raise BadRequest(str(e))
            return (flask.jsonify(message))
        else:
            try:
                if access_token['Role'] == 'admin':
                    if cursor.execute('select DISTINCT UPLOADDATE,FILENAME from purchasingmanifest') == 0:
                        return {'message': 'No manifest found'}, 404
                else:
                    row_count = cursor.execute(
                        'select DISTINCT UPLOADDATE,FILENAME from purchasingmanifest where USER = %s', access_token['UserName'])
                    if row_count == 0:
                        return {'message': 'No manifest found'}, 404
                row = cursor.fetchall()
                message = []
                for i in range(0, len(row)):
                    message.append({
                        "uploadDate":row[i][0],
                        "fileName":row[i][1]
                    })
                return flask.jsonify(message)
            except InterfaceError as e:
                CreateApi.reAssignDb()
                print(e)
            except Exception as e:
                return {'message': str(e)}, 500

    def put(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            t = datetime.datetime.today().strftime('%Y-%m-%d')
            parser = reqparse.RequestParser()
            parser.add_argument('NO', required=True, help='No is Required')
            parser.add_argument('Status', required=True, help='status is Required')
            parser.add_argument('Data', required=False)
            try:
                args = parser.parse_args()
            except HTTPException as e:
                raise BadRequest("Bad Request")
            cursor = db.cursor()
            if args['Status'] == 'perfect':
                try:
                    row_count = cursor.execute(
                        'select NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHTexcel,NETWEIGHTnorex,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,REPLACEMENT,FILENAME from bufferpurchasingmanifest where USER = %s', (access_token['UserName']))
                    row = cursor.fetchall()
                    for i in range(0, row_count):
                        if cursor.execute(
                                'insert into purchasingmanifest(UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,FILENAME) '
                                'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                (
                                        str(row[i][1]), str(row[i][2]), str(row[i][3]), str(
                                            row[i][4]), str(row[i][5]), str(row[i][6]), str(
                                            row[i][7]), str(row[i][8]), str(row[i][9]), str(
                                            row[i][10]), str(row[i][11]), str(row[i][12]), str(
                                            row[i][13]), str(row[i][14]), str(row[i][15]), str(
                                            row[i][16]), str(row[i][17]), str(row[i][18]), str(
                                            row[i][19]), str(row[i][20]), str(row[i][22]), str(
                                            row[i][23]), str(row[i][24]), str(row[i][25]), t,
                                        access_token['UserName'],str(row[i][29]))) == 0:
                            db.rollback()
                            return {'message', 'please try again'}, 500
                    if cursor.execute('DELETE FROM bufferpurchasingmanifest WHERE USER = %s',
                                      access_token['UserName']) == 0:
                        return {'message', 'please try again'}, 500
                    # Email.email('Manifest uploaded', row, access_token['UserName'],
                    #             ['swadasmaunil@gmail.com'], 'manifestUpload')
                    if Log.register(flask.request.headers.get('Authorization'), "Accept manifest", True):
                        db.commit()
                        return {'status': 'perfect'}
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
            elif args['Status'] == 'editManifest':
                Data = flask.request.get_json()['Data']
                keys = list(Data.keys())
                try:
                    for key in keys:
                        if key == "SHIPMENTDATE":
                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET SHIPMENTDATE = %s , LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (dateparser.parse(Data['SHIPMENTDATE']), datetime.datetime.now(),
                                 access_token['UserName'],
                                 args['NO']))
                        if key == "TICKET":
                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET TICKET = %s , LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (str(Data['TICKET']), datetime.datetime.now(), access_token['UserName'], args['NO']))
                        if key == "NBP":
                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET NBP = %s , LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (str(Data['NBP']), datetime.datetime.now(), access_token['UserName'], args['NO']))
                        if key == "NOREX":
                            q_len = cursor.execute("select QTY,LENGTH from purchasingmanifest WHERE NO = %s",
                                                   args['NO'])
                            q = cursor.fetchone()
                            norex_len = cursor.execute(
                                'SELECT MODEL,DESCRIPTION,LBFT,ASTRO,KEYMARK FROM rawvalues where NOREX = %s AND LOCATION = %s ',
                                (Data['NOREX'], Data['LOCATION']))
                            norex = cursor.fetchone()
                            if norex_len == 0:
                                raise BadRequest("Norex Not Found")
                            netwt = calculate_netweight(q[0], q[1], norex[2])
                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET NOREX = %s, LOCATION = %s, MODEL = %s ,DESCRIPTION = %s ,LBFT = %s ,ASTRO = %s ,KEYMARK= %s , NETWEIGHT = %s , LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (Data['NOREX'], Data['LOCATION'], norex[0], norex[1], norex[2], norex[3], norex[4],
                                 netwt,
                                 datetime.datetime.now(), access_token['UserName'], args['NO']))
                        if key == "PROJECTID":
                            try:
                                if not update_project(cursor, Data['PROJECTID'], 'purchasingmanifest', 'NO', args['NO'],
                                                      access_token['UserName'],access_token['Role']):
                                    return {'message', 'please try again'}, 500
                            except ProjectNotFound as e:
                                return {'message': str(e)}, 404
                            except Exception as e:
                                return {'message': str(e)}, 500
                        if key == "QTY":
                            cursor.execute("select LENGTH,NOREX,LOCATION from purchasingmanifest WHERE NO = %s",
                                           args['NO'])
                            LEN = cursor.fetchone()
                            cursor.execute('SELECT LBFT FROM rawvalues where NOREX = %s AND LOCATION = %s',
                                           (LEN[1], LEN[2]))
                            LBFT = cursor.fetchone()
                            netwt = calculate_netweight(Data['QTY'], LEN[0], LBFT[0])
                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET QTY = %s ,NETWEIGHT = %s, LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (Data['QTY'], netwt, datetime.datetime.now(), access_token['UserName'], args['NO']))
                        if key == "LENGTH":
                            cursor.execute("select QTY,NOREX,LOCATION from purchasingmanifest WHERE NO = " + args['NO'])
                            QTY = cursor.fetchone()

                            cursor.execute(
                                'SELECT LBFT FROM rawvalues where NOREX = ' + QTY[1] + ' AND LOCATION = "' + QTY[
                                    2] + '"')
                            LBFT = cursor.fetchone()

                            netwt = float(Data['LENGTH']) * float(QTY[0]) * float(LBFT[0]) / 12

                            row_count = cursor.execute(
                                'UPDATE purchasingmanifest SET LENGTH = %s ,NETWEIGHT = %s, LASTDATE = %s , LASTUSER = %s where NO = %s',
                                (
                                    str(Data['LENGTH']), str(netwt), datetime.datetime.now(), access_token['UserName'],
                                    args['NO']))
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
                if Log.register(flask.request.headers.get('Authorization'), "Update manifest", True):
                    db.commit()
                else:
                    raise BadRequest("Try again")
                try:
                    cursor.execute(
                        'SELECT NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER FROM purchasingmanifest where NO = %s',
                        args['NO'])
                    row = cursor.fetchone()
                    return flask.jsonify({
                        "NO": row[0],
                        "UPLOADDATE": row[1],
                        "SHIPMENTDATE": row[2],
                        "EXTRUDER": row[3],
                        "PROJECTID": row[4],
                        "PROJECTNAME": row[5],
                        "NBP": row[6],
                        "BL": row[7],
                        "MANIFEST": row[8],
                        "TICKET": row[9],
                        "SO": row[10],
                        "ITEM": row[11],
                        "ASTRO": row[12],
                        "KEYMARK": row[13],
                        "DESCRIPTION": row[14],
                        "FINISHID": row[15],
                        "FINISHNAME": row[16],
                        "LENGTH": row[17],
                        "QTY": row[18],
                        "LBFT": row[19],
                        "NETWEIGHT": row[20],
                        "NOREX": row[21],
                        "LOCATION": row[22],
                        "MODEL": row[23],
                        "USER": row[24],
                        "LASTDATE": row[25],
                        "LASTUSER": row[26]
                    })
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def delete(self):
        try:
            access_token = authenticator(flask.request.headers.get('Authorization'))
            try:
                Data = flask.request.get_json()
            except HTTPException as e:
                raise BadRequest("Bad Request")
            cursor = db.cursor()
            if Data['status'] == 'delete':
                try:
                    cursor.execute(
                        "DELETE from purchasingmanifest where UPLOADDATE = %s and USER = %s",
                        (dateparser.parse(Data['date']), access_token['UserName']))
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
                db.commit()
            elif (Data['status'] == 'addtowarehouse'):
                try:
                    user_count = cursor.execute(
                        "SELECT NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LASTDATE,LASTUSER from purchasingmanifest where UPLOADDATE = %s and USER = %s",
                        (dateparser.parse(Data['date']), access_token['UserName']))
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
                user = cursor.fetchall()
                try:
                    for i in range(0, user_count):
                        cursor.execute(
                            'INSERT into warehousemanifest (UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LASTDATE,LASTUSER) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                            (
                                str(user[i][1]), str(user[i][2]), str(
                                    user[i][3]), str(user[i][4]), str(user[i][5]), str(
                                    user[i][6]), str(user[i][7]), str(user[i][8]), str(
                                    user[i][9]), str(user[i][10]), str(user[i][11]), str(
                                    user[i][12]), str(user[i][13]), str(user[i][14]), str(
                                    user[i][15]), str(user[i][16]), str(user[i][17]), str(
                                    user[i][18]), str(user[i][19]), str(user[i][20]), str(
                                    user[i][21]), str(user[i][22]), datetime.datetime.now(),
                                str(access_token['UserName'])))
                    cursor.execute(
                        "DELETE from purchasingmanifest where UPLOADDATE = %s and USER = %s",
                        (dateparser.parse(Data['date']), access_token['UserName']))
                except InterfaceError as e:
                    CreateApi.reAssignDb()
                    print(e)
                except Exception as e:
                    return {"message": str(e)}, 500
                db.commit()
            return ({"message": "success"})
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)
