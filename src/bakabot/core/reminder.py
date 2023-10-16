import asyncio
from typing import Tuple

import disnake
from core.schedule.day import Day
from core.schedule.schedule import Schedule
from utils.utils import from_sec_to_time, get_weekday_sec, getTextChannel, rand_rgb, read_db, write_db


class Reminder:
    # Constants for lesson times and remind times
    REMIND = [21600, 26100, 29400, 32700, 36600, 39900, 43200, 44400, 47700, 51000, 54000, 57000, 60000]
    LESSON_TIMES = [
        [25500, 28200],
        [28800, 31500],
        [32100, 34800],
        [36000, 38700],
        [39300, 42000],
        [42600, 45300],
        [43800, 48600],
        [47100, 49800],
        [50400, 53100],
        [53400, 56100],
        [56400, 59100],
        [59400, 62100],
    ]
    FULL_DAY = 86400

    @staticmethod
    def get_remind_time(schedule: Schedule, weekDaySec: Tuple[int, int]) -> int:
        """Gets the needed wait time for the nearest lesson and returns it"""
        weekDay, currentTimeSec = weekDaySec
        # Saturday
        if weekDay == 5:
            return Reminder.FULL_DAY * 2 + Reminder.REMIND[0] - currentTimeSec
        # Sunday
        if weekDay == 6:
            return Reminder.FULL_DAY + Reminder.REMIND[0] - currentTimeSec

        # Gets the next lesson for the day (if there is one)
        nextLesson = Reminder.next_reminder_lesson(schedule.days[weekDay], currentTimeSec)
        # Friday after no more lessons
        if weekDay == 4 and nextLesson is None:
            return Reminder.FULL_DAY * 3 + Reminder.REMIND[0] - currentTimeSec

        # School day with some upcoming lessons
        if nextLesson:
            # Gets the needed time for the next lesson
            for remindTime in Reminder.REMIND:
                if remindTime > currentTimeSec:
                    return remindTime - currentTimeSec
        # School day with no upcoming lessons (waits for the next day)
        return Reminder.FULL_DAY - currentTimeSec + Reminder.REMIND[0]

    @staticmethod
    def next_reminder_lesson(day: Day, currentTimeSec: int, current: bool | None = None):
        """Gets the next nearest lesson for reminder"""
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

    @staticmethod
    async def reminder(client: disnake.Client, when: int):
        """Sends a reminder of the lesson to the discord channel"""
        await asyncio.sleep(when)

        weekDay, currentTimeSec = get_weekday_sec()
        scheduleDay = Schedule.db_schedule().days[weekDay]

        channelId = read_db("channelReminder")
        if channelId is None:
            raise ValueError("No reminder channel set")

        lesson = Reminder.next_reminder_lesson(scheduleDay, currentTimeSec, current=True)
        if lesson:
            # Sends the full day schedule at 6:00am
            if Reminder.REMIND[0] - 60 < currentTimeSec < Reminder.REMIND[0] + 60:
                await Reminder.remind_whole_day_schedule(scheduleDay, client)

            # Checking if the lesson isn't the same as the previously reminded one
            lastLesson = read_db("lastLesson")
            if (
                lastLesson is None
                or lesson.hour != lastLesson.hour
                or lesson.subject != lastLesson.subject
                or lesson.classroom != lastLesson.classroom
            ):
                # Creates the embed with the reminder info
                embed = disnake.Embed(color=disnake.Color.from_rgb(*rand_rgb()))

                # Title with the start and end times of the lesson
                lessonStartTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][0])
                lessonEndTime = from_sec_to_time(Reminder.LESSON_TIMES[lesson.hour][1])
                embed.title = lessonStartTime + " - " + lessonEndTime

                # The lesson image
                fileName = "nextLesson.png"

                reminderLessonShortName: bool | None = read_db("reminderShort")
                if reminderLessonShortName is None:
                    raise ValueError("DB value for 'reminderShort' is None")

                lessonImg = await lesson.render(reminderLessonShortName, True, file_name=fileName)
                embed.set_image(url=f"attachment://{fileName}")

                # Sends the message

                await getTextChannel(channelId, client).send(file=lessonImg, embed=embed)

                # Saves the current lesson into the lastLesson database
                write_db("lastLesson", lesson)
        # Prevents sending multiple reminders
        await asyncio.sleep(1)

    @staticmethod
    async def remind_whole_day_schedule(day: Day, client: disnake.Client):
        """Sends the whole day schedule"""
        # Creates the embed with today's schedule
        embed = disnake.Embed(color=disnake.Color.from_rgb(*rand_rgb()))
        embed.title = "Dnešní rozvrh"

        # The schedule image
        fileName = "todaysSchedule.png"
        scheduleImg = await day.render(False, True, file_name=fileName)
        embed.set_image(url=f"attachment://{fileName}")

        # Sends the message
        channelId = read_db("channelReminder")
        if channelId is None:
            raise ValueError("No reminder channel set")

        await getTextChannel(channelId, client).send(file=scheduleImg, embed=embed)

    @staticmethod
    async def start_reminding(client: disnake.Client):
        """Starts an infinite loop for checking changes in the grades"""
        while True:
            when = Reminder.get_remind_time(Schedule.db_schedule(), get_weekday_sec())
            await Reminder.reminder(client, when)
