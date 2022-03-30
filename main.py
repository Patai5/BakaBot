import asyncio
import logging

import discord

from core.bot_commands import Commands
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
    # keep_alive()

    client = discord.Client()

    # After client gets ready
    @client.event
    async def on_ready():
        print("Ready!")

        await client.change_presence(activity=discord.Activity(name="Bakaláři", type=3))
        await start_feature_couroutines(client)

    @client.event
    async def on_message(message):
        if not message.author.bot:
            await Commands(message, client).execute()

    token = os_environ("token")
    client.run(token)


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
    else:
        # First time startup
        if not read_db("schedule1"):
            write_db("schedule1", Schedule.json_dumps(await Schedule.get_schedule(False)))
        if not read_db("schedule2"):
            write_db("schedule2", Schedule.json_dumps(await Schedule.get_schedule(True)))
        if not read_db("grades"):
            write_db("grades", Grades.json_dumps(await Grades.get_grades()))

        # Starts the courutines
        await asyncio.gather(
            Schedule.start_detecting_changes(60, client),
            Grades.start_detecting_changes(60, client),
            Reminder.start_reminding(client),
        )


if __name__ == "__main__":
    main()
