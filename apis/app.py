from flask import Flask, request, jsonify, send_from_directory
import os
import json
from dotenv import load_dotenv, dotenv_values
from amadeus_api import AmadeusAPI


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
print("env_path:", env_path)
print("exists:", os.path.exists(env_path))
print("dotenv_values keys:", list(dotenv_values(env_path).keys()))

from flight_api import search_flights, init_flight_results_file
from amadeus_api import AmadeusAPI


load_dotenv(dotenv_path=env_path)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_PATH = os.path.join(ROOT_DIR, "flight_results.json")

app = Flask(__name__)

print("ENV ID loaded:", bool(os.getenv("AMADEUS_CLIENT_ID")))
print("ENV SECRET loaded:", bool(os.getenv("AMADEUS_CLIENT_SECRET")))

cid = (os.getenv("AMADEUS_CLIENT_ID") or "").strip()
cs = (os.getenv("AMADEUS_CLIENT_SECRET") or "").strip()
print("ID length:", len(cid))
print("SECRET length:", len(cs))


# Create API client ONCE
api = AmadeusAPI(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

# Optional: clear results file on startup (same behavior as before)
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump({"query": {}, "results": []}, f, indent=2)

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
# API route
# ---------------------------
@app.post("/api/flights")
def flights_route():
    body = request.get_json(force=True)

    origin = body.get("origin", "JFK")
    destination = body.get("destination", "")
    dates = (body.get("dates") or "").strip()
    budget = body.get("budget")

    # dates expected: "YYYY-MM-DD to YYYY-MM-DD"
    depart_date = None
    return_date = None

    if "to" in dates:
        parts = [p.strip() for p in dates.split("to")]
        if len(parts) == 2:
            depart_date, return_date = parts[0], parts[1]
    else:
        # allow one-way: "YYYY-MM-DD"
        depart_date = dates

    if not depart_date:
        return jsonify({"error": "Missing/invalid dates. Expected 'YYYY-MM-DD to YYYY-MM-DD'."}), 400

    payload = api.search_flights_clean(
        origin=origin,
        destination=destination,
        depart_date=depart_date,
        return_date=return_date,
        budget=budget,
        adults=1,
        max_results=5,
        results_path=RESULTS_PATH,
    )

    if isinstance(payload, dict) and payload.get("error"):
        return jsonify(payload), 400

    return jsonify(payload), 200

@app.post("/api/hotels")
def hotels_route():
    print("✅ /api/hotels HIT", flush=True)
    body = request.get_json(force=True)
    print("✅ body:", body, flush=True)

    destination = (body.get("destination") or "").strip()
    dates = (body.get("dates") or "").strip()
    budget = body.get("budget")

    # dates expected: "YYYY-MM-DD to YYYY-MM-DD"
    check_in = None
    check_out = None

    if "to" in dates:
        parts = [p.strip() for p in dates.split("to")]
        if len(parts) == 2:
            check_in, check_out = parts[0], parts[1]

    if not destination or not check_in or not check_out:
        return jsonify({"error": "Missing destination or invalid dates. Expected 'YYYY-MM-DD to YYYY-MM-DD'."}), 400

    payload = api.search_hotels_clean(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=1,
        budget=budget,
        currency="USD",
        max_results=8,
    )

    if isinstance(payload, dict) and payload.get("error"):
        return jsonify(payload), 400

    return jsonify(payload), 200




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
    app.run(debug=True, use_reloader=False)
