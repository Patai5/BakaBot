from __future__ import annotations

import asyncio
import copy

import discord
from core.grades.grade import Grade
from core.grades.parse_grades import parseGrades

from bakabot.utils.utils import MessageTimers, get_sec, getThreadChannel, log_html, login, read_db, request, write_db


class Grades:
    def __init__(self, grades: list[Grade]):
        self.grades = grades

    @staticmethod
    def empty_grade(subject: str = "", weight: int = 1, grade: float = 1):
        """Makes a Grade object with as little parameters as possible"""
        return Grade("", "", subject, weight, "", [0, 0, 0], grade)

    def by_subject(self, subject: str):
        """Returns only Grades with the wanted subject"""
        gradesBySubject: list[Grade] = []
        for grade in self.grades:
            if grade.subject == subject:
                gradesBySubject.append(grade)
        return Grades(gradesBySubject)

    def average(self) -> float | None:
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

    def future_average(self, grade: Grade):
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
    def db_grades() -> Grades:
        """Gets Grades object from the database"""
        grades: Grades | None = read_db("grades")

        if grades is None:
            raise Exception("Grades not found in database")

        return grades

    def db_save(self):
        """Saves the grades to the database"""
        write_db("grades", self)

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
    SUBJECTS_REVERSED: dict[str, str] = {}
    for key, value in zip(SUBJECTS.keys(), SUBJECTS.values()):
        SUBJECTS_REVERSED.update({value: key})
    SUBJECTS_LOWER: dict[str, str] = {}
    for key in SUBJECTS.keys():
        SUBJECTS_LOWER.update({key.lower(): key})

    @staticmethod
    async def request_grades(client: discord.Client) -> str | None:
        """Requests grades from bakalari server and returns the response as a string"""

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

        await session.close()

        responseHtml = await response.text()

        loggingName = "grades"
        log_html(responseHtml, loggingName)

        return responseHtml

    @staticmethod
    async def getGrades(client: discord.Client) -> Grades | None:
        """Requests grades from bakalari server and parses them into a Grades object"""
        gradesResponse = await Grades.request_grades(client)

        if gradesResponse is None:
            return None

        return parseGrades(gradesResponse)

    # Variable to store running timers
    message_remove_timers: list[list[int]] = []

    PREDICTOR_EMOJI = "📊"

    @staticmethod
    async def create_predection(message: discord.message.Message, client: discord.Client):
        from bakabot.core.predictor import Predictor

        """Generates a predict message with the current subject"""
        # Subject
        embed = message.embeds[0].to_dict()

        embedAuthor = embed.get("author")
        if embedAuthor is None:
            raise Exception("No author in prediction embed")

        subjectFromEmbed = embedAuthor.get("name")
        if subjectFromEmbed is None:
            raise Exception("No subject in prediction embed")

        subject = Grades.SUBJECTS_REVERSED.get(subjectFromEmbed) or subjectFromEmbed

        # Removes the reaction
        await MessageTimers.delete_message_reaction(message, "gradesMessages", Grades.PREDICTOR_EMOJI, client)

        # Sends the grade predictor
        await Predictor.predict_embed(subject, message.channel.id, client)

    @staticmethod
    async def delete_grade_reaction(message: discord.Message, emoji: discord.message.EmojiInputType, delay: int):
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
                    Grades.message_remove_timers.remove(timer)

                    toRemoveMessages: list[list[int]] | None = read_db("gradesMessages")
                    if toRemoveMessages is None:
                        raise Exception("No gradesMessages in database")

                    toRemoveMessages.remove([message.id, message.channel.id])
                    write_db("gradesMessages", toRemoveMessages)
                except:
                    pass

    @staticmethod
    async def detect_changes(client: discord.Client):
        """Detects changes in grades and sends them to discord"""

        # Finds and returns the actual changes
        def find_changes(gradesOld: Grades, gradesNew: Grades) -> list[Grade]:
            newGrades: list[Grade] = []
            oldIDs = [grade.id for grade in gradesOld.grades]
            for grade in gradesNew.grades:
                # New unrecognized ID
                if grade.id not in oldIDs:
                    newGrades.append(grade)
            return newGrades

        # Discord message with the information about the changes
        async def changed_message(changed: list[Grade], grades: Grades, client: discord.Client):
            channelId: int | None = read_db("channelGrades")
            if channelId is None:
                raise Exception("No channelGrades in database")

            for grade in changed:
                # Makes the embed
                embed = grade.show(grades)

                # Sends the embed
                message = await getThreadChannel(channelId, client).send(embed=embed)

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
        gradesNew = await Grades.getGrades(client)
        # Gets the old Grades object
        gradesOld = Grades.db_grades()
        # If bakalari server is down
        if gradesNew is None:
            return None

        # Detects any changes and sends the message and saves the schedule if needed
        changed = find_changes(gradesOld, gradesNew)
        if changed:
            await changed_message(changed, gradesNew, client)
            gradesNew.db_save()

    @staticmethod
    async def start_detecting_changes(interval: int, client: discord.Client):
        """Starts an infinite loop for checking changes in the grades"""
        while True:
            try:
                await Grades.detect_changes(client)
            except Exception as e:
                print("ERROR:", e)

                channelId: int | None = read_db("channelGrades")
                if channelId is None:
                    raise Exception("No channelGrades in database")

                # Notifies the user
                unknownErrorMessage = "An unknown error occured while checking for changes in grades."
                await getThreadChannel(channelId, client).send(unknownErrorMessage)

                break
            await asyncio.sleep(interval)
