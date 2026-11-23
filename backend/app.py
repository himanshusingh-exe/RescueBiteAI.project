from flask import session
from werkzeug.security import check_password_hash
import os




from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
from werkzeug.security import generate_password_hash
from mysql.connector import IntegrityError
from db import get_db_connection

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "rescuebite-development-key-change-before-deployment"
)

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



@app.post("/api/restaurants/login")
def restaurant_login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, restaurant_name, password_hash
            FROM restaurants
            WHERE email = %s
            """,
            (email,)
        )

        restaurant = cursor.fetchone()

        if not restaurant or not check_password_hash(
            restaurant[2], password
        ):
            return jsonify({
                "error": "Invalid email or password."
            }), 401

        session["restaurant_id"] = restaurant[0]
        session["restaurant_name"] = restaurant[1]
        session.permanent = bool(data.get("remember"))

        return jsonify({
            "message": "Login successful!",
            "restaurant_id": restaurant[0],
            "restaurant_name": restaurant[1]
        }), 200

    except Exception:
        app.logger.exception("Restaurant login failed")
        return jsonify({"error": "Login failed. Please try again."}), 500

    finally:
        if cursor:
            cursor.close()
        connection.close()

@app.get("/api/admin/restaurants")
def get_restaurants():
    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                restaurant_name,
                owner_name,
                email,
                phone,
                city,
                cuisine,
                created_at
            FROM restaurants
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()

        restaurants = []

        for row in rows:
            restaurants.append({
                "id": row["id"],
                "name": row["restaurant_name"],
                "cuisine": row["cuisine"] or "Not specified",
                "city": row["city"] or "Not specified",
                "email": row["email"],
                "phone": row["phone"] or "Not provided",
                "donations": 0,
                "meals": 0,
                "rating": 0,
                "status": "pending",
                "verified": False,
                "joined": row["created_at"].strftime("%Y-%m-%d")
                    if row["created_at"] else ""
            })

        return jsonify({"restaurants": restaurants}), 200

    except Exception:
        app.logger.exception("Could not fetch restaurants")
        return jsonify({"error": "Could not load restaurants."}), 500

    finally:
        if cursor:
            cursor.close()
        connection.close()


@app.get("/api/restaurants/me")
def get_logged_in_restaurant():
    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({"error": "Please log in first."}), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, restaurant_name FROM restaurants WHERE id = %s",
            (restaurant_id,)
        )

        restaurant = cursor.fetchone()

        if not restaurant:
            session.clear()
            return jsonify({"error": "Restaurant account not found."}), 404

        return jsonify({"restaurant": restaurant}), 200

    except Exception:
        app.logger.exception("Could not fetch logged-in restaurant")
        return jsonify({"error": "Could not fetch restaurant."}), 500

    finally:
        if cursor:
            cursor.close()
        connection.close()


@app.get("/api/donations")
def get_donations():
    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({"error": "Please log in first."}), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                food_name,
                quantity,
                storage_method,
                packaging_type,
                notes,
                status,
                created_at
            FROM food_donations
            WHERE restaurant_id = %s
            ORDER BY created_at DESC
        """, (restaurant_id,))

        donations = cursor.fetchall()

        return jsonify({"donations": donations}), 200

    except Exception:
        app.logger.exception("Could not fetch donation history")
        return jsonify({"error": "Could not fetch donations."}), 500

    finally:
        if cursor:
            cursor.close()
        connection.close()        


@app.post("/api/donations")
def create_donation():
    data = request.get_json(silent=True) or {}

    restaurant_id = session.get("restaurant_id")
    if not restaurant_id:
        return jsonify({"error": "Please log in before submitting a donation."}), 401
    food_name = data.get("food_name", "").strip()
    quantity = data.get("quantity", "").strip()
    storage_method = data.get("storage_method", "")
    packaging_type = data.get("packaging_type", "")
    notes = data.get("notes", "")

    if not restaurant_id or not food_name or not quantity:
        return jsonify({"error": "Please fill in all required fields."}), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({"error": "Database connection failed."}), 500

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO food_donations
            (restaurant_id, food_name, quantity, storage_method,
             packaging_type, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'available')
        """, (
            restaurant_id,
            food_name,
            quantity,
            storage_method,
            packaging_type,
            notes
        ))

        connection.commit()

        return jsonify({
            "message": "Food donation saved successfully!",
            "donation_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        app.logger.exception("Donation submission failed")
        return jsonify({"error": "Could not save donation."}), 500

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
