from flask import current_app
from flask_mail import Mail, Message
from token_creator import generate_confirmation_token, confirm_token
from flask import Flask, flash, redirect, url_for, render_template, request, session, jsonify, Blueprint
from json import dumps, loads
from marshmallow import Schema, fields, ValidationError, validate, validates
import json, phonenumbers


def init_mail():
    mail = Mail(current_app)
    return mail

def send_json_email(to_email, json_content):
    mail = init_mail()
    msg = Message(json_content['subject'], recipients=[to_email])
    msg.body = json_content['message']
    msg.html = json_content['message']  # Use the same message as HTML (you can customize this)

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

def send_reset_email(user):
        mail = init_mail()
        token = generate_confirmation_token(user.email, current_app)
        link = current_app.config['REACT_SERVER']
        reset_url = link + f"/reset_password/{token}"  # Update this URL
        print('reset  url', reset_url)
        msg = Message('Password Reset Request', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
        msg.body = f"""To reset your password follow this link: {reset_url}
If you did not make this request, ignore this email no changes will be made
        """
        mail.send(msg)

def my_func(json_str:str):
    """ Your Function that Requires JSON string"""

    a_dict = loads(json_str)

    return a_dict


class RegisterSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    repeat_password = fields.String(required=True)
 #   because on web they check letters and numbers
    college_id = fields.Integer(required=True)

    telNumber = fields.String(required=True)

        # Custom validation function for telNumber
    @validates('telNumber')
    def validate_telNumber(self, value):
        # Parse the phone number to validate and format it
        parsed_number = phonenumbers.parse(value, 'US')
        print(parsed_number)
        
        # Check if the phone number is valid
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError('Invalid telephone number')
