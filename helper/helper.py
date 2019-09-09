import datetime

from flask_jwt import jwt
from pymysql import InterfaceError

from Config.api import CreateApi
from customErrors import ProjectNotFound, NorexNotFound, ColorNotFound, InvalidProjectUpdate

db = CreateApi.create_db_connection()

tag_inc = 70000


def authenticator(auth):
    try:
        auth = auth[2:-1]
    except TypeError:
        print(auth)
    return jwt.decode(auth, 'secret', algorithms='HS256', verify=False)


def update_project(cursor, project_id, table, key_name, key, user, Role):
    # cursor is db.cursor
    # project_ id is new project id
    # table is table name
    # key_name is primary key's name
    # key is primary key value
    # user is person who called the function
    try:
        key_count = cursor.execute('SELECT FINISHNAME,FINISHID from ' + table + ' where ' + key_name + ' = %s', (key))
        finish_name = cursor.fetchone()
        if finish_name[0] == 'MILL FINISH' or finish_name[0] == 'CLEAR ANODIZE' or project_id == '9999':
            project_count = cursor.execute("SELECT PROJECTNAME from projects where PROJECTID = %s", (project_id))
            if project_count == 0:
                raise ProjectNotFound('Project not found')
            project = cursor.fetchone()
            row_count = cursor.execute(
                'UPDATE ' + table + ' SET PROJECTID = %s , PROJECTNAME = %s ,LASTDATE = %s ,LASTUSER = %s where ' + key_name + ' = %s',
                (project_id, project[0], datetime.datetime.now(), user, key))
            if row_count == 0:
                return False
        else:
            project_count = cursor.execute(
                "SELECT PROJECTNAME, FINISHID, FINISHNAME from projects where PROJECTID = %s",
                (project_id))
            if project_count == 0:
                raise ProjectNotFound('Project not found')
            project = cursor.fetchone()
            if finish_name[1] == project[1] or Role == 'admin':
                row_count = cursor.execute(
                    'UPDATE ' + table + ' SET PROJECTID = %s, PROJECTNAME = %s, FINISHID = %s, FINISHNAME = %s,LASTDATE = %s ,LASTUSER = %s where ' + key_name + ' = %s',
                    (project_id, project[0], project[1], project[2], datetime.datetime.now(), user, key))
                if row_count == 0:
                    return False
            else:
                raise InvalidProjectUpdate("Finish of current project and new project is not same")
        return True
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)


def calculate_netweight(qty, len, lbft):
    return float(qty) * float(len) * float(lbft) / 12


# edittag
def edittag_json_response_array(cursor, barcode):
    try:
        row_count = cursor.execute(
            'SELECT BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,TAGSTATUS,LASTDATE,LASTUSER,TICKET FROM inventorystorage WHERE BARCODE = %s',
            (barcode))
        row = cursor.fetchone()
        image_count = cursor.execute(
            "SELECT IMAGE from rawvalues where NOREX='" + str(row[15]) + "' and LOCATION ='" + str(row[16]) + "'")
        value = cursor.fetchone()
        if (row_count and image_count > 0):
            return {
                "BARCODE": row[0],
                "TAG": row[1],
                "SHIPMENTDATE": row[2],
                "PROJECTID": row[3],
                "PROJECTNAME": row[4],
                "ASTRO": row[6],
                "KEYMARK": row[7],
                "DESCRIPTION": row[8],
                "FINISHID": row[9],
                "FINISHNAME": row[10],
                "LENGTH": row[11],
                "QTY": row[12],
                "NOREX": row[15],
                "LOCATION": row[16],
                "LOCATIONGRID": row[17],
                "MODEL": row[18],
                "TICKET": row[24],
                "IMAGE": value[0]
            }
        else:
            raise Exception
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        print(e)


def move_to_empty_storage(cursor, barcode, user):
    try:
        if cursor.execute(
                "insert into emptystorage select * from inventorystorage where BARCODE = %s", (barcode)) > 0:
            if cursor.execute("update emptystorage set LASTUSER = %s, LASTDATE = %s where BARCODE =%s",
                              (user, datetime.datetime.now(), barcode)) > 0:
                return cursor.execute("delete from inventorystorage where BARCODE = %s", (barcode))
            else:
                cursor.rollback()
                raise Exception
        else:
            raise Exception
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)


