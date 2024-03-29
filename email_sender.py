from flask_mail import Message


def send_email(to, subject, template,app,mail):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    print('sending email', msg)
    mail.send(msg)
