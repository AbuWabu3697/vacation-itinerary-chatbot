import requests

class HotelsAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def find_hotels(self, dest_lat, dest_lng, radius=5000):
        url = (
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={dest_lat},{dest_lng}&radius={radius}"
            "&type=lodging"
            f"&key={self.api_key}"
        )
        response = requests.get(url).json()
        return response.get("results", [])
