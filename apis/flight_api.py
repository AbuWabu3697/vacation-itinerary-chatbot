import requests
import json

class FlightAPI:

    def __init__(self, api_key):
        self.api_key = api_key

    def search_flights(self, origin, destination, depart_date, return_date, max_price):
        url = "https://www.googleapis.com/qpxExpress/v1/trips/search"
        headers = { "Content-Type": "application/json" }
        payload = {
            "request": {
                "slice": [
                    { "origin": origin, "destination": destination, "date": depart_date },
                    { "origin": destination, "destination": origin, "date": return_date }
                ],
                "passengers": { "adultCount": 1 },
                "maxPrice": f"USD{max_price}",
                "solutions": 5
            }
        }

        response = requests.post(f"{url}?key={self.api_key}", headers=headers, json=payload)
        return response.json()
