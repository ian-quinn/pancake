from flask_mail import Message
from flask import render_template
from app import mail
from app import app
from threading import Thread

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('Reset Your Password',
               sender='bsimtongji@163.com',
               recipients=[user.email],
               text_body=render_template('user/mail.txt',
                                         user=user, token=token),
               html_body=render_template('user/mail.html',
                                         user=user, token=token))


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()