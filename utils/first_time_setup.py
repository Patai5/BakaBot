import os

import discord
from core.grades import Grades
from core.schedule import Schedule

from utils.utils import read_db, write_db


# Prints the error to console
def setup_channel_error_message(channel: str):
    errorMessage = (
        f'Setup the bot setting channel{channel} to a specific channel by typing the command: "BakaBot settings '
        f'channel{channel}" in your desired discord channel and then restart the bot'
    )
    print(errorMessage)


async def start(client: discord.Client):
    # First time startup
    if not os.path.isdir("./db"):
        os.mkdir("./db")
    if not read_db("schedule1") or not read_db("schedule2"):
        schedule1 = await Schedule.get_schedule(False, client)
        schedule2 = await Schedule.get_schedule(True, client)
        if schedule1 is None or schedule2 is None:
            print("Bakalari's server is currently down. Wait until the server is back online and then restart the bot")
            return None
        else:
            write_db("schedule1", Schedule.json_dumps(schedule1))
            write_db("schedule2", Schedule.json_dumps(schedule2))
    if not read_db("grades"):
        grades = await Grades.get_grades(client)
        if grades is None:
            print("Bakalari's server is currently down. Wait until the server is back online and then restart the bot")
            return None
        elif grades == False:
            write_db("grades", Grades.json_dumps(Grades([])))
        else:
            write_db("grades", Grades.json_dumps(grades))
    if not read_db("gradesMessages"):
        write_db("gradesMessages", [])
    if not read_db("predictorMessages"):
        write_db("predictorMessages", [])
    if not read_db("betts"):
        write_db("betts", {})
    if not read_db("bettMessages"):
        write_db("bettMessages", [])
    if not read_db("bettingMessages"):
        write_db("bettingMessages", [])
    if not read_db("responseChannels"):
        write_db("responseChannels", {})
    if not read_db("bettingScore"):
        write_db("bettingScore", {})
    if not read_db("bettingResponseChannel"):
        write_db("bettingResponseChannel", {})
    if not read_db("bettingSchedule"):
        write_db("bettingSchedule", Schedule.json_dumps(Schedule.db_schedule(False)))
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
        return True
