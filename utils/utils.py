import datetime
import os

import aiohttp
import pytz
from replit import db


# Reads a from the database by key. Returns none if the key doesn't exist
def read_db(key: str):
    if len(db.prefix(key)) == 0:
        return None
    else:
        return db[key]


# Writes to the database
def write_db(key: str, value):
    db[key] = value


# Gets os.environ values by key
def os_environ(key: str):
    return os.environ[key]


# Logs into the server and returns the login session
async def login():
    username = os_environ("username")
    password = os_environ("password")

    url = "https://bakalari.ceskolipska.cz/Login"
    data = {"username": username, "password": password}
    session = aiohttp.ClientSession()
    await session.post(url, data=data)
    return session


# Returns the current time in the Czech republic
def get_sec():
    utcTime = pytz.timezone("UTC").localize(datetime.datetime.utcnow())
    czechTime = utcTime.astimezone(pytz.timezone("Europe/Vienna"))
    sec = czechTime.hour * 3600 + czechTime.minute * 60 + czechTime.second
    return sec


# Returns string of inputed time in seconds to {hours:minutes}
def from_sec_to_time(sec: int):
    hours = int(sec / 3600)
    minutes = int((sec - hours * 3600) / 60)

    # If minutes is less that 10 then print with 0 in front of minetes {1:01}
    if minutes < 10:
        minutes = "0" + str(minutes)
    output = f"{hours}:{minutes}"
    return output
