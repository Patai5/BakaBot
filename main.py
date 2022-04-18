import asyncio
import logging
import os

import discord

from core.bot_commands import Commands, Reactions
from core.grades import Grades
from core.keep_alive import keep_alive
from core.reminder import Reminder
from core.schedule import Schedule
from utils.utils import os_environ, read_db, write_db

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


def main():
    # Keeps the replit on
    keep_alive()

    client = discord.Client(guild_ready_timeout=0)
    client.cached_messages_react = []

    # After client gets ready
    @client.event
    async def on_ready():
        print("Ready!")

        await client.change_presence(activity=discord.Activity(name="Bakaláři", type=3))
        await start_feature_couroutines(client)

    @client.event
    async def on_message(message: discord.Message):
        if not message.author.bot:
            await Commands(message, client).execute()

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

    token = os_environ("token")
    try:
        client.run(token)
    # Resets the replit server if needed
    except:
        os.system("kill 1")


# Starts couroutines needed for some features
async def start_feature_couroutines(client: discord.Client):
    # Prints the error to console
    def setup_channel_error_message(channel: str):
        errorMessage = (
            f'Setup the bot setting channel{channel} to a specific channel by typing the command: "BakaBot settings '
            f'channel{channel}" in your desired discord channel and then restart the bot'
        )
        print(errorMessage)

    # Looks if the bot was properly setup before continueing
    if not read_db("channelGrades"):
        setup_channel_error_message("Grades")
    elif not read_db("channelReminder"):
        setup_channel_error_message("Reminder")
    elif not read_db("channelSchedule"):
        setup_channel_error_message("Schedule")
    elif not read_db("channelStatus"):
        setup_channel_error_message("Status")
    else:
        # First time startup
        if not read_db("schedule1") or not read_db("schedule2"):
            schedule1 = await Schedule.get_schedule(False, client)
            schedule2 = await Schedule.get_schedule(True, client)
            if schedule1 is None or schedule2 is None:
                print(
                    "Bakalari's server is currently down. Wait until the server is back online and then restart the bot"
                )
                return None
            else:
                write_db("schedule1", Schedule.json_dumps(schedule1))
                write_db("schedule2", Schedule.json_dumps(schedule2))
        elif not read_db("grades"):
            grades = await Grades.get_grades(client)
            if grades is None:
                print(
                    "Bakalari's server is currently down. Wait until the server is back online and then restart the bot"
                )
                return None
            else:
                write_db("grades", Grades.json_dumps(grades))
        if not read_db("gradesMessages"):
            write_db("gradesMessages", [])
        if not read_db("predictorMessages"):
            write_db("predictorMessages", [])

        # Starts the courutines
        await asyncio.gather(
            Reactions.query(client),
            Schedule.start_detecting_changes(60, client),
            Grades.start_detecting_changes(60, client),
            Reminder.start_reminding(client),
        )


if __name__ == "__main__":
    main()
