 
from __future__ import annotations
import os
import math
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from functools import lru_cache
from urllib.parse import quote_plus
import html
import base64
import pathlib
import traceback
import streamlit as st

# Load environment variables
load_dotenv()

# --- API keys ---
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID") or ""
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET") or ""
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY") or ""
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY") or ""
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") or ""

# small delay to be gentle with rate limits
API_CALL_DELAY = 0.35

# --- Helper functions (kept consistent with your original code) ---
def safe_json(resp: requests.Response) -> dict:
    try:
        resp.raise_for_status()
        return resp.json()
    except Exception:
        try:
            return resp.json()
        except Exception:
            return {}

def gmaps_search_link(text: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(text)}"

def airport_map_link(iata: str) -> str:
    if not iata:
        return ""
    return gmaps_search_link(f"{iata} airport")

# Airline mapping (original mapping kept)
AIRLINE_NAMES = {
    "EK": "Emirates", "QR": "Qatar Airways", "EY": "Etihad Airways", "TK": "Turkish Airlines",
    "SQ": "Singapore Airlines", "CX": "Cathay Pacific", "QF": "Qantas", "BA": "British Airways",
    "AF": "Air France", "LH": "Lufthansa", "KL": "KLM Royal Dutch Airlines", "IB": "Iberia",
    "AZ": "ITA Airways", "OS": "Austrian Airlines", "LX": "SWISS", "SN": "Brussels Airlines",
    "SK": "SAS Scandinavian Airlines", "AY": "Finnair", "TP": "TAP Air Portugal", "LO": "LOT Polish Airlines",
    "OK": "Czech Airlines", "OA": "Olympic Air", "A3": "Aegean Airlines",
    "AA": "American Airlines", "DL": "Delta Air Lines", "UA": "United Airlines", "AC": "Air Canada",
    "WS": "WestJet", "AS": "Alaska Airlines", "B6": "JetBlue", "F9": "Frontier Airlines",
    "NK": "Spirit Airlines", "WN": "Southwest Airlines", "HA": "Hawaiian Airlines", "PD": "Porter Airlines",
    "SV": "Saudia", "G9": "Air Arabia", "6E": "IndiGo", "XY": "flynas", "FZ": "flydubai",
    "RJ": "Royal Jordanian", "KU": "Kuwait Airways", "ME": "MEA Middle East Airlines",
    "WY": "Oman Air", "GF": "Gulf Air", "J9": "Jazeera Airways", "AI": "Air India",
    "IX": "Air India Express", "UK": "Vistara", "SG": "SpiceJet", "QP": "Akasa Air",
    "G8": "Go First", "S2": "JetKonnect", "BZ": "Blue Dart Aviation", "UL": "SriLankan Airlines",
    "BG": "Biman Bangladesh Airlines", "NH": "All Nippon Airways", "JL": "Japan Airlines",
    "KE": "Korean Air", "OZ": "Asiana Airlines", "BR": "EVA Air", "CI": "China Airlines",
    "MU": "China Eastern Airlines", "CZ": "China Southern Airlines", "CA": "Air China",
    "HU": "Hainan Airlines", "HO": "Juneyao Air", "MF": "XiamenAir", "Z2": "Philippines AirAsia",
    "PR": "Philippine Airlines", "5J": "Cebu Pacific", "VN": "Vietnam Airlines", "VJ": "VietJet Air",
    "FD": "Thai AirAsia", "TG": "Thai Airways", "TR": "Scoot", "MM": "Peach Aviation",
    "JW": "Vanilla Air", "NZ": "Air New Zealand", "JQ": "Jetstar Airways", "VA": "Virgin Australia",
    "PX": "Air Niugini", "ET": "Ethiopian Airlines", "KQ": "Kenya Airways", "MS": "EgyptAir",
    "AT": "Royal Air Maroc", "TU": "Tunisair", "AH": "Air Algérie", "SA": "South African Airways",
    "KM": "Air Malta", "LA": "LATAM Airlines", "AV": "Avianca", "AM": "Aeroméxico",
    "CM": "Copa Airlines", "AR": "Aerolineas Argentinas", "G3": "GOL Linhas Aéreas",
    "AD": "Azul Brazilian Airlines", "4M": "LATAM Argentina", "H2": "Sky Airline",
    "FR": "Ryanair", "U2": "easyJet", "VY": "Vueling", "W6": "Wizz Air", "TO": "Transavia France",
    "HV": "Transavia", "DY": "Norwegian Air Shuttle", "LS": "Jet2.com", "EI": "Aer Lingus",
    "ACV": "Air Calédonie", "PC": "Pegasus Airlines", "PS": "Ukraine International Airlines",
    "MF": "XiamenAir", "XY": "flynas", "SV": "Saudia", "EW": "Eurowings", "EN": "Air Dolomiti",
    "BT": "airBaltic", "RO": "TAROM", "UX": "Air Europa", "HY": "Uzbekistan Airways",
    "SU": "Aeroflot", "MH": "Malaysia Airlines", "BI": "Royal Brunei Airlines", "GA": "Garuda Indonesia",
    "3K": "Jetstar Asia", "ID": "Batik Air", "OD": "Batik Air Malaysia", "FY": "Firefly",
    "AK": "AirAsia", "D7": "AirAsia X", "QZ": "Indonesia AirAsia", "I5": "Indonesia AirAsia X",
}

def valid_image_url(url: str, timeout: int = 6) -> bool:
    if not url:
        return False
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(url, stream=True, timeout=timeout)
        if r.status_code == 200 and 'image' in (r.headers.get('content-type') or ''):
            return True
    except Exception:
        pass
    return False

def unsplash_images(query: str, count: int = 3) -> List[str]:
    if not UNSPLASH_ACCESS_KEY:
        return []
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": count, "client_id": UNSPLASH_ACCESS_KEY},
            timeout=10,
        )
        j = safe_json(r)
        out = []
        for item in j.get("results", [])[:count]:
            url = item.get("urls", {}).get("regular")
            if url:
                out.append(url)
        return out
    except Exception:
        return []

