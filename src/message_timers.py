import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import disnake
from disnake.ext.commands import InteractionBot

from .utils.utils import get_sec, getTextChannel, read_db, write_db

# TODO: Reformat this file


if TYPE_CHECKING:
    from disnake.message import EmojiInputType


@dataclass
class LinkedMessage:
    """Represents a link to a message on discord using it's id and a channel id"""

    id: int
    channelId: int


@dataclass
class MessageTimer:
    message: LinkedMessage
    removeAt: int


@dataclass
class ReactionTimer(MessageTimer):
    reaction: "EmojiInputType"


MessageUnionType = disnake.Message | LinkedMessage
"""Discord message or LinkedMessage type"""


def unionizeMessage(message: MessageUnionType) -> LinkedMessage:
    """Converts a discord message to a LinkedMessage. If the message is already a LinkedMessage, it returns it as is"""
    if isinstance(message, disnake.Message):
        return discordMessageToLinkedMessage(message)
    else:
        return message


def discordMessageToLinkedMessage(message: disnake.Message) -> LinkedMessage:
    """Converts a discord message to a LinkedMessage"""
    return LinkedMessage(message.id, message.channel.id)


class MessageTimers:
    timers: list[MessageTimer] = []
    timers_reactions: list[ReactionTimer] = []

    cached_messages_react: list[disnake.Message] = []

    @staticmethod
    async def delete_message(
        message: MessageUnionType,
        database: str,
        client: InteractionBot,
        delay: int = 0,
    ) -> None:
        """Deletes the specified message from the chat after some delay"""
        linkedMessage = unionizeMessage(message)

        await MessageTimers.message_cache(client, message)

        # Puts the message into the timer variable
        remove_at = get_sec() + delay
        messageTimer = MessageTimer(linkedMessage, remove_at)
        MessageTimers.timers.append(messageTimer)

        # Adds the message into the database
        messagesDatabase: list[MessageTimer] | None = read_db(database)
        if messagesDatabase is None:
            raise Exception(f"Database '{database}' doesn't exist!")

        if not linkedMessage in [messageTimerDb.message for messageTimerDb in messagesDatabase]:
            messagesDatabase.append(messageTimer)
            write_db(database, messagesDatabase)

        # Sleeps for the time of the delay
        await asyncio.sleep(delay)

        for timer in MessageTimers.timers:
            if linkedMessage == timer.message:
                # Checks if the message remove time was changed while sleeping
                if remove_at == timer.removeAt:
                    try:
                        textChannel = getTextChannel(linkedMessage.channelId, client)
                        fetchedMessage = await textChannel.fetch_message(linkedMessage.id)
                        await fetchedMessage.delete()
                    except:
                        print(
                            f"""Couldn't get the desired message! Was probably removed!:\n
                                message_id: {linkedMessage.id}, message_channel: {linkedMessage.channelId}"""
                        )
                    finally:
                        activeTimersRemove = [timer for timer in MessageTimers.timers if linkedMessage == timer.message]
                        for activeTimerRemove in activeTimersRemove:
                            MessageTimers.timers.remove(activeTimerRemove)

                        messagesDatabase = read_db(database)
                        if messagesDatabase is None:
                            raise Exception(f"Database '{database}' doesn't exist!")

                        messagesRemove = [message for message in messagesDatabase if linkedMessage == message.message]
                        for messageRemove in messagesRemove[:]:
                            messagesDatabase.remove(messageRemove)
                        write_db(database, messagesDatabase)
                        return

    @staticmethod
    async def delete_message_reaction(
        message: MessageUnionType,
        database: str,
        reaction: "EmojiInputType",
        client: InteractionBot,
        delay: int = 0,
    ) -> None:
        """Deletes the specified reaction from the message after some delay"""
        linkedMessage = unionizeMessage(message)

        await MessageTimers.message_cache(client, message)

        # Puts the message into the timer variable
        remove_at = get_sec() + delay
        reactionTimer = ReactionTimer(linkedMessage, remove_at, reaction)
        MessageTimers.timers_reactions.append(ReactionTimer(linkedMessage, remove_at, reaction))

        # Adds the message into the database
        messagesDatabase: list[ReactionTimer] | None = read_db(database)
        if messagesDatabase is None:
            raise Exception(f"Database '{database}' doesn't exist!")

        if not [linkedMessage, reaction] in [
            [reactionTimer.message, reactionTimer.reaction] for reactionTimer in messagesDatabase
        ]:
            messagesDatabase.append(reactionTimer)
            write_db(database, messagesDatabase)

        # Sleeps for the time of the delay
        await asyncio.sleep(delay)

        for timer in MessageTimers.timers_reactions:
            if linkedMessage == timer.message:
                # Checks if the message remove time was changed while sleeping
                if reactionTimer.removeAt == timer.removeAt:
                    try:
                        textChanel = getTextChannel(linkedMessage.channelId, client)
                        fetchedMessage = await textChanel.fetch_message(linkedMessage.id)
                    except:
                        print(
                            f"""Couldn't get the desired message! Was probably removed!:\n
                                message_id: {linkedMessage.id}, message_channel: {linkedMessage.channelId}"""
                        )
                    else:
                        try:
                            await fetchedMessage.clear_reaction(reaction)
                        except:
                            print(
                                f"""Couldn't find the desired reaction! Was probably removed!:\n
                                message_id: {linkedMessage.id}, message_channel: {linkedMessage.channelId}, reaction: {reaction}"""
                            )
                    finally:
                        activeTimersRemove = [
                            timer
                            for timer in MessageTimers.timers_reactions
                            if linkedMessage == timer.message and reaction == timer.reaction
                        ]
                        for activeTimerRemove in activeTimersRemove:
                            MessageTimers.timers.remove(activeTimerRemove)

                        messagesDatabase = read_db(database)
                        if messagesDatabase is None:
                            raise Exception(f"Database '{database}' doesn't exist!")

                        messagesRemove = [
                            message
                            for message in messagesDatabase
                            if linkedMessage == message.message and reaction == message.reaction
                        ]
                        for messageRemove in messagesRemove[:]:
                            messagesRemove.remove(messageRemove)
                        write_db(database, messagesRemove)
                        return

    @staticmethod
    async def query_messages(database: str, client: InteractionBot) -> list[disnake.Message]:
        """Queries the messages from a specified database"""

        messagesTimers: list[MessageTimer] | None = read_db(database)
        if messagesTimers is None:
            raise Exception(f"Database '{database}' doesn't exist!")

        foundMessages: list[disnake.Message] = []
        for messageTimer in messagesTimers:
            message = messageTimer.message
            try:
                discordMessage = await getTextChannel(message.channelId, client).fetch_message(message.id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n\t
                        message_id: {message.id}, message_channel: {message.channelId}"""
                )
                toRemoveMessages: list[MessageTimer] | None = read_db(database)
                if toRemoveMessages is None:
                    raise Exception(f"Database '{database}' doesn't exist!")

                toRemoveMessages.remove(messageTimer)
                write_db(database, toRemoveMessages)
            else:
                await MessageTimers.message_cache(client, message)
                foundMessages.append(discordMessage)
        return foundMessages

    @staticmethod
    async def query_messages_reactions(database: str, client: InteractionBot) -> list[disnake.Message]:
        """Queries the reactions from a specified database into the current running client"""

        reactionTimers: list[ReactionTimer] | None = read_db(database)
        if reactionTimers is None:
            raise Exception(f"Database '{database}' doesn't exist!")

        foundMessages: list[disnake.Message] = []
        for reactionTimer in reactionTimers:
            message = reactionTimer.message
            try:
                discordMessage = await getTextChannel(message.channelId, client).fetch_message(message.id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n\t
                        message_id: {message.id}, message_channel: {message.channelId}"""
                )
                toRemoveMessages: list[ReactionTimer] | None = read_db(database)
                if toRemoveMessages is None:
                    raise Exception(f"Database '{database}' doesn't exist!")

                toRemoveMessages.remove(reactionTimer)
                write_db(database, toRemoveMessages)
            else:
                if reactionTimer.reaction in [reaction.emoji for reaction in discordMessage.reactions]:
                    await MessageTimers.message_cache(client, message)
                    foundMessages.append(discordMessage)
                else:
                    toRemoveMessages = read_db(database)
                    if toRemoveMessages is None:
                        raise Exception(f"Database '{database}' doesn't exist!")

                    toRemoveMessages.remove(reactionTimer)
                    write_db(database, toRemoveMessages)
        return foundMessages

    @staticmethod
    async def message_cache(client: InteractionBot, message: MessageUnionType) -> None:
        """Adds the message into the clients custom cached messages"""
        if isinstance(message, LinkedMessage):
            try:
                discordMessage = await getTextChannel(message.channelId, client).fetch_message(message.id)
            except:
                print(
                    f"""Couldn't get the desired message! Was probably removed!:\n
                        message_id: {message.id}, message_channel: {message.channelId}"""
                )
            else:
                if not discordMessage in MessageTimers.cached_messages_react:
                    MessageTimers.cached_messages_react.append(discordMessage)
        elif not message in MessageTimers.cached_messages_react:
            MessageTimers.cached_messages_react.append(message)
