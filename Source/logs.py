import flask
from flask_restful import Resource, reqparse, request
from flask_jwt import jwt
import time, datetime

from pymysql import InterfaceError

from Config.api import CreateApi

db = CreateApi.create_db_connection()


class Log():
    def register(access_token, func_name, msg):
        try:
            if msg is True:
                d = datetime.datetime.today().strftime('%Y-%m-%d')
                t = datetime.datetime.today().strftime('%H:%M:%S')
                x = access_token
                try:
                    x = x[2:-1]
                except TypeError:
                    print(x)
                access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
                cursor = db.cursor()
                row_count = cursor.execute(
                    "Insert into logs(DATE,TIME,USER,ACTION) VALUES ('" + d + "','" + t + "','" + access_token[
                        'UserName'] + "','" + func_name + "')")
                if row_count > 0:
                    print('Logged Succesfully')
                    message = True
                else:
                    print('Log Failure for: ' + access_token['UserName'] + ' ' + func_name)
                    message = False
                db.commit()
                return (message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)

class LogEndPoint(Resource):
    def get(self):
        try:
            x = request.headers.get('Authorization')
            try:
                x = x[2:-1]
            except TypeError:
                print(x)
            access_token = jwt.decode(x, 'secret', algorithms='HS256', verify=False)
            user = request.args.get('user')
            print(user)
            if (user == ""):
                admin = []
                war = []
                pur = []
                warehouseworker = []
                engineering = []
                sawcutter = []
                cursor = db.cursor()
                admin_count = cursor.execute("SELECT UserName from users where ROLE ='admin'")
                ad = cursor.fetchall()
                for i in range(0, admin_count):
                    admin.append(ad[i])
                war_count = cursor.execute("SELECT UserName from users where ROLE ='warehouse'")
                wa = cursor.fetchall()
                for i in range(0, war_count):
                    war.append(wa[i])
                pur_count = cursor.execute("SELECT UserName from users where ROLE ='purchasing'")
                pu = cursor.fetchall()
                for i in range(0, pur_count):
                    pur.append(pu[i])
                warwor_count = cursor.execute("SELECT UserName from users where ROLE ='materialHandler'")
                wawor = cursor.fetchall()
                for i in range(0, warwor_count):
                    warehouseworker.append(wawor[i])
                eng_count = cursor.execute("SELECT UserName from users where ROLE ='engineering'")
                eng = cursor.fetchall()
                for i in range(0, eng_count):
                    engineering.append(eng[i])
                saw_count = cursor.execute("SELECT UserName from users where ROLE ='sawcutter'")
                saw = cursor.fetchall()
                for i in range(0, saw_count):
                    sawcutter.append(saw[i])

                message = {
                    'admin': admin,
                    'warehouse': war,
                    'purchasing': pur,
                    'warehouseworker': warehouseworker,
                    'engineering': engineering,
                    'sawcutter': sawcutter
                }
                return message
            else:
                message = []
                cursor = db.cursor()
                row_count = cursor.execute('SELECT DATE,TIME,USER,ACTION from logs where USER = %s', (str(user)))
                row = cursor.fetchall()
                print(row_count)
                for i in range(0, row_count):
                    message.append({
                        "DATE": row[i][0],
                        "TIME": str(row[i][1]),
                        "USER": row[i][2],
                        "ACTION": row[i][3]
                    })
                return flask.jsonify(message)
        except InterfaceError as e:
            CreateApi.reAssignDb()
            print(e)
        except Exception as e:
            print(e)
