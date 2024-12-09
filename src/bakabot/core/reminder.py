import asyncio

import disnake
from attr import dataclass
from core.schedule.day import Day
from core.schedule.lesson import Lesson
from core.schedule.schedule import Schedule
from disnake.ext.commands import InteractionBot
from utils.utils import from_sec_to_time, get_sec, get_week_day, getTextChannel, rand_rgb, read_db, write_db

REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC = 10 * 60  # 10 minutes
"""The time after the previous class has started to remind about the next class (in seconds)"""
REMIND_WHOLE_DAY_SCHEDULE_TIME = 6 * 60 * 60  # 6 AM
"""The time to remind the user about the whole day schedule (in seconds since midnight)"""

LESSON_LENGTH = 45 * 60  # 45 minutes
FULL_DAY_SECS = 24 * 60 * 60  # 24 hours


@dataclass
class RemindTime:
    timeSec: int
    remindWholeDaySchedule: bool


async def startReminder(client: InteractionBot):
    """Starts an infinite loop for sending the lesson reminders"""
    while True:
        nextRemindTime = getWaitUntilNextRemindTime(Schedule.db_schedule(), get_sec())
        await asyncio.sleep(nextRemindTime.timeSec)

        await remind(Schedule.db_schedule(), nextRemindTime, get_week_day(), client)
        await asyncio.sleep(1)


def getWaitUntilNextRemindTime(schedule: Schedule, currentTimeSec: int) -> RemindTime:
    """Gets the time to wait until the next remind time."""
    nextRemindTime = getNextRemindTime(schedule, currentTimeSec)
    waitUntilNextRemindTime = nextRemindTime.timeSec - currentTimeSec

    return RemindTime(waitUntilNextRemindTime, nextRemindTime.remindWholeDaySchedule)


def getNextRemindTime(schedule: Schedule, currentTimeSec: int) -> RemindTime:
    """
    Gets the next remind time for the schedule in seconds.
    - If we are already past the whole day, get the time for the next day whole day schedule
    - The last lesson is not counted in, as there is nothing to remind after it
    """
    remindWholeDaySchedule = currentTimeSec <= REMIND_WHOLE_DAY_SCHEDULE_TIME
    if remindWholeDaySchedule:
        return RemindTime(REMIND_WHOLE_DAY_SCHEDULE_TIME, remindWholeDaySchedule=True)

    for lessonTime in schedule.lessonTimes[:-1]:
        remindAfterLesson = lessonTime + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC
        isLessonTimeSuitable = remindAfterLesson > currentTimeSec
        if isLessonTimeSuitable:
            return RemindTime(remindAfterLesson, remindWholeDaySchedule=False)

    return RemindTime(FULL_DAY_SECS + REMIND_WHOLE_DAY_SCHEDULE_TIME, remindWholeDaySchedule=True)


async def remind(schedule: Schedule, remindTime: RemindTime, weekDay: int, client: InteractionBot):
    """
    Reminds the user about the next lesson or also the whole day schedule.
    - If it's the right time, remind about the whole day schedule + the next lesson
    """
    isWeekend = weekDay in (5, 6)
    if isWeekend:
        return

    scheduleDay = schedule.days[weekDay]

    if remindTime.remindWholeDaySchedule:
        if not scheduleDay.empty:
            await remindWholeDaySchedule(scheduleDay, client)

    lesson = getLessonToRemind(scheduleDay, schedule.lessonTimes, remindTime.timeSec)
    if lesson:
        await remindLesson(lesson, schedule.lessonTimes[lesson.hour], client)


def getLessonToRemind(day: Day, lessonTimes: list[int], currentTimeSec: int) -> Lesson | None:
    """
    Gets the lesson to remind about. If there is no suitable lesson, return None.
    - Suitable lesson has to be reminded before the class starts and has not been reminded yet
    - Skips over empty lessons by reminding the next lesson already
    """
    remindedLesson = read_db("lastLesson")

    for lesson in day.lessons:
        isLessonEmpty = lesson.empty
        if isLessonEmpty:
            continue

        isLessonTimeSuitable = lessonTimes[lesson.hour] >= currentTimeSec + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC
        if not isLessonTimeSuitable:
            continue

        hasBeenReminded = hasLessonBeenReminded(lesson, remindedLesson)
        if not hasBeenReminded:
            return lesson

    return None


def hasLessonBeenReminded(lesson: Lesson, lastRemindedLesson: Lesson | None) -> bool:
    """Checks if the lesson has been reminded already, by comparing it to the last reminded lesson"""
    return (
        lastRemindedLesson is not None
        and lesson.hour == lastRemindedLesson.hour
        and lesson.subject == lastRemindedLesson.subject
        and lesson.classroom == lastRemindedLesson.classroom
    )


async def remindWholeDaySchedule(day: Day, client: InteractionBot):
    """Sends the whole day schedule"""
    # Creates the embed with today's schedule
    embed = disnake.Embed(color=disnake.Color.from_rgb(*rand_rgb()))
    embed.title = "Dnešní rozvrh"

    # The schedule image
    fileName = "todaysSchedule.png"
    scheduleImg = await day.render(True, False, True, file_name=fileName)
    embed.set_image(url=f"attachment://{fileName}")

    # Sends the message
    channelId = read_db("channelReminder")
    if channelId is None:
        raise ValueError("No reminder channel set")

    await getTextChannel(channelId, client).send(file=scheduleImg, embed=embed)


async def remindLesson(lesson: Lesson, lessonStartTimeSec: int, client: InteractionBot):
    """Sends a reminder of the lesson to the discord channel"""

    # Creates the embed with the reminder info
    embed = disnake.Embed(color=disnake.Color.from_rgb(*rand_rgb()))

    # Title with the start and end times of the lesson
    lessonStartTime = from_sec_to_time(lessonStartTimeSec)
    lessonEndTime = from_sec_to_time(lessonStartTimeSec + LESSON_LENGTH)
    embed.title = lessonStartTime + " - " + lessonEndTime

    # The lesson image
    fileName = "nextLesson.png"

    reminderLessonShortName: bool | None = read_db("reminderShort")
    if reminderLessonShortName is None:
        raise ValueError("DB value for 'reminderShort' is None")

    lessonImg = await lesson.render(reminderLessonShortName, True, file_name=fileName)
    embed.set_image(url=f"attachment://{fileName}")

    # Sends the message
    channelId = read_db("channelReminder")
    if channelId is None:
        raise ValueError("No reminder channel set")

    await getTextChannel(channelId, client).send(file=lessonImg, embed=embed)

    # Saves the current lesson into the lastLesson database
    write_db("lastLesson", lesson)