def unsplash_first(query: str) -> str:
    imgs = unsplash_images(query, 1)
    return imgs[0] if imgs else ""

@lru_cache(maxsize=128)
def get_coords(city: str) -> Optional[Dict[str, float]]:
    if not OPENWEATHERMAP_API_KEY:
        return None
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": OPENWEATHERMAP_API_KEY},
            timeout=10,
        )
        j = safe_json(r)
        if not j:
            return None
        return {"lat": float(j[0]["lat"]), "lon": float(j[0]["lon"]) }
    except Exception:
        return None

def fetch_current_weather(lat: float, lon: float) -> Optional[Dict]:
    """
    Fetch current weather (used as fallback if forecast lacks days).
    """
    if not OPENWEATHERMAP_API_KEY:
        return None
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHERMAP_API_KEY},
            timeout=10,
        )
        j = safe_json(r)
        if not j:
            return None
        temp = j.get("main", {}).get("temp")
        desc = (j.get("weather") or [{}])[0].get("description", "")
        dt = j.get("dt")
        date_str = datetime.utcfromtimestamp(dt).date().isoformat() if dt else datetime.utcnow().date().isoformat()
        return {"date": date_str, "temp_day": int(round(temp)) if temp is not None else "-", "desc": (desc or "").capitalize()}
    except Exception:
        return None

def fetch_openweather_daily(lat: float, lon: float, start_date: str, days: int) -> List[Dict]:
    """
    Robust daily forecast aggregator using OpenWeather 5-day / 3-hour forecast endpoint.
    - start_date: ISO date string (YYYY-MM-DD)
    - days: number of days requested (will be capped sensibly)
    Returns list of dicts: {"date": "YYYY-MM-DD", "temp_day": int or "-", "desc": "Mostly clear"}
    """
    if not OPENWEATHERMAP_API_KEY:
        return []
    # Cap days to a reasonable max; OpenWeather 5-day forecast gives ~5 days of 3-hour data.
    MAX_FORECAST_DAYS = 7  # allow up to 7 days but will fallback if unavailable
    days = max(1, min(days, MAX_FORECAST_DAYS))
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHERMAP_API_KEY},
            timeout=15,
        )
        j = safe_json(r)
        lst = j.get("list", [])
        buckets: Dict[str, List[Dict]] = {}
        for item in lst:
            dt_txt = item.get("dt_txt", "")
            if not dt_txt:
                continue
            day = dt_txt.split(" ")[0]
            buckets.setdefault(day, []).append(item)

        out: List[Dict] = []
        # parse start_date safely
        try:
            start = datetime.fromisoformat(start_date).date()
        except Exception:
            start = datetime.utcnow().date()

        # Build per-day summaries using available buckets; fallback to current weather per missing day
        for i in range(days):
            d = (start + timedelta(days=i)).isoformat()
            items = buckets.get(d, [])
            if items:
                temps = [it.get("main", {}).get("temp") for it in items if it.get("main", {}).get("temp") is not None]
                avg = int(round(sum(temps) / len(temps))) if temps else "-"
                descs = [it.get("weather", [{}])[0].get("description", "") for it in items]
                desc = ""
                if descs:
                    # choose the most frequent description
                    try:
                        desc = max(set(descs), key=descs.count).capitalize()
                    except Exception:
                        desc = (descs[0] or "").capitalize()
                out.append({"date": d, "temp_day": avg, "desc": desc})
            else:
                # no forecast data for this day — try to fetch current weather and use it as a proxy
                cur = fetch_current_weather(lat, lon)
                if cur:
                    # if current weather corresponds to the requested day, use it
                    if cur.get("date") == d:
                        out.append(cur)
                    else:
                        # still use current weather as proxy but mark it as approximate
                        entry = {"date": d, "temp_day": cur.get("temp_day", "-"), "desc": (cur.get("desc","") + " (approx)").strip()}
                        out.append(entry)
                else:
                    out.append({"date": d, "temp_day": "-", "desc": "No data"})
        return out
    except Exception:
        # Last-resort fallback: try current weather once and repeat it for requested days
        try:
            cur = fetch_current_weather(lat, lon)
            if not cur:
                return []
            res = []
            try:
                start = datetime.fromisoformat(start_date).date()
            except Exception:
                start = datetime.utcnow().date()
            for i in range(days):
                d = (start + timedelta(days=i)).isoformat()
                entry = {"date": d, "temp_day": cur.get("temp_day", "-"), "desc": (cur.get("desc","") + " (approx)").strip()}
                res.append(entry)
            return res
        except Exception:
            return []

@lru_cache(maxsize=8)
def amadeus_token() -> Optional[str]:
    if not (AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET):
        return None
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.post(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": AMADEUS_CLIENT_ID,
                "client_secret": AMADEUS_CLIENT_SECRET,
            },
            timeout=12,
        )
        j = safe_json(r)
        return j.get("access_token")
    except Exception:
        return None

def resolve_iata(city: str, token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://test.api.amadeus.com/v1/reference-data/locations",
            headers={"Authorization": f"Bearer {token}"},
            params={"keyword": city, "subType": "CITY"},
            timeout=12,
        )
        j = safe_json(r)
        for item in j.get("data", []):
            code = item.get("iataCode")
            if code:
                return code
    except Exception:
        pass
    return None

def amadeus_airline_lookup(code: str, token: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code_up = code.strip().upper()
    if code_up in AIRLINE_NAMES:
        return AIRLINE_NAMES[code_up]
    if not token:
        return code_up
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://test.api.amadeus.com/v1/reference-data/airlines",
            headers={"Authorization": f"Bearer {token}"},
            params={"airlineCodes": code_up},
            timeout=10,
        )
        j = safe_json(r)
        data = j.get("data", []) or []
        if data:
            name = data[0].get("commonName") or data[0].get("name")
            if name:
                AIRLINE_NAMES[code_up] = name
                return name
    except Exception:
        pass
    return code_up

