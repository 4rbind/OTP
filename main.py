#!/usr/bin/env python3

import os, sqlite3, pyotp, jwt
from Crypto.Hash import SHA256
from flask import *
from datetime import datetime, timezone

con = sqlite3.connect('users.db', check_same_thread=False)
cur = con.cursor()
SECRET_KEY = os.environ.get('SECRET_KEY')

def hash_password(username, password):
	return SHA256.new(f'{username}={password}'.encode()).hexdigest()

def lookup_user(username):
	return list(cur.execute(f"SELECT * FROM users WHERE username = '{username}' LIMIT 1"))

def generate_otp(username):
	return '' if lookup_user(username)[0][3] == '' else pyotp.TOTP(lookup_user(username)[0][3]).now()

def generate_jwt(username):
	# return jwt.encode({'username': username, 'iat': datetime.now(timezone.utc)}, SECRET_KEY)
	return username

def user_login(username, password, otp):
	if lookup_user(username)[0][2] == hash_password(username, password) and otp == generate_otp(username):
		print(otp)
		res = make_response(jsonify({"success": True}))
		res.set_cookie('token', generate_jwt(username), httponly=True)
		cur.execute(f"UPDATE users SET last_login = '{datetime.now()}' WHERE username = '{username}';")
		con.commit()
		return res
	else: return jsonify({"success": False, "error": "wrong credentials", "OTP": otp}), 401

def user_register(username, password, totp=True):
	if lookup_user(username) == []:
		totp = pyotp.random_base32() if totp else ''
		print (totp)
		cur.execute(f"INSERT INTO users (username, password, totp, last_login) VALUES ('{username}', '{hash_password(username, password)}', '{totp}', '{datetime.now()}')")
		con.commit()
		return True
	else:
		return False

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods = ["GET", "POST"])
def login():
	error = None
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		otp = request.form.get('otp')
		if otp == None: 
			otp = ''
		return user_login(username, password, otp)
	return render_template('login.html',error=error)





@app.route('/register', methods = ["GET", "POST"])
def register():
	error = None
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if user_register(username, password):
			otp = generate_otp(username)
			return jsonify({"success": True, "OTP": otp})
		else:
			return jsonify({"success": False, "error": "user with this name is already exist"}), 422
	return render_template('register.html', error=error)



app.run(debug=True)