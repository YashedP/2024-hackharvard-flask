from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    if username == None or password == None:
        return(jsonify({"error": str('Missing username or password')}, 505))
    return(jsonify({'username': username, 'password': password, 'status': 'success'}))

if __name__ == '__main__':
    app.run(debug=True)
