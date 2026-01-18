from flask import Flask, request, jsonify, send_from_directory
import os

from flights import search_flights, init_flight_results_file

# Serve frontend files from repo root
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Clear/create flight_results.json at startup (same behavior as before)
init_flight_results_file()


# ---------------------------
# Frontend routes
# ---------------------------
@app.route("/")
def home():
    return send_from_directory(ROOT_DIR, "index.html")

@app.route("/main.js")
def serve_main_js():
    return send_from_directory(ROOT_DIR, "main.js")

@app.route("/style.css")
def serve_style_css():
    return send_from_directory(ROOT_DIR, "style.css")


# ---------------------------
# API routes
# ---------------------------
@app.post("/api/flights")
def flights_route():
    body = request.get_json(force=True)
    result = search_flights(body)

    # flights.py returns (payload, status_code)
    payload, status = result
    return jsonify(payload), status


if __name__ == "__main__":
    app.run(debug=True)
