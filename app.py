from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import ssl
import certifi
from bson import json_util, ObjectId
import json
import mysql.connector
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Define database configuration
db_config = {
    'host': os.environ.get('MYSQL_HOST'),
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'database': 'perfectMind'
}

# Connect to MySQL database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# gets all events for a cattegory
@app.route('/events/<eventCattegory>', methods=['GET'])
def get_events(eventCattegory):
    try:
        # Execute the query
        query = "SELECT * FROM perfectMind.events WHERE eventCattegory='" + eventCattegory + "'"
        cursor.execute(query)
        # Fetch all rows
        rows = cursor.fetchall()
        # Convert rows to dictionary
        events = []
        for row in rows:
            # Fetch admin name
            cursor.execute("SELECT adminName FROM perfectMind.admin WHERE adminID = %s", (row[1],))
            admin_name = cursor.fetchone()[0]  # Assuming the name is in the first column

            # Fetch community center name
            cursor.execute("SELECT communityCenterName FROM perfectMind.communityCenters WHERE communityCenterID = %s", (row[2],))
            center_name = cursor.fetchone()[0]  # Assuming the name is in the first column

            event = {
                'eventID': row[0],
                'adminID': row[1],
                'adminName': admin_name,
                'communityCenterID': row[2],
                'communityCenterName': center_name,
                'eventName': row[3],
                'eventDate': row[4],
                'eventTime': row[5],
                'eventCapacity': row[6],
                'eventDescription': row[7],
                'eventGenderRestrictions': row[8],
                'eventAgeRestrictions': row[9],
                'eventType': row[10],
                'eventCategory': row[11]
            }
            events.append(event)
        return jsonify(events)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


# Creates an event
@app.route('/events', methods=['POST'])
def create_event():
    try:
        # Extract event parameters from request body
        event_data = request.json
        print('ed', event_data)
        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.events 
            (adminID, communityCenterID, eventName, eventDate, eventTime, eventCapacity, eventDescription, eventGenderRestrictions, eventAgeRestrictions, eventType, eventCattegory)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (event_data['adminID'], event_data['communityCenterID'], event_data['eventName'], event_data['eventDate'], event_data['eventTime'], event_data['eventCapacity'], event_data['eventDescription'], event_data['eventGenderRestrictions'], event_data['eventAgeRestrictions'], event_data['eventType'], event_data['eventCattegory'])
        )

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Event created successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#Allows a user to sign up for an event
@app.route('/eventSignup/<eventID>/<userID>', methods=['POST'])
def eventSignup(eventID, userID):
    try:
        cursor.execute("""
            INSERT INTO perfectMind.event_registration
            VALUES (%s, %s)""",
            (eventID, userID)
        )
        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'successfully signed up for event'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#gets an event by id, inlcuding detials, location, and participants
