from flask import Flask, request, jsonify, send_from_directory
import os
import json
import re
from dotenv import load_dotenv, dotenv_values
import requests
from amadeus_api import AmadeusAPI
import os, json
from groq import Groq
from datetime import datetime

print("✅ RUNNING FILE:", __file__)
print("✅ CWD:", os.getcwd())

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
print("env_path:", env_path)
print("exists:", os.path.exists(env_path))
print("dotenv_values keys:", list(dotenv_values(env_path).keys()))


load_dotenv(dotenv_path=env_path, override=True)

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()

print("✅ GROQ_API_KEY loaded:", bool(GROQ_API_KEY))
print("✅ GROQ_API_KEY prefix:", GROQ_API_KEY[:4])   # should print 'gsk_'
print("✅ GROQ_MODEL:", GROQ_MODEL)
print("GROQ key len:", len(GROQ_API_KEY))
print("GROQ key last4:", GROQ_API_KEY[-4:])


from datetime import datetime

def trip_length_days(depart_date: str, return_date: str) -> int:
    try:
        d0 = datetime.strptime(depart_date, "%Y-%m-%d").date()
        d1 = datetime.strptime(return_date, "%Y-%m-%d").date()
        n = (d1 - d0).days + 1
        return max(1, min(n, 14))  # cap to avoid huge outputs
    except Exception:
        return 1


def safe_call(name, fn):
    try:
        data = fn()
        return {"ok": True, "name": name, "data": data}
    except Exception as e:
        return {"ok": False, "name": name, "error": {"message": str(e)}}

def try_parse_json(s: str):
    try:
        return json.loads(s), None
    except Exception as e:
        return None, str(e)
def parse_dates(dates_str: str):
    found = re.findall(r"\d{4}-\d{2}-\d{2}", dates_str or "")
    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], None
    return None, None

def groq_json(prompt: str) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("Missing GROQ_API_KEY env var")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a travel planner that outputs STRICT JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    r = requests.post(url, headers=headers, json=body, timeout=45)

    if r.status_code == 401:
        # shows EXACT reason from Groq without exposing your key
        raise RuntimeError(f"Groq 401 Unauthorized: {r.text}")

    if r.status_code >= 400:
        raise RuntimeError(f"Groq HTTP {r.status_code}: {r.text}")

    content = r.json()["choices"][0]["message"]["content"]

    # Strip accidental code fences if the model adds them
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1].strip()

    return json.loads(content)