def amadeus_search_flights(origin_iata: str, dest_iata: str, dep_date: str,
                           return_date: Optional[str] = None, adults: int = 1,
                           max_results: int = 5, currency: str = "INR") -> List[Dict]:
    token = amadeus_token()
    if not token:
        return []
    try:
        time.sleep(API_CALL_DELAY)
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin_iata[:3].upper(),
            "destinationLocationCode": dest_iata[:3].upper(),
            "departureDate": dep_date,
            "adults": adults,
            "currencyCode": currency,
            "max": 50,
        }
        if return_date:
            params["returnDate"] = return_date
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=20)
        j = safe_json(r)
        offers = j.get("data", []) or []
        best_by_airline: Dict[str, Dict] = {}
        for off in offers:
            try:
                price = float(off.get("price", {}).get("total", math.inf))
                airline_code = (off.get("validatingAirlineCodes") or ["?"])[0]
                if airline_code not in best_by_airline or price < float(best_by_airline[airline_code]["price"]):
                    best_by_airline[airline_code] = {"offer": off, "price": price}
            except Exception:
                continue
        sorted_offers = sorted(best_by_airline.items(), key=lambda kv: float(kv[1]["price"]))[:max_results]
        results = []
        for airline_code, payload in sorted_offers:
            off = payload["offer"]
            price_val = float(off.get("price", {}).get("total", 0))
            itinerary = off.get("itineraries", [])[0] if off.get("itineraries") else {}
            duration = itinerary.get("duration")
            segments = itinerary.get("segments", [])
            stops = f"{len(segments)-1} stop(s)" if len(segments) > 1 else "Direct"
            dep_arr_times = []
            seg_airports = []
            for seg in segments:
                dep = seg.get("departure").get("at")
                arr = seg.get("arrival").get("at")
                dep_code = seg["departure"].get("iataCode", "")
                arr_code = seg["arrival"].get("iataCode", "")
                dep_arr_times.append(f"{dep} → {arr}")
                seg_airports.append({"dep": dep_code, "arr": arr_code})
            full_name = amadeus_airline_lookup(airline_code, token)
            results.append({
                "airline": full_name or airline_code,
                "airline_code": airline_code,
                "price": price_val,
                "currency": currency,
                "duration": duration,
                "stops": stops,
                "times": dep_arr_times,
                "airports": seg_airports,
            })
        return results
    except Exception:
        return []

def hotellook_hotels(city: str, nights: int, people: int, count: int = 5) -> List[Dict]:
    if not RAPIDAPI_KEY:
        return []
    try:
        time.sleep(API_CALL_DELAY)
        url = "https://hotels4.p.rapidapi.com/locations/v3/search"
        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "hotels4.p.rapidapi.com"}
        params = {"q": city, "locale": "en_US"}
        r = requests.get(url, headers=headers, params=params, timeout=12)
        j = safe_json(r)
        entities = (j.get("sr", []) or [])[:count]
        out = []
        for ent in entities:
            name = ent.get("regionNames", {}).get("shortName") or ent.get("hotelName") or f"{city} Hotel"
            img = unsplash_first(f"{name} {city} hotel")
            approx_price_inr = int(6000 + (people * 1000))
            coords = ent.get("coord") or ent.get("coordinates") or {}
            lat = coords.get("lat")
            lon = coords.get("lon")
            if lat and lon:
                map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            else:
                map_url = gmaps_search_link(f"{name} {city}")
            out.append({"name": name, "price_inr": approx_price_inr, "image": img or "", "map": map_url})
        return out
    except Exception:
        return []

def hotel_suggestions(city: str, per_person_per_night: float, nights: int, people: int, count: int = 5) -> List[Dict]:
    hotels = hotellook_hotels(city, nights, people, count=count)
    if hotels:
        unique = []
        seen = set()
        for h in hotels:
            if h["name"] in seen:
                continue
            seen.add(h["name"])
            if h.get("image") and not valid_image_url(h["image"]):
                h["image"] = unsplash_first(f"{h['name']} {city} hotel")
            unique.append(h)
        return unique[:count]
    imgs = unsplash_images(f"{city} hotel", count=count)
    base = max(2500, int(per_person_per_night))
    multipliers = [0.6, 0.9, 1.1, 1.6, 2.3]
    labels = ["Budget", "Comfort", "Standard", "Premium", "Luxury"]
    out = []
    for i in range(count):
        m = multipliers[i] if i < len(multipliers) else (1.0 + i * 0.25)
        price = int(base * m * max(1, people))
        name = f"{city} {labels[i] if i < len(labels) else f'Hotel {i+1}'}"
        img = imgs[i] if i < len(imgs) else unsplash_first(f"{name} {city} hotel")
        if img and not valid_image_url(img):
            img = ""
        map_url = gmaps_search_link(f"{name} {city}")
        out.append({"name": name, "price_inr": price, "image": img or "", "map": map_url})
    return out

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def overpass_query(query: str) -> dict:
    try:
        time.sleep(API_CALL_DELAY)
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=25)
        return safe_json(r)
    except Exception:
        return {}

def get_bbox_from_coords(lat: float, lon: float, km: float = 8.0) -> Tuple[float, float, float, float]:
    import math as _math
    deg_lat = km / 110.574
    deg_lon = km / (111.320 * max(0.1, _math.cos(_math.radians(lat))))
    return (lat - deg_lat, lon - deg_lon, lat + deg_lat, lon + deg_lon)

def build_poi(city: str, name: str, lat: Optional[float], lon: Optional[float]) -> Dict:
    img = unsplash_first(f"{name} {city}")
    if img and not valid_image_url(img):
        img = ""
    if lat is not None and lon is not None:
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    else:
        map_url = gmaps_search_link(f"{name} {city}")
    return {"name": name, "image": img, "map": map_url}