# =========================
# purchasing helpers
# =========================

def get_rawvalues(cursor, key_name, key):
    row_count = cursor.execute(
        'select NOREX,MODEL,LOCATION,DESCRIPTION,LBFT,ASTRO,KEYMARK from rawvalues where ' + key_name + ' = %s', key)
    if row_count == 0:
        raise NorexNotFound("Can not find NOREX for %s: %s" % (key_name, key))
    return cursor.fetchone()


def get_project(cursor, project_id):
    try:
        row_count = cursor.execute(
            'select PROJECTNAME,FINISHID,FINISHNAME from projects where PROJECTID = %s', project_id)
        if row_count == 0:
            raise ProjectNotFound("Can not find PROJECT: %s" % project_id)
        fetchedProject = cursor.fetchone()
        if fetchedProject[1] == "" or fetchedProject[2] == "":
            raise ColorNotFound("Please enter finish for PROJECT ID:%s" % project_id)
        return fetchedProject
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)


def get_color(cursor, color):
    try:
        row_count = cursor.execute(
            'select FINISHID from colors where FINISHNAME = %s', color)
        if row_count == 0:
            raise ColorNotFound("Can not find UC number for: %s" % color)
        return cursor.fetchone()
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)


def insert_into_buffer_manifest(cursor, UPLOADDATE, SHIPMENTDATE, EXTRUDER, PROJECTID, PROJECTNAME, NBP, BL, MANIFEST,
                                TICKET, SO, ITEM, ASTRO, KEYMARK, DESCRIPTION, FINISHID, FINISHNAME, LENGTH, QTY, LBFT,
                                NETWEIGHTexcel, NETWEIGHTnorex, NOREX, LOCATION, MODEL, USER, LASTDATE, LASTUSER,
                                REPLACEMENT, fileName):
    try:
        row_count = cursor.execute(
            'insert into bufferpurchasingmanifest(UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM, ASTRO, KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHTexcel,NETWEIGHTnorex,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,REPLACEMENT,FILENAME)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (
                UPLOADDATE, SHIPMENTDATE, EXTRUDER, PROJECTID, PROJECTNAME, NBP, BL, MANIFEST, TICKET, SO, ITEM, ASTRO,
                KEYMARK,
                DESCRIPTION, FINISHID, FINISHNAME, LENGTH, QTY, LBFT, NETWEIGHTexcel, NETWEIGHTnorex, NOREX, LOCATION,
                MODEL,
                USER, LASTDATE, LASTUSER, REPLACEMENT, fileName))
        if row_count == 0:
            raise ProjectNotFound("Please try again")
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        print(e)


def get_from_buffer_manifest(cursor, user, replacement):
    try:
        if replacement:
            row_count = cursor.execute(
                'select NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHTexcel,NETWEIGHTnorex,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,REPLACEMENT from bufferpurchasingmanifest where REPLACEMENT = 1 AND USER = %s',
                user)
        else:
            row_count = cursor.execute(
                'select NO,UPLOADDATE,SHIPMENTDATE,EXTRUDER,PROJECTID,PROJECTNAME,NBP,BL,MANIFEST,TICKET,SO,ITEM,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHTexcel,NETWEIGHTnorex,NOREX,LOCATION,MODEL,USER,LASTDATE,LASTUSER,REPLACEMENT from bufferpurchasingmanifest where USER = %s',
                user)
        row = cursor.fetchall()
        response = []
        for i in range(0, row_count):
            response.append({
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
                "NETWEIGHTexcel": row[i][20],
                "NETWEIGHTnorex": row[i][21],
                "NOREX": row[i][22],
                "LOCATION": row[i][23],
                "MODEL": row[i][24],
                "USER": row[i][25],
                "LASTDATE": row[i][26],
                "LASTUSER": row[i][27],
                "REPLACEMENT": row[i][28]
            })
        return response
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        print(e)


