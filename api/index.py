import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import jwt
import os
import pymysql

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
RDS_HOST = os.environ('RDS_HOST')
RDS_PORT = os.environ('RDS_PORT')
RDS_USER = os.environ('RDS_USER')
RDS_PASSWORD = os.environ('RDS_PASSWORD')
RDS_DB = os.environ('RDS_DB')
SECRET_KEY = os.environ('SECRET_KEY')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    date_of_birth = datetime.date(year, month, day)
    
    if email == None or password == None or first_name == None or last_name == None or date_of_birth == None:
        return(jsonify({"message": "One or more attributes are missing", "error": "Bad Request"}, 600))
    
    conn = open_db()

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE email = {email}")
    results = cursor.fetchall()

    if (len(results) > 0):
        cursor.close()
        close_db(conn)
        return(jsonify({"message": "Email already exists", "error": "Bad Request"}, 601))

    cursor.execute(f"INSERT INTO users (first_name, last_name, date_of_birth, email, password, certifications, equipments) VALUES ({first_name}, {last_name}, {date_of_birth}, {email}, {password}, {[]}, {[]})")
    cursor.execute(f"SELECT LAST_INSERT_ID()")
    id = cursor.fetchall()[0][0]

    conn.commit()
    cursor.close()
    close_db(conn)

    token = jwt.encode({
        'id': id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    })

    return(jsonify({"Message": "Logged in", "id": id, "token": token}, 200))

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = open_db()

    if email == None or password == None:
        close_db(conn)
        return(jsonify({"message": "Missing email or password", "error": "Bad Request"}, 600))

    cursor = conn.cursor()

    # If username is not found in the database
    cursor.execute(f"SELECT * FROM users WHERE email = {email}")
    results = cursor.fetchall()
    cursor.close()

    if (len(results) == 0):
        close_db(conn)
        return(jsonify({"message": "Email not found", "error": "Bad Request"}, 602))

    person = results[0]
        
    # If password is wrong in the database
    if person[6] != password:
        close_db(conn)
        return(jsonify({"message": "Password is incorrect", "error": "Bad Request"}, 603))

    close_db(conn)

    token = jwt.encode({
        'id': person[0],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    })

    # Success Code, return everything about the user
    return(jsonify({"Message": "Logged in", "user": person, "token": token}, 200))

@app.route('/api/protected', methods=['GET'])
def protected():
    
    pass

@app.route('api/add-certification', methods=['POST'])
def add_certification():
    data = request.get_json()
    id = data.get('id')
    certification = data.get('certification')
    
    if id == None or certification == None:
        return(jsonify({"message": "Missing id or certifications", "error": "Bad Request"}, 600))

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT certifications FROM users WHERE id = {id}")
    
    results = cursor.fetchall()
    certifications = results[0][0]
    certifications.append(certification)
    
    cursor.execute(f"UPDATE users SET certifications = {certifications} WHERE id = {id}")
    conn.commit()
    
    cursor.close()
    close_db(conn)
    return(jsonify({"message": "Certification added"}, 200))

@app.route('api/add-equipment', methods=['POST'])
def add_equipment():
    data = request.get_json()
    id = data.get('id')
    equipment = data.get('equipment')
    
    if id == None or equipment == None:
        return(jsonify({"message": "Missing id or equipment", "error": "Bad Request"}, 600))

    conn = open_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT equipment FROM users WHERE id = {id}")
    
    results = cursor.fetchall()
    equipment = results[0][0]
    equipment.append(equipment)
    
    cursor.execute(f"UPDATE users SET equipment = {equipment} WHERE id = {id}")
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
            return jsonify({'message': 'Token is missing!'}), 403  # Forbidden if no token

        try:
            # Decode the token to get the user data
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['user_id']  # Extract user ID or other information from token
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401  # Unauthorized if expired
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401  # Unauthorized if invalid

        return f(current_user, *args, **kwargs)  # Call the wrapped function with user data

    return decorator


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