def build_itinerary_prompt(user_input: dict, results: list[dict]) -> str:
    return f"""
You are an expert travel planner.

GOAL:
Create the best possible itinerary using real API data when available.
If flights or transfers are missing/errored, estimate plausible options instead.
Whenever you estimate, label it clearly as "ESTIMATE" and explain assumptions.

USER INPUT:
{json.dumps(user_input, indent=2)}

API RESULTS (each entry is either ok:true with data, or ok:false with error):
{json.dumps(results, indent=2)}

OUTPUT FORMAT (JSON ONLY, no markdown):
{{
  "summary": {{
    "destination": string,
    "dates": string,
    "budget": string,
    "transport": string,
    "assumptions": [string]
  }},
  "cost_breakdown": {{
    "flights": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "hotels": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "local_transport": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "food": {{ "type": "ESTIMATE", "range_usd": [number, number], "notes": string }},
    "activities": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "total_estimated": {{ "range_usd": [number, number] }}
  }},
  "itinerary": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "morning": [string],
      "afternoon": [string],
      "evening": [string],
      "notes": [string]
    }}
  ],
  "recommended_hotels": [
    {{ "name": string, "why": string, "price_total_usd": number|null, "source": "REAL|ESTIMATE" }}
  ],
  "flight_plan": {{
    "source": "REAL|ESTIMATE",
    "options": [
      {{ "summary": string, "price_usd": number|null, "notes": string }}
    ]
  }},
  "transfer_plan": {{
    "source": "REAL|ESTIMATE",
    "options": [
      {{ "summary": string, "price_usd": number|null, "notes": string }}
    ]
  }}
}}

Hard rules:
- Use REAL prices only if present in API data.
- If API failed, provide ESTIMATE ranges and state assumptions.
- Be practical and cluster activities geographically.
""".strip()




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
@app.post("/api/generate-itinerary")
def generate_itinerary():


    body = request.get_json(force=True) or {}

    destination = (body.get("destination") or "").strip()
    dates = (body.get("dates") or "").strip()
    budget = (body.get("budget") or "").strip()
    transport = (body.get("transport") or "").strip()
    interests = body.get("interests") or []
    message = (body.get("message") or "").strip()

    depart_date, return_date = parse_dates(dates)
    num_days = trip_length_days(depart_date, return_date)
    if not destination or not depart_date or not return_date:
        return jsonify({"error": "Missing/invalid destination or dates"}), 400
    num_days = days_between(depart_date, return_date)

    # -------------------------
    # 1) Hotels
    # -------------------------
    hotels_meta = {"source": "ESTIMATE", "data": {}, "notes": "Hotel API not called."}
    try:
        hotels_payload = api.search_hotels_clean(
            destination=destination,
            check_in=depart_date,
            check_out=return_date,
            adults=1,
            room_quantity=1,
            budget=budget if budget else None,
            max_results=8,
        )
        if isinstance(hotels_payload, dict) and hotels_payload.get("error"):
            hotels_meta = {"source": "ESTIMATE", "data": hotels_payload, "notes": "Hotel API error; using estimates."}
        else:
            hotels_meta = {"source": "REAL", "data": hotels_payload, "notes": "From Amadeus."}
    except Exception as e:
        hotels_meta = {"source": "ESTIMATE", "data": {}, "notes": f"Hotel API crashed: {e}"}

    # -------------------------
    # 2) Flights
    # -------------------------
    flights_meta = {"source": "ESTIMATE", "data": {}, "notes": "Flight API unavailable; using estimated guidance."}
    try:
        origin = (body.get("origin") or "BOS").strip()
        flight_payload = api.search_flights_clean(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            budget=budget if budget else None,
            adults=1,
            max_results=5,
        )
        if isinstance(flight_payload, dict) and flight_payload.get("error"):
            flights_meta = {"source": "ESTIMATE", "data": flight_payload, "notes": "Flight API error; using estimate."}
        else:
            flights_meta = {"source": "REAL", "data": flight_payload, "notes": "From Amadeus."}
    except Exception as e:
        flights_meta = {"source": "ESTIMATE", "data": {}, "notes": f"Flight API crashed: {e}"}

    # -------------------------
    # 3) Transfers
    # -------------------------
    transfers_meta = {"source": "ESTIMATE", "data": {}, "notes": "Transfers API unavailable; using estimated local transport."}
    try:
        start_iata = (body.get("start_location") or "BOS").strip()
        end_iata = destination
        start_datetime = f"{depart_date}T12:00:00"
        transfer_payload = api.search_transfers_clean(
            start_iata=api.resolve_iata(start_iata) or "BOS",
            end_iata=api.resolve_iata(end_iata) or "",
            start_datetime=start_datetime,
            passengers=1,
        )
        if isinstance(transfer_payload, dict) and transfer_payload.get("error"):
            transfers_meta = {"source": "ESTIMATE", "data": transfer_payload, "notes": "Transfers API error; using estimate."}
        else:
            transfers_meta = {"source": "REAL", "data": transfer_payload, "notes": "From Amadeus."}
    except Exception as e:
        transfers_meta = {"source": "ESTIMATE", "data": {}, "notes": f"Transfers API crashed: {e}"}

    # -------------------------
    # 4) Build hotel name hints for LLM
    # -------------------------
    hotel_names = []
    try:
        hotel_list = (hotels_meta.get("data") or {}).get("hotels") or []
        for h in hotel_list[:6]:
            name = h.get("name")
            if name:
                hotel_names.append(name)
    except Exception:
        pass

    # -------------------------
    # 5) Groq prompt
    # -------------------------
    prompt = f"""
You are a travel planner. Output STRICT JSON only (no markdown, no code fences).

USER INPUT:
destination: {destination}
origin: {(body.get("origin") or "BOS").strip()}
dates: {depart_date} to {return_date}
budget_max_usd: {budget or "unknown"}
transport_preference: {transport or "any"}
interests: {interests if interests else []}
notes: {message or "none"}

AVAILABLE DATA (may be empty if API failed):
flights_meta: {json.dumps(flights_meta, indent=2)}
hotels_meta: {json.dumps(hotels_meta, indent=2)}
transfers_meta: {json.dumps(transfers_meta, indent=2)}

OUTPUT JSON SCHEMA (must match exactly):
{{
  "summary": {{
    "destination": string,
    "origin": string,
    "dates": string,
    "traveler_count": number,
    "assumptions": [string]
  }},
  "cost_breakdown": {{
    "flights": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "hotels": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "local_transport": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "food": {{ "type": "ESTIMATE", "range_usd": [number, number], "notes": string }},
    "activities": {{ "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string }},
    "total_estimated": {{ "range_usd": [number, number], "notes": string }}
  }},
  "recommended_hotels": [
    {{ "name": string, "price_total_usd": number|null, "why": string, "source": "REAL|ESTIMATE" }}
  ],
  "flight_plan": {{
    "source": "REAL|ESTIMATE",
    "options": [
      {{ "summary": string, "price_usd": number|null, "notes": string }}
    ]
  }},
  "itinerary": [
    {{
      "day": number,
      "title": string,
      "items": [
        {{ "start": string, "end": string, "text": string }}
      ]
    }}
  ]
}}

HARD RULES:
- If flights_meta.source == "REAL", use those prices/options as REAL. If not, create ESTIMATE ranges and state assumptions.
- If hotels_meta.source == "REAL", use those hotels as REAL. If not, create ESTIMATE ranges and state assumptions.
- itinerary length MUST match number of days between depart_date and return_date (inclusive of each overnight day). If 5 days, output 5 day objects.
- Each day.items MUST contain EXACTLY 6 entries with realistic times, meals, transit, and rest.
- At least 3 of 6 items per day should reflect the interests (if any).
""".strip()



    # -------------------------
    # 6) Call Groq, fallback if it fails
    # -------------------------
    try:
        llm_out = groq_json(prompt)
        itinerary = llm_out.get("itinerary", [])
        if not isinstance(itinerary, list) or len(itinerary) != num_days:
            raise ValueError(f"LLM itinerary invalid length: got {len(itinerary)} expected {num_days}")
    except Exception as e:
        print("❌ GROQ ITINERARY FAILED:", str(e), flush=True)
        itinerary = []


    # -------------------------
    # ✅ ALWAYS convert to frontend-friendly schedule[]
    # -------------------------
    fixed_itinerary = []
    for d in itinerary:
        items = d.get("items", []) or []
        schedule = []
        for it in items:
            start = (it.get("start") or "").strip()
            end = (it.get("end") or "").strip()
            text = (it.get("text") or "").strip()
            time = f"{start} - {end}".strip(" -")
            schedule.append({"time": time, "activity": text})

        fixed_itinerary.append({
            "day": d.get("day"),
            "title": d.get("title", f"Day {d.get('day')}"),
            "schedule": schedule
        })


    return jsonify({
        "destination": destination,
        "dates": f"{depart_date} to {return_date}",
        "interests": interests,
        "itinerary": fixed_itinerary,  # ✅ return the converted format
        "travel_data": {
            "flights": flights_meta,
            "transfers": transfers_meta,
            "hotels": hotels_meta,
        }
    }), 200

