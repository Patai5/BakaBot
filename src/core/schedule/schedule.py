from __future__ import annotations

import asyncio
import copy
import traceback

import disnake
from attr import dataclass
from disnake.ext.commands import InteractionBot

from ...constants import NUM_OF_LESSONS_IN_DAY, SCHOOL_DAYS_IN_WEEK
from ...feature_manager.feature_manager import FeatureManager
from ...utils.utils import getTextChannel, log_html, login, os_environ, rand_rgb, read_db, request, write_db
from ..subjects.subjects_cache import SubjectsCache
from ..table import ColumnType, Table
from .day import Day
from .lesson import Lesson


class Schedule:
    def __init__(self, days: list[Day], lessonTimes: list[int], nextWeek: bool = False):
        self.days = days
        """List of the starting hours for the lessons"""
        self.lessonTimes = lessonTimes
        self.nextWeek = nextWeek

        self.insert_missing_days()

    def __str__(self) -> str:
        return f"Schedule(Days: {[(day.nameShort, day.date) for day in self.days]}, NextWeek: {self.nextWeek})"

    def __eq__(self, other: object) -> bool:
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
        firstPerDays: list[int] = []
        for day in self.days:
            lesson = day.first_non_empty_lesson()
            if lesson:
                firstPerDays.append(lesson.hour)

        return min(firstPerDays)

    # Gets the index of the last non empty lesson in common across all days
    def last_non_empty_lessons(self) -> int:
        lastPerDays: list[int] = []
        for day in self.days:
            lesson = day.last_non_empty_lesson()
            if lesson:
                lastPerDays.append(lesson.hour)

        return max(lastPerDays)

    @staticmethod
    def db_schedule(nextWeek: bool = False) -> Schedule:
        """Gets schedule from the database"""
        schedule: Schedule | None = read_db("schedule1") if not nextWeek else read_db("schedule2")

        if schedule is None:
            raise Exception("Schedule not found in database")

        return schedule

    def db_save(self) -> None:
        """Saves the schedule to the database"""
        if not self.nextWeek:
            write_db("schedule1", self)
        else:
            write_db("schedule2", self)

    def insert_missing_days(self) -> None:
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
    async def request_schedule(nextWeek: bool, client: InteractionBot) -> str | None:
        """Returns a BeautifulSoup object from response of the schedule page"""
        # Gets response from the server
        session = await login(client)
        # If bakalari server is down
        if not session:
            return None

        bakalariUrl = os_environ("bakalariUrl")
        scheduleUrlPath = "/next/rozvrh.aspx?s=next" if nextWeek else "/next/rozvrh.aspx"
        url = f"{bakalariUrl}{scheduleUrlPath}"

        response = await request(session, url, True, client)
        # If bakalari server is down
        if not response:
            return None
        html = await response.text()

        await session.close()

        loggingName = "schedule"
        log_html(html, loggingName)

        return html

    @staticmethod
    async def get_schedule(nextWeek: bool, client: InteractionBot) -> Schedule | None:
        """Returns a Schedule object with the extracted information"""
        from .parse_schedule import parseSchedule

        html = await Schedule.request_schedule(nextWeek, client)

        if html is None:
            return None

        return parseSchedule(html, nextWeek)

    async def render(
        self,
        dayStart: int,
        dayEnd: int,
        showDay: bool | None = None,
        showClassroom: bool | None = None,
        exclusives: list[list[bool]] | None = None,
        renderStyle: Table.Style | None = None,
        file_name: str = "table.png",
    ) -> disnake.File:
        """Renders the schedule into an image"""
        # Uses the setting if inputted else tries looking into the database
        if showDay == None:
            showDay = read_db("showDay")
        if showClassroom == None:
            showClassroom = read_db("showClassroom")

        # Full exclusives of False if None as parameter
        if exclusives == None:
            exclusives = [[False for _ in range(NUM_OF_LESSONS_IN_DAY)] for _ in range(SCHOOL_DAYS_IN_WEEK)]

        # Copies itself to work with a Schedule object without damaging the original
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
            columns: ColumnType = []
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
                    lessonSubject = day.lessons[i].subject
                    subjectName = lessonSubject.shortOrFullName if lessonSubject else None

                    column.append(
                        Table.Cell(
                            [Table.Cell.Item(subjectName)],
                            exclusives[day_i][day.lessons[i].hour],
                        )
                    )
                    if showClassroom:
                        column[-1].items.append(Table.Cell.Item(day.lessons[i].classroom))
                columns.append(column)
            table = Table(columns)
        else:
            table = Table([[Table.Cell([Table.Cell.Item("Rozvrh je prázdný")])]])

        # Returns a rendered table image
        return await table.render(file_name=file_name, style=renderStyle)


