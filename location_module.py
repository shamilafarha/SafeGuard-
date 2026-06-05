import requests

# ==============================
# YOUR REAL COORDINATES
# ==============================
# Hardcoded for accuracy — IP-based location is off by 20-30km
MY_LAT = 12.978988870583095
MY_LON = 79.95933015744542

def get_location():
    # Return your real coordinates directly
    # IP-based geolocation was inaccurate by ~26km
    return MY_LAT, MY_LON