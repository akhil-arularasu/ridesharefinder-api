"""Flask App configuration."""
from os import environ, path
from dotenv import load_dotenv
from datetime import timedelta

# Specificy a `.env` file containing key/value config values
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask config variables."""

    # General Config
    ENVIRONMENT = environ.get("ENVIRONMENT")
    FLASK_APP = environ.get("FLASK_APP")
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    SECRET_KEY = 'hello'
    PORT = environ.get("PORT")
    REACT_SERVER = environ.get("REACT_SERVER")

    # mail authentication
    MAIL_USERNAME = "ridesharefinder@gmail.com"
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = "ridesharefinder@gmail.com"

    # Database 
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL').replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOGIN_MANAGER_LOGIN_VIEW = 'login'
    LOGIN_MANAGER_LOGIN_MESSAGE_CATEGORY = 'danger'
    SESSION_TYPE = 'filesystem'  # You can choose another session type if needed
    JWT_SECRET_KEY = environ.get('JWT_SECRET_KEY')  # Replace with a strong secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # Token expires in 7 days

    SECURITY_PASSWORD_SALT = environ.get("SECURITY_PASSWORD_SALT")
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

# Twilio
    TWILIO_ACCOUNT_SID  = environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = environ.get("TWILIO_AUTO_TOKEN")
    TWILIO_FROM_PHONE = environ.get("TWILIO_FROM_PHONE")
      
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
