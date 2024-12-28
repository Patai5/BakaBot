import os

from utils.utils import read_db, write_db


# Prints the error to console
def setup_channel_error_message(channel: str):
    errorMessage = (
        f"Setup the bot setting channel{channel} to a specific channel by typing the command: "
        f'"/channel function:{channel}" in your desired discord channel'
    )
    print(errorMessage)


def initializeDatabase():
    """Initializes the database (if the files can even be called that...)"""

    if not os.path.isdir("./db"):
        os.mkdir("./db")
    if not os.path.isdir("./logs"):
        os.mkdir("./logs")

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

    return True
