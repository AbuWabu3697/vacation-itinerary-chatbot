from flask import Flask, request, jsonify, send_from_directory
import os

from flight_api import search_flights, init_flight_results_file
from amadeus_api import AmadeusAPI

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

@app.post("/api/generate-itinerary")
def generate_itinerary_route():
    body = request.get_json(force=True)
    
    # Extract the data from the request
    destination = body.get('destination')
    dates = body.get('dates')
    budget = body.get('budget')
    adults = body.get('adults', 1)
    room_quantity = body.get('room_quantity', 1)
    transport = body.get('transport')
    interests = body.get('interests', [])
    user_message = body.get('message', '')
    
    # TODO: Add your itinerary generation logic here
    # This could call an AI API, use your existing functions, etc.
    amadeus = AmadeusAPI(os.getenv("AMADEUS_CLIENT_ID"), os.getenv("AMADEUS_CLIENT_SECRET"))

    # ==============================================
    # FLIGHTS
    # ==============================================

    flights = search_flights(body)

    # ==============================================
    # HOTELS
    # ==============================================

    city_code = amadeus.get_city_code(destination)
    hotels = amadeus.search_hotels(city_code)
    hotel_ids = [hotel["hotelId"] for hotel in hotels]
    filtered_hotels = amadeus.filter_hotels(hotel_ids, dates[0], dates[1], adults, room_quantity, budget)

    # ==============================================
    # EXPERIENCES
    # ==============================================

    city_coordinates = amadeus.get_city_coordinates(destination)
    experiences = amadeus.find_activities(city_coordinates["latitude"]+0.25, city_coordinates["latitude"]-0.25, city_coordinates["longitude"]+0.25, city_coordinates["longitude"]-0.25, interests)


    # ==============================================
    # GROK
    # ==============================================

    

    
    itinerary = {
        "message": f"Great! I'm planning a trip to {destination} from {dates} with a {budget} budget.",
        "itinerary": [
            # Your generated itinerary data here
        ]
    }
    
    return jsonify(itinerary), 200


if __name__ == "__main__":
    app.run(debug=True)
