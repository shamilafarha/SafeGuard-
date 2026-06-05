import requests

def get_gps_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        
        # 1. Grab the latitude and longitude
        location = data['loc'].split(',')
        lat, lon = location[0], location[1]
        
        # 2. Grab the city name (NEW)
        city_name = data.get('city', 'Unknown City')
        
        return lat, lon, city_name
    except Exception:
        return "0.000", "0.000", "Unknown Location"

def send_sos_alert(lat, lon, city):
    # Now 'city' is passed in and can be used!
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
    
    # We add the city name to the text to make it clearer for the Guardian
    message = f" EMERGENCY: Threat detected in {city}. Location: {maps_link}"
    
    print(f"SMS SENT to Family & Police: {message}")