@app.post("/api/flights")
def flights_route():
    print("🔥🔥🔥 FLIGHTS ROUTE HIT 🔥🔥🔥", flush=True)
    body = request.get_json(force=True)
    print("🔥 body:", body, flush=True)
    origin = body.get("origin", "JFK")
    destination = body.get("destination", "LAX")
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
    print("✅ /api/hotels HIT")

    body = request.get_json(force=True) or {}
    print("✅ body:", body)

    destination = (body.get("destination") or "").strip()
    dates = (body.get("dates") or "").strip()

    # budget can be "", "4000", 4000, etc.
    budget_raw = body.get("budget")
    budget = None
    if budget_raw is not None:
        s = str(budget_raw).strip()
        if s != "":
            budget = s  # keep as string; your method converts safely

    check_in = None
    check_out = None

    # Expect: "YYYY-MM-DD to YYYY-MM-DD"
    if "to" in dates:
        parts = [p.strip() for p in dates.split("to")]
        if len(parts) == 2:
            check_in, check_out = parts[0], parts[1]
    else:
        return jsonify({"error": "Missing/invalid dates. Expected 'YYYY-MM-DD to YYYY-MM-DD'."}), 400

    if not destination or not check_in or not check_out:
        return jsonify({"error": "Missing destination or dates."}), 400

    print("✅ search_hotels_clean CALLED", destination, check_in, check_out, "budget:", budget)

    payload = api.search_hotels_clean(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=1,
        room_quantity=1,
        budget=budget,
        max_results=8,
    )

    # If backend returns an error object
    if isinstance(payload, dict) and payload.get("error"):
        return jsonify(payload), 400

    return jsonify(payload), 200