@dataclass
class OldNewSchedule:
    old: Schedule
    new: Schedule


class ChangeDetector:
    class Changed:
        def __init__(self, previousLesson: Lesson, updatedLesson: Lesson, day: Day):
            self.previousLesson = previousLesson
            self.updatedLesson = updatedLesson
            self.day = day

    @staticmethod
    async def detect_changes(client: InteractionBot) -> bool:
        """
        Detects any changes in the schedule and sends a discord notification of the changes if there are any

        :return: A boolean indicating whether the server is online
        """
        newCurrentWeek = await Schedule.get_schedule(False, client)
        newNextWeek = await Schedule.get_schedule(True, client)

        # If bakalari server is down, return
        if newCurrentWeek is None or newNextWeek is None:
            return False

        hasScheduleDatabase = read_db("schedule1") and read_db("schedule2")
        if not hasScheduleDatabase:
            newCurrentWeek.db_save()
            newNextWeek.db_save()

        ChangeDetector.handle_update_subjects_cache((newCurrentWeek, newNextWeek), client)

        schedulesCurrentWeek = OldNewSchedule(Schedule.db_schedule(False), newCurrentWeek)
        schedulesNextWeek = OldNewSchedule(Schedule.db_schedule(True), newNextWeek)

        # Iterates over the schedule pairs
        for schedulePair in [schedulesCurrentWeek, schedulesNextWeek]:
            # Finds all the changes between the schedules
            changed = ChangeDetector.find_changes(schedulePair)
            # If there are any changes, sends a message and saves the schedule to the database
            if changed:
                await ChangeDetector.changed_message(changed, client, schedulePair)
                schedulePair.new.db_save()

        return True

    @staticmethod
    def handle_update_subjects_cache(schedules: tuple[Schedule, Schedule], client: InteractionBot) -> None:
        """Updates the subjects cache with the subjects from the schedule"""

        subjects = [
            lesson.subject
            for schedule in schedules
            for day in schedule.days
            for lesson in day.lessons
            if lesson.subject
        ]

        hasMadeChanges = SubjectsCache.handleUpdateSubjects(subjects)
        if hasMadeChanges:
            SubjectsCache.updateCommandsWithSubjects(client)

    @staticmethod
    def find_changes(
        oldNewSchedule: OldNewSchedule,
    ) -> list[ChangeDetector.Changed] | None:
        """Finds any changes in the schedule"""
        changedList: list[ChangeDetector.Changed] = []
        # Iterates over the days
        for dayOld, dayNew in zip(oldNewSchedule.old.days, oldNewSchedule.new.days):
            # Iterates over the lessons and looks for any differences
            for lessonOld, lessonNew in zip(dayOld.lessons, dayNew.lessons):
                changed = ChangeDetector.Changed(lessonOld, lessonNew, dayOld)
                # The actual differences that we are looking for
                if (
                    lessonOld.subject != lessonNew.subject
                    or lessonOld.classroom != lessonNew.classroom
                    or lessonOld.teacher != lessonNew.teacher
                    or lessonOld.changeInfo != lessonNew.changeInfo
                ):
                    changedList.append(changed)
        if len(changedList) != 0:
            return changedList
        else:
            return None

    @staticmethod
    async def changed_message(
        changed: list[ChangeDetector.Changed],
        client: InteractionBot,
        oldNewSchedule: OldNewSchedule,
    ) -> None:
        """Sends the changed schedules over discord"""
        embedsColor = disnake.Color.from_rgb(*rand_rgb())
        # Makes the two embeds containing the changed schedule images
        embedOld = disnake.Embed(color=embedsColor, description="Zastaralý rozvrh")
        embedNew = disnake.Embed(color=embedsColor, description="Aktualizovaný rozvrh")
        embedOld.title = (
            f'Detekována změna v rozvrhu {"příštího" if oldNewSchedule.old.nextWeek else "aktuálního"} týdne'
        )

        # Makes the 2D exclusives array with the changed items
        exclusives = [[False for _ in range(NUM_OF_LESSONS_IN_DAY)] for _ in range(SCHOOL_DAYS_IN_WEEK)]
        for item in changed:
            exclusives[item.day.weekDay][item.updatedLesson.hour] = True

        # Gets the same random render style for both of the schedules
        renderStyle = Table.Style()

        # Generates some images of the changed schedule
        fileNameOld = "scheduleOld.png"
        imgOld = await oldNewSchedule.old.render(1, 5, True, True, exclusives, renderStyle, fileNameOld)
        embedOld.set_image(url=f"attachment://{fileNameOld}")

        fileNameNew = "scheduleNew.png"
        imgNew = await oldNewSchedule.new.render(1, 5, True, True, exclusives, renderStyle, fileNameNew)
        embedNew.set_image(url=f"attachment://{fileNameNew}")

        # Detail of the changes
        changedDetail = disnake.Embed(color=embedsColor)
        changedStr = ""
        for change in changed:
            lessonOld = change.previousLesson
            lessonNew = change.updatedLesson

            changedStr += f"{change.day.nameShort} {lessonOld.hour}. hodina: "
            if lessonOld.empty:
                changedStr += "**∅**"
            else:
                if lessonOld.subject is None:
                    raise ValueError("Old outdated lesson is None")

                changedStr += (
                    f"**{lessonOld.subject.shortOrFullName}{' ' + lessonOld.classroom if lessonOld.classroom else ''}**"
                )
            changedStr += " -> "
            if lessonNew.empty:
                changedStr += "**∅**"
            else:
                if lessonNew.subject is None:
                    raise ValueError("New updated lesson is None")

                changedStr += (
                    f"**{lessonNew.subject.shortOrFullName}{' ' + lessonNew.classroom if lessonNew.classroom else ''}**"
                )
            if lessonNew.changeInfo is not None:
                changedStr += f"; *{lessonNew.changeInfo}*"
            changedStr += "\n"
        changedDetail.description = changedStr

        # Sends the messages
        scheduleChannelId = read_db("channelSchedule")
        if scheduleChannelId is None:
            raise Exception("Schedule channel not found in database")

        channel = getTextChannel(scheduleChannelId, client)
        await channel.send(file=imgOld, embed=embedOld)
        await channel.send(file=imgNew, embed=embedNew)
        await channel.send(embed=changedDetail)

    @staticmethod
    async def start_detecting_changes(interval: int, featureManager: FeatureManager, client: InteractionBot) -> None:
        """Starts an infinite loop for checking changes in the schedule"""
        while True:
            try:
                isServerOnline = await ChangeDetector.detect_changes(client)
            except Exception as e:
                errorMsgPrefix = "An error occurred while checking for changes in grades"
                print(f"\n{errorMsgPrefix}:\n{traceback.format_exc()}\n")

                scheduleChannelId = read_db("channelSchedule")
                if scheduleChannelId is None:
                    raise Exception("Schedule channel not found in database")

                await getTextChannel(scheduleChannelId, client).send(
                    f"{errorMsgPrefix}:\n```{type(e).__name__}: {e}```"
                )
                break

            if isServerOnline:
                asyncio.ensure_future(featureManager.maybe_start_feature("reminder", client))
            await asyncio.sleep(interval)
