from flask import Blueprint, jsonify, request
from utils import *
from db import connection

analytics_service = Blueprint('analytics_service', __name__, url_prefix='/analytics')


@analytics_service.route('/property_ratings_by_area', methods=['GET'])
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

@analytics_service.route('/similarity_ratio', methods=['GET'])
def similarity_ratio():
    try:
        token = request.headers['Authorization']
        user_id = get_user_id(connection, token)
        query = (f"SELECT u.user_id,u.first_name,u.last_name,((SELECT COUNT(*) FROM userdetails ud WHERE ud.user_id = u.user_id AND "
                f"ud.value IN (SELECT value FROM userdetails WHERE user_id = {user_id} AND ud.pref_id = pref_id)) / "
                    f"(SELECT COUNT(*) FROM userdetails WHERE user_id = {user_id})) AS similarity_score "
            f"FROM user u JOIN userdetails ud ON u.user_id = ud.user_id WHERE u.user_id != {user_id} GROUP BY u.user_id "
            f"ORDER BY similarity_score DESC;")
        rows = run_query(connection, query)
        results = []
        for row in rows:
            results.append({
                'user_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'similarity_ratio': row[3]
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_service.route('/popular_properties', methods=['GET'])
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
    
@analytics_service.route('/apps_per_user', methods=['GET'])
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