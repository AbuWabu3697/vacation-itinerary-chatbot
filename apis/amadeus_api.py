import requests

class AmadeusAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.get_access_token()

    # amadeus requires the user to generate an access token from their client id and client secret before making any requests
    # if the app runs for too long, a new access token needs to be generated
    def get_access_token(self):
        url = "https://api.amadeus.com/v1/security/oauth2/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, params=params)
        if response.json()["state"] != "approved":
            raise Exception("Access token not approved")
        self.access_token = response.json()["access_token"]

    # ==============================================
    # FLIGHTS
    # ==============================================
       
    # uses Amadeus' Flight Offers Search API to find the best flight for a given departure and arrival airport, departure date, and return date
    def find_best_flights(self, origin, destination, departure_date, adults, currency="USD", non_stop=True):

        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            # Optional filters:
            "nonStop": non_stop,
            "currencyCode": currency,
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=params)
        print(response.status_code)
        return response.json()

    # takes a flight_offer json object returned by find_best_flights and confirms its avaiblability and final price
    def confirm_flight_details(self, flight_offer):
        pricing_url = "https://test.api.amadeus.com/v1/shopping/flight-offers/pricing"
        body = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": [
                    flight_offer   # the flight offer object from a previous search
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(pricing_url, headers=headers, json=body)
        return response.json()

    # creates a flight order json object that will be use to book the flight 
    def create_flight_order(priced_flight_offer,
                        traveler_id,
                        first_name,
                        last_name,
                        date_of_birth,
                        gender,
                        email,
                        phone_country_code,
                        phone_number,
                        documents=None):

        traveler = {
            "id": traveler_id,
            "dateOfBirth": date_of_birth,
            "name": {
                "firstName": first_name,
                "lastName": last_name
            },
            "gender": gender,
            "contact": {
                "emailAddress": email,
                "phones": [
                    {
                        "deviceType": "MOBILE",
                        "countryCallingCode": phone_country_code,
                        "number": phone_number
                    }
                ]
            }
        }

        if documents:
            traveler["documents"] = documents

        body = {
            "data": {
                "type": "flight-order",
                "flightOffers": [priced_flight_offer],
                "travelers": [traveler]
            }
        }

        return body

    # takes a flight_offer json object returned by confirm_flight_details and books the flight - this requires the bookers persoanl information
    def book_flight(self, flight_offer,
                        traveler_id,
                        first_name,
                        last_name,
                        date_of_birth,
                        gender,
                        email,
                        phone_country_code,
                        phone_number,
                        documents=None):

        """
        Flight Booking Parameters:
        - priced_flight_offer: dict, the full flight offer returned from Flight Offers Price
        - traveler_id: str, unique ID for this traveler
        - first_name: str
        - last_name: str
        - date_of_birth: str, "YYYY-MM-DD"
        - gender: str, "MALE" or "FEMALE"
        - email: str
        - phone_country_code: str, e.g., "1" for US
        - phone_number: str, e.g., "5551234567"
        - documents: list of dicts, optional, each dict with fields:
            documentType, number, issuanceCountry, expiryDate, nationality, issuanceDate, birthPlace, holder (boolean)
            
            """

        booking_url = "https://test.api.amadeus.com/v1/booking/flight-orders"
        body = self.create_flight_order(flight_offer,
                        traveler_id,
                        first_name,
                        last_name,
                        date_of_birth,
                        gender,
                        email,
                        phone_country_code,
                        phone_number,
                        documents=None)

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(booking_url, headers=headers, json=body)
        return response.json()

    # ==============================================
    # HOTELS
    # ==============================================

    # searches for hotels in a 
    def search_hotels(self, city_code):
        hotels_url = "https://test.api.amadeus.com/v3/shopping/hotels/by-city"

        params = {
            # Either provide cityCode or latitude/longitude
            "cityCode": city_code,  # IATA city code e.g. "NYC"
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(hotels_url, headers=headers, params=params)
        return response.json()

    # takes a list of hotel ids and filters them based on the check_in_date, check_out_date, adults, and room_quantity
    def filter_hotels(self, hotel_ids, check_in_date, check_out_date, adults, room_quantity, price_range):
        hotel_info_url = "https://test.api.amadeus.com/v3/shopping/hotels/"
        params = {
            "hotelIds": hotel_ids,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "roomQuantity": room_quantity,
            "priceRange": price_range
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        response = requests.get(hotel_info_url, headers=headers, params=params)
        return response.json()

    def create_hotel_booking_order(offer_id,
                        guest_id,
                        title,
                        first_name,
                        last_name,
                        email,
                        phone,
                        card_vendor_code,
                        card_number,
                        card_expiry_date):
        

        body = {
            "data": {
                "offerId": offer_id,
                "guests": [
                    {
                        "id": guest_id,
                        "name": {
                            "title": title,
                            "firstName": first_name,
                            "lastName": last_name
                        },
                        "contact": {
                            "phone": phone,
                            "email": email
                        }
                    }
                ],
                "payments": [
                    {
                        "id": "1",
                        "method": "creditCard",
                        "card": {
                            "vendorCode": card_vendor_code,
                            "cardNumber": card_number,
                            "expiryDate": card_expiry_date
                        }
                    }
                ]
            }
        }
        return body
    

    """
    Books a hotel chosen by grok

        Parameters required for hotel booking:
        - offer_id (str): offerId from Hotel Offers Search
        - guest_id (str): unique guest identifier (e.g. "1")
        - title (str): MR, MS, MRS, etc.
        - first_name (str)
        - last_name (str)
        - email (str)
        - phone (str): full phone number with country code
        - card_vendor_code (str): VI, MC, AX, etc.
        - card_number (str): credit card number
        - card_expiry_date (str): YYYY-MM
        """
    def book_hotel(self, offer_id,
                                    guest_id,
                                    title,
                                    first_name,
                                    last_name,
                                    email,
                                    phone,
                                    card_vendor_code,
                                    card_number,
                                    card_expiry_date):

        booking_url = "https://test.api.amadeus.com/v1/booking/hotel-bookings"
        

        body = self.create_hotel_booking_order(offer_id,
                                    guest_id,
                                    title,
                                    first_name,
                                    last_name,
                                    email,
                                    phone,
                                    card_vendor_code,
                                    card_number,
                                    card_expiry_date)

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(booking_url, headers=headers, json=body)
        return response.json()


    # ==============================================
    # CAR RENTALS & TRANSFERS
    # ==============================================

    def find_transfers(self,
            start_location,
            end_location,
            start_datetime,
            passengers,
            transfer_type="PRIVATE",
            currency="USD"
            ):

        url = "https://test.api.amadeus.com/v1/shopping/transfers"

        params = {
            "startLocationCode": start_location,
            "endLocationCode": end_location,
            "startDateTime": start_datetime,
            "passengers": passengers,
            "transferType": transfer_type,
            "currency": currency
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=params)
        print(response.status_code)
        return response.json()

    def create_transfer_booking_order(transfer_offer,
                                        first_name,
                                        last_name,
                                        email,
                                        phone_country_code,
                                        phone_number
                                    ):
        body = {
            "data": {
            "offerId": transfer_offer["id"],
            "passengers": [
                {
                    "id": "1",
                    "name": {
                        "firstName": first_name,
                        "lastName": last_name
                    },
                    "contact": {
                        "emailAddress": email,
                        "phones": [
                            {
                                "deviceType": "MOBILE",
                                "countryCallingCode": phone_country_code,
                                "number": phone_number
                            }
                        ]
                    }
                }
            ]
            }
        }
        return body
    
    """
    Books a transfer chosen by grok

        Parameters required for transfer booking:
        - transfer_offer (dict): transfer offer from Transfer Offers Search
        - first_name (str)
        - last_name (str)
        - email (str)
        - phone_country_code (str): e.g., "1" for US
        - phone_number (str): e.g., "5551234567"
    """
    def book_transfer(self, transfer_offer,
                            first_name,
                            last_name,
                            email,
                            phone_country_code,
                            phone_number
                        ):
        booking_url = "https://test.api.amadeus.com/v1/booking/transfers"
        body = self.create_transfer_booking_order(transfer_offer,
                            first_name,
                            last_name,
                            email,
                            phone_country_code,
                            phone_number)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(booking_url, headers=headers, json=body)
        return response.json()

    #==============================================
    # EXPERIENCES
    #==============================================

    # gets longitude and latitude for a given city
    def get_city_coordinates(self, city_name):
        url = "https://test.api.amadeus.com/v1/reference-data/locations/cities"
        params = {
            "keyword": city_name
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"}

        response = requests.get(url, headers=headers, params=params)
        return response.json()


    # finds activities in a given area by longitude and latitude
    def find_activities(self, north, south, east, west, categories=None, limit=20):
        url = "https://test.api.amadeus.com/v1/reference-data/locations/pois/by-square"

        params = {
            "north": north,
            "south": south,
            "east": east,
            "west": west,
            "page[limit]": limit
        }

        if categories:
            params["categories"] = categories

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=params)
        print(response.status_code)
        return response.json()