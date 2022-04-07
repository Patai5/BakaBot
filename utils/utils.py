import asyncio
import datetime
import os

import aiohttp
import discord
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


class MessageTimers:
    timers = []
    timers_reactions = []

    @staticmethod
    async def delete_message(
        message: discord.Message or list[int, int], database: str, client: discord.Client, delay: int = 0
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
    async def message_cache(client, message):
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
