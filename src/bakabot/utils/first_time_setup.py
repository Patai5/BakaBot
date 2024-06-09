import os

from core.grades.grades import Grades
from core.schedule.schedule import ChangeDetector, Schedule
from disnake.ext.commands import InteractionBot
from utils.utils import read_db, write_db


# Prints the error to console
def setup_channel_error_message(channel: str):
    errorMessage = (
        f"Setup the bot setting channel{channel} to a specific channel by typing the command: "
        f'"/channel function:{channel}" in your desired discord channel'
    )
    print(errorMessage)


async def start(client: InteractionBot) -> bool:
    """Initializes the bot and returns a boolean value indicating whether the bot was initialized successfully"""

    if not os.path.isdir("./db"):
        os.mkdir("./db")
    if not os.path.isdir("./logs"):
        os.mkdir("./logs")

    ready = True
    if not read_db("channelGrades"):
        setup_channel_error_message("Grades")
        ready = False
    if not read_db("channelReminder"):
        setup_channel_error_message("Reminder")
        ready = False
    if not read_db("channelSchedule"):
        setup_channel_error_message("Schedule")
        ready = False
    if not read_db("channelStatus"):
        setup_channel_error_message("Status")
        ready = False

    if not ready:
        print("Restart the bot after you are done setting up the bot")
        return False

    if not read_db("gradesMessages"):
        write_db("gradesMessages", [])
    if not read_db("predictorMessages"):
        write_db("predictorMessages", [])
    if not read_db("responseChannels"):
        write_db("responseChannels", {})
    if read_db("showDay") == None:
        write_db("showDay", False)
    if read_db("showClassroom") == None:
        write_db("showClassroom", False)
    if read_db("reminderShort") == None:
        write_db("reminderShort", False)
    if read_db("subjects") == None:
        write_db("subjects", [])

    if not read_db("schedule1") or not read_db("schedule2"):
        schedule1 = await Schedule.get_schedule(False, client)
        schedule2 = await Schedule.get_schedule(True, client)
        if schedule1 is None or schedule2 is None:
            print("Bakalari's server is currently down. Wait until the server is back online and then restart the bot")
            return False
        else:
            ChangeDetector.handle_update_subjects_cache((schedule1, schedule2), client)
            schedule1.db_save()
            schedule2.db_save()
    if not read_db("grades"):
        grades = await Grades.getGrades(client)
        if grades is None:
            print("Bakalari's server is currently down. Wait until the server is back online and then restart the bot")
            return False
        else:
            Grades.handle_update_subjects_cache(grades.grades, client)
            grades.db_save()

    return True
