import logging

import disnake
from disnake.ext import commands

from .bot_commands.bot_commands import setupBotInteractions
from .bot_commands.reactions import Reactions
from .feature_manager.feature_initializer import getFeatureManager
from .message_timers import MessageTimers
from .utils.first_time_setup import initializeDatabase
from .utils.utils import env_load, getTextChannel, os_environ

logger = logging.getLogger("discord")
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"))
logger.addHandler(handler)


def main() -> None:
    env_load()

    client = commands.InteractionBot(intents=disnake.Intents.all())

    async def on_ready() -> None:
        print("Ready!")

        initializeDatabase()

        featureManager = getFeatureManager()
        setupBotInteractions(client, featureManager)

        await client.change_presence(activity=disnake.Activity(name="Bakaláři", type=3))
        await featureManager.initialize(client)

    @client.event
    async def on_raw_reaction_add(reaction: disnake.RawReactionActionEvent) -> None:
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


if __name__ == "__main__":
    main()
