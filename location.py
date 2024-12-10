from datetime import datetime
from math import asin, cos, radians, sin, sqrt, atan2, pi
from routing import find_routes
import sqlite3
from typing import List

users: List["User"] = []

class User:
    username: str
    password: str
    location: tuple
    last_location: tuple
    last_update: datetime
    should_alert: bool
    route_points: list
    active_journey: bool

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.location = [0, 0]
        self.last_location = [0, 0]
        self.last_update = datetime.now()
        self.should_alert = False
        self.route_points = []
        self.active_journey = False

    def update_location(self, location) -> bool:
        self.last_location = tuple(float(x) for x in self.location)
        self.location = location
        self.last_update = datetime.now()
        self.should_alert = is_deviating_from_route(self.route_points, self.location)
        return self.should_alert

    def update_route(self, route_points):
        self.route_points = route_points

    def __str__(self):
        return f"{self.username} ({self.location})"

    def __repr__(self):
        return f"{self.username} ({self.location})"

    def distance_to_route_point(self, route_point) -> float:
        if self.location is None:
            return float("inf")
        return distance(self.location, route_point)

    async def start_journey(self, p1, p2):
        routes = await find_routes(p1, p2)
        polylines = routes[0]["steps"]
        polyline = []
        for step in polylines:
            polyline.extend(step["polyline"])
        self.update_route(polyline)
        self.active_journey = True


def _load_users():
    global users
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, lat REAL, lon REAL, last_lat REAL, last_lon REAL, last_update TEXT, should_alert INTEGER, route_points TEXT, active_journey INTEGER)"
    )
    c.execute("SELECT * FROM users")
    for row in c.fetchall():
        user = User(row[0], row[1])
        user.location = (row[2], row[3])
        user.last_location = (row[4], row[5])
        user.last_update = datetime.fromisoformat(row[6])
        user.should_alert = row[7]
        user.route_points = eval(row[8])
        user.active_journey = row[9]
        users.append(user)
    conn.close()


def _save_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        lat REAL,
        lon REAL,
        last_lat REAL,
        last_lon REAL,
        last_update TEXT,
        should_alert INTEGER,
        route_points TEXT,
        active_journey INTEGER
    )
    """
    )

    for user in users:
        c.execute(
            """
        INSERT INTO users (username, password, lat, lon, last_lat, last_lon, last_update, should_alert, route_points, active_journey)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            password = excluded.password,
            lat = excluded.lat,
            lon = excluded.lon,
            last_lat = excluded.last_lat,
            last_lon = excluded.last_lon,
            last_update = excluded.last_update,
            should_alert = excluded.should_alert,
            route_points = excluded.route_points,
            active_journey = excluded.active_journey
        """,
            (
                user.username,
                user.password,
                user.location[0],
                user.location[1],
                user.last_location[0],
                user.last_location[1],
                user.last_update.isoformat(),
                user.should_alert,
                str(user.route_points),
                user.active_journey,
            ),
        )

    conn.commit()
    conn.close()


_load_users()

def distance(loc1, loc2) -> float:
    lat1, lon1 = loc1
    lat2, lon2 = loc2
    return 6371 * (
        2
        * asin(
            sqrt(
                sin(radians((lat2 - lat1) / 2)) ** 2
                + cos(radians(lat1))
                * cos(radians(lat2))
                * sin(radians((lon2 - lon1) / 2)) ** 2
            )
        )
    )


def get_all_users_as_dict() -> dict:
    result = {}
    for user in users:
        result[user.username] = {
            "location": user.location,
            "last_location": user.last_location,
            "last_update": user.last_update.isoformat(),
            "should_alert": user.should_alert,
            "route_points": user.route_points,
            "active_journey": user.active_journey,
        }
    return result



def get_user(username) -> User:
    for user in users:
        if user.username == username:
            return {
                "username": user.username,
                "location": user.location,
                "last_location": user.last_location,
                "last_update": user.last_update.isoformat(),
                "should_alert": user.should_alert,
                "route_points": user.route_points,
                "active_journey": user.active_journey,
            }
    return None

def get_u(username) -> User:
    for user in users:
        if user.username == username:
            return user
    return None


def is_user(username) -> bool:
    for user in users:
        if user.username == username:
            return True
    return False


def add_user(username, password) -> User:
    user = User(username, password)
    users.append(user)
    return user


def update_user_location(username, location) -> bool:
    user = get_u(username)
    if user is None:
        return False
    return user.update_location(location)


def update_user_route(username, route_points) -> bool:
    user = get_u(username)
    if user is None:
        return False
    user.update_route(route_points)
    return True


def get_nearby_users(location) -> list:
    return [user for user in users if distance(user.location, location) < 1]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth.
    """
    R = 6371000
    to_radians = lambda x: x * pi / 180

    d_lat = to_radians(lat2 - lat1)
    d_lon = to_radians(lon2 - lon1)
    lat1 = to_radians(lat1)
    lat2 = to_radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def point_to_segment_distance(lat, lon, seg_start, seg_end):
    start_lat, start_lon = seg_start
    end_lat, end_lon = seg_end

    d_lat = end_lat - start_lat
    d_lon = end_lon - start_lon

    if d_lat == 0 and d_lon == 0:
        return haversine_distance(lat, lon, start_lat, start_lon)

    t = ((lat - start_lat) * d_lat + (lon - start_lon) * d_lon) / (d_lat**2 + d_lon**2)
    t = max(0, min(1, t))

    nearest_lat = start_lat + t * d_lat
    nearest_lon = start_lon + t * d_lon

    return haversine_distance(lat, lon, nearest_lat, nearest_lon)


def is_deviating_from_route(polyline, user_location, threshold=50):
    user_lat, user_lon = user_location
    user_lat = float(user_lat)
    user_lon = float(user_lon)

    for i in range(len(polyline) - 1):
        seg_start = polyline[i]
        seg_end = polyline[i + 1]
        seg_start = tuple(float(x) for x in seg_start)
        seg_end = tuple(float(x) for x in seg_end)
        distance = point_to_segment_distance(user_lat, user_lon, seg_start, seg_end)

        if distance <= threshold:
            return False

    return True
