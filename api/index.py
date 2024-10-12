from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    if username == None or password == None:
        return(jsonify({'status': 'error', 'message': 'Username or password not provided'}))
    return(jsonify({'username': username, 'password': password, 'status': 'success'}))
