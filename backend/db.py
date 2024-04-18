import mysql.connector
from flask import current_app

connection = None
def connect_to_database(DB_CONFIG):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print("Error: ", err)
        return None