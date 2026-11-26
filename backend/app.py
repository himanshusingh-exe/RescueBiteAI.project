
import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    session
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename
from mysql.connector import IntegrityError

from db import get_db_connection


# =====================================================
# PROJECT CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "rescuebite-development-key-change-before-deployment"
)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "RescueBite AI backend is running"
    })


# =====================================================
# RESTAURANT REGISTRATION
# =====================================================

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
        restaurant_name,
        owner_name,
        email,
        phone,
        address,
        city,
        password
    ]):
        return jsonify({
            "error": "Please fill in all required fields."
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters."
        }), 400

    if password != confirm_password:
        return jsonify({
            "error": "Passwords do not match."
        }), 400

    if terms is not True:
        return jsonify({
            "error": "Please accept the terms and conditions."
        }), 400

    password_hash = generate_password_hash(password)

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO restaurants
            (
                restaurant_name,
                owner_name,
                email,
                phone,
                address,
                city,
                cuisine,
                password_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            restaurant_name,
            owner_name,
            email,
            phone,
            address,
            city,
            cuisine or None,
            password_hash
        )

        cursor.execute(query, values)
        connection.commit()

        return jsonify({
            "message": "Restaurant account created successfully!",
            "restaurant_id": cursor.lastrowid
        }), 201

    except IntegrityError:
        connection.rollback()

        return jsonify({
            "error": "This email or registration detail is already registered."
        }), 409

    except Exception:
        connection.rollback()
        app.logger.exception("Restaurant registration failed")

        return jsonify({
            "error": "Registration failed. Please try again."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# RESTAURANT LOGIN
# =====================================================

@app.post("/api/restaurants/login")
def restaurant_login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required."
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

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

        return jsonify({
            "error": "Login failed. Please try again."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# NGO REGISTRATION
# =====================================================

@app.post("/api/ngos/register")
def register_ngo():

    data = request.get_json(silent=True) or {}

    ngo_name = data.get("ngoName", "").strip()
    registration_number = data.get("regNumber", "").strip()
    contact_person = data.get("contactPerson", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirmPassword", "")

    if not all([ngo_name, registration_number, email, password]):
        return jsonify({
            "error": "Please fill in all required fields."
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters."
        }), 400

    if password != confirm_password:
        return jsonify({
            "error": "Passwords do not match."
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO ngos (
                ngo_name,
                registration_number,
                contact_person,
                email,
                phone,
                address,
                password_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ngo_name,
                registration_number,
                contact_person or None,
                email,
                phone or None,
                address or None,
                password_hash
            )
        )

        connection.commit()

        return jsonify({
            "message": "NGO registered successfully!"
        }), 201

    except IntegrityError:
        connection.rollback()

        return jsonify({
            "error": "This email or registration number is already registered."
        }), 409

    except Exception:
        connection.rollback()
        app.logger.exception("NGO registration failed")

        return jsonify({
            "error": "Registration failed. Please try again."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# NGO LOGIN
# =====================================================

@app.post("/api/ngos/login")
def ngo_login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required."
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, ngo_name, password_hash
            FROM ngos
            WHERE email = %s
            """,
            (email,)
        )

        ngo = cursor.fetchone()

        if not ngo or not check_password_hash(
            ngo[2], password
        ):
            return jsonify({
                "error": "Invalid email or password."
            }), 401

        session["ngo_id"] = ngo[0]
        session["ngo_name"] = ngo[1]

        session.permanent = bool(data.get("remember"))

        return jsonify({
            "message": "Login successful!",
            "ngo_id": ngo[0],
            "ngo_name": ngo[1]
        }), 200

    except Exception:
        app.logger.exception("NGO login failed")

        return jsonify({
            "error": "Login failed. Please try again."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# LOGGED-IN NGO DETAILS
# =====================================================

@app.get("/api/ngos/me")
def get_logged_in_ngo():

    ngo_id = session.get("ngo_id")

    if not ngo_id:
        return jsonify({
            "error": "Please log in first."
        }), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                ngo_name,
                registration_number,
                contact_person,
                email,
                phone,
                address,
                created_at
            FROM ngos
            WHERE id = %s
            """,
            (ngo_id,)
        )

        ngo = cursor.fetchone()

        if not ngo:
            session.pop("ngo_id", None)
            session.pop("ngo_name", None)

            return jsonify({
                "error": "NGO account not found."
            }), 404

        if ngo["created_at"]:
            ngo["created_at"] = ngo["created_at"].strftime("%Y-%m-%d")

        return jsonify({
            "ngo": ngo
        }), 200

    except Exception:
        app.logger.exception("Could not fetch NGO details")

        return jsonify({
            "error": "Could not load NGO details."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()

# =====================================================
# ADMIN - GET RESTAURANTS
# =====================================================

@app.get("/api/admin/restaurants")
def get_restaurants():

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

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
                "joined": (
                    row["created_at"].strftime("%Y-%m-%d")
                    if row["created_at"] else ""
                )
            })

        return jsonify({
            "restaurants": restaurants
        }), 200

    except Exception:
        app.logger.exception("Could not fetch restaurants")

        return jsonify({
            "error": "Could not load restaurants."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# LOGGED-IN RESTAURANT DETAILS
# =====================================================

@app.get("/api/restaurants/me")
def get_logged_in_restaurant():

    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({
            "error": "Please log in first."
        }), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, restaurant_name
            FROM restaurants
            WHERE id = %s
            """,
            (restaurant_id,)
        )

        restaurant = cursor.fetchone()

        if not restaurant:
            session.clear()

            return jsonify({
                "error": "Restaurant account not found."
            }), 404

        return jsonify({
            "restaurant": restaurant
        }), 200

    except Exception:
        app.logger.exception(
            "Could not fetch logged-in restaurant"
        )

        return jsonify({
            "error": "Could not fetch restaurant."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# GET DONATION HISTORY
# =====================================================

@app.get("/api/donations")
def get_donations():

    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({
            "error": "Please log in first."
        }), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

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

        return jsonify({
            "donations": donations
        }), 200

    except Exception:
        app.logger.exception(
            "Could not fetch donation history"
        )

        return jsonify({
            "error": "Could not fetch donations."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# CREATE FOOD DONATION
# =====================================================

@app.post("/api/donations")
def create_donation():

    data = request.get_json(silent=True) or {}

    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({
            "error": "Please log in before submitting a donation."
        }), 401

    food_name = data.get("food_name", "").strip()
    quantity = data.get("quantity", "").strip()

    storage_method = data.get("storage_method", "")
    packaging_type = data.get("packaging_type", "")
    notes = data.get("notes", "")

    if not food_name or not quantity:
        return jsonify({
            "error": "Please fill in all required fields."
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO food_donations
            (
                restaurant_id,
                food_name,
                quantity,
                storage_method,
                packaging_type,
                notes,
                status
            )
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

        return jsonify({
            "error": "Could not save donation."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()


# =====================================================
# RESTAURANT - SEND DONATION REQUEST TO NGO
# =====================================================

@app.post("/api/donation-requests")
def create_donation_request():

    data = request.get_json(silent=True) or {}

    restaurant_id = session.get("restaurant_id")

    if not restaurant_id:
        return jsonify({
            "error": "Please log in as a restaurant first."
        }), 401

    donation_id = data.get("donation_id")
    ngo_id = data.get("ngo_id")

    if not donation_id or not ngo_id:
        return jsonify({
            "error": "Donation ID and NGO ID are required."
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Verify donation belongs to this restaurant.
        cursor.execute("""
            SELECT id, status
            FROM food_donations
            WHERE id = %s AND restaurant_id = %s
        """, (donation_id, restaurant_id))

        donation = cursor.fetchone()

        if not donation:
            return jsonify({
                "error": "Donation not found."
            }), 404

        if str(donation["status"]).lower() != "available":
            return jsonify({
                "error": "This donation is not available."
            }), 400

        # Verify NGO exists.
        cursor.execute("""
            SELECT id
            FROM ngos
            WHERE id = %s
        """, (ngo_id,))

        ngo = cursor.fetchone()

        if not ngo:
            return jsonify({
                "error": "NGO not found."
            }), 404

        # Prevent duplicate requests.
        cursor.execute("""
            SELECT id
            FROM donation_requests
            WHERE donation_id = %s AND ngo_id = %s
        """, (donation_id, ngo_id))

        existing_request = cursor.fetchone()

        if existing_request:
            return jsonify({
                "error": "A request already exists for this NGO and donation."
            }), 409

        cursor.execute("""
            INSERT INTO donation_requests
            (donation_id, ngo_id, status)
            VALUES (%s, %s, 'pending')
        """, (donation_id, ngo_id))

        connection.commit()

        return jsonify({
            "message": "Donation request sent successfully.",
            "request_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        app.logger.exception("Could not create donation request")

        return jsonify({
            "error": "Could not send donation request."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()

# =====================================================
# NGO - VIEW INCOMING DONATION REQUESTS
# =====================================================

@app.get("/api/ngos/requests")
def get_ngo_requests():

    ngo_id = session.get("ngo_id")

    if not ngo_id:
        return jsonify({
            "error": "Please log in as an NGO first."
        }), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                dr.id AS request_id,
                dr.donation_id,
                dr.status AS request_status,
                dr.requested_at,

                fd.food_name,
                fd.quantity,
                fd.storage_method,
                fd.packaging_type,
                fd.notes,
                fd.status AS donation_status,
                fd.created_at,

                r.id AS restaurant_id,
                r.restaurant_name,
                r.owner_name,
                r.email AS restaurant_email,
                r.phone AS restaurant_phone,
                r.address AS restaurant_address,
                r.city AS restaurant_city

            FROM donation_requests dr

            JOIN food_donations fd
                ON dr.donation_id = fd.id

            JOIN restaurants r
                ON fd.restaurant_id = r.id

            WHERE dr.ngo_id = %s

            ORDER BY dr.requested_at DESC
        """, (ngo_id,))

        requests_list = cursor.fetchall()

        for item in requests_list:
            if item["requested_at"]:
                item["requested_at"] = item["requested_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            if item["created_at"]:
                item["created_at"] = item["created_at"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        return jsonify({
            "requests": requests_list
        }), 200

    except Exception:
        app.logger.exception("Could not fetch NGO requests")

        return jsonify({
            "error": "Could not fetch donation requests."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()

# =====================================================
# GET REGISTERED NGOS FOR RESTAURANTS
# =====================================================

@app.get("/api/ngos/list")
def get_ngo_list():

    if not session.get("restaurant_id"):
        return jsonify({
            "error": "Please log in as a restaurant."
        }), 401

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, ngo_name, address
            FROM ngos
            ORDER BY ngo_name ASC
        """)

        ngos = cursor.fetchall()

        return jsonify({
            "success": True,
            "ngos": ngos
        }), 200

    except Exception as error:
        print("NGO list error:", error)

        return jsonify({
            "error": "Could not load registered NGOs."
        }), 500

    finally:
        if cursor:
            cursor.close()

        connection.close()

# =====================================================
# AI FOOD RECOGNITION API
# =====================================================

@app.post("/api/food/recognize")
def recognize_uploaded_food():

    if "image" not in request.files:
        return jsonify({
            "error": "Please upload a food image."
        }), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({
            "error": "No image selected."
        }), 400

    if not allowed_file(image.filename):
        return jsonify({
            "error": "Only JPG, JPEG, PNG and WEBP images are allowed."
        }), 400

    filename = secure_filename(image.filename)

    if not filename:
        return jsonify({
            "error": "Invalid filename."
        }), 400

    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    image_path = UPLOAD_FOLDER / unique_filename

    try:
        image.save(image_path)

        # Import the combined AI model
        from ai.combined_food_recognition import recognize_food

        # Run Indian and international food recognition
        result = recognize_food(str(image_path))

        if not result["success"]:
            return jsonify({
                "error": result.get(
                    "error",
                    "Food recognition failed."
                )
            }), 500

        return jsonify(result), 200

    except Exception:
        app.logger.exception(
            "Food recognition API failed"
        )

        return jsonify({
            "error": "Could not process the uploaded food image."
        }), 500

    finally:
        if image_path.exists():
            image_path.unlink(missing_ok=True)

# =====================================================
# RESTAURANT LOGOUT
# =====================================================

@app.post("/api/logout")
def restaurant_logout():
    session.clear()

    return jsonify({
        "message": "Logged out successfully."
    }), 200
# =====================================================
# FRONTEND ROUTES
# =====================================================

@app.get("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.get("/<page>")
def frontend_page(page):

    if not page.endswith(".html"):
        return jsonify({
            "error": "Page not found"
        }), 404

    return send_from_directory(
        FRONTEND_DIR,
        page
    )


# =====================================================
# RUN FLASK APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(debug=True)
