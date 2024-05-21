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

# Define route to get events
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
        return jsonify({'message': 'Event created successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

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

        # Initialize dictionaries to store event data, community center data, and admin data
        event_data = {}
        community_center_data = {}
        admin_data = {}

        # Convert rows to dictionaries
        for row in rows:
            print(row)
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
                'userID': row[22],
                'userFirstName': row[23],
                'userLastName': row[24],
                'userPhone': row[25],
                'userAddress': row[26],
                'userBirthday': row[27],
                'userGender': row[28],
                'userRace': row[29],
                'userMedConditions': row[30],
                'userEmergencyContactName': row[31],
                'userEmergencyContactRelation': row[32],
                'userEmergencyContactPhone': row[33],
                'userEmergencyContactEmail': row[34],
                # Add more fields if needed
            })


        return jsonify({'data': event_data}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/createUser', methods=["POST"])
def createUser():
    try:
        # Extract event parameters from request body
        user_data = request.json
        print('ud', user_data)
        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.users 
            (userFirstName, userLastName, userPhone, userAddress, userBirthday, userGender, userRace, userMedConditions, userEmContactName, userEmContactRelation, userEmContactPhone, userEmContactEmail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_data['userFirstName'], user_data['userLastName'], user_data['userPhone'], user_data['userAddress'], user_data['userBirthday'], user_data['userGender'], user_data['userRace'], user_data['userMedConditions'], user_data['userEmContactName'], user_data['userEmContactRelation'], user_data['userEmContactPhone'], user_data['userEmContactEmail'])
)

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500


    





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
