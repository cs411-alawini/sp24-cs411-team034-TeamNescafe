from utils import *
from flask import jsonify, request
from db import connection
import hashlib

def authenticate_user(email, password):
    try:
        query = f"SELECT password_hash FROM user WHERE email_id = '{email}';"
        result = run_query(connection, query)
        print(result)
        if result:
            db_password = result[0][0]
            if len(db_password) == 32:
                hashed_password = hashlib.md5(password.encode()).hexdigest()
                return hashed_password == db_password
            else:
                return password == db_password
        else:
            return False

    except Exception as e:
        print("Error:", e)
        return False
    
def login():
    try:
        data = request.json
        email = sanitize_input(data.get('email'))
        password = sanitize_input(data.get('password'))
        if not email or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        if authenticate_user(email, password):
            query = f"SELECT user_id, email_id, role_type, first_name, last_name, phone_number, gender, date_of_birth FROM user WHERE email_id = '{email}';"
            row = run_query(connection, query)[0]
            results = {'user_id': row[0],
                        'email_id': row[1],
                        'role_type': row[2],
                        'first_name': row[3],
                        'last_name': row[4],
                        'phone_number': row[5],
                        'gender': row[6],
                        'date_of_birth': row[7]
                    }
            token = generate_token()
            insert_token(connection, row[0], token)
            return jsonify({'success': True, 'message': 'Login successful', 'token':token, 'user':results})
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500