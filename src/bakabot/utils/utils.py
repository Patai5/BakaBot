import datetime
import os
import pickle
import random

import aiohttp
import discord
import dotenv
import pytz


# Reads a from the database by key. Returns none if the key doesn't exist
def read_db(key: str):
    try:
        with open(f"db/{key}.dat", "rb") as f:
            return pickle.load(f)
    except:
        return None


# Writes to the database
def write_db(key: str, value):
    with open(f"db/{key}.dat", "wb") as f:
        pickle.dump(value, f, protocol=2)


def env_load():
    """Loads the .env file"""
    dotenv.load_dotenv(dotenv.find_dotenv())


# Gets os.environ values by key
def os_environ(key: str):
    intKeys = ("adminID",)
    if key in intKeys:
        return int(os.environ[key])
    else:
        return os.environ[key]


def getThreadChannel(threadId: int, client: discord.Client):
    """Gets the thread channel by the given id. Throws an error if the channel doesn't exist or is not a thread"""
    channel = client.get_channel(threadId)
    if not isinstance(channel, discord.threads.Thread):
        raise Exception(f"No thread channel found for id: '{threadId}'")

    return channel


# Logs into the server and returns the login session
async def login(client: discord.Client):
    username = os_environ("bakalariUsername")
    password = os_environ("bakalariPassword")

    url = "https://bakalari.ceskolipska.cz/Login"
    data = {"username": username, "password": password, "returnUrl": "", "login": ""}
    session = aiohttp.ClientSession()
    try:
        await session.head(url, timeout=25)
        response = await session.post(url, data=data)

        if response.url.name in ("errinfo.aspx", "Login"):
            await status(False, client)
            await session.close()
            return None
    except:
        await status(False, client)
        await session.close()
        return None
    else:
        await status(True, client)
        return session


async def request(session: aiohttp.ClientSession, url: str, get: bool, client: discord.Client):
    try:
        if get:
            response = await session.get(url, timeout=25)
        else:
            response = await session.post(url, timeout=25)

        if response.url.name == "errinfo.aspx":
            await status(False, client)
            await session.close()
            return None
        else:
            return response
    except:
        await status(False, client)
        await session.close()
        return None


async def status(online: bool, client: discord.Client):
    """Send's the current status of the bakalari server to discord"""
    if not read_db("lastStatus"):
        write_db("lastStatus", [online, time_since_epoch_utc()])
    lastStatus = read_db("lastStatus")
    if lastStatus[0] != online:
        if online == True:
            embed = discord.Embed()

            embed.title = "Server is back online!"

            time = for_time(lastStatus[1])
            embed.add_field(name="\u200b", value=f"Server was offline for: {time}")

            embed.color = discord.Color.from_rgb(0, 255, 0)
        else:
            embed = discord.Embed()

            embed.title = "Server has gone offline!"

            time = for_time(lastStatus[1])
            embed.add_field(name="\u200b", value=f"Server was online for: {time}")

            embed.color = discord.Color.from_rgb(255, 0, 0)

        channel = read_db("channelStatus")
        write_db("lastStatus", [online, time_since_epoch_utc()])
        channel = await client.get_channel(channel).send(embed=embed)


def for_time(time: int):
    forTime = time_since_epoch_utc() - time

    intervals = (
        ("years", 29030400),
        ("months", 2419200),
        ("weeks", 604800),
        ("days", 86400),
        ("hours", 3600),
        ("minutes", 60),
        ("seconds", 1),
    )

    def display_time(seconds):
        result = []
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append("{} {}".format(value, name))
        return ", ".join(result[:3])

    return display_time(forTime)


def time_since_epoch_utc():
    utcTime = pytz.timezone("UTC").localize(datetime.datetime.utcnow())
    return int(utcTime.timestamp())


def get_weekday_sec():
    """Returns the current week day and the time in seconds for the Czech republic"""
    utcTime = pytz.timezone("UTC").localize(datetime.datetime.utcnow())
    czechTime = utcTime.astimezone(pytz.timezone("Europe/Vienna"))
    sec = czechTime.hour * 3600 + czechTime.minute * 60 + czechTime.second
    return czechTime.weekday(), sec


def get_sec():
    """Returns the current time in seconds for the Czech republic"""
    return get_weekday_sec()[1]


def get_week_day():
    """Returns the current week day in the Czech republic"""
    return get_weekday_sec()[0]


# Returns string of inputed time in seconds to {hours:minutes}
def from_sec_to_time(sec: int):
    hours = int(sec / 3600)
    minutes = int((sec - hours * 3600) / 60)

    # If minutes is less that 10 then print with 0 in front of minetes {1:01}
    if minutes < 10:
        minutes = "0" + str(minutes)
    output = f"{hours}:{minutes}"
    return output


async def fetch_message(message_channel: int, message_id: int, client: discord.Client):
    try:
        return await client.get_channel(message_channel).fetch_message(message_id)
    except:
        print(
            f"""Couldn't get the desired message! Was probably removed!:\n
                message_id: {message_id}, message_channel: {message_channel}"""
        )


def rand_rgb():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def log_html(html: str, filename: str):
    """Logs the html into a file"""
    timeIdentifier = datetime.datetime.now().strftime("%H-%M")
    with open(f"logs/{filename}-{timeIdentifier}.html", "w", encoding="utf-8") as f:
        f.write(html)
