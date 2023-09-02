import asyncio
import copy
import json
import re

import discord
from bs4 import BeautifulSoup
from core.grades.grade import Grade

from bakabot.utils.utils import MessageTimers, get_sec, log_html, login, read_db, request, write_db


class Grades:
    def __init__(self, grades):
        self.grades = grades

    @staticmethod
    def empty_grade(subject=None, weight=1, grade=1, date=None, id=None):
        """Makes a Grade object with as little parameters as possible"""
        return Grade(id, None, subject, weight, None, date, grade)

    def by_subject(self, subject):
        """Returns only Grades with the wanted subject"""
        gradesBySubject = []
        for grade in self.grades:
            if grade.subject == subject:
                gradesBySubject.append(grade)
        return Grades(gradesBySubject)

    def average(self):
        """Returns the average grade from the self Grades\n
        (Calculated with weights in mind)\n
        returns None if there are no grades"""
        # Total amount of grades
        gradesTotal = 0
        # Total amount of grades included with their weights
        gradesWeightsTotal = 0

        for grade in self.grades:
            # If the grade is not a number, we skip it
            if isinstance(grade.grade, str):
                continue
            gradesTotal += grade.weight
            gradesWeightsTotal += grade.grade * grade.weight

        # Returns None if there are no grades
        if gradesTotal == 0:
            return None

        # Rounds the average and returns it
        return self.round_average(gradesWeightsTotal / gradesTotal)

    def future_average(self, grade):
        """Returns the possible future average with the given grade"""
        # Copyies itself to work with a Grades object without damaging the original
        grades = copy.deepcopy(self)

        # Appends the grade, calculates the average and removes it
        grades.grades.append(grade)

        # Returns averages
        return grades.average()

    @staticmethod
    def round_average(average: float):
        """Rounds the average to some normal nice looking finite number"""
        if average % 1 == 0:
            return int(average)
        if average % 10 == 0:
            return int(average * 10) / 10
        else:
            return int(average * 100) / 100

    @staticmethod
    def json_loads(jsonstring: str):
        """Loads a Grades object from JSON"""
        dictGrades = json.loads(jsonstring)
        grades = Grades([])
        for grade in dictGrades["grades"]:
            grades.grades.append(
                Grade(
                    grade["id"],
                    grade["caption"],
                    grade["subject"],
                    grade["weight"],
                    grade["note"],
                    grade["date"],
                    grade["grade"],
                )
            )
        return grades

    @staticmethod
    def json_dumps(grades):
        """Makes a JSON from Grades object"""
        output = '{"grades": ['
        for grade in grades.grades:
            output += json.dumps(grade.__dict__) + ", "
        if grades.grades:
            output = output[:-2]
        output += "]}"

        return output

    @staticmethod
    def db_grades():
        """Gets Grades object from the database"""
        grades = read_db("grades")
        return Grades.json_loads(grades)

    # Constants for all subjects with their short and long form
    SUBJECTS = {
        "Aj": "Jazyk anglický",
        "Bi": "Biologie",
        "Ch": "Chemie",
        "Čj": "Český jazyk a literatura",
        "D": "Dějepis",
        "Evh": "Estetická výchova - hudební",
        "Evv": "Estetická výchova - výtvarná",
        "Fj": "Jazyk francouzský",
        "Fy": "Fyzika",
        "Inf": "Informatika a výpočetní technika",
        "LpBi": "Laboratorní práce z biologie",
        "LpCh": "Laboratorní práce z chemie",
        "LpFy": "Laboratorní práce z fyziky",
        "M": "Matematika",
        "TH": "Třídnická hodina",
        "Tv": "Tělesná výchova",
        "Z": "Zeměpis",
        "Zsv": "Základy společenských věd",
    }
    SUBJECTS_REVERSED = {}
    for key, value in zip(SUBJECTS.keys(), SUBJECTS.values()):
        SUBJECTS_REVERSED.update({value: key})
    SUBJECTS_LOWER = {}
    for key in SUBJECTS.keys():
        SUBJECTS_LOWER.update({key.lower(): key})

    @staticmethod
    async def get_grades(client: discord.Client):
        """Returns a Grades object with the exctracted information from the server"""
        # Gets response from the server
        session = await login(client)
        # If bakalari server is down
        if not session:
            return None
        url = "https://bakalari.ceskolipska.cz/next/prubzna.aspx?s=chrono"
        response = await request(session, url, True, client)
        # If bakalari server is down
        if not response:
            return None
        responseHtml = await response.text()

        loggingName = "grades"
        log_html(responseHtml, loggingName)

        # Making an BS html parser object from the response
        html = BeautifulSoup(responseHtml, "html.parser")
        await session.close()

        # Web scraping the response
        data = html.find("div", {"id": "cphmain_DivByTime"})
        if not data:
            return False
        data = re.findall(r"\[\{.*?](?=;)", data.script.text)[0]
        # Creates an empty Grades object
        grades = Grades([])
        # Parses the data into a dicture
        dictData = json.loads(data)
        for row in dictData:
            # Reads the data from the dicture (Still need to properly parse it)
            caption = row["caption"]
            id = row["id"]
            subject = row["nazev"]
            weight = row["vaha"]
            note = row["poznamkakzobrazeni"]
            date = row["datum"]
            grade = row["MarkText"]

            # If a there is a caption parse it else None
            if caption != "":
                caption = caption.replace(" <br>", "")
            else:
                caption = None
            # Gets a short name for the subject
            subject = Grades.SUBJECTS_REVERSED[subject]
            # Gets an int of the weight
            weight = int(weight)
            # If a there is a note parse it else None
            if note != "":
                note = note.replace(" <br>", "")
            else:
                note = None
            # Parses the date into list of [Year, Month, Day]
            date = [int(date) for date in re.search(r"(\d{4})-0?(\d{1,2})-0?(\d{1,2})", date).groups((1, 2, 3))]
            # Parses the grade as string or a float
            if re.search(r"^\d-?$", grade):
                if "-" in grade:
                    grade = int(grade[0]) + 0.5
                else:
                    grade = int(grade)

            # Appends the grade to grades
            grades.grades.append(Grade(id, caption, subject, weight, note, date, grade))
        # Returns full Grades object
        return grades

    # Variable to store running timers
    message_remove_timers = []

    PREDICTOR_EMOJI = "📊"

    @staticmethod
    async def create_predection(message: discord.message.Message, client: discord.Client):
        from bakabot.core.predictor import Predictor

        """Generates a predict message with the current subject"""
        # Subject
        subject = Grades.SUBJECTS_REVERSED.get(message.embeds[0].author.name)

        # Removes the reaction
        await MessageTimers.delete_message_reaction(message, "gradesMessages", Grades.PREDICTOR_EMOJI, client)

        # Sends the grade predictor
        predictorMessage = await Predictor.predict_embed(subject, message.channel, client)

    @staticmethod
    async def delete_grade_reaction(message: discord.Message, emoji: discord.emoji, delay: int):
        """Deletes the reaction from the message after some delay"""
        # Puts the message into the timer variable
        Grades.message_remove_timers.append([message.id, get_sec() + delay])
        # Sleeps for the time of the delay
        await asyncio.sleep(delay)

        for timer in Grades.message_remove_timers:
            # Checks if the timer is still active
            if message.id == timer[0]:
                try:
                    # Removes the reaction
                    await message.clear_reaction(emoji)
                    toRemoveMessages = read_db("gradesMessages")
                    Grades.message_remove_timers.remove(timer)
                    toRemoveMessages.remove([message.id, message.channel.id])
                    write_db("gradesMessages", toRemoveMessages)
                except:
                    pass

    @staticmethod
    async def detect_changes(client: discord.Client):
        """Detects changes in grades and sends them to discord"""

        # Finds and returns the actual changes
        def find_changes(gradesOld: Grades, gradesNew: Grades):
            newGrades = []
            oldIDs = [grade.id for grade in gradesOld.grades]
            if gradesNew != False:
                for grade in gradesNew.grades:
                    # New unrecognized ID
                    if grade.id not in oldIDs:
                        newGrades.append(grade)
            return newGrades

        # Discord message with the information about the changes
        async def changed_message(changed: list, grades: Grades, client: discord.Client):
            channel = read_db("channelGrades")
            for grade in changed:
                # Makes the embed
                embed = grade.show(grades)

                # Sends the embed
                message = await client.get_channel(channel).send(embed=embed)

                # Adds the reaction emoji
                await message.add_reaction(Grades.PREDICTOR_EMOJI)

                # Removes the emoji after 1.5 hours of inactivity
                asyncio.ensure_future(
                    MessageTimers.delete_message_reaction(
                        message, "gradesMessages", Grades.PREDICTOR_EMOJI, client, 5400
                    )
                )

        # The main detection code
        # Gets the new Grade object
        gradesNew = await Grades.get_grades(client)
        # Gets the old Grades object
        gradesOld = Grades.db_grades()
        # If bakalari server is down
        if gradesNew is None:
            return None

        # Detects any changes and sends the message and saves the schedule if needed
        changed = find_changes(gradesOld, gradesNew)
        if changed:
            await changed_message(changed, gradesNew, client)
            write_db("grades", Grades.json_dumps(gradesNew))

    @staticmethod
    async def start_detecting_changes(interval: int, client: discord.Client):
        """Starts an infinite loop for checking changes in the grades"""
        while True:
            try:
                await Grades.detect_changes(client)
            except Exception as e:
                print("ERROR:", e)

                # Notifies the user
                unknownErrorMessage = "An unknown error occured while checking for changes in grades."
                await client.get_channel(read_db("channelGrades")).send(unknownErrorMessage)
                break
            await asyncio.sleep(interval)