@app.post("/api/transfers")
def transfers():
    print("✅ /api/transfers HIT", flush=True)
    body = request.get_json(force=True) or {}
    print("➡️ transfers body:", body, flush=True)

    start_input = (body.get("start_location") or "BOS").strip()
    end_input = (body.get("end_location") or "").strip()
    dates = (body.get("dates") or "").strip()

    depart_date, _ = parse_dates(dates)
    if not depart_date:
        return jsonify({"error": "Dates must include YYYY-MM-DD"}), 400

    # Transfers are ground transport: start is usually an AIRPORT code
    start_iata = api.resolve_iata(start_input) or "BOS"

    if not end_input:
        return jsonify({
            "error": "Missing end_location for transfer search.",
            "hint": "Use an address or city name (e.g., '200 N Spring St, Los Angeles, CA' or 'Los Angeles')."
        }), 400

    start_datetime = f"{depart_date}T12:00:00"

    # --- Build Transfers Search BODY (POST /v1/shopping/transfer-offers) ---
    # We don't use endLocationCode; we use destination address fields.
    # Minimal approach: treat end_input as a city and also as the address line if needed.
    transfer_body = {
        "startLocationCode": start_iata,
        "transferType": "PRIVATE",
        "startDateTime": start_datetime,
        "passengers": 1,
        "currency": "USD",

        # destination (simple + forgiving):
        # If the user gives a full address, this still works fine.
        "endAddressLine": end_input,
        "endCityName": end_input,     # if it's a city, good; if it's an address, Amadeus may ignore or still accept
        "endCountryCode": "US",       # ⚠️ you may want to infer this later; hardcode for now

        # recommended by Amadeus examples
        "passengerCharacteristics": [
            {"passengerTypeCode": "ADT", "age": 20}
        ],
    }

    print("➡️ transfers body keys:", sorted(transfer_body.keys()), flush=True)

    try:
        resp = api._request("POST", "/v1/shopping/transfer-offers", json_body=transfer_body)
    except Exception as e:
        print("❌ TRANSFER CRASH:", e, flush=True)
        return jsonify({"error": "Transfer request crashed", "message": str(e)}), 500

    if resp.status_code >= 400:
        try:
            details = resp.json()
        except Exception:
            details = resp.text
        print("❌ TRANSFER HTTP ERROR:", details, flush=True)
        return jsonify({
            "error": "Amadeus transfer request failed",
            "details": details,
            "query": transfer_body
        }), 502

    payload = resp.json() or {}
    data = payload.get("data", []) or []
    print(f"✅ Transfers found: {len(data)}", flush=True)

    # summarize (lightweight)
    summarized = []
    for item in data:
        quotation = (item.get("quotation") or {}).get("monetaryAmount") or {}
        vehicle = item.get("vehicle") or {}
        summarized.append({
            "id": item.get("id"),
            "transferType": item.get("transferType"),
            "vehicleCode": vehicle.get("code"),
            "duration": item.get("duration"),
            "price": quotation.get("value"),
            "currency": quotation.get("currency"),
        })

    return jsonify({
        "start": start_iata,
        "startDateTime": start_datetime,
        "query": transfer_body,
        "transfers": summarized
    }), 200

@app.post("/api/activities")
def activities():
    body = request.get_json(force=True) or {}
    destination = (body.get("destination") or "").strip()
    interests = body.get("interests", [])

    if not destination:
        return jsonify({"error": "Missing destination"}), 400

    return jsonify({
        "error": "Activities/POI lookup is unavailable via Amadeus (endpoint is decommissioned).",
        "suggestion": "Use Google Places API (Text Search + Nearby Search) for activities.",
        "destination": destination,
        "interests": interests
    }), 501



# ---------------------------
# Helpers
# ---------------------------

def days_between(start_yyyy_mm_dd: str, end_yyyy_mm_dd: str) -> int:
    s = datetime.strptime(start_yyyy_mm_dd, "%Y-%m-%d").date()
    e = datetime.strptime(end_yyyy_mm_dd, "%Y-%m-%d").date()
    # inclusive days (Jan 1 to Jan 3 => 3 days)
    return (e - s).days + 1

def safe_get(obj, *keys, default=None):
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default

def summarize_transfer(item):
    return {
        "id": item.get("id"),
        "from": safe_get(item, "start", "locationCode"),
        "to": safe_get(item, "end", "locationCode"),
        "transferType": item.get("transferType"),
        "vehicleType": safe_get(item, "vehicle", "code"),
        "duration": item.get("duration"),
        "currency": safe_get(item, "quotation", "monetaryAmount", "currency"),
        "total": safe_get(item, "quotation", "monetaryAmount", "value"),
    }

def interest_to_poi_categories(interests):
    mapping = {
        "🏛️ Sightseeing": "SIGHTS",
        "🌲 Nature": "NATURE",
        "🛍️ Shopping": "SHOPPING",
        "🎉 Nightlife": "NIGHTLIFE",
        "🍽️ Food": "RESTAURANT",
    }
    cats = []
    for i in interests or []:
        if i in mapping:
            cats.append(mapping[i])
    return ",".join(sorted(set(cats))) if cats else None

def summarize_poi(p):
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "category": p.get("category"),
        "rank": p.get("rank"),
        "address": safe_get(p, "address", "label"),
        "geo": p.get("geoCode"),
    }






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

