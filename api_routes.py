
from flask import Flask, flash, redirect, url_for, render_template, request, session, jsonify, Blueprint
from datetime import datetime, timedelta, time
import cgi
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import babel
import dateutil
from dateutil import parser
from model import Ride, db, Ride_Archive, RideUser, User, College, Location
from socket import gethostname
from flask_migrate import Migrate
import requests
import json, phonenumbers
from flask_session import Session
from decouple import config
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required
from token_creator import generate_confirmation_token, confirm_token
from email_sender import send_email
from flask_mail import Mail, Message
#import uuid
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import func
import jwt
from flask import Flask, jsonify, request
from marshmallow import Schema, fields, ValidationError, validate, validates
from flask import Flask, jsonify, request, Blueprint, render_template, abort, current_app
from extension import send_json_email, RegisterSchema


api_route = Blueprint('api_route',__name__)


@api_route.route("/register", methods=["GET", "POST"])
def apiregister():
        users_dict = request.json


        schema = RegisterSchema()
        try:
            # Validate request body against schema data types
            result = schema.load(users_dict)
        except ValidationError as err:
            # Return a nice message if validation fails
            return jsonify(err.messages), 400
        except Exception as e:
            # Return a nice message if validation fails
            return jsonify(e.messages), 500


        name = users_dict['name']
        email = users_dict['email']
        password = users_dict['password']
        repeat_password = users_dict['repeat_password']
        college_id = users_dict['college_id']
        telNumber = users_dict['telNumber']


        if password != repeat_password:
            return jsonify({'error': 'Passwords do not match'}), 400


        user = User(name=name, email=email, password=current_app.config['bcrypt'].generate_password_hash(password).decode('utf-8'), college_id = college_id, telNumber=telNumber, is_confirmed=False)
        db.session.add(user)
        db.session.commit()
       
        # Generate a unique token for email confirmation
        token = generate_confirmation_token(email, current_app)
        confirm_url = url_for('confirm_email', token=token, _external=True)


           # Create a JSON email template
        json_email_template = {
        "subject": "Please confirm your email",
        "message": f"Please click the link below to confirm your email address: {confirm_url}",
    }


        # Send the JSON email
        if send_json_email(email, json_email_template):
            return jsonify({'message': ' A confirmation email has been sent. If you do not see the email, please be sure to check your Junk Mail inbox.'})
        else:
            return jsonify({'error': 'Invalid Data'}), 500


@api_route.route("/create", methods=["POST"])
@jwt_required()
def apicreate():
        try:
            rides_dict = request.json
            print("Received data:", rides_dict)  
            userId = get_jwt_identity()
            seatsRemaining = rides_dict['seatsRemaining']
            rideDate = rides_dict['rideDate']
            rideTime = datetime.strptime(rides_dict['rideTime'], '%H:%M').time()
            from_location_id = rides_dict['fromLocationId']
            to_location_id = rides_dict['toLocationId']


            # Check if the record already exists
            print("user:", userId)  
            dbRecord = db.session.query(Ride.id, RideUser.id).filter(
                RideUser.ride_id == Ride.id,
                RideUser.user_id == userId,
                Ride.fromLocationId == from_location_id,
                Ride.toLocationId == to_location_id,
                Ride.rideDate == rideDate,
                Ride.isDeleted == False
            ).all()
            print('db record', dbRecord)
            if (dbRecord):
                error_message = "Your ride information already exists in the system. Please Update"
                return jsonify({"error": error_message})
            else:
                new_ride = Ride(rideDate=rideDate, rideTime=rideTime, fromLocationId = from_location_id, toLocationId=to_location_id, seatsRemaining = seatsRemaining)
                print(new_ride)
                db.session.add(new_ride)
                db.session.flush()
                new_ride_user = RideUser(ride_id=new_ride.id, user_id = userId, isHost=True)
                db.session.add(new_ride_user)
                db.session.commit()
            return jsonify({"message": "Ride Request Created!"})
        except Exception as e:
            return jsonify({"error": str(e)})
       