def attractions_osm(city: str, lat: float, lon: float, count: int = 5) -> List[Dict]:
    south, west, north, east = get_bbox_from_coords(lat, lon, km=10)
    q = f"""
    [out:json][timeout:25];
    (
      node["tourism"="attraction"]({south},{west},{north},{east});
      way["tourism"="attraction"]({south},{west},{north},{east});
      node["historic"]({south},{west},{north},{east});
      node["landmark"]({south},{west},{north},{east});
    );
    out center 50;
    """
    j = overpass_query(q)
    elements = j.get("elements", [])
    named = [e for e in elements if e.get("tags", {}).get("name")]
    def score(e):
        t = e.get("tags", {})
        s = 0
        if e.get("type") == "way": s += 2
        if "wikidata" in t or "wikipedia" in t: s += 3
        if "tourism" in t: s += 1
        return s
    named.sort(key=score, reverse=True)
    out = []
    seen = set()
    for e in named:
        if len(out) >= count:
            break
        t = e.get("tags", {})
        name = t.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        center = e.get("center") or {}
        lat0 = center.get("lat") or e.get("lat")
        lon0 = center.get("lon") or e.get("lon")
        out.append(build_poi(city, name, lat0, lon0))
    if not out:
        imgs = unsplash_images(city, count=count)
        for i in range(count):
            nm = f"{city} Attraction {i+1}"
            map_url = gmaps_search_link(f"{nm} {city}")
            out.append({"name": nm, "image": imgs[i] if i < len(imgs) else "", "map": map_url})
    return out

def restaurants_osm(city: str, lat: float, lon: float, count: int = 5) -> List[Dict]:
    south, west, north, east = get_bbox_from_coords(lat, lon, km=8)
    q = f"""
    [out:json][timeout:25];
    node["amenity"~"restaurant|cafe|fast_food"]({south},{west},{north},{east});
    out 100;
    """
    j = overpass_query(q)
    elements = j.get("elements", [])
    named = [e for e in elements if e.get("tags", {}).get("name")]
    out = []
    seen = set()
    for e in named:
        if len(out) >= count:
            break
        name = e.get("tags", {}).get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        if e.get("lat") and e.get("lon"):
            map_url = f"https://www.google.com/maps/search/?api=1&query={e.get('lat')},{e.get('lon')}"
        else:
            map_url = gmaps_search_link(f"{name} {city}")
        img = unsplash_first(f"{name} {city}")
        if img and not valid_image_url(img):
            img = ""
        out.append({"name": name, "image": img, "map": map_url})
    if not out:
        for i in range(count):
            nm = f"{city} Restaurant {i+1}"
            out.append({"name": nm, "image": "", "map": gmaps_search_link(f"{nm} {city}" )})
    return out

def shopping_spots_osm(city: str, lat: float, lon: float, count: int = 5) -> List[Dict]:
    south, west, north, east = get_bbox_from_coords(lat, lon, km=8)
    q = f"""
    [out:json][timeout:25];
    (
      node["shop"~"mall|department_store|supermarket|boutique"]({south},{west},{north},{east});
      way["shop"~"mall|department_store"]({south},{west},{north},{east});
    );
    out center 100;
    """
    j = overpass_query(q)
    elements = j.get("elements", [])
    named = [e for e in elements if e.get("tags", {}).get("name")]
    out = []
    seen = set()
    for e in named:
        if len(out) >= count:
            break
        name = e.get("tags", {}).get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        center = e.get("center") or {}
        lat0 = center.get("lat") or e.get("lat")
        lon0 = center.get("lon") or e.get("lon")
        if lat0 and lon0:
            map_url = f"https://www.google.com/maps/search/?api=1&query={lat0},{lon0}"
        else:
            map_url = gmaps_search_link(f"{name} {city}")
        img = unsplash_first(f"{name} {city}")
        if img and not valid_image_url(img):
            img = ""
        out.append({"name": name, "image": img, "map": map_url})
    if not out:
        for i in range(count):
            nm = f"{city} Shopping {i+1}"
            out.append({"name": nm, "image": "", "map": gmaps_search_link(f"{nm} {city}" )})
    return out

def wikivoyage_top_places(city: str, count: int = 5) -> List[Dict]:
    try:
        s = f"{city}"
        time.sleep(API_CALL_DELAY)
        r = requests.get(
            "https://en.wikivoyage.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": s, "format": "json", "srlimit": count},
            timeout=10,
        )
        j = safe_json(r)
        hits = j.get("query", {}).get("search", [])
        out = []
        for h in hits[:count]:
            title = h.get("title")
            time.sleep(API_CALL_DELAY)
            r2 = requests.get(
                "https://en.wikivoyage.org/w/api.php",
                params={"action": "query", "prop": "extracts", "exintro": 1, "titles": title, "format": "json"},
                timeout=10,
            )
            j2 = safe_json(r2)
            extract = ""
            for _, pdata in j2.get("query", {}).get("pages", {}).items():
                extract = pdata.get("extract", "")
            img = unsplash_first(f"{title} {city}")
            if img and not valid_image_url(img):
                img = ""
            map_url = gmaps_search_link(f"{title} {city}")
            out.append({"name": title, "image": img or "", "map": map_url, "desc": extract})
        return out
    except Exception:
        return []

def packing_tips(temp_c: Optional[float], desc: str, duration_days: int, place_type: Optional[str] = None) -> str:
    tips = []
    if isinstance(temp_c, (int, float)):
        if temp_c <= 5:
            tips.append("Heavy coat, thermal layers, gloves")
        elif temp_c <= 15:
            tips.append("Warm jacket and layers")
        elif temp_c <= 25:
            tips.append("Light jacket or sweater")
        else:
            tips.append("Light/casual clothes, breathable fabrics")
    else:
        tips.append("Layered clothing")
    if "rain" in (desc or "").lower():
        tips.append("Umbrella or raincoat")
    if "snow" in (desc or "").lower():
        tips.append("Warm boots and waterproof outerwear")
    if duration_days >= 7:
        tips.append("Pack extra clothing or plan for laundry")
    if place_type and "beach" in (place_type or "").lower():
        tips.append("Swimwear and beach towel")
    return ", ".join(tips)

