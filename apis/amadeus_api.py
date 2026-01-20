import os
import re
import csv
import json
import requests
<<<<<<< HEAD
from datetime import datetime
from difflib import get_close_matches
from requests.auth import HTTPBasicAuth
from datetime import datetime

IATA_RE = re.compile(r"^[A-Z]{3}$")

=======
import os
import csv
>>>>>>> main

class AmadeusAPI:
    """
    One consolidated Amadeus wrapper:
    - Uses OAuth token (requests-based) like your original file
    - Adds new methods: airport loading, IATA resolution (Amadeus + local), and clean flight summaries
    - Keeps your original: hotels, hotel booking, transfers, transfer booking, city coords, activities, flight booking payload
    """

    def __init__(self, client_id, client_secret, hostname="test", data_dir=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.hostname = hostname

        print("client_id loaded:", bool(self.client_id))
        print("client_secret loaded:", bool(self.client_secret))
        if self.client_id:
            print("client_id len:", len(self.client_id))
        if self.client_secret:
            print("client_secret len:", len(self.client_secret))

        self.access_token = None
        self.get_access_token()



    # =========================================================
    # AUTH
    # =========================================================
    def get_access_token(self):
        base = "https://test.api.amadeus.com" if self.hostname == "test" else "https://api.amadeus.com"
        url = f"{base}/v1/security/oauth2/token"

        data = {"grant_type": "client_credentials"}

        # Basic Auth carries the client_id/client_secret
        response = requests.post(
            url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )

        # Helpful debug if it fails again
        try:
            token_json = response.json()
        except Exception:
            raise Exception(f"Token endpoint returned non-JSON: {response.status_code} {response.text}")

        if response.status_code != 200 or "access_token" not in token_json:
            raise Exception(f"Failed to get access token: {token_json}")

        self.access_token = token_json["access_token"]


    def _headers(self, json_content=False):
        h = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        if json_content:
            h["Content-Type"] = "application/json"
        return h

    def _base_url(self):
        return "https://test.api.amadeus.com" if self.hostname == "test" else "https://api.amadeus.com"
    
    def _request(self, method, path, *, params=None, json_body=None, timeout=20):
        """
        Makes an Amadeus request. If token is expired (401), refresh token and retry once.
        """
        url = f"{self._base_url()}{path}"

        def do_request():
            return requests.request(
                method,
                url,
                headers=self._headers(json_content=(json_body is not None)),
                params=params,
                json=json_body,
                timeout=timeout,
            )

        resp = do_request()

        # If token expired/invalid, refresh and retry once
        if resp.status_code == 401:
            try:
                payload = resp.json()
            except Exception:
                payload = {}

            # Check for token-expired style errors, but even plain 401 we can refresh
            self.get_access_token()
            resp = do_request()

        print("AMADEUS FINAL URL:", url)
        return resp


    # =========================================================
    # NEW METHODS (from your new file) — Airports + IATA
    # =========================================================
    def _load_airports(self):
        if self._airports_loaded:
            return

        path = os.path.join(self.data_dir, "airports.dat")
        if not os.path.exists(path):
            # If you don't have airports.dat, we can still resolve via Amadeus API
            self._airports_loaded = True
            return

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 5:
                    continue
                name, city, country, iata = row[1], row[2], row[3], row[4]
                if iata and iata != r"\N" and len(iata) == 3:
                    self._airports.append(
                        {
                            "name": name.strip(),
                            "city": city.strip(),
                            "country": country.strip(),
                            "iata": iata.strip().upper(),
                        }
                    )

        self._airports_loaded = True

    def _resolve_iata_local(self, query: str):
        self._load_airports()
        q = (query or "").strip().lower()
        if not q:
            return None

        # Exact city match
        for a in self._airports:
            if a["city"].lower() == q:
                return a["iata"]

        # Fuzzy city match
        cities = list({a["city"] for a in self._airports})
        close = get_close_matches(query, cities, n=1, cutoff=0.8)
        if close:
            best_city = close[0].lower()
            for a in self._airports:
                if a["city"].lower() == best_city:
                    return a["iata"]

        return None

    def resolve_iata(self, query: str):
        """
        Returns IATA code for a city/airport input:
        - If already a 3-letter IATA, returns it
        - Else tries Amadeus Locations API
        - Else falls back to local airports.dat
        """
        if not query:
            return None

        q = query.strip().upper()
        if IATA_RE.match(q):
            return q

        # 1) Try Amadeus Locations API
        try:
            url = f"{self._base_url()}/v1/reference-data/locations"
            params = {
                "keyword": query,
                "subType": "CITY,AIRPORT",
                "page[limit]": 10,
            }
            resp = self._request("GET", "/v1/reference-data/locations", params=params)
            data = (resp.json() or {}).get("data", []) if resp.status_code < 400 else []

            # Prefer CITY then AIRPORT
            for x in data:
                if x.get("subType") == "CITY" and x.get("iataCode"):
                    return x["iataCode"]
            for x in data:
                if x.get("subType") == "AIRPORT" and x.get("iataCode"):
                    return x["iataCode"]
        except Exception:
            pass

        # 2) Fallback to local dataset
        return self._resolve_iata_local(query)

    # =========================================================
    # NEW METHODS — Clean flight summaries
    # =========================================================
    def _extract_flight_codes(self, offer):
        codes = []
        for itin in offer.get("itineraries", []):
            for seg in itin.get("segments", []):
                carrier = seg.get("carrierCode")
                number = seg.get("number")
                if carrier and number:
                    codes.append(f"{carrier} {number}")
        return codes

    def _count_stops(self, itinerary):
        segments = itinerary.get("segments", []) if itinerary else []
        return max(0, len(segments) - 1)

    def _summarize_itinerary(self, itin, dictionaries):
        if not itin:
            return None

        segs = itin.get("segments", [])
        if not segs:
            return None

        first = segs[0]
        last = segs[-1]

        carrier_codes = []
        for s in segs:
            cc = s.get("carrierCode")
            if cc and cc not in carrier_codes:
                carrier_codes.append(cc)

        carrier_dict = (dictionaries or {}).get("carriers", {})
        airline_names = [carrier_dict.get(cc, cc) for cc in carrier_codes]

        return {
            "from": first.get("departure", {}).get("iataCode"),
            "to": last.get("arrival", {}).get("iataCode"),
            "departAt": first.get("departure", {}).get("at"),
            "arriveAt": last.get("arrival", {}).get("at"),
            "stops": self._count_stops(itin),
            "duration": itin.get("duration"),
            "airlines": airline_names,
            "carrierCodes": carrier_codes,
        }

    def _summarize_offer(self, offer, dictionaries):
        itineraries = offer.get("itineraries", [])
        outbound = itineraries[0] if len(itineraries) > 0 else None
        inbound = itineraries[1] if len(itineraries) > 1 else None

        return {
            "id": offer.get("id"),
            "price": {
                "total": offer.get("price", {}).get("total"),
                "currency": offer.get("price", {}).get("currency"),
            },
            "flightCodes": self._extract_flight_codes(offer),
            "outbound": self._summarize_itinerary(outbound, dictionaries),
            "inbound": self._summarize_itinerary(inbound, dictionaries),
        }

    def save_json(self, payload: dict, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def search_flights_clean(
        self,
        origin,
        destination,
        depart_date,
        return_date=None,
        adults=1,
        budget=None,
        currency="USD",
        max_results=5,
        results_path=None,
        non_stop=None,
    ):
        """
        NEW: Flight search that returns summarized clean JSON.
        - origin/destination can be city names or IATA
        - budget (maxPrice) optional
        - non_stop optional (True/False)
        """
        origin_code = self.resolve_iata(origin) or "JFK"
        dest_code = self.resolve_iata(destination)

        if not dest_code:
            return {"error": f"Could not resolve destination '{destination}'"}

        url = f"{self._base_url()}/v2/shopping/flight-offers"

        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": dest_code,
            "departureDate": depart_date,
            "adults": adults,
            "currencyCode": currency,
            "max": max_results,
        }

        if return_date:
            params["returnDate"] = return_date

        if budget is not None:
            params["maxPrice"] = int(float(budget))

        if non_stop is not None:
            params["nonStop"] = bool(non_stop)

        resp = self._request("GET", "/v2/shopping/flight-offers", params=params)
        payload = resp.json()


        if resp.status_code >= 400:
            return {"error": "Amadeus request failed", "details": payload}

        data = payload.get("data", []) or []
        dictionaries = payload.get("dictionaries", {}) or {}

        summarized = [self._summarize_offer(o, dictionaries) for o in data]

        result_payload = {
            "origin": origin_code,
            "destination": dest_code,
            "depart_date": depart_date,
            "return_date": return_date,
            "offers": summarized,
            "saved_at": datetime.now().isoformat(),
        }

        if results_path:
            self.save_json(result_payload, results_path)

        return result_payload

    # =========================================================
    # ORIGINAL METHODS (kept) — Flights booking
    # =========================================================
    def find_best_flights(self, origin, destination, departure_date, adults, currency="USD", non_stop=True):
        """
        Original raw flight offers search. Consider using search_flights_clean instead.
        """
        url = f"{self._base_url()}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "nonStop": non_stop,
            "currencyCode": currency,
        }
        response = requests.get(url, headers=self._headers(), params=params)
        return response.json()

    def confirm_flight_details(self, flight_offer):
        pricing_url = f"{self._base_url()}/v1/shopping/flight-offers/pricing"
        body = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": [flight_offer],
            }
        }
        response = requests.post(pricing_url, headers=self._headers(json_content=True), json=body)
        return response.json()

    # FIXED: added self
    def create_flight_order(
        self,
        priced_flight_offer,
        traveler_id,
        first_name,
        last_name,
        date_of_birth,
        gender,
        email,
        phone_country_code,
        phone_number,
        documents=None,
    ):
        traveler = {
            "id": traveler_id,
            "dateOfBirth": date_of_birth,
            "name": {"firstName": first_name, "lastName": last_name},
            "gender": gender,
            "contact": {
                "emailAddress": email,
                "phones": [
                    {
                        "deviceType": "MOBILE",
                        "countryCallingCode": phone_country_code,
                        "number": phone_number,
                    }
                ],
            },
        }

        if documents:
            traveler["documents"] = documents

        return {
            "data": {
                "type": "flight-order",
                "flightOffers": [priced_flight_offer],
                "travelers": [traveler],
            }
        }

    def book_flight(
        self,
        flight_offer,
        traveler_id,
        first_name,
        last_name,
        date_of_birth,
        gender,
        email,
        phone_country_code,
        phone_number,
        documents=None,
    ):
        booking_url = f"{self._base_url()}/v1/booking/flight-orders"
        body = self.create_flight_order(
            flight_offer,
            traveler_id,
            first_name,
            last_name,
            date_of_birth,
            gender,
            email,
            phone_country_code,
            phone_number,
            documents=documents,  # FIXED: actually pass documents through
        )
        response = requests.post(booking_url, headers=self._headers(json_content=True), json=body)
        return response.json()

    # =========================================================
    # ORIGINAL METHODS (kept) — Hotels
    # =========================================================
    def search_hotels(self, city_code):
        resp = self._request(
            "GET",
            "/v1/reference-data/locations/hotels/by-city",
            params={"cityCode": city_code, "radius": 20, "radiusUnit": "KM"},
            timeout=25,
        )
        return resp.json()



    # gets the IATA city code for a given city name

    def get_city_code(self, city_name):
        # Get the path to airports.dat (it's in ../data/ relative to apis/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        airports_file = os.path.join(current_dir, '..', 'data', 'airports.dat')
        
        # Normalize city name for comparison (case-insensitive, strip whitespace)
        city_name_lower = city_name.strip().lower()
        
        try:
            with open(airports_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 5:
                        # Field 2 is the city name, Field 4 is the IATA code
                        airport_city = row[2].strip().lower()
                        iata_code = row[4].strip()
                        
                        # Check for exact match or if city name contains the search term
                        if airport_city == city_name_lower or city_name_lower in airport_city:
                            # Skip if IATA code is \N (not available)
                            if iata_code and iata_code != '\\N':
                                return iata_code
            
            # If no match found, return None or raise an exception
            return None
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find airports.dat at {airports_file}")
        except Exception as e:
            raise Exception(f"Error reading airports.dat: {str(e)}")

    # searches for hotels in a 
    def search_hotels(self, city_code):
        hotels_url = "https://test.api.amadeus.com/v3/shopping/hotels/by-city"

    def filter_hotels(self, hotel_ids, check_in_date, check_out_date, adults, room_quantity, price_range=None, currency="USD"):
        params = {
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency,
        }
        resp = self._request("GET", "/v3/shopping/hotel-offers", params=params, timeout=35)
        return resp.json()




    # FIXED: added self
    def create_hotel_booking_order(
        self,
        offer_id,
        guest_id,
        title,
        first_name,
        last_name,
        email,
        phone,
        card_vendor_code,
        card_number,
        card_expiry_date,
    ):
        return {
            "data": {
                "offerId": offer_id,
                "guests": [
                    {
                        "id": guest_id,
                        "name": {"title": title, "firstName": first_name, "lastName": last_name},
                        "contact": {"phone": phone, "email": email},
                    }
                ],
                "payments": [
                    {
                        "id": "1",
                        "method": "creditCard",
                        "card": {
                            "vendorCode": card_vendor_code,
                            "cardNumber": card_number,
                            "expiryDate": card_expiry_date,
                        },
                    }
                ],
            }
        }

    def book_hotel(
        self,
        offer_id,
        guest_id,
        title,
        first_name,
        last_name,
        email,
        phone,
        card_vendor_code,
        card_number,
        card_expiry_date,
    ):
        booking_url = f"{self._base_url()}/v1/booking/hotel-bookings"
        body = self.create_hotel_booking_order(
            offer_id,
            guest_id,
            title,
            first_name,
            last_name,
            email,
            phone,
            card_vendor_code,
            card_number,
            card_expiry_date,
        )
        response = requests.post(booking_url, headers=self._headers(json_content=True), json=body)
        return response.json()
     # =========================================================
    # ORIGINAL METHODS (kept) — Hotels
    # =========================================================
    def search_hotels(self, city_code):
        hotels_url = f"{self._base_url()}/v3/shopping/hotels/by-city"
        params = {"cityCode": city_code}
        response = requests.get(hotels_url, headers=self._headers(), params=params, timeout=20)
        return response.json()

    def filter_hotels(self, hotel_ids, check_in_date, check_out_date, adults, room_quantity, price_range):
        hotel_info_url = f"{self._base_url()}/v3/shopping/hotels"
        params = {
            "hotelIds": hotel_ids,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "roomQuantity": room_quantity,
            "priceRange": price_range,
        }
        response = requests.get(hotel_info_url, headers=self._headers(), params=params, timeout=20)
        return response.json()

    # FIXED: added self
    def create_hotel_booking_order(
        self,
        offer_id,
        guest_id,
        title,
        first_name,
        last_name,
        email,
        phone,
        card_vendor_code,
        card_number,
        card_expiry_date,
    ):
        return {
            "data": {
                "offerId": offer_id,
                "guests": [
                    {
                        "id": guest_id,
                        "name": {"title": title, "firstName": first_name, "lastName": last_name},
                        "contact": {"phone": phone, "email": email},
                    }
                ],
                "payments": [
                    {
                        "id": "1",
                        "method": "creditCard",
                        "card": {
                            "vendorCode": card_vendor_code,
                            "cardNumber": card_number,
                            "expiryDate": card_expiry_date,
                        },
                    }
                ],
            }
        }

    def book_hotel(
        self,
        offer_id,
        guest_id,
        title,
        first_name,
        last_name,
        email,
        phone,
        card_vendor_code,
        card_number,
        card_expiry_date,
    ):
        booking_url = f"{self._base_url()}/v1/booking/hotel-bookings"
        body = self.create_hotel_booking_order(
            offer_id,
            guest_id,
            title,
            first_name,
            last_name,
            email,
            phone,
            card_vendor_code,
            card_number,
            card_expiry_date,
        )
        response = requests.post(booking_url, headers=self._headers(json_content=True), json=body, timeout=20)
        return response.json()
    
        # =========================================================
    # NEW METHODS — Clean hotel summaries (budget-aware)
    # =========================================================

    def _hotel_offer_total(self, offer) -> float | None:
        try:
            return float(offer.get("price", {}).get("total"))
        except Exception:
            return None


    def _nights_between(self, check_in, check_out):
        try:
            d1 = datetime.strptime(check_in, "%Y-%m-%d")
            d2 = datetime.strptime(check_out, "%Y-%m-%d")
            return max(1, (d2 - d1).days)
        except Exception:
            return None


    def search_hotels_clean(
    self,
    destination,
    check_in,
    check_out,
    adults=1,
    room_quantity=1,
    budget=None,          # overall trip budget max (ex: 4000)
    currency="USD",
    max_results=8
    ):
        print("✅ search_hotels_clean CALLED", destination, check_in, check_out)

        # Convert destination -> city code (PAR for Paris)
        city_code = self.resolve_iata(destination.split(",")[0].strip())
        print("✅ resolved city_code:", city_code)

        if not city_code:
            return {"error": f"Could not resolve destination '{destination}'"}

        # Optional: reserve ~40% of trip budget for hotels (total stay)
        hotel_budget_total = None
        if budget:
            try:
                hotel_budget_total = float(budget) * 0.4
            except Exception:
                hotel_budget_total = None

        # ---------------------------------------------------------
        # 1) HOTEL LIST (MUST BE v1) -> get hotelIds
        # ---------------------------------------------------------
        list_params = {"cityCode": city_code, "radius": 20, "radiusUnit": "KM"}
        print("✅ HOTEL LIST PARAMS SENT:", list_params)

        list_resp = self._request(
            "GET",
            "/v1/reference-data/locations/hotels/by-city",
            params=list_params,
            timeout=25,
        )
        hotel_list_payload = list_resp.json() if list_resp is not None else {}

        print("✅ HOTEL LIST status:", getattr(list_resp, "status_code", None))
        print("✅ HOTEL LIST keys:", list(hotel_list_payload.keys()))
        print("✅ HOTEL LIST errors:", hotel_list_payload.get("errors"))

        if hotel_list_payload.get("errors"):
            return {"error": "Amadeus request failed", "details": hotel_list_payload}

        hotel_list = hotel_list_payload.get("data") or []
        if not hotel_list:
            return {
                "destination": destination,
                "city_code": city_code,
                "check_in": check_in,
                "check_out": check_out,
                "hotels": [],
            }

        hotel_ids = [h.get("hotelId") for h in hotel_list if h.get("hotelId")]
        hotel_ids = hotel_ids[:25]  # keep request reasonable

        if not hotel_ids:
            return {
                "destination": destination,
                "city_code": city_code,
                "check_in": check_in,
                "check_out": check_out,
                "hotels": [],
            }

        # ---------------------------------------------------------
        # 2) HOTEL OFFERS (MUST BE v3) -> requires hotelIds
        # ---------------------------------------------------------
        offers_params = {
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": check_in,
            "checkOutDate": check_out,
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency,
        }
        print("✅ HOTEL OFFERS PARAMS SENT:", offers_params)

        offers_resp = self._request(
            "GET",
            "/v3/shopping/hotel-offers",
            params=offers_params,
            timeout=35,
        )
        offers_payload = offers_resp.json() if offers_resp is not None else {}

        print("✅ HOTEL OFFERS status:", getattr(offers_resp, "status_code", None))
        print("✅ HOTEL OFFERS keys:", list(offers_payload.keys()))
        print("✅ HOTEL OFFERS errors:", offers_payload.get("errors"))
        print("✅ HOTEL OFFERS data length:", len(offers_payload.get("data") or []))

        if offers_payload.get("errors"):
            return {"error": "Amadeus request failed", "details": offers_payload}

        data = offers_payload.get("data") or []

        # ---------------------------------------------------------
        # 3) Summarize + budget filter
        # ---------------------------------------------------------
        results = []
        for item in data:
            hotel = item.get("hotel") or {}
            offers = item.get("offers") or []
            if not offers:
                continue

            # choose cheapest offer
            cheapest = None
            cheapest_val = None
            for o in offers:
                total = (o.get("price") or {}).get("total")
                try:
                    val = float(total)
                except Exception:
                    continue
                if cheapest_val is None or val < cheapest_val:
                    cheapest_val = val
                    cheapest = o

            if not cheapest:
                continue

            # budget filter (compare total stay cost vs reserved hotel budget)
            if hotel_budget_total is not None and cheapest_val is not None and cheapest_val > hotel_budget_total:
                continue

            results.append({
                "id": hotel.get("hotelId"),
                "name": hotel.get("name"),
                "rating": hotel.get("rating"),
                "address": hotel.get("address"),
                "cheapestOffer": {
                    "checkInDate": cheapest.get("checkInDate") or check_in,
                    "checkOutDate": cheapest.get("checkOutDate") or check_out,
                    "rateType": cheapest.get("rateType"),
                    "boardType": cheapest.get("boardType"),
                    "roomType": ((cheapest.get("room") or {}).get("typeEstimated") or {}).get("category"),
                    "price": cheapest.get("price"),
                }
            })

            if len(results) >= max_results:
                break

        return {
            "destination": destination,
            "city_code": city_code,
            "check_in": check_in,
            "check_out": check_out,
            "hotels": results,
        }






    
    #Helper Methods for Hotels

    def _parse_iso_date(self, s: str):
        # expects "YYYY-MM-DD"
        return datetime.strptime(s, "%Y-%m-%d").date()


    def resolve_city_code(self, city_query: str):
        """
        Resolve a user city name (e.g. 'Paris') -> IATA CITY code (e.g. 'PAR').
        Uses /v1/reference-data/locations with subType=CITY.
        """
        if not city_query:
            return None

        # If user typed PAR already, keep it
        q = city_query.strip().upper()
        if IATA_RE.match(q):
            return q

        params = {
            "keyword": city_query,
            "subType": "CITY",
            "page[limit]": 10,
        }

        resp = self._request("GET", "/v1/reference-data/locations", params=params)
        if resp.status_code >= 400:
            return None

        data = (resp.json() or {}).get("data", []) or []
        for x in data:
            if x.get("subType") == "CITY" and x.get("iataCode"):
                return x["iataCode"]

        return None

    def _summarize_hotel_offer(self, offer: dict):
        # Amadeus hotel offers payloads vary a bit, so we defensively read fields
        hotel = offer.get("hotel", {}) or {}
        o = (offer.get("offers") or [])
        # Sometimes endpoint returns a single offer object; sometimes list.
        first_offer = o[0] if isinstance(o, list) and o else offer.get("offer") or {}

        price = (first_offer.get("price") or {})
        total = price.get("total")
        currency = price.get("currency")

        # Some payloads provide "variations" / "base" etc — keep total if present.
        check_in = first_offer.get("checkInDate")
        check_out = first_offer.get("checkOutDate")

        return {
            "hotelId": hotel.get("hotelId"),
            "name": hotel.get("name"),
            "rating": hotel.get("rating"),
            "cityCode": hotel.get("cityCode"),
            "address": (hotel.get("address") or {}).get("lines") or [],
            "latitude": (hotel.get("geoCode") or {}).get("latitude"),
            "longitude": (hotel.get("geoCode") or {}).get("longitude"),
            "offer": {
                "id": first_offer.get("id"),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "roomType": (first_offer.get("room") or {}).get("typeEstimated", {}),
                "guests": (first_offer.get("guests") or {}),
                "price": {"total": total, "currency": currency},
            },
        }


    # =========================================================
    # ORIGINAL METHODS (kept) — Transfers
    # =========================================================
    def find_transfers(
        self,
        start_location,
        end_location,
        start_datetime,
        passengers,
        transfer_type="PRIVATE",
        currency="USD",
    ):
        url = f"{self._base_url()}/v1/shopping/transfers"
        params = {
            "startLocationCode": start_location,
            "endLocationCode": end_location,
            "startDateTime": start_datetime,
            "passengers": passengers,
            "transferType": transfer_type,
            "currency": currency,
        }
        response = requests.get(url, headers=self._headers(), params=params)
        return response.json()

    # FIXED: added self
    def create_transfer_booking_order(
        self,
        transfer_offer,
        first_name,
        last_name,
        email,
        phone_country_code,
        phone_number,
    ):
        return {
            "data": {
                "offerId": transfer_offer["id"],
                "passengers": [
                    {
                        "id": "1",
                        "name": {"firstName": first_name, "lastName": last_name},
                        "contact": {
                            "emailAddress": email,
                            "phones": [
                                {
                                    "deviceType": "MOBILE",
                                    "countryCallingCode": phone_country_code,
                                    "number": phone_number,
                                }
                            ],
                        },
                    }
                ],
            }
        }

    def book_transfer(
        self,
        transfer_offer,
        first_name,
        last_name,
        email,
        phone_country_code,
        phone_number,
    ):
        booking_url = f"{self._base_url()}/v1/booking/transfers"
        body = self.create_transfer_booking_order(
            transfer_offer,
            first_name,
            last_name,
            email,
            phone_country_code,
            phone_number,
        )
        response = requests.post(booking_url, headers=self._headers(json_content=True), json=body)
        return response.json()

    # =========================================================
    # ORIGINAL METHODS (kept) — Experiences / POIs
    # =========================================================
    def get_city_coordinates(self, city_name):
        url = f"{self._base_url()}/v1/reference-data/locations/cities"
        params = {"keyword": city_name}
        response = requests.get(url, headers=self._headers(), params=params)
        return response.json()

    def find_activities(self, north, south, east, west, categories=None, limit=20):
        url = f"{self._base_url()}/v1/reference-data/locations/pois/by-square"
        params = {
            "north": north,
            "south": south,
            "east": east,
            "west": west,
            "page[limit]": limit,
        }
        if categories:
            params["categories"] = categories

        response = requests.get(url, headers=self._headers(), params=params)
        return response.json()
