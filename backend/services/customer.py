from flask import Blueprint, jsonify, request
from utils import *
from db import connection, connect_to_database
from datetime import datetime


customer_service = Blueprint('customer_service', __name__, url_prefix='/customer')

@customer_service.route('/min_max_rent', methods=['GET'])
def min_max_rent():
    try:
        conn = connect_to_database()
        conn.start_transaction('SERIALIZABLE')
        if conn:
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
                rows = run_query(conn, query)

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
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/submit_application', methods=['POST'])
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

        conn = connect_to_database()
        conn.start_transaction('SERIALIZABLE')
        
        if conn:
            try:
                query = (f"INSERT INTO applications (unit_id, user_id, created_at, status) "
                         f"VALUES ({unit_id}, {user_id}, '{created_at}', 'pending');")
                if not run_update_query(conn, query):
                    success = False
                    return jsonify({'success': success}), 409
                result = {'success': success}
                return jsonify(result)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    try:
        headers = request.headers
        token = headers['Authorization']
        user_id = get_user_id(connection, token)
        if check_agent_role(connection, user_id):
            return jsonify({'error': "User is an Agent"}), 403

        data = request.json

        conn = connect_to_database()
        if conn:
            try:
                for i,(key,val) in enumerate(data.items()):
                    if val != '-':
                        query = (f"INSERT INTO userdetails (user_id, pref_id, value) "
                                 f"VALUES ({user_id}, {i+2}, '{val}');")
                        run_update_query(conn, query)

                result = {'success': True}
                return jsonify(result)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/list_properties', methods=['GET'])
def list_properties():
    try:
        data = request.args
        bedrooms = sanitize_input(data.get('bedrooms'))
        bathrooms = sanitize_input(data.get('bathrooms'))
        pricemin = sanitize_input(data.get('pricemin'))
        pricemax = sanitize_input(data.get('pricemax'))
        areamin = sanitize_input(data.get('areamin', ))
        areamax = sanitize_input(data.get('areamax'))
        pincode = sanitize_input(data.get('pincode'))
        propertyName = sanitize_input(data.get('propertyName'))
        companyName = sanitize_input(data.get('companyName'))

        conn = connect_to_database()
        conn.start_transaction('SERIALIZABLE')
        if conn:
            try:
                query = ("select distinct p.property_id, p.name, c.name, p.address, p.pincode from property p JOIN company c ON p.company_id = c.company_id JOIN unit u ON u.property_id = p.property_id")
                whereParts = []
                if bedrooms:
                    whereParts.append(f"u.bedrooms={bedrooms}")
                if bathrooms:
                    whereParts.append(f"u.bathrooms={bathrooms}")
                if areamin:
                    whereParts.append(f"u.area>={areamin}")
                if areamax:
                    whereParts.append(f"u.area>={areamax}")
                if pricemin:
                    whereParts.append(f"u.price>={pricemin}")
                if pricemax:
                    whereParts.append(f"u.price<={pricemax}")
                if pincode:
                    whereParts.append(f"p.pincode={pincode}")
                if propertyName:
                    whereParts.append(f"p.name LIKE '%{propertyName}%'")
                if companyName:
                    whereParts.append(f"c.name LIKE '%{companyName}%'")
                if len(whereParts) > 0:
                    query += " WHERE "
                    query += " and ".join(whereParts)
                query += ' order by p.name;'
                rows = run_query(conn, query)

                query2 = ("select * from propertyphoto;")
                rows2 = run_query(conn, query2)

                results = []
                for row in rows:
                    results.append({
                        'property_id': row[0],
                        'property_name': row[1],
                        'company_name': row[2],
                        'address': row[3],
                        'pincode': row[4],
                        'photos': [row2[1] for row2 in rows2 if row2[0] == row[0]]
                    })
                return jsonify(results)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@customer_service.route('/get_property_from_id', methods=['GET'])
