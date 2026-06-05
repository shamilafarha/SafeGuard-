def send_alert(lat, lon):
    if lat is None or lon is None:
        print("Location not available")
        return

    map_link = f"https://www.google.com/maps?q={lat},{lon}"

    print("\n SOS ALERT ")
    print("Location:", map_link)