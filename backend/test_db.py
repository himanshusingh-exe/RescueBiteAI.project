
from db import get_db_connection

connection = get_db_connection()

if connection and connection.is_connected():
    print("SUCCESS: Connected to RescueBite AI database!")
    print("Database:", connection.database)
    connection.close()
else:
    print("FAILED: Could not connect to database.")