def get_property_from_id():
    try:
        property_id = request.args.get('property_id')

        conn = connect_to_database()
        if conn:
            try:
                query = f"SELECT p.name, p.address, p.latitude, p.longitude, c.name, p.pincode FROM property as p join company as c on p.company_id=c.company_id where p.property_id = {property_id};"
                rows = run_query(conn, query)

                query2 = (f"select * from propertyphoto where property_id = {property_id};")
                rows2 = run_query(conn, query2)

                query3 = f"SELECT u.first_name, u.last_name, r.created_at, r.comment, r.rating, r.user_id FROM reviews as r join user as u on r.user_id=u.user_id where r.property_id = {property_id};"
                rows3 = run_query(conn, query3)

                query4 = f"SELECT unit_id, apartment_no from unit where property_id={property_id};"
                rows4 = run_query(conn, query4)

                reviews = []
                avgRating = 0
                if len(rows3) > 0:
                    for row in rows3:
                        avgRating += int(row[4])
                        reviews.append({
                            'user_name': row[0] + ' ' + row[1],
                            'created_at': row[2],
                            'comment': row[3],
                            'rating': row[4],
                            'user_id': row[5]
                        })
                    avgRating /= len(reviews)

                units = []
                for row in rows4:
                    units.append({
                        'unit_id': row[0],
                        'apartment_no': row[1]
                    })

                results = []
                for row in rows:
                    results.append({
                        'name': row[0],
                        'address': row[1],
                        'latitude': row[2],
                        'longitude': row[3],
                        'company_name': row[4],
                        'pincode': row[5],
                        'photos': [row2[1] for row2 in rows2],
                        'avgRating': avgRating,
                        'reviews': reviews,
                        'units': units
                    })
                return jsonify(results[0])
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/my_applications', methods=['GET'])
def my_applications():
    try:
        token = request.headers['Authorization']

        conn = connect_to_database()
        conn.start_transaction('SERIALIZABLE')
        user_id = get_user_id(conn, token)
        if conn:
            try:
                query = (f"SELECT u.apartment_no, p.name, u.price, a.status, u.unit_id, u.property_id "
                         f"FROM applications a "
                         f"JOIN unit u ON u.unit_id = a.unit_id "
                         f"JOIN property p ON p.property_id = u.property_id "
                         f"WHERE a.user_id = {user_id}; ")
                rows = run_query(conn, query)

                results = []
                for row in rows:
                    results.append({
                        'apartment_no': row[0],
                        'property_name': row[1],
                        'price': row[2],
                        'status': row[3],
                        'unit_id': row[4],
                        'property_id': row[5]
                    })
                return jsonify(results)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/check_application_status', methods=['GET'])
def check_application_status():
    try:
        token = request.headers['Authorization']
        user_id = get_user_id(connection, token)
        unit_id = request.args['unit_id']
       
        conn = connect_to_database()
        if conn:
            try:
                query = (f"SELECT a.status "
                         f"FROM applications a "
                         f"WHERE a.user_id = {user_id} and a.unit_id = {unit_id}; ")
                rows = run_query(conn, query)
                if not rows[0][0]:
                    results = {"status": "None"}
                else:
                    results = {"status": rows[0][0]}
                return jsonify(results)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/get_roommates', methods=['GET'])
