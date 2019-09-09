from flask import Flask
from flask_restful import Api
from flaskext.mysql import MySQL
from flask_cors import CORS
from flask_mail import Mail
from Source.email import mail

mysql = MySQL()
app = Flask(__name__, template_folder='templates')
CORS(app)
app.secret_key = 'development'
api = Api(app)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'inventorymanagementsystem'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
db = mysql.connect()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nas.inventorysystem@gmail.com'
app.config['MAIL_PASSWORD'] = 'Maunil@inv'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


class CreateApi():
    @staticmethod
    def create_api():
        return app

    @staticmethod
    def create_db_connection():
        return db

    @staticmethod
    def get_api():
        return api

    @staticmethod
    def get_email():
        return mail

    @staticmethod
    def reAssignDb():
        global db
        db.cursor().close()
        db = mysql.connect()
