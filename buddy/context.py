"""Real-world context: where you are, what's nearby, what the weather is doing.

All three services are free and need no API key:
- Nominatim (OpenStreetMap) — turn a place name into coordinates
- Overpass  (OpenStreetMap) — find parks, viewpoints, piers etc. nearby
- Open-Meteo                — current weather

Every call has a short timeout and returns a safe default on failure,
so the app keeps working on bad hackathon Wi-Fi.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import requests

from .security import coarsen, sanitize_text, valid_coords

TIMEOUT = 8
HEADERS = {"User-Agent": "OutsideBuddy/0.1 (open-source hackathon project)"}

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS_MIRRORS = ["https://overpass-api.de/api/interpreter",
                    "https://overpass.kumi.systems/api/interpreter"]
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

# Default: University of Galway
DEFAULT_PLACE = ("University of Galway", 53.2785, -9.0606)

# WMO weather codes -> short label
_WEATHER = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "heavy showers",
    95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm",
}
_WET = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}


@dataclass
class Weather:
    label: str = "unknown"
    temp_c: float | None = None
    wet: bool = False
    is_day: bool = True
    ok: bool = False

    def summary(self) -> str:
        if not self.ok:
            return "weather unavailable"
        t = f"{self.temp_c:.0f}°C, " if self.temp_c is not None else ""
        return f"{t}{self.label}, {'daytime' if self.is_day else 'dark outside'}"


@dataclass
class Place:
    name: str
    kind: str
    distance_m: int

    def line(self) -> str:
        return f"{self.name} ({self.kind}, ~{self.distance_m} m)"


@dataclass
class Context:
    place_name: str
    lat: float
    lon: float
    weather: Weather = field(default_factory=Weather)
    nearby: list[Place] = field(default_factory=list)


def geocode(query: str) -> tuple[str, float, float] | None:
    q = sanitize_text(query, 80)
    if not q:
        return None
    try:
        r = requests.get(
            NOMINATIM,
            params={"q": q, "format": "json", "limit": 1},
            headers=HEADERS, timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
        if not valid_coords(lat, lon):
            return None
        parts = [p.strip() for p in sanitize_text(data[0].get("display_name", q), 120).split(",")]
        name = ", ".join([parts[0], parts[-1]] if len(parts) > 1 else parts)  # "Salthill, Ireland"
        return name, lat, lon
    except (requests.RequestException, ValueError, KeyError):
        return None


def get_weather(lat: float, lon: float) -> Weather:
    lat, lon = coarsen(lat, lon)
    try:
        r = requests.get(
            OPEN_METEO,
            params={"latitude": lat, "longitude": lon,
                    "current": "temperature_2m,weather_code,is_day"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        cur = r.json()["current"]
        code = int(cur.get("weather_code", -1))
        return Weather(
            label=_WEATHER.get(code, "mixed"),
            temp_c=float(cur.get("temperature_2m")),
            wet=code in _WET,
            is_day=bool(cur.get("is_day", 1)),
            ok=True,
        )
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return Weather()


def _distance_m(lat1, lon1, lat2, lon2) -> int:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return int(2 * r * math.asin(math.sqrt(a)))


def get_nearby(lat: float, lon: float, radius_m: int = 1500, limit: int = 8) -> list[Place]:
    """Public outdoor-friendly spots near you, closest first."""
    q = f"""
    [out:json][timeout:10];
    (
      nwr(around:{radius_m},{lat},{lon})["leisure"~"^(park|garden|nature_reserve)$"]["name"];
      nwr(around:{radius_m},{lat},{lon})["tourism"~"^(viewpoint|artwork|museum|attraction)$"]["name"];
      nwr(around:{radius_m},{lat},{lon})["natural"~"^(beach|water|wood)$"]["name"];
      nwr(around:{radius_m},{lat},{lon})["man_made"="pier"]["name"];
      nwr(around:{radius_m},{lat},{lon})["historic"]["name"];
      nwr(around:{radius_m},{lat},{lon})["amenity"="library"]["name"];
    );
    out center 40;
    """
    for url in OVERPASS_MIRRORS:      # try a second server if the first is busy
        try:
            r = requests.post(url, data={"data": q}, headers=HEADERS, timeout=TIMEOUT + 4)
            r.raise_for_status()
            return _parse_places(r.json(), lat, lon, limit)
        except (requests.RequestException, ValueError, KeyError):
            continue
    return []


def _parse_places(payload: dict, lat: float, lon: float, limit: int) -> list[Place]:
    seen, places = set(), []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        name = sanitize_text(tags.get("name", ""), 60)
        if not name or name.lower() in seen:
            continue
        plat = el.get("lat") or el.get("center", {}).get("lat")
        plon = el.get("lon") or el.get("center", {}).get("lon")
        if plat is None or plon is None:
            continue
        kind = (tags.get("leisure") or tags.get("tourism") or tags.get("natural")
                or tags.get("man_made") or ("historic site" if "historic" in tags else None)
                or tags.get("amenity") or "place")
        seen.add(name.lower())
        places.append(Place(name, sanitize_text(kind, 20).replace("_", " "),
                            _distance_m(lat, lon, plat, plon)))
    places.sort(key=lambda p: p.distance_m)
    return places[:limit]


def build_context(place_name: str, lat: float, lon: float) -> Context:
    return Context(place_name, lat, lon, get_weather(lat, lon), get_nearby(lat, lon))
