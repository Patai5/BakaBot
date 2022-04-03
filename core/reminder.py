import asyncio
import datetime

import discord
from utils.utils import from_sec_to_time, get_sec, read_db, write_db

from core.schedule import Schedule


class Reminder:
    # Constants for lesson times and remind times
    REMIND = [21600, 26100, 29400, 32700, 36600, 39900, 43200, 46500, 47700, 51000, 54000, 57000, 60000]
    LESSON_TIMES = [
        [25500, 28200],
        [28800, 31500],
        [32100, 34800],
        [36000, 38700],
        [39300, 42000],
        [42600, 45300],
        [45900, 48600],
        [47100, 49800],
        [50400, 53100],
        [53400, 56100],
        [56100, 59100],
        [59400, 62100],
    ]

    # Gets the needed wait time for the nearest lesson and creates the reminder
    @staticmethod
    async def create_reminder(client: discord.Client):
        weekday = datetime.datetime.today().weekday()
        # Friday after school
        if weekday == 4 and get_sec() > Reminder.REMIND[-1]:
            when = 86400 - get_sec() + 172800 + Reminder.REMIND[0]
            await Reminder.reminder(client, when)
        # Saturday
        elif weekday == 5:
            when = 86400 - get_sec() + 86400 + Reminder.REMIND[0]
            await Reminder.reminder(client, when)
        # Sunday
        elif weekday == 6:
            when = 86400 - get_sec() + Reminder.REMIND[0]
            await Reminder.reminder(client, when)
        # School day
        else:
            lesson = await Reminder.next_reminder_lesson()
            # If there are anymore lessons for the day
            if lesson:
                # Gets the needed time for the next lesson
                for remindTime in Reminder.REMIND:
                    if remindTime > get_sec():
                        when = remindTime - get_sec()
                        break
                await Reminder.reminder(client, when)
            else:
                # Waits until the next day
                when = 86400 - get_sec() + Reminder.REMIND[0]
                await Reminder.reminder(client, when)

    # Gets the next nearest lesson for reminder
    @staticmethod
    async def next_reminder_lesson(current: bool = None):
        schedule = await Schedule.db_schedule(False)
        weekday = datetime.datetime.today().weekday()
        day = schedule.days[weekday]

        currentTimeSec = get_sec()
        for lesson in day.lessons:
            # Current in case the time is dirrectly on the lessons yet you still want it
            if current:
                if Reminder.REMIND[lesson.hour] > currentTimeSec - 10:
                    if not lesson.empty:
                        return lesson
            else:
                if Reminder.REMIND[lesson.hour] > currentTimeSec:
                    if not lesson.empty:
                        return lesson
        return None

    # Sends a reminder of the lesson to the discord channel
    @staticmethod
    async def reminder(client: discord, when: int):
        await asyncio.sleep(when)

        channel = read_db("channelReminder")
        lesson = await Reminder.next_reminder_lesson(current=True)
        if lesson:
            # Creates a lastLesson database if needed for the first time
            if not read_db("lastLesson"):
                write_db("lastLesson", Schedule.Lesson.json_dumps(lesson))
            # Checking if the lesson isn't the same as the previously reminded one
            lastLesson = Schedule.Lesson.json_loads(read_db("lastLesson"))
            if (
                lesson.hour != lastLesson.hour
                or lesson.subject != lastLesson.subject
                or lesson.classroom != lastLesson.classroom
            ):
                # Creates the embed with the reminder info
                embed = discord.Embed()

                # Title with the start and end times of the lesson
                lessonStartTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][0])
                lessonEndTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][1])
                lessonTimes = lessonStartTime + " - " + lessonEndTime

                # The lesson asci table
                lessonTable = "```" + lesson.show(True) + "```"
                embed.add_field(name=lessonTimes, value=lessonTable, inline=False)

                # If lesson has a topic
                if lesson.topic:
                    embed.add_field(name="\u200b", value=lesson.topic, inline=False)

                # Sends the message
                await client.get_channel(channel).send(embed=embed)

                # Saves the current lesson into the lastLesson database
                write_db("lastLesson", Schedule.Lesson.json_dumps(lesson))
        # Prevents sending multiple reminders
        await asyncio.sleep(1)

    # Starts an infinite loop for checking changes in the grades
    @staticmethod
    async def start_reminding(client: discord.Client):
        while True:
            await Reminder.create_reminder(client)
