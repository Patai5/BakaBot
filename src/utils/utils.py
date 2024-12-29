import datetime
import os
import pickle
import random
from typing import Any

import aiohttp
import disnake
import dotenv
import pytz
from disnake.ext.commands import InteractionBot


# Reads a from the database by key. Returns none if the key doesn't exist
def read_db(key: str) -> Any | None:
    try:
        with open(f"db/{key}.dat", "rb") as f:
            return pickle.load(f)
    except:
        return None


# Writes to the database
def write_db(key: str, value: Any) -> None:
    with open(f"db/{key}.dat", "wb") as f:
        pickle.dump(value, f, protocol=2)


def env_load() -> None:
    """Loads the .env file"""
    dotenv.load_dotenv(dotenv.find_dotenv())


# Gets os.environ values by key
def os_environ(key: str) -> str | int:
    intKeys = ("adminID",)
    if key in intKeys:
        return int(os.environ[key])
    else:
        return os.environ[key]


def getTextChannel(channelId: int, client: InteractionBot) -> disnake.TextChannel:
    """Gets the text channel by the given id. Throws an error if the channel doesn't exist or is not a text channel"""
    channel = client.get_channel(channelId)
    if not isinstance(channel, disnake.TextChannel):
        raise Exception(f"No text channel found for id: '{channelId}'")

    return channel


# Logs into the server and returns the login session
async def login(client: InteractionBot) -> aiohttp.ClientSession | None:
    username = os_environ("bakalariUsername")
    password = os_environ("bakalariPassword")
    bakalariUrl = os_environ("bakalariUrl")

    url = f"{bakalariUrl}/Login"
    data: dict[str, str | int] = {
        "username": username,
        "password": password,
        "returnUrl": "",
        "login": "",
    }
    session = aiohttp.ClientSession()
    try:
        await session.head(url, timeout=aiohttp.ClientTimeout(total=25))
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


async def request(
    session: aiohttp.ClientSession, url: str, get: bool, client: InteractionBot
) -> aiohttp.ClientResponse | None:
    try:
        if get:
            response = await session.get(url, timeout=aiohttp.ClientTimeout(total=25))
        else:
            response = await session.post(url, timeout=aiohttp.ClientTimeout(total=25))

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


async def status(online: bool, client: InteractionBot) -> None:
    """Send's the current status of the bakalari server to discord"""
    lastStatus: tuple[bool, int] | None = read_db("lastStatus")

    if lastStatus is None:
        lastStatus = (online, time_since_epoch_utc())
        write_db("lastStatus", lastStatus)

    if lastStatus[0] != online:
        if online == True:
            title = "Server is back online!"
            color = disnake.Color.from_rgb(0, 255, 0)
            embed = disnake.Embed(title=title, color=color)

            time = for_time(lastStatus[1])
            embed.add_field(name="\u200b", value=f"Server was offline for: {time}")
        else:
            title = "Server has gone offline!"
            color = disnake.Color.from_rgb(255, 0, 0)
            embed = disnake.Embed(color=color)

            time = for_time(lastStatus[1])
            embed.add_field(name="\u200b", value=f"Server was online for: {time}")

        channelId = read_db("channelStatus")
        if channelId is None:
            raise ValueError("No status channel set")

        write_db("lastStatus", [online, time_since_epoch_utc()])
        await getTextChannel(channelId, client).send(embed=embed)


def for_time(time: int) -> str:
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

    def display_time(seconds: int) -> str:
        result: list[str] = []
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append("{} {}".format(value, name))
        return ", ".join(result[:3])

    return display_time(forTime)


def time_since_epoch_utc() -> int:
    utcTime = datetime.datetime.now(datetime.timezone.utc)
    return int(utcTime.timestamp())


def get_weekday_sec() -> tuple[int, int]:
    """Returns the current week day and the time in seconds for the Czech republic"""
    utcTime = datetime.datetime.now(datetime.timezone.utc)
    czechTime = utcTime.astimezone(pytz.timezone("Europe/Vienna"))
    sec = czechTime.hour * 3600 + czechTime.minute * 60 + czechTime.second
    return czechTime.weekday(), sec


def get_sec() -> int:
    """Returns the current time in seconds for the Czech republic"""
    return get_weekday_sec()[1]


def get_week_day() -> int:
    """Returns the current week day in the Czech republic"""
    return get_weekday_sec()[0]


# Returns string of inputed time in seconds to {hours:minutes}
def from_sec_to_time(sec: int) -> str:
    hours = int(sec / 3600)
    minutes = int((sec - hours * 3600) / 60)

    # If minutes is less that 10 then print with 0 in front of minetes {1:01}
    minutesStr = "0" + str(minutes) if minutes < 10 else str(minutes)

    output = f"{hours}:{minutesStr}"
    return output


async def fetch_message(message_channel: int, message_id: int, client: InteractionBot) -> disnake.Message | None:
    try:
        return await getTextChannel(message_channel, client).fetch_message(message_id)
    except:
        print(
            f"""Couldn't get the desired message! Was probably removed!:\n
                message_id: {message_id}, message_channel: {message_channel}"""
        )
        return None


def rand_rgb() -> tuple[int, int, int]:
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def log_html(html: str, filename: str) -> None:
    """Logs the html into a file"""
    timeIdentifier = datetime.datetime.now().strftime("%H-%M")
    with open(f"logs/{filename}-{timeIdentifier}.html", "w", encoding="utf-8") as f:
        f.write(html)
