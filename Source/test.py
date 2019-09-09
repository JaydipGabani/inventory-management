import flask
from flask import request
from xml.sax.saxutils import escape
from flask_restful import Resource, reqparse
from flask_jwt import jwt
import json
from Config.api import CreateApi
import re

db = CreateApi.create_db_connection()


class Test(Resource):
    def post(self):
        data = flask.request.get_json()
        cursor = db.cursor()
        row_count=cursor.execute("select BARCODE,TAG,SHIPMENTDATE,PROJECTID from inventorystorage where BARCODE = 3862")
        row=cursor.fetchone()
        message = []
        for i in range(0,row_count):
            message.append(
                {
                    "BARCODE": row[0],
                    "TAG": row[1],
                    "SHIPMENTDATE": row[2],
                    "PROJECTID": row[3],

                }
            )
        return (flask.jsonify(message))

    def get(self):
        cursor = db.cursor()
        row_count = cursor.execute("select MAX(CAST(PROJECTID AS Int)) from projects WHERE PROJECTID != '9999'")
        max = cursor.fetchone()
        row_count = cursor.execute("select max(PROJECTID) from projects WHERE PROJECTID LIKE '" + str(max[0]) + "%'")
        max=cursor.fetchone()
        return {"id":max[0]}