def get_roommates():
    try:
        token = request.headers['Authorization']
        user_id = get_user_id(connection, token)

        conn = connect_to_database()
        if conn:
            try:
                query = (
                    f"SELECT u.user_id,u.first_name,u.last_name,u.email_id,JSON_ARRAYAGG(JSON_OBJECT('pref_id', ud.pref_id,'value', ud.value)) AS prefs,"
                    f"((SELECT COUNT(*) FROM userdetails ud WHERE ud.user_id = u.user_id AND "
                    f"LOWER(ud.value) IN (SELECT LOWER(value) FROM userdetails WHERE user_id = {user_id} AND ud.pref_id = pref_id)) / "
                    f"(SELECT COUNT(*) FROM userdetails WHERE user_id = {user_id})) AS similarity_score "
                    f"FROM user u JOIN userdetails ud ON u.user_id = ud.user_id WHERE u.user_id != {user_id} GROUP BY u.user_id "
                    f"ORDER BY similarity_score DESC;")
                rows = run_query(conn, query)
                results = []
                for row in rows:
                    results.append({
                        'user_id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'email_id': row[3],
                        'prefs': json.loads(row[4]),
                        'similarity_ratio': row[5]
                    })
                query = (f"SELECT * from preferences")
                rows = run_query(conn, query)
                preferences = {}
                for row in rows:
                    preferences[row[0]] = row[1]

                query = (f"SELECT pref_id, value from userdetails where user_id = {user_id}")
                rows = run_query(conn, query)
                current_user_preferences = []
                for row in rows:
                    current_user_preferences.append({
                        'pref_id': row[0],
                        'value': row[1]
                    })
               
                return jsonify({
                    'preferences': preferences,
                    'roommates': results,
                    'current_user_preferences': current_user_preferences
                })
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/add_review', methods=['POST'])
def add_review():
    try:
        headers = request.headers
        token = headers['Authorization']
        conn = connect_to_database()

        data = request.json
        property_id = data.get('property_id')
        comment = data.get('comment')
        rating = data.get('rating')
        created_at = datetime.now().strftime('%Y-%m-%d')
        success = True

        
        if conn and conn.is_connected():
            conn.start_transaction('SERIALIZABLE')

            user_id = get_user_id(conn, token)
            if check_agent_role(conn, user_id):
                return jsonify({'error': "User is an Agent"}), 403
            try:
                query = (f"INSERT INTO reviews (user_id, property_id, created_at, comment, rating) "
                         f"VALUES ({user_id}, {property_id}, '{created_at}', '{comment}', '{rating}');")
                if not run_update_query(conn, query):
                    success = False
                    file1 = open('./backend/error.txt', 'r')
                    error = file1.read()
                    return jsonify({'success': success, 'error': error}), 409
                result = {'success': success}
                return jsonify(result)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_service.route('/advanced_properties_filter', methods=['GET'])
def advanced_properties_filter():
    try:
        token = request.headers['Authorization']
        user_id = get_user_id(connection, token)
        if check_agent_role(connection, user_id):
            return jsonify({'error': "User is an Agent"}), 403
        data = request.args
        flag = sanitize_input(data.get('flag'))
        pricemin = sanitize_input(data.get('pricemin'))
        pricemax = sanitize_input(data.get('pricemax'))
        areamin = sanitize_input(data.get('areamin'))
        areamax = sanitize_input(data.get('areamax'))
        conn = connect_to_database()
        if conn:
            cursor = conn.cursor()
            if(cursor):
                try:
                    cursor.callproc('complex_stored_procedure_for_filtering', [flag, areamin, areamax, pricemin, pricemax])
                    results = []
                    for result in cursor.stored_results():

                        results.append(result.fetchall())
                    sub = results[0]                    
                    final_result_pro_max = []
                    for i in sub:
                        final_result_pro_max.append(
                            i[0]
                        )
                    return jsonify({'data': final_result_pro_max})
                finally:
                    conn.close()
            else:
                return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@customer_service.route('/delete_review',methods=['POST'])
def delete_review():
    try:
        headers = request.headers
        token = headers['Authorization']
        user_id = get_user_id(connection, token)
        if check_agent_role(connection, user_id):
            return jsonify({'error': "User is an Agent"}), 403

        data = request.json
        user_id = data.get('user_id')
        property_id = data.get('property_id')

        success = True

        conn = connect_to_database()
        if conn:
            try:
                query = (f"DELETE FROM reviews WHERE user_id = {user_id} AND property_id = {property_id};")
                if not run_update_query(conn, query):
                    success = False
                    return jsonify({'success': success}), 409
                result = {'success': success}
                return jsonify(result)
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Failed to establish database connection.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