def get_rejection_for_replacement(cursor, replacementProject, replacementNorex):
    try:
        rejection = []
        rejectionQuery = ""
        for i in range(0, len(replacementProject) - 1):
            rejectionQuery += '(NOREX = "' + replacementNorex[i] + '" AND PROJECTID = "' + replacementProject[
                i] + '") OR '
        rejectionQuery += '(NOREX = "' + replacementNorex[len(replacementProject) - 1] + '" AND PROJECTID = "' + \
                          replacementProject[len(replacementProject) - 1] + '")'
        row_count = cursor.execute(
            'select REJECTIONDATE,BARCODE,TAG,SHIPMENTDATE,PROJECTID,PROJECTNAME,NBP,ASTRO,KEYMARK,DESCRIPTION,FINISHID,FINISHNAME,LENGTH,QTY,LBFT,NETWEIGHT,NOREX,LOCATION,LOCATIONGRID,MODEL,EASCO,EXTRUDER,TAGSTATUS,LASTDATE,LASTUSER from rejection where ' + rejectionQuery)
        row = cursor.fetchall()
        for i in range(0, row_count):
            rejection.append({
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
                "EXTRUDER": row[i][21],
                "TAGSTATUS": row[i][22],
                "LASTDATE": row[i][23],
                "LASTUSER": row[i][24]
            })
        return rejection
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        print(e)


def update_project_tuple(cursor, args, user):
    try:
        # inventory storage
        cursor.execute(
            'update inventorystorage set PROJECTNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], datetime.datetime.now(), user, args['PROJECTID']))
        cursor.execute(
            'update inventorystorage set FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s AND FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE"',
            (args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(), user, args['PROJECTID']))

        # buffer purchasing manifest
        cursor.execute(
            'update bufferpurchasingmanifest set PROJECTNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], datetime.datetime.now(), user, args['PROJECTID']))
        cursor.execute(
            'update bufferpurchasingmanifest set FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s AND FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE"',
            (args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(), user, args['PROJECTID']))

        # purchasing manifest
        cursor.execute(
            'update purchasingmanifest set PROJECTNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], datetime.datetime.now(), user, args['PROJECTID']))
        cursor.execute(
            'update purchasingmanifest set FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s AND FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE"',
            (args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(), user, args['PROJECTID']))

        # warehouse manifest
        cursor.execute(
            'update warehousemanifest set PROJECTNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], datetime.datetime.now(), user, args['PROJECTID']))
        cursor.execute(
            'update warehousemanifest set FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s AND FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE"',
            (args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(), user, args['PROJECTID']))

        # rejection
        cursor.execute(
            'update rejection set PROJECTNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], datetime.datetime.now(), user, args['PROJECTID']))
        cursor.execute(
            'update rejection set FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s AND FINISHID != "MILL FINISH" AND FINISHID != "CLEAR ANODIZE"',
            (args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(), user, args['PROJECTID']))

        # projects
        cursor.execute(
            'update projects set PROJECTNAME = %s, FINISHID = %s, FINISHNAME = %s, LASTDATE = %s,LASTUSER = %s WHERE PROJECTID=%s',
            (args['PROJECTNAME'], args['FINISHID'], args['FINISHNAME'], datetime.datetime.now(),
             user, args['PROJECTID']))
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        print(e)


# =========================
# source helper helper
# =========================

def get_max_norex(cursor):
    try:
        max_norex = cursor.execute("select MAX(NOREX) from rawvalues where LOCATION = 'teterboro'")
        max = cursor.fetchone()
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        return {"message": str(e)}, 500
    return {"NOREX": max[0]}


def get_max_project(cursor):
    try:
        row_count = cursor.execute("select MAX(PROJECTID) from projects WHERE PROJECTID != '9999'")
        max = cursor.fetchone()
        row_count = cursor.execute("select max(PROJECTID) from projects WHERE PROJECTID LIKE '" + str(max[0]) + "%'")
        max = cursor.fetchone()
        return {"PROJECT": max[0]}
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        raise Exception(e)


def get_max_barcode(cursor):
    try:
        max_barcode = cursor.execute("select MAX(BARCODE) from inventorystorage")
        max = cursor.fetchone()
    except InterfaceError as e:
        CreateApi.reAssignDb()
        print(e)
    except Exception as e:
        return {"message": str(e)}, 500
    return {"BARCODE": max[0]}
