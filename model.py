from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime
from flask_login import UserMixin # Add this line
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer #<---HERE
db = SQLAlchemy()

def create_app():
    db.create_all()    
    return app

class College(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)  # Use the appropriate column type and length
    email_pattern = db.Column("email_pattern", db.String, nullable=False)
    college_name = db.Column("college_name", db.String)
    students = db.relationship('User', backref='college', lazy='dynamic') # foreign key setup
    
    def get_colleges():
    # Query the database to get a list of college objects
        college_objects = College.query.all()
    # Create a list of tuples with (college_id, college_name) for choices
        colleges = [(str(college.id), college.college_name) for college in college_objects]
        return colleges

class Location(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)  # Use the appropriate column type and length
    college_id = db.Column("college_id", db.Integer)  # Use the appropriate column type and length
    location_name = db.Column("location_name", db.String)
    isCampus = db.Column("isCampus", db.Boolean, nullable=False, default = False)
    latitude = db.Column(db.Float, nullable = False)
    longitude = db.Column(db.Float, nullable = False)


class RideUser(db.Model):
    id = db.Column("id", db.Integer, primary_key = True)
    ride_id = db.Column("ride_id", db.Integer, db.ForeignKey("ride.id"))
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("user.id"))
    isHost = db.Column("isHost", db.Boolean, nullable=False, default=True)
    isDeleted = db.Column("isDeleted", db.Boolean, nullable=False, default = False)
    createTS = db.Column("CreatedAt", db.Time, default=datetime.now().time())    
    updateTS = db.Column("UpdatedAt", db.Time, default=datetime.now().time())

class Ride(db.Model):
    id = db.Column("id", db.Integer, primary_key = True)
    rideDate = db.Column("Date", db.Date)
    rideTime = db.Column("Departure Time", db.Time)
    createTS = db.Column("CreatedAt", db.Time, default=datetime.now().time())    
    updateTS = db.Column("UpdatedAt", db.Time, default=datetime.now().time())
    isDeleted = db.Column("isDeleted", db.Boolean, nullable=False, default = False)
    seatsRemaining = db.Column("seatsRemaining", db.Integer, default = 3)
    startLocationName = db.Column(db.String(255), nullable = False)
    startLatitude = db.Column(db.Float, nullable = False)
    startLongitude = db.Column(db.Float, nullable = False)
    endLocationName = db.Column(db.String(255), nullable = False)
    endLatitude = db.Column(db.Float, nullable = False)
    endLongitude = db.Column(db.Float, nullable = False)


class Ride_Archive(db.Model):
    id = db.Column("id", db.Integer, primary_key = True)
    rideDate = db.Column("Date", db.Integer)
    rideTime = db.Column("Departure Time", db.Time)
    createTS = db.Column("CreatedAt", db.Time, default=datetime.now().time())    
    updateTS = db.Column("UpdatedAt", db.Time, default=datetime.now().time())
    isDeleted = db.Column("isDeleted", db.Boolean, nullable=False, default = False)
    seatsRemaining = db.Column("seatsRemaining", db.Integer, default = 3)
    startLocationName = db.Column(db.String(255), nullable = False)
    startLatitude = db.Column(db.Float, nullable = False)
    startLongitude = db.Column(db.Float, nullable = False)
    endLocationName = db.Column(db.String(255), nullable = False)
    endLatitude = db.Column(db.Float, nullable = False)
    endLongitude = db.Column(db.Float, nullable = False)


class User(UserMixin, db.Model):

    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  # Add this line for the name column
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    college_id = db.Column("college_id", db.Integer, db.ForeignKey("college.id"))  # Use the appropriate column type and length
    telNumber = db.Column(db.BigInteger, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_driver = db.Column(db.Boolean, nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    createTS = db.Column("CreatedAt", db.Time, default=datetime.now().time())    
    updateTS = db.Column("UpdatedAt", db.Time, default=datetime.now().time())    

    def __init__(self, name, email, password, college_id, telNumber, is_driver=False, is_admin=False, is_confirmed=False):
        self.name = name  # Set the name attribute
        self.email = email
        self.password = password
        self.college_id = college_id
        self.telNumber = telNumber
        self.isDriver = is_driver
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_confirmed = is_confirmed

    def is_authenticated(self):
        if self.is_confirmed:
            return True
        else:
            return False

    def __repr__(self):
        return f"<email {self.email}>"