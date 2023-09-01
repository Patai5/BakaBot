from __future__ import annotations

import asyncio
import copy

import discord
from bs4 import BeautifulSoup
from core.schedule.day import Day
from core.schedule.parse_schedule import parseSchedule

from bakabot.constants import NUM_OF_LESSONS_IN_DAY, SCHOOL_DAYS_IN_WEEK
from bakabot.core.table import Table
from bakabot.utils.utils import log_html, login, rand_rgb, read_db, request, write_db


class Schedule:
    DAYS = {"po": 0, "út": 1, "st": 2, "čt": 3, "pá": 4}
    DAYS_REVERSED = {}
    for key, value in zip(DAYS.keys(), DAYS.values()):
        DAYS_REVERSED.update({value: key})

    def __init__(self, days: list[Day], nextWeek: bool = False) -> Schedule:
        self.days = days
        self.nextWeek = nextWeek

        self.insert_missing_days()

    def __str__(self) -> str:
        return f"Schedule(Days: {[(day.nameShort, day.date) for day in self.days]}, NextWeek: {self.nextWeek})"

    def __eq__(self, other: Schedule) -> bool:
        if not isinstance(other, Schedule):
            return False
        if not (self.nextWeek == other.nextWeek):
            return False
        for day1, day2 in zip(self.days, other.days):
            if day1 != day2:
                return False
        return True

    # Gets the index of the first non empty lesson in common across all days
    def first_non_empty_lessons(self) -> int:
        firstPerDays = []
        for day in self.days:
            lesson = day.first_non_empty_lesson()
            if lesson:
                firstPerDays.append(lesson.hour)
        if firstPerDays:
            return min(firstPerDays)
        else:
            return None

    # Gets the index of the last non empty lesson in common across all days
    def last_non_empty_lessons(self) -> int:
        lastPerDays = []
        for day in self.days:
            lesson = day.last_non_empty_lesson()
            if lesson:
                lastPerDays.append(lesson.hour)
        if lastPerDays:
            return max(lastPerDays)
        else:
            return None

    @staticmethod
    def db_schedule(nextWeek: bool = False):
        """Gets schedule from the database"""
        return read_db("schedule1") if not nextWeek else read_db("schedule2")

    def db_save(self):
        """Saves the schedule to the database"""
        if not self.nextWeek:
            write_db("schedule1", self)
        else:
            write_db("schedule2", self)

    def insert_missing_days(self):
        """Inserts missing days into the schedule to make it a full week"""
        if self.days:
            start = self.days[0].weekDay
            end = self.days[-1].weekDay
        else:
            start = 5
            end = 4

        for weekDay in range(start):
            self.days.insert(weekDay, Day([], weekDay, None))
        for weekDay in range(end, 4):
            self.days.insert(weekDay + 1, Day([], weekDay, None))

    @staticmethod
    async def request_schedule(nextWeek: bool, client: discord.Client) -> BeautifulSoup | None:
        """Returns a BeautifulSoup object from response of the schedule page"""
        # Gets response from the server
        session = await login(client)
        # If bakalari server is down
        if not session:
            return None
        if nextWeek:
            url = "https://bakalari.ceskolipska.cz/next/rozvrh.aspx?s=next"
        else:
            url = "https://bakalari.ceskolipska.cz/next/rozvrh.aspx"
        response = await request(session, url, True, client)
        # If bakalari server is down
        if not response:
            return None
        responseHtml = await response.text()

        loggingName = "schedule"
        log_html(responseHtml, loggingName)

        # Making an BS html parser object from the response
        html = BeautifulSoup(responseHtml, "html.parser")
        await session.close()
        return html

    @staticmethod
    async def get_schedule(nextWeek: bool, client: discord.Client) -> Schedule | None:
        """Returns a Schedule object with the exctracted information"""
        html = await Schedule.request_schedule(nextWeek, client)

        if html is None:
            return None

        return parseSchedule(html, nextWeek)

    def render(
        self,
        dayStart: int,
        dayEnd: int,
        showDay: bool = None,
        showClassroom: bool = None,
        exclusives: list = None,
        renderStyle: Table.Style = None,
        file_name: str = "table.png",
    ):
        """Renders the schedule into an image"""
        # Uses the setting if inputed else tries looking into the database
        if showDay == None:
            showDay = read_db("showDay")
        if showClassroom == None:
            showClassroom = read_db("showClassroom")

        # Full exclusives of False if None as parameter
        if exclusives == None:
            exclusives = [[False for i in range(NUM_OF_LESSONS_IN_DAY)] for i in range(SCHOOL_DAYS_IN_WEEK)]

        # Copyies itself to work with a Schedule object without damaging the original
        schedule = copy.deepcopy(self)
        # Uses only needed days
        schedule.days = schedule.days[dayStart - 1 : dayEnd]

        # Gets the first not empty day
        firstNonEmptyDay = None
        for day in schedule.days:
            if not day.empty:
                firstNonEmptyDay = day
                break
        # Continues if there is at least one non empty day
        if firstNonEmptyDay:
            # Cuts the first empty lessons from the start of the days in schedule
            cutToHour = schedule.first_non_empty_lessons()
            for day in schedule.days:
                for lesson in day.lessons[:]:
                    if lesson.hour < cutToHour:
                        day.lessons.remove(lesson)
            # Cuts the last empty lessons from the end of the days in schedule
            cutToHour = schedule.last_non_empty_lessons()
            for day in schedule.days:
                for lesson in day.lessons[:]:
                    if lesson.hour > cutToHour:
                        day.lessons.remove(lesson)

            # Prepares columns for the Table object
            columns = []
            # Adds short names of the days to the left of the table
            if showDay:
                column = [Table.Cell([Table.Cell.Item("")])]
                for day in schedule.days:
                    column.append(Table.Cell([Table.Cell.Item(day.nameShort)]))
                columns.append(column)
            for i in range(len(schedule.days[0].lessons)):
                # Adds the lesson hour to the top of the table
                column = [Table.Cell([Table.Cell.Item(f"{schedule.days[0].lessons[i].hour}.")])]

                # Adds the actual lessons to the table
                for day_i, day in enumerate(schedule.days):
                    column.append(
                        Table.Cell(
                            [Table.Cell.Item(day.lessons[i].subjectShort)], exclusives[day_i][day.lessons[i].hour]
                        )
                    )
                    if showClassroom:
                        column[-1].items.append(Table.Cell.Item(day.lessons[i].classroom))
                columns.append(column)
            table = Table(columns)
        else:
            table = Table([[Table.Cell([Table.Cell.Item("Rozvrh je prázdný")])]])

        # Returns a rendered table image
        return table.render(file_name=file_name, style=renderStyle)


