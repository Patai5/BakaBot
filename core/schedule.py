import asyncio
import copy
import datetime
import json
import random
import re

import discord
from bs4 import BeautifulSoup
from utils.utils import get_sec, login, rand_rgb, read_db, request, write_db

from core.table import Table


class Schedule:
    DAYS = {"po": 0, "út": 1, "st": 2, "čt": 3, "pá": 4}
    DAYS_REVERSED = {}
    for key, value in zip(DAYS.keys(), DAYS.values()):
        DAYS_REVERSED.update({value: key})

    def __init__(self, days: list, nextWeek: bool):
        self.days = days
        self.nextWeek = nextWeek

    class Day:
        def __init__(self, lessons: list, day: str, date: str, empty: bool):
            self.lessons = lessons
            self.day = day
            self.date = date
            self.empty = empty

            # Prevents the day from being empty
            if empty and not lessons:
                for i in range(12):
                    lessons.append(Schedule.Lesson(i, "", "", None, None))

        # Gets the first non empty lesson of the day. If none then returns None
        def first_non_empty_lesson(self):
            for lesson in self.lessons:
                if not lesson.empty:
                    return lesson
            return None

        # Gets the last non empty lesson of the day. If none then returns None
        def last_non_empty_lesson(self):
            for lesson in reversed(self.lessons):
                if not lesson.empty:
                    return lesson
            return None

    class Lesson:
        def __init__(self, hour: int, subject: str, classroom: str, changeInfo: str, topic: str):
            self.hour = hour
            self.subject = subject
            self.classroom = classroom
            self.changeInfo = changeInfo
            self.topic = topic

            if self.subject == "":
                self.empty = True
            else:
                self.empty = False

        def render(self, showClassroom: bool = None, renderStyle: Table.Style = None, file_name: str = "temp.png"):
            """Returns a lesson redered as an image"""
            if showClassroom == None:
                showClassroom = read_db("showClassroom")

            cell = Table.Cell([Table.Cell.Item(self.subject)])
            if showClassroom:
                cell.items.append(Table.Cell.Item(self.classroom))
            return Table([[cell]]).render(file_name=file_name, style=renderStyle)

        # Loads a Lesson object from JSON
        @staticmethod
        def json_loads(jsonstring: str):
            dictLesson = json.loads(jsonstring)
            lesson = Schedule.Lesson(
                dictLesson["hour"],
                dictLesson["subject"],
                dictLesson["classroom"],
                dictLesson["changeInfo"],
                dictLesson["topic"],
            )
            return lesson

        # Makes a JSON from Lesson
        @staticmethod
        def json_dumps(lesson):
            return json.dumps(lesson.__dict__)

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

    # Gets Schedule object from the database
    @staticmethod
    def db_schedule(nextWeek: bool = False):
        if not nextWeek:
            return Schedule.json_loads(read_db("schedule1"))
        else:
            return Schedule.json_loads(read_db("schedule2"))

    # Loads a Schedule object from JSON
    @staticmethod
    def json_loads(jsonstring: str):
        dictSchedule = json.loads(jsonstring)
        days = []
        for day in dictSchedule["days"]:
            lessons = []
            for lesson in day["lessons"]:
                lessons.append(Schedule.Lesson.json_loads(json.dumps(lesson)))
            days.append(Schedule.Day(lessons, day["day"], day["date"], day["empty"]))
        schedule = Schedule(days, dictSchedule["nextWeek"])
        return schedule

    # Makes a JSON from Schedule
    @staticmethod
    def json_dumps(schedule):
        output = '{"days": ['
        for day in schedule.days:
            output = output + '{"lessons": ['
            for lesson in day.lessons:
                output = output + Schedule.Lesson.json_dumps(lesson) + ", "
            output = output[:-2] + "]"
            output = f'{output}, "day": "{day.day}", "date": "{day.date}", "empty": {str(day.empty).lower()}}}, '
        output = output[:-2] + "]"
        output = output + ', "nextWeek": ' + str(schedule.nextWeek).lower() + "}"
        return output

    def insert_missing_days(self):
        """Inserts missing days into the schedule to make it a full week"""
        if self.days:
            start = Schedule.DAYS[self.days[0].day]
            end = Schedule.DAYS[self.days[-1].day]
        else:
            start = 5
            end = 4

        for day in range(start):
            self.days.insert(day, Schedule.Day([], Schedule.DAYS_REVERSED[day], "", True))
        for day in range(end, 4):
            self.days.insert(day, Schedule.Day([], Schedule.DAYS_REVERSED[day], "", True))

    # Returns a Schedule object with the exctracted information
    @staticmethod
    async def get_schedule(nextWeek: bool, client: discord.Client):
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
        # Making an BS html parser object from the response
        html = BeautifulSoup(await response.text(), "html.parser")
        await session.close()

        # Web scraping the response
        days = html.find_all("div", {"class": "day-row"})[-5:]
        if not days:
            return None
        for day_i, day in enumerate(days):
            lessons = day.div.div.find_all("div", {"class": "day-item"})

            empty = False
            if not lessons:
                empty = True
            else:
                # Removes useless lesson from bakalari
                lessons.pop(7)
                for lesson_i, lesson in enumerate(lessons):
                    # Gets main data of a lesson
                    data = lesson.find_all("div", {"class": "day-item-hover"})

                    # Gets change info
                    changeInfo = re.search('(?<="changeinfo":")[^"]+(?=")', str(data))
                    if changeInfo:
                        changeInfo = changeInfo.group()
                        # Changed info
                        if "Suplování" in changeInfo:
                            # When Suplovani then gets the teacher that's beaing replaced aswell
                            teacher_div = lesson.find("div", {"class": "bottom"})
                            teacher = re.search("(?<=>).*(?=</)", str(teacher_div)).group()
                            changeInfo += " --> " + teacher
                    else:
                        # Removed info
                        changeInfo = re.search('(?<="removedinfo":")[^"]+(?=")', str(data))
                        if changeInfo:
                            changeInfo = changeInfo.group()

                    # Prevents from returning an empty lesson
                    # Continues only if it finds the lesson's subject
                    subject_div = lesson.find("div", {"class": "middle"})
                    if subject_div and subject_div.text:
                        subject = re.search("(?<=>).*(?=</)", str(subject_div)).group()
                        mainData_div = lesson.find_all("div", {"class": "day-item-hover"})

                        # Finds the classroom
                        classroom = re.search('(?<="room":")[^"]+(?=")', str(mainData_div))
                        if classroom:
                            classroom = classroom.group()
                        # Prevents empty classroom
                        if not classroom:
                            classroom = ""

                        # Finds the topic
                        topic = re.search('(?<="theme":")[^"]+(?=")', str(mainData_div))
                        if topic:
                            topic = topic.group()
                    else:
                        subject = ""
                        classroom = ""
                        topic = None
                    # Creates Lesson object and saves it into lessons list
                    lessons[lesson_i] = Schedule.Lesson(lesson_i, subject, classroom, changeInfo, topic)
            # Gets the short version of the day's name
            dayShort_div = day.div.div.div.div
            dayShort = re.search("(?<=<div>)\s*?(..)(?=<br\/>)", str(dayShort_div)).group(1)
            # Gets the date
            date = dayShort_div.span.text

            # Creates Day object and saves it into the days list
            days[day_i] = Schedule.Day(lessons, dayShort, date, empty)
        schedule = Schedule(days, nextWeek)
        schedule.insert_missing_days()
        # Returns full Schedule object
        return schedule

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
            exclusives = [[False for i in range(13)] for i in range(5)]

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
                    column.append(Table.Cell([Table.Cell.Item(day.day)]))
                columns.append(column)
            for i in range(len(schedule.days[0].lessons)):
                # Adds the lesson hour to the top of the table
                column = [Table.Cell([Table.Cell.Item(f"{schedule.days[0].lessons[i].hour}.")])]

                # Adds the actual lessons to the table
                for day_i, day in enumerate(schedule.days):
                    column.append(
                        Table.Cell([Table.Cell.Item(day.lessons[i].subject)], exclusives[day_i][day.lessons[i].hour])
                    )
                    if showClassroom:
                        column[-1].items.append(Table.Cell.Item(day.lessons[i].classroom))
                columns.append(column)
            table = Table(columns)
        else:
            table = Table([[Table.Cell([Table.Cell.Item("Rozvrh je prázdný")])]])

        # Returns a rendered table image
        return table.render(file_name=file_name, style=renderStyle)

    @staticmethod
    async def new_week_message(currentWeek, nextWeek, client: discord.Client):
        """Sends the messages for the newly detected week +Betting"""
        from core.betting import Betting

        randomReaction = [
            "Hurá",
            "Kurwa",
            "Do píči",
            "Cука блять",
            "Tak tohleto je těžce v prdeli",
            "Hrnčíř je zmrd",
            "Škodová je odporná zmrdná, vyšoustaná, vyšlukovaná, vypařízkovaná špína",
            "Jakože nemám nic proti lidem s dvojciferným IQ ale Škodová má jednociferný",
        ]

        # Generates the title
        titleNext = f"\\**{random.choice(randomReaction)}*\\*\n**Detekován nový týden**:"
        titleCurrent = "**Aktualní týden**:"
        # Generates the schedule tables
        scheduleNext = f"```{nextWeek.show(1, 5, True, True)}```"
        scheduleCurrent = f"```{currentWeek.show(1, 5, True, True)}```"

        # Sends the messages
        channel = client.get_channel(read_db("channelSchedule"))
        await channel.send(titleNext)
        await channel.send(scheduleNext)
        await channel.send(titleCurrent)
        await channel.send(scheduleCurrent)
        bettingSchedule = Schedule.json_loads(read_db("bettingSchedule"))
        Betting.update_week(currentWeek)
        await Betting.start_betting(client)
        removed, added = Betting.get_removed_added(bettingSchedule, currentWeek)
        # Czech bullshit
        if removed == 1:
            czech = "a"
            hour = "a"
        elif 1 < removed <= 4:
            czech = "y"
            hour = "y"
        else:
            czech = "o"
            hour = ""
        if added == 1:
            czech2 = "a"
        elif 1 < added <= 4:
            czech2 = "y"
        else:
            czech2 = "o"
        await channel.send(f"Tento týden odpadl{czech} **{removed}** hodin{hour}, přidaných byl{czech2} **{added}**")

    # Detects changes in schedule and sends them to discord
    @staticmethod
    async def detect_changes(client: discord.Client):
        def is_week_change() -> bool:
            """Returns a boolean value if the weeks are currently changing"""
            weekday = datetime.datetime.today().weekday()
            # If the current day is monday or sunday
            if weekday == 0 or weekday == 6:
                # If current time is around midnight
                if 86280 < get_sec() or get_sec() < 120:
                    return True
            return False

        # Finds and returns the actual changes
        def find_changes(scheduleOld: Schedule, scheduleNew: Schedule):
            changedlist = []
            for (dayOld, dayNew) in zip(scheduleOld.days, scheduleNew.days):
                for (lessonOld, lessonNew) in zip(dayOld.lessons, dayNew.lessons):
                    changed = lessonOld, lessonNew, dayOld.day
                    # The actuall differences that we are looking for
                    if (
                        lessonOld.subject != lessonNew.subject
                        or lessonOld.classroom != lessonNew.classroom
                        or lessonOld.changeInfo != lessonNew.changeInfo
                    ):
                        changedlist.append(changed)
            if len(changedlist) != 0:
                return changedlist
            else:
                return None

        async def changed_message(changed: list, client: discord.Client, scheduleOld: Schedule, scheduleNew: Schedule):
            """Sends the changed schedules"""
            embedsColor = discord.Color.from_rgb(*rand_rgb())
            # Makes the two embeds containing the changed schedule images
            embedOld = discord.Embed(color=embedsColor)
            embedNew = discord.Embed(color=embedsColor)

            embedOld.title = f'Detekována změna v rozvrhu {"příštího" if scheduleOld.nextWeek else "aktuálního"} týdne'
            embedOld.description = "Zastaralý rozvrh"
            embedNew.description = "Aktualizovaný rozvrh"

            # Makes the 2D exclusives array with the right values
            exclusives = [[False for i in range(14)] for i in range(5)]
            for item in changed:
                exclusives[Schedule.DAYS[item[2]]][item[1].hour] = True

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
            for lessonOld, lessonNew, day in changed:
                changedStr += f"{day} {lessonOld.hour}. hodina: "
                changedStr += "**∅**" if lessonOld.empty else f"**{lessonOld.subject} {lessonOld.classroom}**"
                changedStr += " -> "
                changedStr += "**∅**" if lessonNew.empty else f"**{lessonNew.subject} {lessonNew.classroom}**"
                if lessonNew.changeInfo is not None:
                    changedStr += f"; *{lessonNew.changeInfo}*"
                changedStr += "\n"
            changedDetail.description = changedStr

            # Sends the messages
            channel = read_db("channelSchedule")
            await client.get_channel(channel).send(file=imgOld, embed=embedOld)
            await client.get_channel(channel).send(file=imgNew, embed=embedNew)
            await client.get_channel(channel).send(embed=changedDetail)

        # The main detection code
        # Gets the new Schedule objects
        scheduleNew1 = await Schedule.get_schedule(False, client)
        scheduleNew2 = await Schedule.get_schedule(True, client)
        # Gets the old Schedule objects
        scheduleOld1 = Schedule.db_schedule(False)
        scheduleOld2 = Schedule.db_schedule(True)
        # If bakalari server is down
        if scheduleNew1 is None or scheduleNew2 is None:
            return None

        # Detects any changes and sends the message and saves the schedule if needed
        # Current schedule
        changed = find_changes(scheduleOld1, scheduleNew1)
        if changed:
            # When the weeks are changing
            if is_week_change():
                await Schedule.new_week_message(scheduleNew1, scheduleNew2, client)
            else:
                await changed_message(changed, client, scheduleOld1, scheduleNew1)
            write_db("schedule1", Schedule.json_dumps(scheduleNew1))
        # Next week's schedule
        changed = find_changes(scheduleOld2, scheduleNew2)
        if changed:
            if not is_week_change():
                await changed_message(changed, client, scheduleOld2, scheduleNew2)
            write_db("schedule2", Schedule.json_dumps(scheduleNew2))

    # Starts an infinite loop for checking changes in the schedule
    @staticmethod
    async def start_detecting_changes(interval: int, client: discord.Client):
        while True:
            await Schedule.detect_changes(client)
            await asyncio.sleep(interval)
