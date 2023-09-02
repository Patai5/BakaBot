import asyncio
import copy
import datetime

import discord
from core.grades.grades import Grades
from utils.utils import MessageTimers, read_db, write_db


class Reactions:
    def __init__(self, message: discord.Message, user: discord.Member, emoji: discord.emoji, client: discord.Client):
        self.message = message
        self.user = user
        self.emoji = emoji
        self.client = client
        self.userReactions = [reaction for reaction in self.message.reactions if reaction.count > 1]

    class Predictor:
        queryMessagesDatabase = "predictorMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    if message.edited_at:
                        editedFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.edited_at).seconds
                        if editedFromNowSec > 300:
                            await MessageTimers.delete_message(message, cls.queryMessagesDatabase, client)
                        else:
                            asyncio.ensure_future(
                                MessageTimers.delete_message(
                                    message,
                                    cls.queryMessagesDatabase,
                                    client,
                                    300 - editedFromNowSec,
                                )
                            )
                    else:
                        createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                        if createdFromNowSec > 300:
                            await MessageTimers.delete_message(message, cls.queryMessagesDatabase, client)
                        else:
                            asyncio.ensure_future(
                                MessageTimers.delete_message(
                                    message,
                                    cls.queryMessagesDatabase,
                                    client,
                                    300 - createdFromNowSec,
                                )
                            )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction):
            stage = Predictor.get_stage(reaction.message)
            if stage == 1:
                await Predictor.update_grade(reaction, reaction.client)
            elif stage == 2:
                await Predictor.update_weight(reaction, reaction.client)

    class Grades:
        queryMessagesDatabase = "gradesMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages_reactions(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                    if createdFromNowSec > 5400:
                        await MessageTimers.delete_message_reaction(
                            message, cls.queryMessagesDatabase, Grades.PREDICTOR_EMOJI, client
                        )
                    else:
                        asyncio.ensure_future(
                            MessageTimers.delete_message_reaction(
                                message,
                                cls.queryMessagesDatabase,
                                Grades.PREDICTOR_EMOJI,
                                client,
                                5400 - createdFromNowSec,
                            )
                        )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction):
            if reaction.emoji.name == Grades.PREDICTOR_EMOJI:
                await Grades.create_predection(reaction.message, reaction.client)

    REACTIONS = {Predictor, Grades}

    # Executes the message's command
    async def execute(self):
        for user in self.message.reactions:
            if user.me:
                for reaction in Reactions.REACTIONS:
                    if reaction.queryMessagesDatabase:
                        for message in read_db(reaction.queryMessagesDatabase):
                            if self.message.id == message[0]:
                                await reaction.execute(self)
                                return

    @staticmethod
    async def query(client: discord.Client):
        for reaction in Reactions.REACTIONS:
            if reaction.queryMessagesDatabase:
                asyncio.ensure_future(reaction.query(client))


class Responses:
    def __init__(self, message: discord.Message, client: discord.Client):
        self.message = message
        self.client = client
        self.isResponse = message.channel.id in self.client.response_channel_cache

    # Executes the message's command
    async def execute(self):
        if self.isResponse:
            responseFor = self.RESPONSE_FOR.get(self.client.response_channel_cache.get(self.channel.id))
            await responseFor.response(self.message, self.client)

    @staticmethod
    async def query(client: discord.Client):
        """Queries the response channels to the client cache and removes the messages to be removed"""
        responseChannels = read_db("responseChannels")
        for responseChannel in copy.copy(responseChannels):
            users = read_db(f"{responseChannels[responseChannel]}ResponseChannel")
            for user in copy.copy(users):
                try:
                    message = await client.get_channel(responseChannel).fetch_message(users[user])
                except:
                    print(
                        f"""Couldn't get the desired message! Was probably removed!:\n
                        message_id: {users[user]}, message_channel: {responseChannel}"""
                    )
                    del users[user]
            write_db(f"{responseChannels[responseChannel]}ResponseChannel", users)
            if users:
                client.response_channel_cache[responseChannel] = responseChannels[responseChannel]
            else:
                del responseChannels[responseChannel]
        write_db("responseChannels", responseChannels)

        for response in Responses.RESPONSES:
            if response.queryMessagesDatabase:
                await response.query(client)
