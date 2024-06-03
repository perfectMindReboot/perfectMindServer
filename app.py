from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import ssl
import certifi
from bson import json_util, ObjectId
import json
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime
import csv


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

#gets all events for an admin
@app.route('/adminEvents/<adminID>', methods=['GET'])
def get_admin_events(adminID):
    try:
        # Execute the query to get event details, participants, community center, and admin information using JOINs
        query = """
            SELECT e.*, cc.*, a.*, u.*, er.*
            FROM perfectMind.events e
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID
            LEFT JOIN perfectMind.admin a ON e.adminID = a.adminID
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            LEFT JOIN perfectMind.users u ON er.userID = u.userID
            WHERE e.adminID = %s
        """
        cursor.execute(query, (adminID,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()
        print("rows", rows)

        # Initialize a dictionary to store events where the eventID is the key
        events = {}

        # Convert rows to dictionaries
        for row in rows:    
            # Get event ID
            event_id = row[0]

            # Check if event already exists in the dictionary
            if event_id not in events:
                # Populate event data
                event_data = {
                    'eventID': event_id,
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

                # Add the event to the dictionary
                events[event_id] = event_data

            # Check if there are participants
            if row[23] is not None:
                # Append participant data to eventParticipants list of the corresponding event
                events[event_id]['eventParticipants'].append({
                    'userID': row[23],
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
                })

        # Convert the dictionary values to a list of events
        events_list = list(events.values())

        return jsonify({'data': events_list}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
#Gets csv file for an event
import csv
import io
from flask import Response

@app.route('/getUserEvents/<userID>', methods=['GET'])
@app.route('/getUserEvents/<userID>', methods=['GET'])
def get_user_events(userID):
    try:
        query = """
            SELECT * FROM perfectMind.event_registration er 
            LEFT JOIN perfectMind.events e ON er.eventID = e.eventID 
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID 
            WHERE er.userID = %s
        """
        cursor.execute(query, (userID,))
        
        rows = cursor.fetchall()

        events = []
        
        for row in rows:
            # Populate event data
            event_data = {
                'eventID': row[0],  # Assuming eventID is the first column
                'eventCommunityCenterName': row[15],
                'eventCommunityCenterLocation': row[16],
                'eventName': row[5],
                'eventDate': row[6],
                'eventTime': row[7],
                'eventCapacity': row[8],
                'eventDescription': row[9],
                'eventGenderRestrictions': row[10],
                'eventAgeRestrictions': row[11],
                'eventType': row[12],
                'eventCategory': row[13],
            }
            events.append(event_data)

        return jsonify({'data': events}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/downloadCSV/<eventID>', methods=['GET'])
def download_csv(eventID):
    try:
        # Execute the query to get event details and participants for the specified eventID
        query = """
            SELECT e.*, u.*
            FROM perfectMind.events e
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            LEFT JOIN perfectMind.users u ON er.userID = u.userID
            WHERE e.eventID = %s
        """
        cursor.execute(query, (eventID,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()

        # Prepare CSV data
        csv_data = []

        # Extract event details and participant information
        event_details = None
        for row in rows:
            print('row', row)
            if event_details is None:
                # Extract event details (assuming they are the same for all rows)
                event_details = {
                    'Event Name': row[3],
                    'Event Date': row[4],
                    'Event Time': row[5],
                    'Event Capacity': row[6],
                    'Event Description': row[7],
                    # Add more event details if needed
                }
            # Extract participant information
            participant_info = {
                'Event Name': event_details['Event Name'],
                'Event Date': event_details['Event Date'],
                'Present': '',
                'First Name': row[13],
                'Last Name': row[14],
                'Email': row[15],
                'Phone': row[16],
                'Address': row[17],
                'BirthDate': row[18],
                'Gender': row[19],
                'Race': row[20],
                'Medical Conditions': row[21],
                'Emergency Contact Name': row[22],
                'Emergency Contact Relation': row[23],
                'Emergency Contact Phone': row[24],
                'Emergency Contact Email': row[25],
                # Add more participant details if needed
            }
            csv_data.append(participant_info)

        # Create a string buffer to write CSV data
        csv_buffer = io.StringIO()

        # Create a CSV writer
        writer = csv.DictWriter(csv_buffer, fieldnames=participant_info.keys())

        # Write header
        writer.writeheader()

        # Write participant information
        writer.writerows(csv_data)

        # Move the buffer cursor to the beginning
        csv_buffer.seek(0)

        # Create a Flask response with CSV content
        response = Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=event_{eventID}_participants.csv'}
        )

        return response

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500


# gets all events for a cattegory
@app.route('/events/<eventCattegory>', methods=['GET'])
def get_events(eventCattegory):
    try:
        # Execute the query to get event details and participants count
        query = """
            SELECT e.eventID, e.eventName, e.eventDate, e.eventTime, e.eventCapacity, e.eventDescription,
                   e.eventGenderRestrictions, e.eventAgeRestrictions, e.eventType, e.eventCattegory,
                   cc.communityCenterName, cc.communityCenterAddress,
                   COUNT(er.userID) as participantCount
            FROM perfectMind.events e
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            WHERE e.eventCattegory = %s
            GROUP BY e.eventID, e.eventName, e.eventDate, e.eventTime, e.eventCapacity, e.eventDescription,
                     e.eventGenderRestrictions, e.eventAgeRestrictions, e.eventType, e.eventCattegory,
                     cc.communityCenterName, cc.communityCenterAddress
        """
        cursor.execute(query, (eventCattegory,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()
        print("rows", rows)

        # Convert rows to dictionaries
        events = []
        for row in rows:
            print("row", row)
            event_data = {
                'eventID': row[0],
                'eventName': row[1],
                'eventDate': row[2],
                'eventTime': row[3],
                'eventCapacity': row[4],
                'eventDescription': row[5],
                'eventGenderRestrictions': row[6],
                'eventAgeRestrictions': row[7],
                'eventType': row[8],
                'eventCategory': row[9],
                'eventCommunityCenterName': row[10],
                'eventCommunityCenterLocation': row[11],
                'eventParticipants': row[12]  # Count of participants
            }
            events.append(event_data)

        return jsonify({'data': events}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


# Creates an event
from datetime import datetime

@app.route('/events', methods=['POST'])
def create_event():
    try:
        # Extract event parameters from request body
        event_data = request.json
        print('ed', event_data)

        # Extract date and time from the provided strings
        event_date = datetime.strptime(event_data['eventDate'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        event_time = event_data['eventTime']  # Assuming it's already in the format "5PM to 7PM"

        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.events 
            (adminID, communityCenterID, eventName, eventDate, eventTime, eventCapacity, eventDescription, eventGenderRestrictions, eventAgeRestrictions, eventType, eventCattegory)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (event_data['adminID'], event_data['communityCenterID'], event_data['eventName'], event_date, event_time, event_data['eventCapacity'], event_data['eventDescription'], event_data['eventGenderRestrictions'], event_data['eventAgeRestrictions'], event_data['eventType'], event_data['eventCattegory'])
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

@app.route('/deleteRegistrations', methods=['DELETE'])
def deleteRegistrations():
    try:
        cursor.execute("DELETE FROM perfectMind.event_registration")
        conn.commit()
        return jsonify({'message': 'All registrations deleted successfully'}), 200
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
            print("event participant:", row[38], row[24], row[25], row[26], row[27], row[28], row[29])
        

            # Append participant data to eventParticipants list
            event_data['eventParticipants'].append({
                'userID': row[23],
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

#Gets all events for a date
@app.route('/getEventsByDate/<eventDate>', methods=["GET"])
def getEventsByDate(eventDate):
    try:
        # Execute the query to get event details and participants count
        query = """
            SELECT e.eventID, e.eventName, e.eventDate, e.eventTime, e.eventCapacity, e.eventDescription,
                   e.eventGenderRestrictions, e.eventAgeRestrictions, e.eventType, e.eventCattegory,
                   cc.communityCenterName, cc.communityCenterAddress,
                   COUNT(er.userID) as participantCount
            FROM perfectMind.events e
            LEFT JOIN perfectMind.communityCenters cc ON e.communityCenterID = cc.communityCenterID
            LEFT JOIN perfectMind.event_registration er ON e.eventID = er.eventID
            WHERE e.eventDate = %s
            GROUP BY e.eventID, e.eventName, e.eventDate, e.eventTime, e.eventCapacity, e.eventDescription,
                     e.eventGenderRestrictions, e.eventAgeRestrictions, e.eventType, e.eventCattegory,
                     cc.communityCenterName, cc.communityCenterAddress
        """
        cursor.execute(query, (eventDate,))
        
        # Fetch all rows for the query
        rows = cursor.fetchall()
        print("rows", rows)

        # Convert rows to dictionaries
        events = []
        for row in rows:
            print("row", row)
            event_data = {
                'eventID': row[0],
                'eventName': row[1],
                'eventDate': row[2],
                'eventTime': row[3],
                'eventCapacity': row[4],
                'eventDescription': row[5],
                'eventGenderRestrictions': row[6],
                'eventAgeRestrictions': row[7],
                'eventType': row[8],
                'eventCategory': row[9],
                'eventCommunityCenterName': row[10],
                'eventCommunityCenterLocation': row[11],
                'eventParticipants': row[12]  # Count of participants
            }
            events.append(event_data)

        return jsonify({'data': events}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#Creates a user
@app.route('/createUser', methods=["POST"])
def createUser():
    try:
        # Extract event parameters from request body
        user_data = request.json
        print('ud', user_data)
        
        # Convert ISO 8601 format to MySQL datetime format
        user_birthday = datetime.fromisoformat(user_data['userBirthday']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert event into database
        cursor.execute("""
            INSERT INTO perfectMind.users 
            (userFirstName, userLastName, userEmail, userPhone, userAddress, userBirthday, userGender, userRace, userMedConditions, userEmContactName, userEmContactRelation, userEmContactPhone, userEmContactEmail, fireBaseUID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_data['userFirstName'], user_data['userLastName'], user_data['userEmail'], user_data['userPhone'], user_data['userAddress'], user_birthday, user_data['userGender'], user_data['userRace'], user_data['userMedConditions'], user_data['userEmContactName'], user_data['userEmContactRelation'], user_data['userEmContactPhone'], user_data['userEmContactEmail'], user_data['fireBaseUID'])
        )

        # # Fetch the last inserted user's ID
        # user_id = cursor.lastrowid

        # Commit the transaction
        conn.commit()

        # Retrieve the user details using the fetched ID
        cursor.execute("SELECT * FROM perfectMind.users u WHERE u.fireBaseUID = %s", (user_data['fireBaseUID'],))
        created_user = cursor.fetchone()

        # Return the user details as a response
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'userID': created_user[0],
                'userFirstName': created_user[1],
                'userLastName': created_user[2],
                'userEmail': created_user[3],
                'userPhone': created_user[4],
                'userAddress': created_user[5],
                'userBirthday': created_user[6],
                'userGender': created_user[7],
                'userRace': created_user[8],
                'userMedConditions': created_user[9],
                'userEmContactName': created_user[10],
                'userEmContactRelation': created_user[11],
                'userEmContactPhone': created_user[12],
                'userEmContactEmail': created_user[13],
                'fireBaseUID': created_user[14]
            }
        }), 201

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
@app.route('/signIn/<fireBaseUID>', methods=["GET"])
def signIn(fireBaseUID):
    try:
        # Query the user table
        query_user = """
            SELECT *
            FROM perfectMind.users u
            WHERE u.fireBaseUID = %s
        """
        cursor.execute(query_user, (fireBaseUID,))
        user_row = cursor.fetchone()
        
        # If user is found, return user data
        if user_row:
            user_data = {
                'userID': user_row[0],
                'userFirstName': user_row[1],
                'userLastName': user_row[2],
                'userEmail': user_row[3],
                'userPhone': user_row[4],
                'userAddress': user_row[5],
                'userBirthday': user_row[6].strftime('%Y-%m-%d'),  # Format the date
                'userGender': user_row[7],
                'userRace': user_row[8],
                'userMedConditions': user_row[9],
                'userEmContactName': user_row[10],
                'userEmContactRelation': user_row[11],
                'userEmContactPhone': user_row[12],
                'userEmContactEmail': user_row[13],
                'fireBaseUID': user_row[14]
            }
            return jsonify({'data': user_data}), 200
        
        # If user is not found, query the admin table
        query_admin = """
            SELECT *
            FROM perfectMind.admin a
            WHERE a.fireBaseUID = %s
        """
        cursor.execute(query_admin, (fireBaseUID,))
        admin_row = cursor.fetchone()
        
        # If admin is found, return admin data
        if admin_row:
            admin_data = {
                'adminID': admin_row[0],
                'communityCenterID': admin_row[1],
                'adminName': admin_row[2],
                'adminEmail': admin_row[3],
                'fireBaseUID': admin_row[4],
            }
            return jsonify({'data': admin_data}), 200
        
        # If neither user nor admin is found, return "User not found" error
        return jsonify({'error': 'User not found'}), 404
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500

#See all event registrations
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
