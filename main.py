from aiohttp import web
from routing import find_routes, search_place
from location import (
    add_user,
    get_user,
    is_user,
    _save_users,
    get_all_users_as_dict,
    update_user_location,
)

app = web.Application()


async def routes(request):
    try:
        p1 = request.query["p1"]
        p2 = request.query["p2"]
    except KeyError:
        return web.json_response({"error": "Missing 'p1' or 'p2'"}, status=400)
    routes = await find_routes(p1, p2)
    return web.json_response(routes, headers={"Access-Control-Allow-Origin": "*"})


async def search(request):
    try:
        query = request.query["query"]
    except KeyError:
        try:
            query = request.query["q"]
        except KeyError:
            return web.json_response({"error": "Missing 'query'"}, status=400)
    places = await search_place(query)
    return web.json_response(places, headers={"Access-Control-Allow-Origin": "*"})


async def distance(request):
    try:
        lat1 = request.query["lat1"]
        lon1 = request.query["lon1"]
        lat2 = request.query["lat2"]
        lon2 = request.query["lon2"]
    except KeyError:
        return web.json_response(
            {"error": "Missing 'lat1', 'lon1', 'lat2', or 'lon2"}, status=400
        )
    distance = await distance(lat1, lon1, lat2, lon2)
    return web.json_response(
        {"distance": distance}, headers={"Access-Control-Allow-Origin": "*"}
    )


app.router.add_get("/routes", routes)
app.router.add_get("/search", search)
app.router.add_get("/distance", distance)


async def add_user_handler(request):
    try:
        username = request.query["u"]
        password = request.query["p"]

        if is_user(username):
            return web.json_response({"error": "User already exists"}, status=400)
    except KeyError:
        return web.json_response({"error": "Missing 'u' or 'p'"}, status=400)
    user = add_user(username, password)
    return web.json_response(
        {"username": user.username},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def update_user_location_handler(request):
    try:
        username = request.query["u"]
        lat = request.query["lat"]
        lon = request.query["lon"]
    except KeyError:
        return web.json_response({"error": "Missing 'u', 'lat', or 'lon'"}, status=400)
    user = get_user(username)
    if user is None:
        return web.json_response({"error": "User not found"}, status=404)
    alert = update_user_location(username, (lat, lon))
    return web.json_response(
        {"alert": alert},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def login_check_handler(request):
    try:
        username = request.query["u"]
        password = request.query["p"]
    except KeyError:
        return web.json_response({"error": "Missing 'u' or 'p'"}, status=400)
    user = get_user(username)
    if user is None:
        return web.json_response({"error": "User not found"}, status=404)
    if user.password != password:
        return web.json_response({"error": "Incorrect password"}, status=400)
    return web.json_response(
        {"username": user.username},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def get_user_handler(request):
    try:
        username = request.query["u"]
    except KeyError:
        return web.json_response({"error": "Missing 'u'"}, status=400)
    user = get_user(username)
    if user is None:
        return web.json_response({"error": "User not found"}, status=404)
    return web.json_response(
        user,
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def user_start_journey_handler(request):
    try:
        username = request.query["u"]
        p1 = request.query["p1"]
        p2 = request.query["p2"]
    except KeyError:
        return web.json_response({"error": "Missing 'u', 'p1', or 'p2'"}, status=400)
    user = get_user(username)
    if user is None:
        return web.json_response({"error": "User not found"}, status=404)
    await user.start_journey(p1, p2)
    return web.json_response(
        {"username": user.username},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def commit(request):
    _save_users()
    return web.json_response(
        {"success": True},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def get_all_users(request):
    return web.json_response(
        get_all_users_as_dict(),
        headers={"Access-Control-Allow-Origin": "*"},
    )

async def index(request):
    return web.FileResponse('index.html')

app.router.add_get("/add_user", add_user_handler)
app.router.add_get("/update_user_location", update_user_location_handler)
app.router.add_get("/login_check", login_check_handler)
app.router.add_get("/get_user", get_user_handler)
app.router.add_get("/user_start_journey", user_start_journey_handler)
app.router.add_get("/commit", commit)
app.router.add_get("/get_all_users", get_all_users)
app.router.add_get("/", index)

import os
PORT = os.environ.get('PORT', 8080)

web.run_app(app, port=int(PORT))
