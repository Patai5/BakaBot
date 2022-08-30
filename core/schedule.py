import asyncio
import copy
import datetime
import json
import random
import re

import discord
from bs4 import BeautifulSoup
from utils.utils import get_sec, login, read_db, request, write_db

from core.table import Table


class Schedule:
    def __init__(self, days: list, nextWeek: bool):
        self.days = days
        self.nextWeek = nextWeek

    class Day:
        def __init__(self, lessons: list, day: str, empty: bool):
            self.lessons = lessons
            self.day = day
            self.empty = empty

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

            if self.subject == " ":
                self.empty = True
            else:
                self.empty = False

        # Generates an asci table of the lesson
        def show(self, classroom: bool):
            column = []
            if classroom:
                column.append(Table.ColumnItem(self.subject, False))
                column.append(Table.ColumnItem(self.classroom, True))
            else:
                column.append(Table.ColumnItem(self.subject, True))
            table = Table([column])
            return table.show()

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
            days.append(Schedule.Day(lessons, day["day"], day["empty"]))
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
            output = output + ', "day": "' + day.day + '", "empty": ' + str(day.empty).lower() + "}, "
        output = output[:-2] + "]"
        output = output + ', "nextWeek": ' + str(schedule.nextWeek).lower() + "}"
        return output

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

            # Prevents day from being empty
            empty = False
            if not lessons:
                empty = True
                for i in range(12):
                    lessons.append(Schedule.Lesson(i, " ", " ", None, None))
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
                            classroom = " "

                        # Finds the topic
                        topic = re.search('(?<="theme":")[^"]+(?=")', str(mainData_div))
                        if topic:
                            topic = topic.group()
                    else:
                        subject = " "
                        classroom = " "
                        topic = None
                    # Creates Lesson object and saves it into lessons list
                    lessons[lesson_i] = Schedule.Lesson(lesson_i, subject, classroom, changeInfo, topic)
            # Gets the short version of the day's name
            dayShort_div = day.div.div.div.div
            dayShort = re.search("(?<=<div>)\s*?(..)(?=<br\/>)", str(dayShort_div)).group(1)

            # Creates Day object and saves it into the days list
            days[day_i] = Schedule.Day(lessons, dayShort, empty)
        # Returns full Schedule object
        schedule = Schedule(days, nextWeek)
        return schedule

    # Generates an asci table of the Schedule
    def show(
        self,
        dayStart: int,
        dayEnd: int,
        showDay: bool = None,
        showClassroom: bool = None,
        exclusives: list = None,
        image: bool = False,
    ):
        # Uses the setting if inputed else tries looking into the database
        if showDay == None:
            showDay = read_db("showDay")
            if showDay == None:
                showDay = False
        if showClassroom == None:
            showClassroom = read_db("showClassroom")
            if showClassroom == None:
                showClassroom = False
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
                column = [Table.ColumnItem(" ", True)]
                for day in schedule.days:
                    if showClassroom:
                        column.append(Table.ColumnItem(day.day, False))
                        column.append(Table.ColumnItem(" ", True))
                    else:
                        column.append(Table.ColumnItem(day.day, True))
                columns.append(column)
            for i in range(len(schedule.days[0].lessons)):
                # Adds the lesson hour to the top of the table
                column = [Table.ColumnItem(str(schedule.days[0].lessons[i].hour) + ".", True)]

                # Adds the actual lessons to the table
                for day_i, day in enumerate(schedule.days):
                    if showClassroom:
                        column.append(
                            Table.ColumnItem(day.lessons[i].subject, False, exclusives[day_i][day.lessons[i].hour])
                        )
                        column.append(
                            Table.ColumnItem(day.lessons[i].classroom, True, exclusives[day_i][day.lessons[i].hour])
                        )
                    else:
                        column.append(
                            Table.ColumnItem(day.lessons[i].subject, True, exclusives[day_i][day.lessons[i].hour])
                        )
                columns.append(column)
            # Returns printed Table of schedule
            output = Table(columns).show()
            return output
        else:
            return "V rozvrhu nic není"

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

        # Discord message with the information about the changes
        async def changed_message(changed: list, nextWeek: bool, client: discord.Client, schedule: Schedule):
            # Makes an ascii string with the lessons update
            def embed_lessons(lessonOld: Schedule.Lesson, lessonNew: Schedule.Lesson):
                # Generates an ascii table of the lesson
                lessonOldTable = lessonOld.show(True)
                lessonNewTable = lessonNew.show(True)
                # Splits the ascii table into rows
                lessonOldTable = lessonOldTable.split("\n")
                lessonNewTable = lessonNewTable.split("\n")

                output = "```"
                # Merges the lessons ascii tables into one string
                for lessonOldRow, lessonNewRow, row in zip(lessonOldTable, lessonNewTable, range(4)):
                    if row != 2:
                        output = output + lessonOldRow + "     " + lessonNewRow
                    else:
                        # Adds a nice arrow to indicate the updated lesson
                        output = output + lessonOldRow + " --> " + lessonNewRow
                    output = output + "\n"
                output = output + "```"
                return output

            channel = read_db("channelSchedule")
            # Creation of the embed
            embed = discord.Embed()
            embed.title = "Detekována změna v rozvrhu"
            # Seperate fields for the changed items
            for changedItem in changed:
                lessonOld, lessonNew, day = changedItem
                # Stops at the discord embed field amount limit
                if len(embed.fields) >= 23:
                    embed.add_field(
                        name="Maximální počet embedů v jedné zprávě vyplýtván",
                        value="Asi Hrnec změnil hodně " "předmětů najednou :(",
                        inline=True,
                    )
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
                    break

                # Creating the title
                if nextWeek:
                    title = "Příští týden"
                else:
                    title = "Tento týden"
                title += f" , {day}, {lessonOld.hour}. hodina"
                # Creating the content
                content = embed_lessons(lessonOld, lessonNew)
                # Adding the field to the embed
                embed.add_field(name=title, value=content, inline=True)

                # Change info field if needed
                if lessonNew.changeInfo:
                    title = "Change info"
                    content = lessonNew.changeInfo
                    embed.add_field(name=title, value=content, inline=True)
                elif lessonOld.changeInfo:
                    title = "Change info bylo odstraněno"
                    embed.add_field(name=title, value="\u200b", inline=True)

                # Empty field for inline property
                embed.add_field(name="\u200b", value="\u200b", inline=False)
            # Removes the last empty field and sets the color for the embed
            embed.remove_field(len(embed.fields) - 1)
            embed.color = discord.Color.from_rgb(200, 36, 36)

            # Makes the 2D exclusives array with the right values
            exclusives = [[False for i in range(14)] for i in range(5)]
            DAYS = {"po": 0, "út": 1, "st": 2, "čt": 3, "pá": 4}
            for item in changed:
                exclusives[DAYS[item[2]]][item[1].hour] = True

            # Generates an ascii table of the changed schedule
            scheduleToShow = (
                "```"
                + schedule.show(
                    1,
                    5,
                    showDay=True,
                    showClassroom=True,
                    exclusives=exclusives,
                )
                + "```"
            )

            # Sends the messages
            await client.get_channel(channel).send(embed=embed)
            await client.get_channel(channel).send(scheduleToShow)

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
                await changed_message(changed, False, client, scheduleNew1)
            write_db("schedule1", Schedule.json_dumps(scheduleNew1))
        # Next week's schedule
        changed = find_changes(scheduleOld2, scheduleNew2)
        if changed:
            if not is_week_change():
                await changed_message(changed, True, client, scheduleNew2)
            write_db("schedule2", Schedule.json_dumps(scheduleNew2))

    # Starts an infinite loop for checking changes in the schedule
    @staticmethod
    async def start_detecting_changes(interval: int, client: discord.Client):
        while True:
            await Schedule.detect_changes(client)
            await asyncio.sleep(interval)