class ChangeDetector:
    class Changed:
        def __init__(self, previousLesson, updatedLesson, day):
            self.previousLesson = previousLesson
            self.updatedLesson = updatedLesson
            self.day = day

    @staticmethod
    async def detect_changes(client: discord.Bot):
        """Detects any changes in the schedule and sends a discord notification of the changes if there are any"""
        # Gets the schedules from bakalari and the database and pairs them together
        schedulesCurrentWeek = [Schedule.db_schedule(False), await Schedule.get_schedule(False, client)]
        schedulesNextWeek = [Schedule.db_schedule(True), await Schedule.get_schedule(True, client)]

        # If bakalari server is down, return
        if schedulesCurrentWeek[1] is None or schedulesNextWeek[1] is None:
            return None

        # Iterates over the schedule pairs
        for schedulePair in [schedulesCurrentWeek, schedulesNextWeek]:
            # Finds all the changes between the schedules
            changed = ChangeDetector.find_changes(*schedulePair)
            # If there are any changes, sends a message and saves the schedule to the database
            if changed:
                await ChangeDetector.changed_message(changed, client, *schedulePair)
                schedulePair[1].db_save()

    @staticmethod
    def find_changes(scheduleOld: Schedule, scheduleNew: Schedule):
        """Finds any changes in the schedule"""
        changedlist = []
        # Iterates over the days
        for dayOld, dayNew in zip(scheduleOld.days, scheduleNew.days):
            # Iterates over the lessons and looks for any differences
            for lessonOld, lessonNew in zip(dayOld.lessons, dayNew.lessons):
                changed = ChangeDetector.Changed(lessonOld, lessonNew, dayOld)
                # The actuall differences that we are looking for
                if (
                    lessonOld.subject != lessonNew.subject
                    or lessonOld.classroom != lessonNew.classroom
                    or lessonOld.teacher != lessonNew.teacher
                    or lessonOld.changeInfo != lessonNew.changeInfo
                ):
                    changedlist.append(changed)
        if len(changedlist) != 0:
            return changedlist
        else:
            return None

    @staticmethod
    async def changed_message(changed: list, client: discord.Client, scheduleOld: Schedule, scheduleNew: Schedule):
        """Sends the changed schedules over discord"""
        embedsColor = discord.Color.from_rgb(*rand_rgb())
        # Makes the two embeds containing the changed schedule images
        embedOld = discord.Embed(color=embedsColor, description="Zastaralý rozvrh")
        embedNew = discord.Embed(color=embedsColor, description="Aktualizovaný rozvrh")
        embedOld.title = f'Detekována změna v rozvrhu {"příštího" if scheduleOld.nextWeek else "aktuálního"} týdne'

        # Makes the 2D exclusives array with the changed items
        exclusives = [[False for i in range(NUM_OF_LESSONS_IN_DAY)] for i in range(SCHOOL_DAYS_IN_WEEK)]
        for item in changed:
            exclusives[item.day.weekDay][item.updatedLesson.hour] = True

        # Gets the same random render style for both of the schedules
        renderStyle = Table.Style()

        # Generates some images of the changed schedule
        fileNameOld = "scheduleOld.png"
        imgOld = await scheduleOld.render(1, 5, True, True, exclusives, renderStyle, fileNameOld)
        embedOld.set_image(url=f"attachment://{fileNameOld}")

        fileNameNew = "scheduleNew.png"
        imgNew = await scheduleNew.render(1, 5, True, True, exclusives, renderStyle, fileNameNew)
        embedNew.set_image(url=f"attachment://{fileNameNew}")

        # Detail of the changes
        changedDetail = discord.Embed(color=embedsColor)
        changedStr = ""
        for change in changed:
            lessonOld = change.previousLesson
            lessonNew = change.updatedLesson

            changedStr += f"{change.day.nameShort} {lessonOld.hour}. hodina: "
            if lessonOld.empty:
                changedStr += "**∅**"
            else:
                changedStr += f"**{lessonOld.subjectShort}{' ' + lessonOld.classroom if lessonOld.classroom else ''}**"
            changedStr += " -> "
            if lessonNew.empty:
                changedStr += "**∅**"
            else:
                changedStr += f"**{lessonNew.subjectShort}{' ' + lessonNew.classroom if lessonNew.classroom else ''}**"
            if lessonNew.changeInfo is not None:
                changedStr += f"; *{lessonNew.changeInfo}*"
            changedStr += "\n"
        changedDetail.description = changedStr

        # Sends the messages
        channel = read_db("channelSchedule")
        await client.get_channel(channel).send(file=imgOld, embed=embedOld)
        await client.get_channel(channel).send(file=imgNew, embed=embedNew)
        await client.get_channel(channel).send(embed=changedDetail)

    @staticmethod
    async def start_detecting_changes(interval: int, client: discord.Client):
        """Starts an infinite loop for checking changes in the schedule"""
        while True:
            try:
                await ChangeDetector.detect_changes(client)
            except Exception as e:
                print("ERROR:", e)

                # Notifies the user
                unknownErrorMessage = "An unknown error occured while checking for changes in schedule."
                await client.get_channel(read_db("channelSchedule")).send(unknownErrorMessage)
                break
            await asyncio.sleep(interval)
