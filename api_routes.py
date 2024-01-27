
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
from marshmallow import Schema, fields, ValidationError, validate, validates
from flask import Flask, jsonify, request, Blueprint, render_template, abort, current_app
from extension import send_json_email, RegisterSchema, send_reset_email, send_sms
import re

api_route = Blueprint('api_route',__name__)

@api_route.route("/reset_password", methods=["GET", "POST"])
def api_reset_request():
    if request.method == "POST":
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'message': 'Invalid email, please try again or register if you are a new user.', 'status': 'danger'}), 400
        else:
            send_reset_email(user)
            return jsonify({'message': 'An email has been sent with instructions to reset your password.', 'status': 'info'}), 200
    return jsonify({'message': 'Method not allowed', 'status': 'error'}), 405

@api_route.route("/reset_password/<token>", methods=["GET", "POST"])
def api_reset_password(token):
    try:
        email = confirm_token(token, current_app)
    except:
        return jsonify({'message': 'The confirmation link is invalid or has expired.', 'status': 'danger'}), 400
    user = User.query.filter_by(email=email).first_or_404()
    if request.method == "POST":
        data = request.get_json()
        hashed_password = current_app.config['bcrypt'].generate_password_hash(data['password']).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        return jsonify({'message': 'Your password has been changed! You should now be able to log in.', 'status': 'success'}), 200
    return jsonify({'message': 'Method not allowed', 'status': 'error'}), 405