@api_route.route("/search", methods=["GET"])
@jwt_required()
def apiridesQuery():
        try:
            from_location_id = request.args.get("fromLocationId")
            to_location_id = request.args.get("toLocationId")
            ride_date = request.args.get("rideDate")      
            start_time = datetime.strptime(request.args.get("startTime"), '%H:%M').time()
            end_time = datetime.strptime(request.args.get("endTime"), '%H:%M').time()


            rides_list = db.session.query(Ride.id, Ride.seatsRemaining, Ride.fromLocationId, Ride.toLocationId, Ride.rideDate, Ride.rideTime).filter(
    #           User.id == Ride.user_id,
                Ride.id == RideUser.ride_id,
                User.id == RideUser.user_id,
                RideUser.isHost == True,
                Ride.fromLocationId == from_location_id,
                Ride.toLocationId == to_location_id,
                Ride.rideTime.between(start_time, end_time),
                Ride.rideDate == ride_date,
                Ride.isDeleted == False
            ).order_by(Ride.rideTime).all()


            rides_list_as_dicts = [
                {
                    "rideId": record[0],
                    "seatsRemaining": record[1],
                    "fromLocationId": record[2],
                    "toLocationId": record[3],
                    "rideDate": record[4].strftime('%Y-%m-%d'),  # Convert date to string
                    "rideTime": record[5].strftime('%H:%M'),    # Convert time to string
                }
                for record in rides_list
            ]
               
            return jsonify(rides=rides_list_as_dicts)
        except Exception as e:
            return jsonify({"error": str(e)})


@api_route.route("/myRideSearch", methods=["GET"])
@jwt_required()
def apiMyRidesQuery():
        try:
            print('myRideSearch')
            print('JWT', get_jwt_identity())
            userId = get_jwt_identity()
            print('userId', userId)
            # Query to get list of ride IDs
            ride_ids_subquery = db.session.query(RideUser.ride_id).filter(
                RideUser.user_id == userId,
                RideUser.isDeleted == False
            ).subquery()

            # Query Ride model using ride IDs
            rides = db.session.query(
                Ride.id,
                Ride.seatsRemaining,
                Ride.fromLocationId,
                Ride.toLocationId,
                Ride.rideDate,
                Ride.rideTime
            ).filter(
                Ride.id.in_(ride_ids_subquery),
                Ride.isDeleted == False
            ).order_by(Ride.rideTime).all()

            # Format the results as a list of dicts or similar, depending on your requirement
            rides_list = [
                {
                    "ride_id": ride[0],
                    "seatsRemaining": ride[1],
                    "fromLocationId": ride[2],
                    "toLocationId": ride[3],
                    "rideDate": ride[4].strftime('%Y-%m-%d'),
                    "rideTime": ride[5].strftime('%H:%M')
                } for ride in rides
            ]

            return jsonify(rides_list)

        except Exception as e:
            return jsonify({"error": str(e)})

