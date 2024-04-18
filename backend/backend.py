from flask import Flask, jsonify, request, globals
from flask_cors import CORS
from utils import *
from datetime import datetime
from routes.auth import *
from db import connect_to_database

configuration = load_backend_config()
DB_CONFIG = configuration['DB_CONFIG']
PORT = configuration['PORT']
ENV = configuration['ENV']
VERSION = configuration['VERSION']

app = Flask(f"SuiteMate Server v{VERSION}")
CORS(app)

connection = connect_to_database(DB_CONFIG)
app.connection = connection

app.route('/api/login', methods=['POST'])(login)

@app.route('/api/get_unit_from_id', methods=['GET'])
def get_unit_from_id():
    try:
        unit_id = request.args.get('unit_id')
        query = f"SELECT u.apartment_no, u.bedrooms, u.bathrooms, u.price, u.availability, u.area , up.photo FROM unit u NATURAL JOIN unitphoto up where u.unit_id = {unit_id};"
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                'apartment_no': row[0],
                'bedrooms': row[1],
                'bathrooms': row[2],
                'price': row[3],
                'availability': row[4],
                'area': row[5],
                'photo': row[6],
            })
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/update_application', methods=['POST'])
def update_application():
    try:
        token = request.headers['Authorization']
        agent_id = get_user_id(connection, token)
        user_id = request.json.get('user_id')
        unit_id = request.json.get('unit_id')
        status = request.json.get('status')
        success = True

        if check_agent_role(connection, agent_id):
            if status=="approved":
                query = (f"UPDATE applications set status='{status}' where user_id = {user_id} and unit_id = {unit_id};"
                        f"UPDATE unit set availability=false where unit_id={unit_id};")
                if not run_update_query(connection, query):
                    success = False
                    return jsonify({'success': success}), 409

            elif status=="rejected":
                query = f"UPDATE applications set status='{status}' where user_id = {user_id} and unit_id = {unit_id};"
                if not run_update_query(connection, query):
                    success = False
                    return jsonify({'success': success}), 409   
        else:
            success = False
            return jsonify({'success': success}), 409 

        results = {'success': success}
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sign_up', methods=['POST'])
def sign_up():
    try:
        data = request.json
        email_id = data['email_id']
        password_hash = hashlib.md5(data['password'].encode()).hexdigest()
        role_type = 'Customer'
        first_name = data['first_name']
        last_name = data['last_name']
        phone_number = data['phone_number']
        gender = data['gender']
        dob = data['date_of_birth']

        #checking if email is not present already
        if verify_unique_email(connection, email_id):
            query = (f"insert into user (email_id, password_hash, role_type, first_name, last_name, phone_number, gender, date_of_birth) "
                    f"VALUES ('{email_id}', '{password_hash}', '{role_type}', '{first_name}', '{last_name}', '{phone_number}', '{gender}', '{dob}');")
            if not run_update_query(connection, query):
                return jsonify({'success': False, 'message': "Failed to sign up"}), 409
        else:
            return jsonify({'success': False, 'message': "Email Id is already in use!"}), 409

        results = {'success': True, 'message':'Sign Up Successful'}
        return jsonify(results)

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/property_ratings_by_area', methods=['GET'])
def property_ratings_by_area():
    try:
        query_params = request.args
        min_area = query_params['min_area']
        max_area = query_params['max_area']

        query = (f"SELECT review.property_id, "
                f"prop.name, "
                f"prop.pincode, "
                f"AVG(review.rating) AS avg_rating, "
                f"COUNT(review.rating) AS num_reviews "
                f"FROM reviews review "
                f"JOIN property prop ON prop.property_id = review.property_id "
                f"WHERE review.property_id IN ( "
                f"SELECT DISTINCT p.property_id "
                f"FROM property p "
                f"JOIN unit u ON p.property_id = u.property_id "
                f"WHERE u.availability = 1 AND u.area >= {min_area} AND u.area <= {max_area} "
                f") "
                f"GROUP BY review.property_id "
                f"HAVING num_reviews >= 2;")
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                'property_id': row[0],
                'name': row[1],
                'pincode': row[2],
                'avg_rating': row[3],
                'num_reviews': row[4]
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/popular_properties', methods=['GET'])
def popular_properties():
    try:
        query_params = request.args
        bathrooms = query_params['bathrooms']
        bedrooms = query_params['bedrooms']

        query = (f"SELECT q1.property_id, q1.num_applications / q2.num_units AS popularity_ratio "
                f"FROM (SELECT p.property_id, COUNT(a.unit_id) AS num_applications "
                f"FROM property p "
                f"LEFT JOIN unit u ON p.property_id = u.property_id "
                f"LEFT JOIN applications a ON u.unit_id = a.unit_id "
                f"WHERE p.property_id IN (SELECT DISTINCT property.property_id "
                f"FROM property "
                f"JOIN unit ON property.property_id = unit.property_id "
                f"WHERE unit.availability = TRUE AND unit.bedrooms > {bedrooms} AND unit.bathrooms > {bathrooms}) "
                f"GROUP BY p.property_id) AS q1 "
                f"INNER JOIN "
                f"(SELECT p.property_id, COUNT(u.unit_id) AS num_units "
                f"FROM property p "
                f"LEFT JOIN unit u ON p.property_id = u.property_id "
                f"WHERE p.property_id IN (SELECT DISTINCT property.property_id "
                f"FROM property "
                f"JOIN unit ON property.property_id = unit.property_id "
                f"WHERE unit.availability = TRUE AND unit.bedrooms > {bedrooms} AND unit.bathrooms > {bathrooms}) "
                f"GROUP BY p.property_id) AS q2 "
                f"ON q1.property_id = q2.property_id "
                f"HAVING popularity_ratio > 0; ")
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                'property_id': row[0],
                'popularity_ratio': row[1]
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/apps_per_user', methods=['GET'])
def apps_per_user():
    try:
        query = "SELECT email_id,phone_number, count(*) AS Application_Count FROM user u NATURAL JOIN userdetails ud GROUP BY phone_number,email_id;"
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                'email_id': row[0],
                'phone_number': row[1],
                'Application_Count': row[2]
            })
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/min_max_rent', methods=['GET'])
def min_max_rent():
    try:
        query = (f"SELECT p.pincode, "
                f"MIN(u.price) AS Min_Rent, "
                f"MAX(u.price) AS Max_Rent, "
                f"ROUND(AVG(u.price)) AS Avg_Rent, "
                f"MIN(u.area) AS Min_Area, "
                f"MAX(u.area) AS Max_Area, "
                f"ROUND(AVG(u.area)) AS Avg_Area "
                f"FROM property p "
                f"NATURAL JOIN unit u "
                f"GROUP BY p.pincode;")
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                    'pincode': row[0],
                    'min_rent': row[1],
                    'max_rent': row[2],
                    'avg_rent': row[3],
                    'min_area': row[4],
                    'max_area': row[5],
                    'avg_area': row[6]
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/get_unit_app_count', methods=['GET'])
def get_unit_app_count():
    try:
        headers = request.headers
        token = headers['Authorization']
        user_id = get_user_id(connection, token)
        if not check_agent_role(connection, user_id):
            return jsonify({'error': "User is not an Agent"}), 403
        query_params = request.args
        company_id = query_params['company_id']
        
        query = (f"SELECT u.apartment_no, "
                f"p.name, "
                f"COUNT(*) "
                f"FROM unit u "
                f"JOIN property p ON p.property_id = u.property_id "
                f"JOIN applications app ON app.unit_id = u.unit_id "
                f"WHERE p.company_id = {company_id} "
                f"GROUP BY u.unit_id;")
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                    'apartment_num': row[0],
                    'property_name': row[1],
                    'num_applications': row[2]
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/get_units_for_agent', methods=['GET'])
def get_units_for_agent():
    """This API is used to get the units that are to be managed by an agent.
    
    Args:
        No Arguments
    
    Returns:
        JSON: A JSON object containing the details of the units that are to be managed by the agent.
        {
            "data": [
                {
                    "apartment_no": 100,
                    "area": 418,
                    "availability": 1,
                    "bathrooms": 0.5,
                    "bedrooms": 1,
                    "company_id": 36,
                    "pincode": 61854,
                    "price": 800.0,
                    "property_name": "Allen Oasis",
                    "unit_id": 2
                }
            ]
        }
    """
    try:
        headers = request.headers
        token = headers['Authorization']
        user_id = get_user_id(connection, token)
        if(not check_agent_role(connection, user_id)):
            return jsonify({'success': False, 'error': "User is not an Agent"}), 409
        query = (
                f"SELECT u.unit_id, "
                f"u.apartment_no, "
                f"u.bedrooms, "
                f"u.bathrooms, "
                f"u.price, "
                f"u.availability, "
                f"u.area, "
                f"p.name, "
                f"p.pincode, "
                f"p.company_id "
                f"FROM unit u "
                f"JOIN property p ON p.property_id = u.property_id "
                f"JOIN agentcompanyrelationship acr ON acr.company_id = p.company_id "
                f"WHERE acr.user_id = {user_id};"
            )
        rows = run_query(connection, query)

        results = []
        for row in rows:
            results.append({
                    'unit_id': row[0],
                    'apartment_no': row[1],
                    'bedrooms': row[2],
                    'bathrooms': row[3],
                    'price': row[4],
                    'availability': row[5],
                    'area': row[6],
                    'property_name': row[7],
                    'pincode': row[8],
                    'company_id': row[9],
                })
        return jsonify({"data": results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submit_application', methods=['POST'])
def submit_application():
    try:
        headers = request.headers
        token = headers['Authorization']
        user_id = get_user_id(connection, token)
        if check_agent_role(connection, user_id):
            return jsonify({'error': "User is an Agent"}), 403

        data = request.json
        unit_id = data.get('unit_id')
        created_at = datetime.now().strftime('%Y-%m-%d')
        success = True

        query = (f"INSERT INTO applications (unit_id, user_id, created_at, status) "
                f"VALUES ({unit_id}, {user_id}, '{created_at}', 'pending');")
        if not run_update_query(connection, query):
            success = False
            return jsonify({'success': success}), 409
        result = {'success': success}
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_properties', methods=['GET'])
def list_properties():
    try:
        query = ("select p.property_id, p.name, c.name, p.address, p.pincode from property p JOIN company c ON p.company_id = c.company_id;")
        rows = run_query(connection, query)

        query2 = ("select * from propertyphoto;")
        rows2 = run_query(connection, query2)

        results = []
        for row in rows:
            results.append({
                    'property_id': row[0],
                    'property_name': row[1],
                    'company_name': row[2],
                    'address': row[3],
                    'pincode': row[4],
                    'photos':[row2[1] for row2 in rows2 if row2[0]==row[0]]
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=(ENV == 'dev'), port=PORT)