@api_route.route("/colleges", methods=["GET"])
def get_colleges():
    try:
        colleges = College.query.all()
        colleges_data = [{"id": college.id, "name": college.college_name} for college in colleges]
        return jsonify(colleges_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'An account with this email already exists'}), 400

        # Check if college_id and email pattern match
        college = College.query.get(college_id)

        # uncomment the following 3 lines soon
        # email_pattern = r'.*' + re.escape(college.email_pattern) + r'$'
        # if not college or not re.match(email_pattern, email):
        #     return jsonify({'error': 'Email does not match institution @edu email pattern'}), 400


        user = User(name=name, email=email, password=current_app.config['bcrypt'].generate_password_hash(password).decode('utf-8'), college_id = college_id, telNumber=telNumber, is_confirmed=False)
        db.session.add(user)
        db.session.commit()
       
        # Generate a unique token for email confirmation
        token = generate_confirmation_token(email, current_app)
        confirm_url = url_for('confirm_email', token=token, _external=True)


        # Create a JSON email template
        json_email_template = {
            "subject": "Please confirm your email",
            "message": f"Please click the link below to confirm your account and login:<br><a href='{confirm_url}'>Activate RideShareFinder Acccount</a>",
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
           
            # Initialize an empty list to store the updated ride information
            updated_rides = []

            for ride in rides_list:
                fromLocationId, toLocationId = ride[2], ride[3]

                fromLocation = db.session.query(Location.location_name).filter(Location.id == fromLocationId).first()
                toLocation = db.session.query(Location.location_name).filter(Location.id == toLocationId).first()

                fromLocationName = fromLocation[0] if fromLocation else None
                toLocationName = toLocation[0] if toLocation else None

                ride_info = {
                    "ride_id": ride[0],
                    "seatsRemaining": ride[1],
                    "fromLocationId": fromLocationId,
                    "toLocationId": toLocationId,
                    "rideDate": ride[4].strftime('%Y-%m-%d'),
                    "rideTime": ride[5].strftime('%H:%M'),
                    "fromLocationName": fromLocationName,
                    "toLocationName": toLocationName
                }
                updated_rides.append(ride_info)
               
            return jsonify(updated_rides)
        except Exception as e:
            return jsonify({"error": str(e)})

@api_route.route("/myRideSearch", methods=["GET"])
@jwt_required()
def apiMyRidesQuery():
    try:
        print('myRideSearch')
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

        # Initialize an empty list to store the updated ride information
        updated_rides = []

        for ride in rides:
            fromLocationId, toLocationId = ride[2], ride[3]

            fromLocation = db.session.query(Location.location_name).filter(Location.id == fromLocationId).first()
            toLocation = db.session.query(Location.location_name).filter(Location.id == toLocationId).first()

            fromLocationName = fromLocation[0] if fromLocation else None
            toLocationName = toLocation[0] if toLocation else None

            ride_info = {
                "ride_id": ride[0],
                "seatsRemaining": ride[1],
                "fromLocationId": fromLocationId,
                "toLocationId": toLocationId,
                "rideDate": ride[4].strftime('%Y-%m-%d'),
                "rideTime": ride[5].strftime('%H:%M'),
                "fromLocationName": fromLocationName,
                "toLocationName": toLocationName
            }

            updated_rides.append(ride_info)

        return jsonify(updated_rides)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Adding a status code for the error response

@api_route.route("/locations", methods=["GET"])
@jwt_required()
def get_locations():
    try:
        userId = get_jwt_identity()
        user = User.query.filter(User.id == userId).first()
        college_id = user.college_id if user else None

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
            error_message = "You have already joined this ride group."
            return jsonify({"error": error_message})

        if currentRide.seatsRemaining > 0:
            # Decrease seats remaining
            currentRide.seatsRemaining -= 1
            # Create a new RideUser record
            new_ride_user = RideUser(ride_id=ride_id, user_id=userId, isHost=False)
            db.session.add(new_ride_user)
            db.session.add(currentRide)  # Add currentRide to the session to update it
            db.session.commit()

            # Send SMS to all users in the ride group except the new user
            ride_users = RideUser.query.filter(
                RideUser.ride_id == ride_id, 
                RideUser.user_id != userId, 
                RideUser.isDeleted == False
            ).all()

            for ride_user in ride_users:
                user_to_notify = User.query.get(ride_user.user_id)
                if user_to_notify:
                    message_txt = "A new user has joined your ride group."
                    send_sms(user_to_notify.telNumber, message_txt)

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
        currentRideUser = RideUser.query.filter_by(ride_id=ride_id, user_id = userId, isDeleted = False).first_or_404()
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

        # Notify other users in the ride group
        other_users_in_ride = RideUser.query.filter(
            RideUser.ride_id == ride_id, 
            RideUser.user_id != userId, 
            RideUser.isDeleted == False
        ).all()

        message_txt = "A user has left your ride group."
        for user in other_users_in_ride:
            user_to_notify = User.query.get(user.user_id)
            if user_to_notify:
                send_sms(user_to_notify.telNumber, message_txt)

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
        ).order_by(RideUser.isHost.desc()).all()  # Descending order to get hosts first

        # Initialize an empty list to store the updated ride information
        updated_rides = []

        for ride in rideDetails_list:
            fromLocationId, toLocationId = ride[2], ride[3]

            fromLocation = db.session.query(Location.location_name).filter(Location.id == fromLocationId).first()
            toLocation = db.session.query(Location.location_name).filter(Location.id == toLocationId).first()

            fromLocationName = fromLocation[0] if fromLocation else None
            toLocationName = toLocation[0] if toLocation else None

            ride_info = {
                "name": ride[0],
                "telNumber": ride[1],
                "fromLocationId": fromLocationId,
                "toLocationId": toLocationId,
                "rideDate": ride[4].strftime('%Y-%m-%d'),
                "rideTime": ride[5].strftime('%H:%M'),
                "seatsRemaining": ride[6],
                "fromLocationName": fromLocationName,
                "toLocationName": toLocationName
            }

            updated_rides.append(ride_info)

        return jsonify(rides=updated_rides)
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

@api_route.route("/userAccount", methods=["GET"])
@jwt_required()
def api_account_get():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user:
            college_name = user.college.college_name if user.college else None
            user_data = {
                "name": user.name,
                "telNumber": user.telNumber,
                "collegeId": user.college_id,
                "collegeName": college_name  # Include the college name in the response
            }
            return jsonify(user_data)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@api_route.route("/campuses", methods=["GET"])
@jwt_required()
def api_campuses():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.college:
            return jsonify({"error": "User or User's College not found"}), 404
        
        email_pattern = user.college.email_pattern
        similar_colleges = College.query.filter_by(email_pattern=email_pattern).all()
        campuses = [{"id": college.id, "name": college.college_name} for college in similar_colleges]
        
        return jsonify(campuses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@api_route.route("/logout", methods=["GET"])
@jwt_required()
def apilogout():
    session.clear()
    print('sesion cleared')
    logout_user()
    return jsonify({'message': 'You have been logged out.'})