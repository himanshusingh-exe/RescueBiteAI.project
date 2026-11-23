
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="RescueBite2026",
            database="rescuebite_db"
        )
        return connection

    except Error as error:
        print("Database connection error:", error)
        return None
