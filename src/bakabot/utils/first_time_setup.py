import logging
import os

import discord
from core.schedule.schedule import Schedule

from bakabot.core.grades import Grades
from bakabot.utils.utils import read_db, write_db


# Prints the error to console
def setup_channel_error_message(channel: str):
    errorMessage = (
        f'Setup the bot setting channel{channel} to a specific channel by typing the command: "BakaBot settings '
        f'channel{channel}" in your desired discord channel'
    )
    print(errorMessage)


async def start(client: discord.Client):
    # First time startup
    if not os.path.isdir("./db"):
        os.mkdir("./db")
    if not os.path.isdir("./logs"):
        os.mkdir("./logs")
    if not read_db("schedule1") or not read_db("schedule2"):
        schedule1 = await Schedule.get_schedule(False, client)
        schedule2 = await Schedule.get_schedule(True, client)
        if schedule1 is None or schedule2 is None:
            print("Bakalari's server is currently down. Wait until the server is back online and then restart the bot")
            return None
        else:
            schedule1.db_save()
            schedule2.db_save()
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
    if not read_db("responseChannels"):
        write_db("responseChannels", {})
    if read_db("showDay") == None:
        write_db("showDay", False)
    if read_db("showClassroom") == None:
        write_db("showClassroom", False)
    if read_db("reminderShort") == None:
        write_db("reminderShort", False)
    # Looks if the bot was properly setup before continueing
    ready = True
    if read_db("html2imgBrowserPath") == None:
        write_db(
            "html2imgBrowserPath",
            input("Please enter the path to your browser executable (Leave empty for auto by Pyppeteer): "),
        )
        ready = False
    if not read_db("channelGrades"):
        setup_channel_error_message("Grades")
        ready = False
    elif not read_db("channelReminder"):
        setup_channel_error_message("Reminder")
        ready = False
    elif not read_db("channelSchedule"):
        setup_channel_error_message("Schedule")
        ready = False
    elif not read_db("channelStatus"):
        setup_channel_error_message("Status")
        ready = False

    if ready:
        return True
    else:
        print("Restart the bot after you are done setting up the bot")
