from __future__ import annotations

import asyncio
import datetime

import disnake
from disnake.ext.commands import InteractionBot

from ..constants import PREDICTOR_EMOJI
from ..core.predictor import create_prediction, get_stage, update_grade, update_weight
from ..message_timers import MessageTimer, MessageTimers
from ..utils.utils import read_db


class Reactions:
    def __init__(
        self,
        message: disnake.Message,
        user: disnake.Member,
        emoji: disnake.PartialEmoji,
        client: InteractionBot,
    ):
        self.message = message
        self.user = user
        self.emoji = emoji
        self.client = client
        self.userReactions = [reaction for reaction in self.message.reactions if reaction.count > 1]

    class Predictor:
        queryMessagesDatabase = "predictorMessages"

        @classmethod
        async def query(cls, client: InteractionBot) -> None:
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
        async def execute(cls, reaction: Reactions) -> None:
            stage = get_stage(reaction.message)
            if stage == 1:
                await update_grade(reaction, reaction.client)
            elif stage == 2:
                await update_weight(reaction, reaction.client)

    class Grades:
        queryMessagesDatabase = "gradesMessages"

        @classmethod
        async def query(cls, client: InteractionBot) -> None:
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages_reactions(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                    if createdFromNowSec > 5400:
                        await MessageTimers.delete_message_reaction(
                            message, cls.queryMessagesDatabase, PREDICTOR_EMOJI, client
                        )
                    else:
                        asyncio.ensure_future(
                            MessageTimers.delete_message_reaction(
                                message,
                                cls.queryMessagesDatabase,
                                PREDICTOR_EMOJI,
                                client,
                                5400 - createdFromNowSec,
                            )
                        )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction: Reactions) -> None:
            if reaction.emoji.name == PREDICTOR_EMOJI:
                await create_prediction(reaction.message, reaction.client)

    REACTIONS: set[type[Predictor] | type[Grades]] = {Predictor, Grades}

    # Executes the message's command
    async def execute(self) -> None:
        for user in self.message.reactions:
            if user.me:
                for reaction in Reactions.REACTIONS:
                    if reaction.queryMessagesDatabase:
                        reactionDatabase: list[MessageTimer] | None = read_db(reaction.queryMessagesDatabase)
                        if reactionDatabase is None:
                            raise ValueError("Reaction database not found")

                        for message in reactionDatabase:
                            if self.message.id == message.message.id:
                                await reaction.execute(self)
                                return

    @staticmethod
    async def query(client: InteractionBot) -> None:
        for reaction in Reactions.REACTIONS:
            if reaction.queryMessagesDatabase:
                asyncio.ensure_future(reaction.query(client))