@api_route.route("/locations", methods=["GET"])
@jwt_required()
def get_locations():
    try:
        college_id = 1

        query = Location.query.filter(Location.college_id == college_id).all()

        locations_list = [
            {
                'location_id': loc.id, 
                'location_name': loc.location_name, 
                'isCampus': loc.isCampus
            } 
            for loc in query
        ]
        print(locations_list)
        return jsonify(locations_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_route.route("/join", methods=["POST"])
@jwt_required()
def apiJoin():
    try:
        rides_dict = request.json
        ride_id = rides_dict['ride_id']
        userId = get_jwt_identity()
        
        # Retrieve the ride record
        currentRide = Ride.query.filter_by(id=ride_id).first_or_404()
        
        # Check if the user is already in a ride group
        existing_ride_user = RideUser.query.filter_by(
            ride_id=ride_id,
            user_id=userId,
            isDeleted=False 
        ).first()

        if existing_ride_user:
            error_message = "You have already joined this ride group, please leave before joining a new one."
            return jsonify({"error": error_message})

        if currentRide.seatsRemaining > 0:
            # Decrease seats remaining
            currentRide.seatsRemaining -= 1
            # Create a new RideUser record
            new_ride_user = RideUser(ride_id=ride_id, user_id=userId, isHost=False)
            db.session.add(new_ride_user)
            db.session.add(currentRide)  # Add currentRide to the session to update it
            db.session.commit()
            return jsonify({"message": "Joined Ride Group!"})
        else:
            return jsonify({"error": "No seats available in this ride group."})

    except Exception as e:
        return jsonify({"error": str(e)})

@api_route.route("/leave", methods=["POST"])
@jwt_required()
def apiLeave():
    try:
        rides_dict = request.json
        ride_id = rides_dict['rideId']
        userId = get_jwt_identity()
        currentRide = Ride.query.filter(Ride.id == ride_id).first_or_404()
        currentRideUser = RideUser.query.filter_by(ride_id=ride_id, user_id = userId).first_or_404()
        if currentRideUser:
            currentRideUser.isDeleted = True
            currentRide.seatsRemaining = currentRide.seatsRemaining + 1
            db.session.add(currentRideUser)
            db.session.flush()
        number_of_users = RideUser.query.filter(RideUser.ride_id == ride_id, RideUser.isDeleted == False).count()
        if number_of_users == 0:
            if currentRide:
                currentRide.isDeleted = True
        db.session.add(currentRide)
        db.session.commit()
        print('left')
        return jsonify({"message": "Left Ride Group."})
    except Exception as e:
        return jsonify({"error": str(e)})

@api_route.route("/rideDetails", methods=["GET"])
@jwt_required()
def apirideDetails():
     try:
        rideId = request.args.get("rideId")
        rideDetails_list = db.session.query(User.name, User.telNumber, Ride.fromLocationId, Ride.toLocationId, Ride.rideDate, Ride.rideTime, Ride.seatsRemaining).filter(
             Ride.id == RideUser.ride_id,
             RideUser.user_id == User.id,
             Ride.id == rideId,
             Ride.isDeleted == False,
             RideUser.isDeleted == False
         )
        rideDetails_list_as_dicts = [
            {
                "name": record[0],
                "telNumber": record[1],
                "fromLocationId": record[2],
                "toLocationId": record[3],
                "rideDate": record[4].strftime('%Y-%m-%d'),  # Convert date to string
                "rideTime": record[5].strftime('%H:%M'),    # Convert time to string
                "seatsRemaining": record[6]
            }
        for record in rideDetails_list
        ]
        return jsonify(rides=rideDetails_list_as_dicts)
     except Exception as e:
        return jsonify({"error": str(e)})


@api_route.route("/login", methods=["GET", "POST"])
def apilogin():
        users_dict = request.json
        print("Received data:", users_dict)  

        email = users_dict['email']
        password = users_dict['password']

        user = User.query.filter_by(email=email).first()


        if user and current_app.config['bcrypt'].check_password_hash(user.password, password.encode('utf-8')):
            if user.is_confirmed:
                access_token = create_access_token(identity=user.id)
                login_user(user)
                return jsonify({'access_token': access_token, 'message': 'Login successful'})
            else:
                # User is not confirmed
                return jsonify({'error': 'User authentication pending. Please check your Email.'})
        else:
            # Invalid email or password
            return jsonify({'error': 'Invalid email and/or password'})


@api_route.route("/account", methods=["PUT"])
@jwt_required()
def api_account_update():
    try:
        # Get the current user's identity
        current_user_id = get_jwt_identity()


        # Get user account details from the request JSON data
        account_data = request.json
        new_name = account_data.get('name')
        new_telephone = account_data.get('telNumber')
        college_id = account_data.get('collegeId') # @todo validate college for user when expanding
        # @todo add validations here
        my_college = College.query.filter_by(id=college_id).first()
        # Update the user's account details
        user_to_update = User.query.get(current_user_id)
        if user_to_update:
            user_to_update.name = new_name
            user_to_update.telNumber = new_telephone
            user_to_update.college_id = my_college.id

            db.session.commit()

            return jsonify({"message": "User account updated successfully"})
        else:
            return jsonify({"error": "User not found"})
    except Exception as e:
        return jsonify({"error": str(e)})


@api_route.route("/logout")
def apilogout():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not logged in'}), 401  # Unauthorized status
    logout_user()
    return jsonify({'message': 'You have been logged out.'})