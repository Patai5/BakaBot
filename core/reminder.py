import asyncio

import discord

from core.schedule import Schedule
from utils.utils import (
    from_sec_to_time,
    get_sec,
    get_week_day,
    get_weekday_sec,
    rand_rgb,
    read_db,
    write_db,
)


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
    FULL_DAY = 86400

    @staticmethod
    async def create_reminder(client: discord.Client):
        """Gets the needed wait time for the nearest lesson and creates the reminder"""
        weekDay, currentTimeSec = get_weekday_sec()

        # Friday after school
        if weekDay == 4 and currentTimeSec > Reminder.REMIND[-1]:
            when = Reminder.FULL_DAY * 3 + Reminder.REMIND[0] - currentTimeSec
        # Saturday
        elif weekDay == 5:
            when = Reminder.FULL_DAY * 2 + Reminder.REMIND[0] - currentTimeSec
        # Sunday
        elif weekDay == 6:
            when = Reminder.FULL_DAY + Reminder.REMIND[0] - currentTimeSec
        # School day
        else:
            lesson = await Reminder.next_reminder_lesson(weekDaySec=(weekDay, currentTimeSec))
            # If there are anymore lessons for the day
            if lesson:
                # Gets the needed time for the next lesson
                for remindTime in Reminder.REMIND:
                    if remindTime > currentTimeSec:
                        when = remindTime - currentTimeSec
                        break
            else:
                # Waits until the next day
                when = Reminder.FULL_DAY - currentTimeSec + Reminder.REMIND[0]
        await Reminder.reminder(client, when)

    @staticmethod
    async def next_reminder_lesson(current: bool = None, weekDaySec: tuple = (get_week_day(), get_sec())):
        """Gets the next nearest lesson for reminder"""
        schedule = Schedule.db_schedule()
        weekDay, currentTimeSec = weekDaySec
        day = schedule.days[weekDay]

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
            # Sends the full day schedule at 6:00am
            if Reminder.REMIND[0] - 60 < get_sec() < Reminder.REMIND[0] + 60:
                await Reminder.remind_whole_day_schedule(client)

            # Creates a lastLesson database if needed for the first time
            if not read_db("lastLesson"):
                write_db("lastLesson", lesson)
            # Checking if the lesson isn't the same as the previously reminded one
            lastLesson = read_db("lastLesson")
            if (
                lesson.hour != lastLesson.hour
                or lesson.subject != lastLesson.subject
                or lesson.classroom != lastLesson.classroom
            ):
                # Creates the embed with the reminder info
                embed = discord.Embed(color=discord.Color.from_rgb(*rand_rgb()))

                # Title with the start and end times of the lesson
                lessonStartTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][0])
                lessonEndTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][1])
                embed.title = lessonStartTime + " - " + lessonEndTime

                # The lesson image
                fileName = "nextLesson.png"
                lessonImg = await lesson.render(True, read_db("reminderShort"), file_name=fileName)
                embed.set_image(url=f"attachment://{fileName}")

                # Sends the message
                await client.get_channel(channel).send(file=lessonImg, embed=embed)

                # Saves the current lesson into the lastLesson database
                write_db("lastLesson", lesson)
        # Prevents sending multiple reminders
        await asyncio.sleep(1)

    # Sends the whole day schedule
    @staticmethod
    async def remind_whole_day_schedule(client: discord.Client):
        # Gets the schedule to be shown
        schedule = Schedule.db_schedule()
        weekday = get_week_day()

        # Creates the embed with today's schedule
        embed = discord.Embed(color=discord.Color.from_rgb(*rand_rgb()))
        embed.title = "Dnešní rozvrh"

        # The schedule image
        fileName = "todaysSchedule.png"
        scheduleImg = await schedule.render(weekday + 1, weekday + 1, False, True, file_name=fileName)
        embed.set_image(url=f"attachment://{fileName}")

        # Sends the message
        channel = read_db("channelReminder")
        await client.get_channel(channel).send(file=scheduleImg, embed=embed)

    # Starts an infinite loop for checking changes in the grades
    @staticmethod
    async def start_reminding(client: discord.Client):
        while True:
            await Reminder.create_reminder(client)
