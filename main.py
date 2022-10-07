import asyncio
import logging

import discord

import utils.first_time_setup as first_time_setup
from core.bot_commands import COGS, Reactions, Responses
from core.grades import Grades
from core.reminder import Reminder
from core.schedule import Schedule
from html2img.html2img import Html2img
from utils.utils import env_load, os_environ

logger = logging.getLogger("discord")
logger.setLevel(level=logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


def main():
    env_load()

    client = discord.Bot(command_prefix=None, intents=discord.Intents.all())

    for cog in COGS:
        client.add_cog(cog(client))

    client.cached_messages_react = []
    client.response_channel_cache = {}

    # After client gets ready
    @client.event
    async def on_ready():
        print("Ready!")

        await client.change_presence(activity=discord.Activity(name="Bakaláři", type=3))
        await start_feature_couroutines(client)

    @client.event
    async def on_message(message: discord.Message):
        if not message.author.bot:
            await Responses(message, client).execute()

    @client.event
    async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
        for message in client.cached_messages_react:
            if reaction.message_id == message.id:
                if not reaction.member.bot:
                    await Reactions(
                        await client.get_channel(reaction.channel_id).fetch_message(reaction.message_id),
                        reaction.member,
                        reaction.emoji,
                        client,
                    ).execute()

    client.run(os_environ("token"))


# Starts couroutines needed for some features
async def start_feature_couroutines(client: discord.Client):
    if await first_time_setup.start(client):
        # Starts the courutines
        await asyncio.gather(
            Html2img.browser_init(),
            Reactions.query(client),
            Responses.query(client),
            Schedule.start_detecting_changes(60, client),
            Grades.start_detecting_changes(60, client),
            Reminder.start_reminding(client),
        )


if __name__ == "__main__":
    main()
