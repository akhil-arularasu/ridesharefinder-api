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
    SECRET_KEY = "hello"
    PORT = environ.get("PORT")

    # mail authentication
    MAIL_USERNAME = "ridesharefinder@gmail.com"
    MAIL_PASSWORD = "zzplvgkjffoxbhvk"
    MAIL_DEFAULT_SENDER = "ridesharefinder@gmail.com"

    # Database 
    #SQLALCHEMY_DATABASE_URI = 'postgresql://oipmjphdmoruca:9a37269d62370bc00e05edf6fd1c40eba48fb464bbb527975541400c5b822fd2@ec2-3-230-24-12.compute-1.amazonaws.com:5432/dao53i37c8qfbs'
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOGIN_MANAGER_LOGIN_VIEW = 'login'
    LOGIN_MANAGER_LOGIN_MESSAGE_CATEGORY = 'danger'
    SESSION_TYPE = 'filesystem'  # You can choose another session type if needed
    JWT_SECRET_KEY = 'mykey'  # Replace with a strong secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # Token expires in 7 days


    SECURITY_PASSWORD_SALT = 'my_precious_two'
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

      
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
