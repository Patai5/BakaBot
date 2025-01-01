from __future__ import annotations

import asyncio
import copy
import traceback

from disnake.ext.commands import InteractionBot

from ...constants import PREDICTOR_EMOJI
from ...message_timers import MessageTimers
from ...utils.utils import getTextChannel, log_html, login, os_environ, read_db, request, write_db
from ..subjects.subject import Subject
from ..subjects.subjects_cache import SubjectsCache
from .grade import Grade


class Grades:
    def __init__(self, grades: list[Grade]):
        self.grades = list(grades)

    def by_subject_name(self, subjectName: str) -> Grades:
        """Returns only Grades with the wanted subject name"""

        gradesBySubject = filter(lambda grade: grade.subjectName == subjectName, self.grades)
        return Grades(list(gradesBySubject))

    def average(self) -> float | None:
        """Returns the average grade from the self Grades\n
        (Calculated with weights in mind)\n
        returns None if there are no grades"""
        # Total amount of grades
        gradesTotal = 0
        # Total amount of grades included with their weights
        gradesWeightsTotal: int | float = 0

        for grade in self.grades:
            if grade.gradeValue is None:
                continue
            gradesTotal += grade.weight
            gradesWeightsTotal += grade.gradeValue * grade.weight

        # Returns None if there are no grades
        if gradesTotal == 0:
            return None

        # Rounds the average and returns it
        return self.round_average(gradesWeightsTotal / gradesTotal)

    def future_average(self, grade: Grade) -> float | None:
        """Returns the possible future average with the given grade"""
        # Copies itself to work with a Grades object without damaging the original
        grades = copy.deepcopy(self)

        # Appends the grade, calculates the average and removes it
        grades.grades.append(grade)

        # Returns averages
        return grades.average()

    @staticmethod
    def round_average(average: float) -> int | float:
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

    def db_save(self) -> None:
        """Saves the grades to the database"""
        write_db("grades", self)

    @staticmethod
    async def request_grades(client: InteractionBot) -> str | None:
        """Requests grades from bakalari server and returns the response as a string"""

        # Gets response from the server
        session = await login(client)
        # If bakalari server is down
        if not session:
            return None

        bakalariUrl = os_environ("bakalariUrl")
        url = f"{bakalariUrl}/next/prubzna.aspx?s=chrono"
        response = await request(session, url, True, client)
        # If bakalari server is down
        if not response:
            return None

        responseHtml = await response.text()

        await session.close()

        loggingName = "grades"
        log_html(responseHtml, loggingName)

        return responseHtml

    @staticmethod
    async def getGrades(client: InteractionBot) -> Grades | None:
        """Requests grades from bakalari server and parses them into a Grades object"""
        from ..grades.parse_grades import parseGrades

        gradesResponse = await Grades.request_grades(client)
        if gradesResponse is None:
            return None

        return parseGrades(gradesResponse)

    @staticmethod
    def handle_update_subjects_cache(grades: list[Grade], client: InteractionBot) -> None:
        """Updates the SubjectsCache with the new subjects, if needed"""

        subjects = [Subject(grade.subjectName, None) for grade in grades]

        hasMadeChanges = SubjectsCache.handleUpdateSubjects(subjects)
        if hasMadeChanges:
            SubjectsCache.updateCommandsWithSubjects(client)

    @staticmethod
    async def detect_changes(client: InteractionBot) -> None:
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
        async def changed_message(changed: list[Grade], grades: Grades, client: InteractionBot) -> None:
            channelId: int | None = read_db("channelGrades")
            if channelId is None:
                raise Exception("No channelGrades in database")

            for grade in changed:
                # Makes the embed
                embed = grade.show(grades)

                # Sends the embed
                message = await getTextChannel(channelId, client).send(embed=embed)

                # Adds the reaction emoji
                await message.add_reaction(PREDICTOR_EMOJI)

                # Removes the emoji after 1.5 hours of inactivity
                asyncio.ensure_future(
                    MessageTimers.delete_message_reaction(message, "gradesMessages", PREDICTOR_EMOJI, client, 5400)
                )

        gradesNew = await Grades.getGrades(client)

        # If bakalari server is down
        if gradesNew is None:
            return None

        hasGrades = read_db("grades")
        if not hasGrades:
            write_db("grades", gradesNew)

        Grades.handle_update_subjects_cache(gradesNew.grades, client)

        # Detects any changes and sends the message and saves the schedule if needed
        gradesOld = Grades.db_grades()
        changed = find_changes(gradesOld, gradesNew)
        if changed:
            await changed_message(changed, gradesNew, client)
            gradesNew.db_save()

    @staticmethod
    async def start_detecting_changes(interval: int, client: InteractionBot) -> None:
        """Starts an infinite loop for checking changes in the grades"""
        while True:
            try:
                await Grades.detect_changes(client)
            except Exception as e:
                errorMsgPrefix = "An error occurred while checking for changes in grades"
                print(f"\n{errorMsgPrefix}:\n{traceback.format_exc()}\n")

                channelId: int | None = read_db("channelGrades")
                if channelId is None:
                    raise Exception("No channelGrades in database")

                await getTextChannel(channelId, client).send(f"{errorMsgPrefix}:\n```{type(e).__name__}: {e}``")
                break
            await asyncio.sleep(interval)
