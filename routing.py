from aiohttp import ClientSession, ClientTimeout
from urllib.parse import quote_plus
from utils import clean_html_instructions, decode_google_maps_polyline
import os
from dotenv import load_dotenv

load_dotenv()
# from aiohttp_sse import sse_response

GOOGLE_API_KEY = os.getenv("GMAPS_KEY") 


async def find_routes(place1, place2):
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.get(
            f"https://maps.googleapis.com/maps/api/directions/json?origin=place_id:{place1}&destination=place_id:{place2}&key={GOOGLE_API_KEY}"
        ) as response:
            resp = await response.json()
            result = []
            for route in resp["routes"]:
                result.append(
                    {
                        "distance": route["legs"][0]["distance"]["text"],
                        "duration": route["legs"][0]["duration"]["text"],
                        "steps": [
                            {
                                "distance": step["distance"]["text"],
                                "duration": step["duration"]["text"],
                                "instruction": clean_html_instructions(
                                    step["html_instructions"]
                                ),
                                "start_location": step["start_location"],
                                "end_location": step["end_location"],
                                "maneuver": step.get("maneuver", ''),
                                "polyline": decode_google_maps_polyline(step["polyline"]["points"]),
                            }
                            for step in route["legs"][0]["steps"]
                        ],
                    }
                )

            return result


async def search_place(query: str):
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.get(
            f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={quote_plus(query)}&key={GOOGLE_API_KEY}"
        ) as response:
            resp = await response.json()
            result = []
            for place in resp["results"]:
                result.append(
                    {
                        "name": place["name"],
                        "address": place["formatted_address"],
                        "location": place["geometry"]["location"],
                        "place_id": place["place_id"],
                    }
                )

            return result


async def distance(lat1, lon1, lat2, lon2):
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.get(
            f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat1},{lon1}&destinations={lat2},{lon2}&key={GOOGLE_API_KEY}"
        ) as response:
            resp = await response.json()
            try:
                return resp["rows"][0]["elements"][0]["distance"]["value"]
            except:
                return "Unknown"