@app.route('/getEvent/<eventID>', methods=["GET"])
def getEvent(eventID):
    try:
        # Execute the query to get event details, participants, community center, and admin information using JOINs
        query = """
            SELECT e.*, cc.*, a.*, u.*, er.*
            FROM perfectMind.events e
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID
            LEFT JOIN perfectMind.admin a ON e.adminID = a.adminID
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            LEFT JOIN perfectMind.users u ON er.userID = u.userID
            WHERE e.eventID = %s
        """
        cursor.execute(query, (eventID,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()
        print("rows", rows)

        # Initialize dictionaries to store event data, community center data, and admin data
        event_data = {}
        community_center_data = {}
        admin_data = {}

        # Convert rows to dictionaries
        for row in rows:
            print("rows", row)
            # Populate event data
            if not event_data:
                event_data = {
                    'eventID': row[0],
                    # 'eventCommunityCenterCoordinator': row[16],
                    'eventCommunityCenterName': row[13],
                    'eventCommunityCenterLocation': row[14],
                    'eventName': row[3],
                    'eventDate': row[4],
                    'eventTime': row[5],
                    'eventCapacity': row[6],
                    'eventDescription': row[7],
                    'eventGenderRestrictions': row[8],
                    'eventAgeRestrictions': row[9],
                    'eventType': row[10],
                    'eventCategory': row[11],
                    'eventParticipants': []  # Initialize eventParticipants for the event
                }
        

            # Append participant data to eventParticipants list
            event_data['eventParticipants'].append({
                'userID': row[38],
                'userFirstName': row[24],
                'userLastName': row[25],
                'userEmail': row[26],
                'userPhone': row[27],
                'userAddress': row[28],
                'userBirthday': row[29],
                'userGender': row[30],
                'userRace': row[31],
                'userMedConditions': row[32],
                'userEmergencyContactName': row[33],
                'userEmergencyContactRelation': row[34],
                'userEmergencyContactPhone': row[35],
                'userEmergencyContactEmail': row[36],
                'fireBaseUID': row[37]
                # Add more fields if needed
            })


        return jsonify({'data': event_data}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/getEventsByDate/<eventDate>', methods=["GET"])
def getEventsByDate(eventDate):
    try:
        # Execute the query to get event details, participants, community center, and admin information using JOINs
        query = """
            SELECT e.*, cc.*, a.*, u.*, er.*
            FROM perfectMind.events e
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID
            LEFT JOIN perfectMind.admin a ON e.adminID = a.adminID
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            LEFT JOIN perfectMind.users u ON er.userID = u.userID
            WHERE e.eventDate = %s
        """
        cursor.execute(query, (eventDate,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()
        print("rows", rows)

        # Initialize a dictionary to store events data
        events = {}

        # Convert rows to dictionaries
        for row in rows:
            print("row", row)
            event_id = row[0]
            
            # Check if the event already exists in the dictionary
            if event_id not in events:
                # Populate event data
                events[event_id] = {
                    'eventID': row[0],
                    'eventCommunityCenterName': row[13],
                    'eventCommunityCenterLocation': row[14],
                    'eventName': row[3],
                    'eventDate': row[4],
                    'eventTime': row[5],
                    'eventCapacity': row[6],
                    'eventDescription': row[7],
                    'eventGenderRestrictions': row[8],
                    'eventAgeRestrictions': row[9],
                    'eventType': row[10],
                    'eventCategory': row[11],
                    'eventParticipants': []  # Initialize eventParticipants for the event
                }
            
            # Append participant data to eventParticipants list
            participant_data = {
                'userID': row[38],
                'userFirstName': row[24],
                'userLastName': row[25],
                'userEmail': row[26],
                'userPhone': row[27],
                'userAddress': row[28],
                'userBirthday': row[29],
                'userGender': row[30],
                'userRace': row[31],
                'userMedConditions': row[32],
                'userEmergencyContactName': row[33],
                'userEmergencyContactRelation': row[34],
                'userEmergencyContactPhone': row[35],
                'userEmergencyContactEmail': row[36],
                'fireBaseUID': row[37]
            }
            events[event_id]['eventParticipants'].append(participant_data)

        # Convert the events dictionary to a list
        events_list = list(events.values())

        return jsonify({'data': events_list}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#Creates a user
@app.route('/createUser', methods=["POST"])
def createUser():
    try:
        # Extract event parameters from request body
        print('ud', user_data)
        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.users 
            (userFirstName, userLastName, userEmail, userPhone, userAddress, userBirthday, userGender, userRace, userMedConditions, userEmContactName, userEmContactRelation, userEmContactPhone, userEmContactEmail, fireBaseUID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_data['userFirstName'], user_data['userLastName'], user_data['userEmail'], user_data['userPhone'], user_data['userAddress'], user_data['userBirthday'], user_data['userGender'], user_data['userRace'], user_data['userMedConditions'], user_data['userEmContactName'], user_data['userEmContactRelation'], user_data['userEmContactPhone'], user_data['userEmContactEmail'], user_data['fireBaseUID'],)
)

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#creates Admin
@app.route('/createAdmin', methods=["POST"])
def createAdmin():
    try:
        user_data = request.json
        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.admin 
            (communityCenterID, adminName, adminEmail, fireBaseUID)
            VALUES (%s, %s, %s, %s)""",
            (user_data['communityCenterID'], user_data['adminName'], user_data['adminEmail'], user_data['fireBaseUID'])
)

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Admin created successfully'}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    
#User SignIn
@app.route('/userSignIn/<fireBaseUID>', methods=["GET"])
def getUser(fireBaseUID):
    try:
        query = """
            SELECT *
            FROM perfectMind.users u
            WHERE u.fireBaseUID = %s
        """
        cursor.execute(query, (fireBaseUID,))
        
        # Fetch the row for the query
        row = cursor.fetchone()
        print(row)
        
        if row:
            user_data = {
                'userID': row[0],
                'userFirstName': row[1],
                'userLastName': row[2],
                'userEmail': row[3],
                'userPhone': row[4],
                'userAddress': row[5],
                'userBirthday': row[6].strftime('%Y-%m-%d'),  # Format the date
                'userGender': row[7],
                'userRace': row[8],
                'userMedConditions': row[9],
                'userEmContactName': row[10],
                'userEmContactRelation': row[11],
                'userEmContactPhone': row[12],
                'userEmContactEmail': row[13],
                'fireBaseUID': row[14]
            }
            return jsonify({'data': user_data}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#Admin Signin
@app.route('/adminSignIn/<fireBaseUID>', methods=["GET"])
def adminSignIn(fireBaseUID):
    try:
        query = """
            SELECT *
            FROM perfectMind.admin a
            WHERE a.fireBaseUID = %s
        """
        cursor.execute(query, (fireBaseUID,))
        
        # Fetch the row for the query
        row = cursor.fetchone()
        print(row)
        
        if row:
            user_data = {
                'adminID': row[0],
                'communityCenterID': row[1],
                'adminName': row[2],
                'adminEmail': row[3],
                'fireBaseUID': row[4],
            }
            return jsonify({'data': user_data}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/eventRegistration', methods=['GET'])
def eventRegistration():
    try:
        query = """
            SELECT *
            FROM perfectMind.event_registration
        """
        cursor.execute(query)
        
        # Fetch the row for the query
        rows = cursor.fetchall()
        print(rows)
        eventRegistrations = []
        for row in rows:
            eventReg={
                "eventID": row[0],
                "userID": row[1]
            }
            eventRegistrations.append(eventReg)
        
        return jsonify({'data': eventRegistrations}), 200
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
