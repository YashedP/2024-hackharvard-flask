from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)

@app.route('/api/login', methods=['POST'])
def login():
    username = request.args.get('username')
    password = request.args.get('password')

    if username == None or password == None:
        return(jsonify({'status': 'error', 'message': 'Username or password not provided'}))
    return(jsonify({'username': username, 'password': password, 'status': 'success'}))
