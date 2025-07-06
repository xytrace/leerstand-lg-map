import requests
import urllib.parse

USER_AGENT = "LeerstandBot (victor.budinich@gmail.com)"  # Replace with your real contact

def clean_address(addr: str) -> str:
    return f"{addr}, Lüneburg, Deutschland"

async def geocode_address(addr: str) -> tuple[float, float] | tuple[None, None]:
    full_address = clean_address(addr)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": full_address,
        "format": "json",
        "limit": 1,
        "addressdetails": 0
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        results = response.json()

        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print(f"Geocoding failed: {e}")
        return None, None