def unique_places(places: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for p in places:
        name = (p.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(p)
    return out

def budget_breakdown(flights: List[Dict], hotels: List[Dict], duration_days: int, people: int, currency: str, 
                     total_budget_inr: int, hotel_index: int = 2, safety_buffer_pct: float = 0.08) -> Dict:
    effective_budget = int(total_budget_inr * (1.0 - safety_buffer_pct))
    flight_pp = 0.0
    if flights:
        try:
            flight_pp = float(flights[0]["price"])
        except Exception:
            flight_pp = 0.0
    if hotels:
        idx = max(0, min(hotel_index, len(hotels) - 1))
        hotel_per_night_inr = hotels[idx]["price_inr"]
        selected_hotel_name = hotels[idx].get("name", "")
    else:
        idx = 0
        hotel_per_night_inr = 6000
        selected_hotel_name = "Default Hotel"
    nights = max(1, duration_days - 1)
    hotel_total_inr = int(hotel_per_night_inr * nights)
    food_inr = int(1200 * people * duration_days)
    local_inr = int(800 * people * duration_days)
    sights_inr = int(1500 * people)
    buffer_inr = int(0.08 * (hotel_total_inr + food_inr + local_inr + sights_inr))
    subtotal_inr = hotel_total_inr + food_inr + local_inr + sights_inr + buffer_inr
    flight_pp_inr = int(round(flight_pp))
    flights_total_inr = int(flight_pp_inr * people)
    grand_total_inr = int(flights_total_inr + subtotal_inr)
    fits_in_effective = grand_total_inr <= effective_budget
    return {
        "flight_per_person": flight_pp,
        "flight_currency": currency,
        "flight_per_person_inr": int(flight_pp_inr),
        "flights_total_inr": flights_total_inr,
        "hotel_per_night_inr": int(hotel_per_night_inr),
        "hotel_total_inr": int(hotel_total_inr),
        "food_inr": int(food_inr),
        "local_inr": int(local_inr),
        "sights_inr": int(sights_inr),
        "buffer_inr": int(buffer_inr),
        "grand_total_inr": int(grand_total_inr),
        "subtotal_inr": int(subtotal_inr),
        "effective_budget_inr": effective_budget,
        "fits_in_effective": fits_in_effective,
        "selected_hotel_index": idx,
        "selected_hotel_name": selected_hotel_name,
    }
    # Export HTML summary (download & open)
def build_html_summary(meta: Dict) -> str:
    to_city = html.escape(meta.get("to_city",""))
    from_city = html.escape(meta.get("from_city",""))
    dep_date = html.escape(meta.get("dep_date",""))
    return_date = html.escape(meta.get("return_date",""))
    people = meta.get("people",1)
    flights = meta.get("flights",[])
    hotels = meta.get("hotels",[])
    places = meta.get("places",[])
    restaurants = meta.get("restaurants",[])
    shops = meta.get("shops",[])
    weather = meta.get("weather",[])
    imgs = meta.get("images", [])
    bd = meta.get("bd", {})

    css = """
    :root{--bg1:#071026;--accent1:#b89252;--accent2:#7c3aed;--muted:#94a3b8}
    body{margin:0;font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;background:linear-gradient(135deg,#041226,#01111a);color:#e6eef8}
    .wrap{max-width:1100px;margin:36px auto;padding:28px}
    .hero{display:flex;gap:20px;align-items:center}
    .title{flex:1}
    .title h1{margin:0;font-size:28px}
    .meta{color:var(--muted);margin-top:8px}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:22px}
    .card{background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));border-radius:14px;padding:16px;box-shadow:0 8px 30px rgba(2,6,23,0.6);border:1px solid rgba(255,255,255,0.03)}
    .img{height:140px;border-radius:10px;overflow:hidden;background:#071025;display:flex;align-items:center;justify-content:center}
    .img img{width:100%;height:100%;object-fit:cover}
    .small{font-size:13px;color:var(--muted)}
    .btn{display:inline-block;padding:8px 12px;border-radius:10px;background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#081226;text-decoration:none;font-weight:700}
    .footer{margin-top:28px;color:var(--muted);font-size:13px;text-align:center}
    @media(max-width:980px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:640px){.grid{grid-template-columns:1fr}}
    """
    def flight_card(f):
        airline = html.escape(str(f.get("airline","-")))
        price = html.escape(str(int(round(f.get("price",0)))) + " " + f.get("currency",""))
        dur = html.escape(str(f.get("duration","-")))
        segs = "<br>".join(html.escape(s) for s in f.get("segments",[]))
        return f"<div class='card'><h3>{airline}</h3><div class='small'><strong>{price}</strong></div><div class='small'>{dur}</div><div class='small'>{segs}</div></div>"
    def hotel_card(h):
        name = html.escape(h.get("name","")); price = f"{h.get('price_inr',0):,} INR/night"; img = h.get("image",""); map_url = h.get("map","")
        img_tag = f"<div class='img'><img src='{html.escape(img)}' alt='{name}'/></div>" if img else "<div class='img'><div class='small'>No image</div></div>"
        return f"<div class='card'>{img_tag}<h3 style='margin-top:10px'>{name}</h3><div class='small row'><div>Price</div><div><strong>{price}</strong></div></div><div style='margin-top:10px'><a class='btn' href='{html.escape(map_url)}' target='_blank'>Open map</a></div></div>"
    def place_card(p):
        name = html.escape(p.get("name","")); desc = p.get("desc",""); desc_snip = html.escape((desc[:220]+"...") if desc and len(desc)>220 else desc or ""); img = p.get("image",""); map_url = p.get("map","")
        img_tag = f"<div class='img'><img src='{html.escape(img)}' alt='{name}'/></div>" if img else "<div class='img'><div class='small'>No image</div></div>"
        return f"<div class='card'>{img_tag}<h3 style='margin-top:10px'>{name}</h3><div class='small' style='margin-top:6px'>{desc_snip}</div><div style='margin-top:10px'><a class='btn' href='{html.escape(map_url)}' target='_blank'>View on map</a></div></div>"

    flights_html = "".join(flight_card(f) for f in flights[:4]) if flights else "<div class='card'><h3>No flights</h3></div>"
    hotels_html = "".join(hotel_card(h) for h in hotels[:6]) if hotels else "<div class='card'><h3>No hotels</h3></div>"
    places_html = "".join(place_card(p) for p in places[:6]) if places else "<div class='card'><h3>No attractions</h3></div>"
    weather_html = "".join(f"<div class='card'><h3>{html.escape(w.get('date','-'))}</h3><div class='small'>{html.escape(str(w.get('temp_day','-')))}°C — {html.escape(w.get('desc','-'))}</div></div>" for w in weather) or "<div class='card'><h3>No forecast</h3></div>"
    rest_html = "".join(hotel_card(r) if r.get('image') else f"<div class='card'><h3>{html.escape(r.get('name','-'))}</h3><div class='small'><a href='{html.escape(r.get('map',''))}'>Open map</a></div></div>" for r in restaurants[:6]) if restaurants else "<div class='card'><h3>No restaurants</h3></div>"
    shops_html = "".join(hotel_card(s) if s.get('image') else f"<div class='card'><h3>{html.escape(s.get('name','-'))}</h3><div class='small'><a href='{html.escape(s.get('map',''))}'>Open map</a></div></div>" for s in shops[:6]) if shops else "<div class='card'><h3>No shopping</h3></div>"

    header_img = imgs[0] if imgs else ""
    header_bg = f"background-image:url('{html.escape(header_img)}');background-size:cover;background-position:center;border-radius:12px;padding:18px;" if header_img else "background:linear-gradient(90deg,var(--accent1),var(--accent2));border-radius:12px;padding:18px;"

    grand = f"{bd.get('grand_total_inr',0):,} INR"
    budget_html = f"<div class='card'><h3>Budget</h3><div class='small'>Grand Total: <strong>{grand}</strong></div><div class='small'>Flights: {bd.get('flights_total_inr',0):,} INR</div><div class='small'>Hotels: {bd.get('hotel_total_inr',0):,} INR</div></div>"

    html_doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Trip to {to_city}</title><style>{css}</style></head><body>
    <div class='wrap'>
      <div class='hero'>
        <div class='title'><h1>✨ {to_city} — Luxury Travel Concierge</h1><div class='meta'>{from_city} • {dep_date} → {return_date} • {people} people</div></div>
        <div style="{header_bg}width:220px;height:120px;flex-shrink:0;border-radius:12px">{(f"<img src='{html.escape(header_img)}' style='width:100%;height:100%;object-fit:cover;border-radius:12px'/>") if header_img else ""}</div>
      </div>

      <h2>Flights</h2><div class='grid'>{flights_html}</div>
      <h2>Hotels</h2><div class='grid'>{hotels_html}</div>
      <h2>Weather</h2><div class='grid'>{weather_html}</div>
      <h2>Top Attractions</h2><div class='grid'>{places_html}</div>
      <h2>Restaurants</h2><div class='grid'>{rest_html}</div>
      <h2>Shopping</h2><div class='grid'>{shops_html}</div>
      <h2>Budget</h2><div class='grid'>{budget_html}</div>
      <div class='footer'>Generated by Luxury Travel Concierge • {datetime.now().isoformat()}</div>
    </div></body></html>"""
    return html_doc
# -------------------------------
# Streamlit UI (single-file app)
# -------------------------------
st.set_page_config(page_title="Luxury Travel Concierge", page_icon="🌐", layout="wide")

# Basic top-of-page content so Streamlit never shows a blank screen
st.markdown(
    """
    <style>
    :root{--gold:#b89252;--royal:#4c2bdc;--muted:#9fb0c8}
    .brand { padding:16px;border-radius:12px;background:linear-gradient(90deg,var(--gold),var(--royal)); color:#021423; box-shadow:0 10px 40px rgba(0,0,0,0.6); }
    .card { background: rgba(255,255,255,0.03); padding:12px; border-radius:12px; border:1px solid rgba(255,255,255,0.03); transition: transform .18s ease; }
    .card:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(2,6,23,0.6); }
    .small { color:var(--muted); font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='brand'><h2 style='margin:0'>🌐 Luxury Travel Concierge</h2><div class='small'>Elegant · Vibrant · Curated trip planning</div></div>", unsafe_allow_html=True)
st.write("")

# Sidebar form for inputs
with st.sidebar.form(key="planner_form"):
    st.header("Plan your trip")
    from_city = st.text_input("From (city or IATA)", value="Delhi")
    to_city = st.text_input("To (city)", value="Paris")
    dep_date = st.date_input("Departure date", value=datetime.now().date() + timedelta(days=45))
    duration = st.number_input("Trip duration (days)", min_value=1, max_value=30, value=4)
    people = st.number_input("Number of people", min_value=1, max_value=10, value=1)
    budget_currency = st.selectbox("Budget currency", ("INR", "USD", "EUR"), index=0)
    total_budget = st.number_input("Total budget (approx)", min_value=1000, value=100000)
    submit = st.form_submit_button("Plan my trip ✨")

# Quick API-key status
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.write("**Amadeus**:", "✅" if AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET else "⚠️ Not configured")
with col2:
    st.write("**OpenWeather**:", "✅" if OPENWEATHERMAP_API_KEY else "⚠️ Not configured")
with col3:
    st.write("**Unsplash**:", "✅" if UNSPLASH_ACCESS_KEY else "⚠️ Not configured")
with col4:
    st.write("**Hotels (RapidAPI)**:", "✅" if RAPIDAPI_KEY else "⚠️ Not configured")

if submit:
    dep_date_str = dep_date.isoformat()
    return_date = (dep_date + timedelta(days=duration)).isoformat()
    SAFETY_BUFFER_PCT = 0.10

    # Fetch data with spinner
    with st.spinner("Gathering destination photos, weather, flights, hotels & POIs..."):
        # Images
        imgs = []
        try:
            imgs = unsplash_images(to_city, 5) or []
            if len(imgs) < 5:
                imgs += unsplash_images(f"{to_city} city", 5 - len(imgs))
        except Exception:
            imgs = []

        # Coordinates + weather
        coords = None
        weather = []
        try:
            coords = get_coords(to_city)
            if coords:
                # UPDATED WEATHER CALL (robust fallback)
                weather = fetch_openweather_daily(coords["lat"], coords["lon"], dep_date_str, duration)
        except Exception:
            coords = None
            weather = []

        # Flights
        flights = []
        try:
            token = amadeus_token()
            origin_iata = resolve_iata(from_city, token) or from_city.upper()
            dest_iata = resolve_iata(to_city, token) or to_city.upper()
            flights = amadeus_search_flights(origin_iata, dest_iata, dep_date_str, return_date=return_date, adults=people, currency=budget_currency)
        except Exception:
            flights = []

        # Fallback mock flight if none found
        if not flights:
            flights = [{"airline": "SampleAir", "price": int(100000 + (abs(hash(to_city)) % 20000)), "currency": budget_currency, "duration":"10H", "times":[f"{from_city} → {to_city}"], "airports":[] }]

        # Hotels
        nights = max(1, duration - 1)
        per_person_night_budget = total_budget / max(1, (people * nights))
        hotels = []
        try:
            hotels = hotel_suggestions(to_city, per_person_night_budget, nights=nights, people=people, count=6)
        except Exception:
            hotels = []

        # POIs
        places = restaurants = shops = []
        try:
            if coords:
                lat = coords["lat"]; lon = coords["lon"]
                places = wikivoyage_top_places(to_city, 6) or attractions_osm(to_city, lat, lon, 6)
                restaurants = restaurants_osm(to_city, lat, lon, 8)
                shops = shopping_spots_osm(to_city, lat, lon, 8)
        except Exception:
            places = restaurants = shops = []

    # De-duplicate lists
    places = unique_places(places)
    restaurants = unique_places(restaurants)
    shops = unique_places(shops)
    hotels = unique_places(hotels)

    # Auto-balance budget
    chosen_hotel_index = min(2, max(0, len(hotels)-1)) if hotels else 0
    current_duration = duration
    adjustments = []
    total_budget_inr = int(round(total_budget)) if budget_currency == "INR" else int(round(total_budget))
    bd = budget_breakdown(flights, hotels, current_duration, people, budget_currency, total_budget_inr, hotel_index=chosen_hotel_index, safety_buffer_pct=SAFETY_BUFFER_PCT)
    while not bd["fits_in_effective"] and chosen_hotel_index > 0:
        chosen_hotel_index -= 1
        bd = budget_breakdown(flights, hotels, current_duration, people, budget_currency, total_budget_inr, hotel_index=chosen_hotel_index, safety_buffer_pct=SAFETY_BUFFER_PCT)
        adjustments.append(f"Downgraded hotel tier to index {chosen_hotel_index}.")
    while not bd["fits_in_effective"] and current_duration > 2:
        old = current_duration
        current_duration -= 1
        bd = budget_breakdown(flights, hotels, current_duration, people, budget_currency, total_budget_inr, hotel_index=chosen_hotel_index, safety_buffer_pct=SAFETY_BUFFER_PCT)
        adjustments.append(f"Reduced trip duration from {old} to {current_duration} days.")
    budget_fit = bd["fits_in_effective"]

    # Render UI
    st.markdown("---")
    st.subheader(f"✨ Trip Snapshot — {to_city}")
    left, right = st.columns([2,3])

    with left:
        st.markdown(f"**From:** {from_city}")
        st.markdown(f"**Dates:** {dep_date_str} → {return_date}  •  {current_duration} days")
        st.markdown(f"**People:** {people}")
        st.markdown(f"**Budget:** {int(total_budget):,} {budget_currency}")
        if adjustments:
            with st.expander("Auto-adjustments performed"):
                for a in adjustments:
                    st.info(a)

    with right:
        if imgs:
            cols_img = st.columns(5)
            for i, url in enumerate(imgs[:5]):
                try:
                    cols_img[i].image(url, use_container_width=True, caption=f"{to_city} photo {i+1}")
                except Exception:
                    cols_img[i].write("Image unavailable")
        else:
            st.info("No Unsplash images available. (Check UNSPLASH_ACCESS_KEY)")

    st.markdown("### ✈️ Flights")
    for f in flights:
        price_disp = f.get("price")
        try:
            price_disp = f"{int(round(float(price_disp))):,} {f.get('currency',budget_currency)}"
        except Exception:
            price_disp = str(price_disp)
        airline_name = f.get("airline") or f.get("airline_code") or "Unknown"
        st.markdown(f"**{airline_name}** — **{price_disp}** • {f.get('duration','-')}")
        if f.get("times"):
            with st.expander("Show segments/times"):
                for t in f.get("times", []):
                    st.write(t)
        if f.get("airports"):
            for seg in f.get("airports"):
                dep = seg.get("dep"); arr = seg.get("arr")
                if dep or arr:
                    st.markdown(f"• Airports: {dep or '?'} → {arr or '?'}")
                    if dep:
                        st.markdown(f"[{dep} map]({airport_map_link(dep)})")
                    if arr:
                        st.markdown(f"[{arr} map]({airport_map_link(arr)})")

    st.markdown("### 🏨 Hotels")
    if hotels:
        for i in range(0, len(hotels), 3):
            row = hotels[i:i+3]
            cols = st.columns(3)
            for idx, h in enumerate(row):
                with cols[idx]:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    if h.get("image"):
                        st.markdown(f"<div style='border-radius:8px;overflow:hidden'><img src='{html.escape(h['image'])}' style='width:100%;height:140px;object-fit:cover;' /></div>", unsafe_allow_html=True)
                    st.markdown(f"**{h.get('name','-')}**")
                    st.markdown(f"<div class='small'>Price: <strong>{h.get('price_inr',0):,} INR/night</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"[Open map]({h.get('map','')})")
                    if bd.get("selected_hotel_index") == (i + idx):
                        st.success("Selected")
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hotels discovered. (Enable RAPIDAPI_KEY to fetch real hotels)")

    st.markdown("### 🌦️ Weather & Packing Tips")
    if weather:
        # Ensure not to create zero columns; also limit to a safe number (max 10 to avoid layout issues)
        max_cols = min(len(weather), 10)
        # if more days than max_cols, chunk into rows
        if len(weather) <= max_cols:
            cols_w = st.columns(len(weather))
            for k, w in enumerate(weather):
                with cols_w[k]:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown(f"**{w.get('date','-')}**")
                    st.markdown(f"**{w.get('temp_day','-')}°C**")
                    st.markdown(f"<div class='small'>{w.get('desc','-')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='small'>Packing: {packing_tips(w.get('temp_day'), w.get('desc',''), current_duration)}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            # chunk and render rows of up to max_cols each
            for i in range(0, len(weather), max_cols):
                chunk = weather[i:i+max_cols]
                cols_w = st.columns(len(chunk))
                for k, w in enumerate(chunk):
                    with cols_w[k]:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"**{w.get('date','-')}**")
                        st.markdown(f"**{w.get('temp_day','-')}°C**")
                        st.markdown(f"<div class='small'>{w.get('desc','-')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='small'>Packing: {packing_tips(w.get('temp_day'), w.get('desc',''), current_duration)}</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Weather data unavailable. Check OPENWEATHERMAP_API_KEY.")

    st.markdown("### 📍 Attractions")
    if places:
        for p in places[:8]:
            st.markdown(f"**{p.get('name')}** — [map]({p.get('map','')})")
            if p.get("image"):
                st.image(p.get("image"), width=240)
            if p.get("desc"):
                st.caption(html.unescape(p.get("desc"))[:250] + ("..." if len(p.get("desc",""))>250 else ""))
    else:
        st.info("No attractions found (Wikivoyage/OSM).")

    st.markdown("### 🍽️ Restaurants & 🛍️ Shopping")
    rcol, scol = st.columns(2)
    with rcol:
        st.markdown("**Restaurants / Cafes**")
        if restaurants:
            for r in restaurants[:8]:
                st.markdown(f"- {r.get('name')} — [map]({r.get('map','')})")
        else:
            st.info("No restaurants found.")
    with scol:
        st.markdown("**Shopping**")
        if shops:
            for s in shops[:8]:
                st.markdown(f"- {s.get('name')} — [map]({s.get('map','')})")
        else:
            st.info("No shopping spots found.")

    st.markdown("---")
    st.subheader("💰 Budget Breakdown")
    b1, b2 = st.columns(2)
    with b1:
        st.write(f"Flight (per person): **{bd.get('flight_per_person',0):,} {bd.get('flight_currency')}** (~{bd.get('flight_per_person_inr',0):,} INR)")
        st.write(f"Flights total ({people} pax): **{bd.get('flights_total_inr',0):,} INR**")
        st.write(f"Hotel per night: **{bd.get('hotel_per_night_inr',0):,} INR**")
        st.write(f"Hotel total: **{bd.get('hotel_total_inr',0):,} INR**")
    with b2:
        st.write(f"Food estimate: **{bd.get('food_inr',0):,} INR**")
        st.write(f"Local transport: **{bd.get('local_inr',0):,} INR**")
        st.write(f"Sightseeing/misc: **{bd.get('sights_inr',0):,} INR**")
        st.write(f"Safety buffer applied: **{bd.get('buffer_inr',0):,} INR**")
        st.markdown(f"### GRAND TOTAL: **{bd.get('grand_total_inr',0):,} INR**")
        if budget_fit:
            st.success("Within safe budget (after buffer)")
        else:
            st.error("Exceeds safe budget after buffer")

    st.markdown("---")
    st.subheader("🗺️ General Map")
    if coords:
        lat = coords["lat"]; lon = coords["lon"]
        map_iframe = f"https://www.google.com/maps?q={lat},{lon}&z=12&output=embed"
        st.markdown(f'<iframe src="{map_iframe}" width="100%" height="450" style="border:1px solid rgba(255,255,255,0.06); border-radius:8px;"></iframe>', unsafe_allow_html=True)
        st.markdown(f"[Open in Google Maps](https://www.google.com/maps/search/?api=1&query={lat},{lon})")
    else:
        st.info("Could not resolve coordinates for an embeddable map. Try a more specific destination.")
    st.markdown("---")
    meta = {
        "from_city": from_city, "to_city": to_city, "dep_date": dep_date_str, "return_date": return_date,
        "duration": current_duration, "people": people, "budget_currency": budget_currency,
        "flights": flights, "hotels": hotels, "places": places, "restaurants": restaurants, "shops": shops,
        "weather": weather, "images": imgs, "bd": bd
    }

    html_content = build_html_summary(meta)
    html_bytes = html_content.encode("utf-8")
    data_url = "data:text/html;base64," + base64.b64encode(html_bytes).decode()

    dl_col, open_col, file_col = st.columns([1,1,1])
    with dl_col:
        st.download_button("⬇️ Download HTML summary", html_bytes, file_name="trip_summary.html", mime="text/html")
    with open_col:
        st.markdown(f"[🔗 Open HTML summary in new tab]({data_url})", unsafe_allow_html=True)
    with file_col:
        try:
            p = pathlib.Path.cwd() / "trip_summary.html"
            p.write_text(html_content, encoding="utf-8")
            file_url = f"file://{str(p.resolve())}"
            st.markdown(f"[🖥️ Open saved HTML file]({file_url})", unsafe_allow_html=True)
        except Exception:
            st.info("Could not write HTML file to disk (permission issue).")

    st.success("Trip plan ready — download or open the HTML summary.")
    st.balloons()

