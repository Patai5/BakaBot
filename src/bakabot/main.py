import asyncio
import logging

import disnake
from bot_commands.bot_commands import setupBotInteractions
from bot_commands.reactions import Reactions
from core.grades.grades import Grades
from core.reminder import startReminder
from core.schedule.schedule import ChangeDetector
from core.subjects.subjects_cache import SubjectsCache
from disnake.ext import commands
from disnake.ext.commands import InteractionBot
from message_timers import MessageTimers
from utils import first_time_setup
from utils.utils import env_load, getTextChannel, os_environ

logger = logging.getLogger("discord")
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"))
logger.addHandler(handler)


def main():
    env_load()

    client = commands.InteractionBot(intents=disnake.Intents.all())

    async def on_ready():
        print("Ready!")

        setupBotInteractions(client)

        startedSuccessfully = await first_time_setup.start(client)
        if not startedSuccessfully:
            return

        await client.change_presence(activity=disnake.Activity(name="Bakaláři", type=3))
        initialize_features()
        await start_feature_couroutines(client)

    @client.event
    async def on_raw_reaction_add(reaction: disnake.RawReactionActionEvent):
        for message in MessageTimers.cached_messages_react:
            if reaction.message_id == message.id:
                if reaction.member is None:
                    raise Exception("Reaction member is None")

                if not reaction.member.bot:
                    await Reactions(
                        await getTextChannel(reaction.channel_id, client).fetch_message(reaction.message_id),
                        reaction.member,
                        reaction.emoji,
                        client,
                    ).execute()

    client.add_listener(on_ready)
    client.add_listener(on_raw_reaction_add)

    client.run(os_environ("token"))


# Starts couroutines needed for some features
async def start_feature_couroutines(client: InteractionBot):
    await asyncio.gather(
        Reactions.query(client),
        ChangeDetector.start_detecting_changes(60, client),
        Grades.start_detecting_changes(60, client),
        startReminder(client),
    )


def initialize_features():
    """Initializes key components of the bot"""

    SubjectsCache.initialize()


if __name__ == "__main__":
    main()
