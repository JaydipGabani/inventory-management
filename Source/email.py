from flask import render_template
from flask_mail import Message
from Config.api import CreateApi

db = CreateApi.create_db_connection()
mail = CreateApi.get_email()


class Email():
    def email(subject, body, user, email, template):
        if template == 'email':
            msg = Message(subject=subject, sender='nas.inventorysystem@gmail.com', recipients=email)
            msg.html = render_template('email.html', user=user, body=body)
            mail.send(msg)
            return True
        elif template == 'exceptionInQty':
            msg = Message(subject=subject, sender='nas.inventorysystem@gmail.com', recipients=email)
            msg.html = render_template('exceptionQty.html', user=user, body=body)
            mail.send(msg)
            return True
        elif template == 'manifestUpload':
            msg = Message(subject=subject, sender='nas.inventorysystem@gmail.com', recipients=email)
            msg.html = render_template('manifestUpload.html', user=user, body=body)
            mail.send(msg)
            return True
