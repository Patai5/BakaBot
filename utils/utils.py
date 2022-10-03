import asyncio
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
    return os.environ[key]


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


class MessageTimers:
    timers = []
    timers_reactions = []

    @staticmethod
    async def delete_message(
        message: discord.Message or list[int, int],
        database: str,
        client: discord.Client,
        delay: int = 0,
        function=None,
    ):
        """Deletes the specified message from the chat after some delay\n
        message = discord.Message or list[message_id, message_channel]"""
        if type(message) == discord.Message:
            message_id = message.id
            message_channel = message.channel.id
        else:
            message_id = message[0]
            message_channel = message[1]

        await MessageTimers.message_cache(client, message)

        # Puts the message into the timer variable
        remove_at = get_sec() + delay
        MessageTimers.timers.append([message_id, message_channel, remove_at])

        # Adds the message into the database
        messeges_database = read_db(database)
        if not [message_id, message_channel] in [[message[0], message[1]] for message in messeges_database]:
            messeges_database.append([message_id, message_channel, remove_at])
            write_db(database, messeges_database)

        # Sleeps for the time of the delay
        await asyncio.sleep(delay)

        for timer in MessageTimers.timers:
            if message_id == timer[0] and message_channel == timer[1]:
                # Checks if the message remove time was changed while sleeping
                if remove_at == timer[2]:
                    try:
                        message = await client.get_channel(message_channel).fetch_message(message_id)
                        await message.delete()
                    except:
                        print(
                            f"""Couldn't get the desired message! Was probably removed!:\n
                                message_id: {message_id}, message_channel: {message_channel}"""
                        )
                    finally:
                        if function:
                            function()

                        activeTimersRemove = [
                            timer
                            for timer in MessageTimers.timers
                            if timer[0] == message_id and timer[1] == message_channel
                        ]
                        for activeTimerRemove in activeTimersRemove:
                            MessageTimers.timers.remove(activeTimerRemove)

                        messages_database = read_db(database)
                        messagesRemove = [
                            message
                            for message in messages_database
                            if message[0] == message_id and message[1] == message_channel
                        ]
                        for messageRemove in messagesRemove:
                            messages_database.remove(messageRemove)
                        write_db(database, messages_database)
                        return

    @staticmethod
    def stop_message_removal(message: discord.Message or list[int, int], database: str, client: discord.Client):
        """Stops the specified message from being removed from the chat\n
        message = discord.Message or list[message_id, message_channel]"""
        if type(message) == discord.Message:
            message_id = message.id
            message_channel = message.channel.id
        else:
            message_id = message[0]
            message_channel = message[1]

        messeges_database = read_db(database)
        for timer in messeges_database[:]:
            if message_id == timer[0]:
                messeges_database.remove(timer)
        write_db(database, messeges_database)

        for timer in MessageTimers.timers[:]:
            if message_id == timer[0]:
                MessageTimers.timers.remove(timer)

    @staticmethod
    async def delete_message_reaction(
        message: discord.Message or list[int, int],
        database: str,
        reaction: discord.emoji,
        client: discord.Client,
        delay: int = 0,
    ):
        """Deletes the specified reaction from the message after some delay\n
        message = discord.Message or list[message_id, message_channel]"""
        if type(message) == discord.Message:
            message_id = message.id
            message_channel = message.channel.id
        else:
            message_id = message[0]
            message_channel = message[1]

        await MessageTimers.message_cache(client, message)

        # Puts the message into the timer variable
        remove_at = get_sec() + delay
        MessageTimers.timers_reactions.append([message_id, message_channel, reaction, remove_at])

        # Adds the message into the database
        messeges_database = read_db(database)
        if not [message_id, message_channel, reaction] in [
            [message[0], message[1], message[2]] for message in messeges_database
        ]:
            messeges_database.append([message_id, message_channel, reaction, remove_at])
            write_db(database, messeges_database)

        # Sleeps for the time of the delay
        await asyncio.sleep(delay)

        for timer in MessageTimers.timers_reactions:
            if message_id == timer[0] and message_channel == timer[1]:
                # Checks if the message remove time was changed while sleeping
                if remove_at == timer[3]:
                    try:
                        message = await client.get_channel(message_channel).fetch_message(message_id)
                    except:
                        print(
                            f"""Couldn't get the desired message! Was probably removed!:\n
                                message_id: {message_id}, message_channel: {message_channel}"""
                        )
                    else:
                        try:
                            await message.clear_reaction(reaction)
                        except:
                            print(
                                f"""Couldn't find the desired reaction! Was probably removed!:\n
                                message_id: {message_id}, message_channel: {message_channel}, reaction: {reaction}"""
                            )
                    finally:
                        activeTimersRemove = [
                            timer
                            for timer in MessageTimers.timers
                            if timer[0] == message_id and timer[1] == message_channel
                        ]
                        for activeTimerRemove in activeTimersRemove:
                            MessageTimers.timers.remove(activeTimerRemove)

                        messages_database = read_db(database)
                        messagesRemove = [
                            message
                            for message in messages_database
                            if message[0] == message_id and message[1] == message_channel
                        ]
                        for messageRemove in messagesRemove:
                            messages_database.remove(messageRemove)
                        write_db(database, messages_database)
                        return

    @staticmethod
    async def query_messages(database: str, client: discord.Client):
        """Queries the messages from a specified database"""

        messages = read_db(database)
        foundMessages = []
        for message in messages:
            message_id = message[0]
            message_channel = message[1]
            remove_at = message[2]
            try:
                message = await client.get_channel(message_channel).fetch_message(message_id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n\t
                        message_id: {message_id}, message_channel: {message_channel}"""
                )
                toRemoveMessages = read_db(database)
                toRemoveMessages.remove([message_id, message_channel, remove_at])
                write_db(database, toRemoveMessages)
            else:
                await MessageTimers.message_cache(client, message)
                foundMessages.append(message)
        return foundMessages

    @staticmethod
    async def query_messages_reactions(database: str, client: discord.Client):
        """Queries the reactions from a specified database into the current running client"""

        messages = read_db(database)
        foundMessages = []
        for message in messages:
            message_id = message[0]
            message_channel = message[1]
            reaction = message[2]
            remove_at = message[3]
            try:
                message = await client.get_channel(message_channel).fetch_message(message_id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n\t
                        message_id: {message_id}, message_channel: {message_channel}"""
                )
                toRemoveMessages = read_db(database)
                toRemoveMessages.remove([message_id, message_channel, reaction, remove_at])
                write_db(database, toRemoveMessages)
            else:
                if reaction in [reaction.emoji for reaction in message.reactions]:
                    await MessageTimers.message_cache(client, message)
                    foundMessages.append(message)
                else:
                    toRemoveMessages = read_db(database)
                    toRemoveMessages.remove([message_id, message_channel, reaction, remove_at])
                    write_db(database, toRemoveMessages)
        return foundMessages

    @staticmethod
    async def message_cache(client: discord.Client, message: discord.Message):
        """Adds the message into the clients custom cached messages"""
        if not type(message) == discord.Message:
            message_id = message[0]
            message_channel = message[1]
            try:
                message = await client.get_channel(message_channel).fetch_message(message_id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n
                        message_id: {message_id}, message_channel: {message_channel}"""
                )
            else:
                if not message in client.cached_messages_react:
                    client.cached_messages_react.append(message)
        if not message in client.cached_messages_react:
            client.cached_messages_react.append(message)

    @staticmethod
    def response_channel_cache(channel: int, client: discord.Client, responseChannelType: str, remove: bool = False):
        """Adds/Removes the response channel from the client cache"""
        if remove:
            if channel in client.response_channel_cache:
                del client.response_channel_cache[channel]
        else:
            if not channel in client.response_channel_cache:
                client.response_channel_cache[channel] = responseChannelType

    @staticmethod
    def response_channel(
        channel: int, user: int, message: int, responseFor: str, client: discord.Client, remove: bool = False
    ):
        """Adds/Removes the response channel from the database and client cache"""
        database = f"{responseFor}ResponseChannel"
        responseChannelUsers = read_db(database)
        if remove:
            if user in responseChannelUsers:
                responseChannelUsers.pop(user)
                write_db(database, responseChannelUsers)
                if not responseChannelUsers:
                    responseChannels = read_db("responseChannels")
                    responseChannels.pop(channel)
                    write_db("responseChannels", responseChannels)
                    MessageTimers.response_channel_cache(channel, client, responseFor, remove)
        else:
            if user not in responseChannelUsers:
                responseChannelUsers[user] = message
                write_db(database, responseChannelUsers)
                responseChannels = read_db("responseChannels")
                if channel not in responseChannels:
                    responseChannels[channel] = responseFor
                    write_db("responseChannels", responseChannels)
                    MessageTimers.response_channel_cache(channel, client, responseFor, remove)
