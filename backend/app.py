
from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
from werkzeug.security import generate_password_hash
from mysql.connector import IntegrityError
from db import get_db_connection

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "RescueBite AI backend is running"
    })


@app.post("/api/restaurants/register")
def register_restaurant():
    data = request.get_json(silent=True) or {}

    restaurant_name = data.get("restaurantName", "").strip()
    owner_name = data.get("ownerName", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    cuisine = data.get("cuisine", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirmPassword", "")
    terms = data.get("terms")

    if not all([
        restaurant_name, owner_name, email,
        phone, address, city, password
    ]):
        return jsonify({"error": "Please fill in all required fields."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must contain at least 8 characters."}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    if terms is not True:
        return jsonify({"error": "Please accept the terms and conditions."}), 400

    password_hash = generate_password_hash(password)

    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO restaurants
            (restaurant_name, owner_name, email, phone,
             address, city, cuisine, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            restaurant_name, owner_name, email, phone,
            address, city, cuisine or None, password_hash
        )

        cursor.execute(query, values)
        connection.commit()

        return jsonify({
            "message": "Restaurant account created successfully!",
            "restaurant_id": cursor.lastrowid
        }), 201

    except IntegrityError:
        connection.rollback()
        return jsonify({"error": "This email or registration detail is already registered."}), 409

    except Exception:
        connection.rollback()
        app.logger.exception("Restaurant registration failed")
        return jsonify({"error": "Registration failed. Please try again."}), 500

    finally:
        if cursor:
            cursor.close()
        connection.close()


@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<page>")
def frontend_page(page):
    if not page.endswith(".html"):
        return jsonify({"error": "Page not found"}), 404
    return send_from_directory(FRONTEND_DIR, page)


if __name__ == "__main__":
    app.run(debug=True)
