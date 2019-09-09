import flask
from flask_restful import Resource, reqparse, request
from flask_jwt import jwt
import datetime

from pymysql import InterfaceError

from Config.api import CreateApi
from Source.logs import Log
from helper.helper import authenticator

db = CreateApi.create_db_connection()


class Norex(Resource):
    def get(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            message = []
            query = "Select NOREX, LOCATION, ASTRO, KEYMARK, EASCO, WINSYS, DESCRIPTION, MODEL, LBFT, SH, CAVITY, LASTDATE, LASTUSER, IMAGE from rawvalues where "
            COUNT = request.args.get('COUNT')
            COUNT = int(COUNT)
            COLUMN = request.args.get('COLUMN')
            VALUE = request.args.get('VALUE')
            if COUNT >= 1:
                COLUMN = COLUMN.split(',')
                VALUE = VALUE.split(',')
                for i in range(0, COUNT):
                    if i == COUNT - 1:
                        query = query + COLUMN[COUNT - 1] + '= \'' + VALUE[COUNT - 1] + '\''
                        break
                    query = query + COLUMN[i] + '= \'' + VALUE[i] + '\' AND '
            else:
                query = query + COLUMN + ' 1'
            print('QUERY :' + query)
            cursor = db.cursor()
            row_count = cursor.execute(query)
            if (row_count == 0):
                return {"message": "norex does not exists"}, 404
            row = cursor.fetchall()
            for i in range(0, row_count):
                m = {
                    "NOREX": row[i][0],
                    "LOCATION": row[i][1],
                    "ASTRO": row[i][2],
                    "KEYMARK": row[i][3],
                    "EASCO": row[i][4],
                    "WINSYS": row[i][5],
                    "DESCRIPTION": row[i][6],
                    "MODEL": row[i][7],
                    "LBFT": row[i][8],
                    "SH": row[i][9],
                    "CAVITY": row[i][10],
                    "LASTDATE": row[i][11],
                    "LASTUSER": row[i][12],
                    "IMAGE": row[i][13],
                }
                message.append(m)
            return (flask.jsonify(message))
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

    def post(self):
        try:
            access_token = authenticator(request.headers.get('Authorization'))
            parser = reqparse.RequestParser()
            parser.add_argument('NOREX')
            parser.add_argument('LOCATION')
            parser.add_argument('ASTRO')
            parser.add_argument('KEYMARK')
            parser.add_argument('EASCO')
            parser.add_argument('WINSYS')
            parser.add_argument('DESCRIPTION')
            parser.add_argument('MODEL')
            parser.add_argument('LBFT')
            parser.add_argument('SH')
            parser.add_argument('CAVITY')
            parser.add_argument('IMAGE')
            args = parser.parse_args()
            cursor = db.cursor()
            row_count = cursor.execute(
                'insert into rawvalues(NOREX,LOCATION,ASTRO,KEYMARK,EASCO,WINSYS,DESCRIPTION,MODEL,LBFT,SH,CAVITY,IMAGE,LASTDATE,LASTUSER) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (args['NOREX'], args['LOCATION'], args['ASTRO'], args['KEYMARK'], args['EASCO'], args['WINSYS'],
                 args['DESCRIPTION'], args['MODEL'], args['LBFT'], args['SH'], args['CAVITY'], args['IMAGE'],
                 datetime.datetime.now(), access_token['UserName']))
            if row_count > 0:
                if Log.register(request.headers.get('Authorization'),
                                'New NOREX added with NOREXID: %s ,LOCATION: %s,ASTRO: %s,KEYMARK: %s,EASCO: %s,WINSYS: %s,DESCRIPTION: %s,MODEL: %s,LBFT: %s,SH: %s,CAVITY: %s,' % (
                                        args['NOREX'], args['LOCATION'], args['ASTRO'], args['KEYMARK'], args['EASCO'],
                                        args['WINSYS'],
                                        args['DESCRIPTION'], args['MODEL'], args['LBFT'], args['SH'], args['CAVITY']),
                                True):
                    db.commit()
                    return {'Message': 'Successful'}
                else:
                    db.rollback()
                    return {'message': 'Error - Try Again'}, 500
            else:
                db.rollback()
                return {'message': 'Error - Try Again'}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            if "Duplicate entry" in str(e):
                message = {'message': "Norex %s already exists." % args['NOREX']}
            else:
                message = {"message": str(e)}
            db.rollback()
            return message, 500

    def put(self):
        access_token = authenticator(request.headers.get('Authorization'))
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('NOREX')
            parser.add_argument('LOCATION')
            parser.add_argument('ASTRO')
            parser.add_argument('KEYMARK')
            parser.add_argument('EASCO')
            parser.add_argument('WINSYS')
            parser.add_argument('DESCRIPTION')
            parser.add_argument('MODEL')
            parser.add_argument('LBFT')
            parser.add_argument('SH')
            parser.add_argument('CAVITY')
            parser.add_argument('IMAGE')
            args = parser.parse_args()
            cursor = db.cursor()
            cursor.execute(
                'UPDATE rawvalues SET ASTRO = %s , KEYMARK = %s , EASCO = %s ,WINSYS = %s , DESCRIPTION = %s , MODEL = %s , LBFT = %s , SH = %s , CAVITY = %s , IMAGE = %s , LASTDATE = %s ,LASTUSER = %s WHERE NOREX = %s AND LOCATION = %s',
                (args['ASTRO'], args['KEYMARK'], args['EASCO'], args['WINSYS'], args['DESCRIPTION'], args['MODEL'],
                 args['LBFT'], args['SH'], args['CAVITY'], args['IMAGE'],
                 str(datetime.datetime.now()), access_token['UserName'], args['NOREX'], args['LOCATION']))
            cursor.execute(
                'update bufferpurchasingmanifest set ASTRO=%s , KEYMARK=%s,DESCRIPTION = %s, MODEL = %s, LBFT = %s , LASTDATE = %s ,LASTUSER = %s ,NETWEIGHTnorex=QTY*LENGTH*(%s)/12 WHERE NOREX = %s AND LOCATION = %s'
                , (args['ASTRO'], args['KEYMARK'], args['DESCRIPTION'],
                   args['MODEL'], args['LBFT'], str(datetime.datetime.now()), access_token['UserName'],
                   args['LBFT'],
                   args['NOREX'], args['LOCATION']))
            cursor.execute(
                'update purchasingmanifest set ASTRO=%s , KEYMARK=%s,DESCRIPTION = %s, MODEL = %s, LBFT = %s , LASTDATE = %s ,LASTUSER = %s ,NETWEIGHT=(QTY*LENGTH*(%s)/12) WHERE NOREX = %s AND LOCATION = %s',
                (args['ASTRO'], args['KEYMARK'], args['DESCRIPTION'],
                 args['MODEL'], args['LBFT'], str(datetime.datetime.now()), access_token['UserName'], args['LBFT'],
                 args['NOREX'], args['LOCATION']))
            cursor.execute(
                'update warehousemanifest set ASTRO=%s , KEYMARK=%s,DESCRIPTION = %s, LBFT = %s , LASTDATE = %s ,LASTUSER = %s, NETWEIGHT=(QTY*LENGTH*(%s)/12) WHERE NOREX = %s AND LOCATION = %s',
                (args['ASTRO'], args['KEYMARK'], args['DESCRIPTION'], args['LBFT'], str(datetime.datetime.now()),
                 access_token['UserName'], args['LBFT'],
                 args['NOREX'], args['LOCATION']))
            cursor.execute(
                'update inventorystorage set ASTRO=%s , KEYMARK=%s,DESCRIPTION = %s, MODEL = %s, LBFT = %s , LASTDATE = %s ,LASTUSER = %s ,NETWEIGHT=(QTY*LENGTH*(%s)/12) WHERE NOREX = %s AND LOCATION = %s',
                (args['ASTRO'], args['KEYMARK'], args['DESCRIPTION'],
                 args['MODEL'], args['LBFT'], str(datetime.datetime.now()), access_token['UserName'], args['LBFT'],
                 args['NOREX'], args['LOCATION']))
            if Log.register(request.headers.get('Authorization'),
                            'NOREX updated with with NOREXID: %s ,LOCATION: %s,ASTRO: %s,KEYMARK: %s,EASCO: %s,WINSYS: %s,DESCRIPTION: %s,MODEL: %s,LBFT: %s,SH: %s,CAVITY: %s,' % (
                                    args['NOREX'], args['LOCATION'], args['ASTRO'], args['KEYMARK'], args['EASCO'],
                                    args['WINSYS'],
                                    args['DESCRIPTION'], args['MODEL'], args['LBFT'], args['SH'], args['CAVITY']),
                            True):
                db.commit()
                return {'Message': 'Successful'}
            else:
                db.rollback()
                return {"message": "Some error occurred,Please try again!"}, 500
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            db.rollback()
            return {'message': str(e)}, 500
