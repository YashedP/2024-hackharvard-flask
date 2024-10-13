import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json
import jwt
import os
import pymysql

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
RDS_HOST = os.environ['RDS_HOST']
RDS_PORT = int(os.environ['RDS_PORT'])
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB = os.environ['RDS_DB']
SECRET_KEY = os.environ['SECRET_KEY']

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if email == None or password == None or first_name == None or last_name == None:
        return make_response(jsonify({"message": "One or more attributes are missing", "error": "Bad Request"}, 600))
    
    conn = open_db()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
    results = cursor.fetchall()

    if (len(results) > 0):
        cursor.close()
        close_db(conn)
        return make_response(jsonify({"message": "Email already exists", "error": "Bad Request"}), 400)

    certifications = []
    equipments = []

    cursor.execute(
        "INSERT INTO user (first_name, last_name, email, password, certifications, equipments) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (first_name, last_name, email, password, json.dumps(certifications), json.dumps(equipments))
    )

    conn.commit()
    # get the last user added
    cursor.execute(f"SELECT LAST_INSERT_ID()")
    user = cursor.fetchall()[0]

    cursor.close()
    close_db(conn)

    token = jwt.encode({
        "user": user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, SECRET_KEY, algorithm='HS256')

    return make_response(jsonify({"message": "Logged in", "user": user, "token": token}), 200)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = open_db()

    if email == None or password == None:
        close_db(conn)
        return make_response(jsonify({"message": "Missing email or password", "error": "Bad Request"}, 600))

    cursor = conn.cursor()

    # If username is not found in the database
    cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
    results = cursor.fetchall()
    cursor.close()

    if (len(results) == 0):
        close_db(conn)
        return make_response(jsonify({"message": "Email not found", "error": "Bad Request"}, 602))

    user = results[0]
        
    # If password is wrong in the database
    if user[6] != password:
        close_db(conn)
        return make_response(jsonify({"message": "Password is incorrect", "error": "Bad Request"}, 603))

    close_db(conn)

    token = jwt.encode({
        "user": user,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, SECRET_KEY, algorithm='HS256')

    # Success Code, return everything about the user
    return make_response(jsonify({"message": "Logged in", "user": user, "token": token}), 200)

@app.route('/api/add-certification', methods=['POST'])
def add_certification():
    data = request.get_json()
    id = data.get('id')
    certification = data.get('certification')
    
    if id == None or certification == None:
        return make_response(jsonify({"message": "Missing id or certification", "error": "Bad Request"}, 600))

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute("SELECT certifications FROM user WHERE id = %s", (id,))
    
    results = cursor.fetchall()
    certifications = results[0][0]
    certifications.append(certification)
    
    cursor.execute("UPDATE user SET certifications = %s WHERE id = %s", (certifications, id))
    conn.commit()
    
    cursor.close()
    close_db(conn)
    return(jsonify({"message": "Certification added"}, 200))

@app.route('/api/add-equipment', methods=['POST'])
def add_equipment():
    data = request.get_json()
    id = data.get('id')
    equipment = data.get('equipment')
    
    if id == None or equipment == None:
        return make_response(jsonify({"message": "Missing id or equipment", "error": "Bad Request"}, 600))

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute("SELECT equipment FROM user WHERE id = %s", (id,))
    
    results = cursor.fetchall()
    equipment = results[0][0]
    equipment.append(equipment)
    
    cursor.execute("UPDATE user SET equipment = %s WHERE id = %s", (equipment, id))
    conn.commit()
    
    cursor.close()
    close_db(conn)
    return(jsonify({"message": "Equipment added"}, 200))

def token_required(f):
    @wraps(f)  # This helps to maintain the original function's metadata
    def decorator(*args, **kwargs):
        token = None
        # Check if the token is provided in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Get the token from "Bearer <token>"

        if not token:
            return make_response(jsonify({"message": "Token is missing", "error": "Forbidden"}), 403)

        try:
            # Decode the token to get the user data
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['user_id']  # Extract user ID or other information from token
        except jwt.ExpiredSignatureError:
            return make_response(jsonify({"message": "Token has expired", "error": "Unauthorized"}), 401)
        except jwt.InvalidTokenError:
            return make_response(jsonify({"message": "Invalid token", "error": "Unauthorized"}), 401)
        
        return f(current_user, *args, **kwargs)  # Call the wrapped function with user data

    return decorator

@app.route('/api/protected', methods=['GET'])
def protected(current_user):
    return jsonify({"message": f"Welcome, user {current_user}!", "status": "Access granted"})

if __name__ == '__main__':
    app.run(debug=True)

def open_db():
    return pymysql.connect(
        host = RDS_HOST,
        port = RDS_PORT,
        user = RDS_USER,
        password = RDS_PASSWORD,
        database = RDS_DB
    )

def close_db(conn):
    conn.close()
