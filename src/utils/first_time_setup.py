import os

from .utils import read_db, write_db


def initializeDatabase() -> bool:
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
