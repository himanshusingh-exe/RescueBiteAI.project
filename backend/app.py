from flask import Flask, jsonify, send_from_directory
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "RescueBite AI backend is running"
    })

@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/<page>")
def frontend_page(page):
    # Only serve HTML files from our frontend folder.
    if not page.endswith(".html"):
        return jsonify({"error": "Page not found"}), 404
    return send_from_directory(FRONTEND_DIR, page)

if __name__ == "__main__":
    app.run(debug=True)
