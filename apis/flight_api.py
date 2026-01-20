
from flask import Flask, request, jsonify, render_template, send_from_directory
from amadeus import Client, ResponseError
import os, re
import csv
import os
from difflib import get_close_matches
import json
from datetime import datetime


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIRPORTS = []
AIRPORTS_LOADED = False

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "flight_results.json")

# Always create/clear file on startup
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump({"query": {}, "results": []}, f, indent=2)

print("Initialized flight_results.json at:", RESULTS_PATH)



app = Flask(__name__)
# Serve frontend files from the repo root (one level up from /apis)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------
# Amadeus Client
# ---------------------------
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname="test"
)

IATA_RE = re.compile(r"^[A-Z]{3}$")

# ---------------------------
# Helpers
# ---------------------------

def parse_dates(dates_str):
    found = re.findall(r"\d{4}-\d{2}-\d{2}", dates_str or "")
    if len(found) == 1:
        return found[0], None
    if len(found) >= 2:
        return found[0], found[1]
    return None, None

def load_airports():
    global AIRPORTS_LOADED
    if AIRPORTS_LOADED:
        return

    path = os.path.join(ROOT_DIR, "data", "airports.dat")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Format: ID, Name, City, Country, IATA, ICAO, Lat, Long, ...
            if len(row) < 5:
                continue
            name, city, country, iata = row[1], row[2], row[3], row[4]
            if iata and iata != r"\N" and len(iata) == 3:
                AIRPORTS.append({
                    "name": name.strip(),
                    "city": city.strip(),
                    "country": country.strip(),
                    "iata": iata.strip().upper()
                })

    AIRPORTS_LOADED = True

def resolve_iata_local(query: str):
    load_airports()
    q = (query or "").strip().lower()
    if not q:
        return None

    # Exact city match
    for a in AIRPORTS:
        if a["city"].lower() == q:
            return a["iata"]

    # Fuzzy city match
    cities = list({a["city"] for a in AIRPORTS})
    close = get_close_matches(query, cities, n=1, cutoff=0.8)
    if close:
        best_city = close[0].lower()
        for a in AIRPORTS:
            if a["city"].lower() == best_city:
                return a["iata"]

    return None


def resolve_iata(query: str):
    if not query:
        return None

    q = query.strip().upper()
    if IATA_RE.match(q):
        return q

    # 1) Try Amadeus first
    try:
        resp = amadeus.reference_data.locations.get(
            keyword=query,
            subType="CITY,AIRPORT",
            page={"limit": 10}
        )
        data = resp.data or []
        for x in data:
            if x.get("subType") == "CITY" and x.get("iataCode"):
                return x["iataCode"]
        for x in data:
            if x.get("subType") == "AIRPORT" and x.get("iataCode"):
                return x["iataCode"]
    except Exception:
        pass

    # 2) Fallback to local dataset
    local = resolve_iata_local(query)
    if local:
        return local

    return None


def extract_flight_codes(offer):
    codes = []
    for itin in offer.get("itineraries", []):
        for seg in itin.get("segments", []):
            carrier = seg.get("carrierCode")
            number = seg.get("number")
            if carrier and number:
                codes.append(f"{carrier} {number}")
    return codes


def count_stops(itinerary):
    segments = itinerary.get("segments", [])
    return max(0, len(segments) - 1)


def summarize_itinerary(itin, dictionaries):
    if not itin:
        return None

    segs = itin.get("segments", [])
    first = segs[0] if segs else None
    last = segs[-1] if segs else None

    carrier_codes = []
    for s in segs:
        cc = s.get("carrierCode")
        if cc and cc not in carrier_codes:
            carrier_codes.append(cc)

    carrier_dict = dictionaries.get("carriers", {}) if dictionaries else {}
    airline_names = [carrier_dict.get(cc, cc) for cc in carrier_codes]

    return {
        "from": first.get("departure", {}).get("iataCode") if first else None,
        "to": last.get("arrival", {}).get("iataCode") if last else None,
        "departAt": first.get("departure", {}).get("at") if first else None,
        "arriveAt": last.get("arrival", {}).get("at") if last else None,
        "stops": count_stops(itin),
        "duration": itin.get("duration"),
        "airlines": airline_names,
        "carrierCodes": carrier_codes,
    }


def summarize_offer(offer, dictionaries):
    itineraries = offer.get("itineraries", [])
    outbound = itineraries[0] if len(itineraries) > 0 else None
    inbound = itineraries[1] if len(itineraries) > 1 else None

    return {
        "id": offer.get("id"),
        "price": {
            "total": offer.get("price", {}).get("total"),
            "currency": offer.get("price", {}).get("currency")
        },
        "flightCodes": extract_flight_codes(offer),
        "outbound": summarize_itinerary(outbound, dictionaries),
        "inbound": summarize_itinerary(inbound, dictionaries)
    }

def search_flights(body):
    """
    Search for flights based on request body.
    Returns: (payload_dict, status_code)
    """
    origin_input = body.get("origin", "JFK")
    destination_input = body.get("destination", "")
    dates = body.get("dates", "")
    budget = body.get("budget", "")

    depart_date, return_date = parse_dates(dates)
    if not depart_date:
        return ({"error": "Dates must be in YYYY-MM-DD format"}, 400)

    origin = resolve_iata(origin_input) or "JFK"
    destination = resolve_iata(destination_input)

    if not destination:
        return ({"error": f"Could not resolve destination '{destination_input}'"}, 400)

    max_price = None
    if budget:
        try:
            max_price = int(float(budget))
        except ValueError:
            return ({"error": "Budget must be numeric"}, 400)

    try:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": depart_date,
            "adults": 1,
            "currencyCode": "USD",
            "max": 5
        }

        if return_date:
            params["returnDate"] = return_date
        if max_price is not None:
            params["maxPrice"] = max_price

        resp = amadeus.shopping.flight_offers_search.get(**params)

    except ResponseError as e:
        return ({"error": "Amadeus request failed", "message": str(e)}, 500)

    data = resp.data or []
    dictionaries = resp.result.get("dictionaries", {})

    summarized = [summarize_offer(o, dictionaries) for o in data]

    result_payload = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date,
        "return_date": return_date,
        "offers": summarized,
        "saved_at": datetime.now().isoformat()
    }

    # Save to file
    out_path = os.path.join(os.path.dirname(__file__), "flight_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)

    return (result_payload, 200)

# ---------------------------
# Routes
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

@app.post("/api/flights")
def flights():
    body = request.get_json(force=True)
    payload, status = search_flights(body)
    return jsonify(payload), status





if __name__ == "__main__":
    app.run(debug=True)
>>>>>>> main
