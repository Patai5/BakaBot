import json
import re

from bs4 import BeautifulSoup, Tag
from constants import SCHOOL_DAYS_IN_WEEK
from core.schedule.day import Day
from core.schedule.lesson import Lesson
from core.schedule.schedule import Schedule


def parseSchedule(body: BeautifulSoup, nextWeek: bool) -> Schedule | None:
    """Parses a schedule object from the html. Returns None on bakalari's bugs. Throws ValueError on parsing errors"""

    scheduleEl = body.select_one("div#schedule > div")
    if scheduleEl is None:
        raise ValueError("Couldn't find schedule element")

    daysEls = scheduleEl.select("div.day-row")

    encounteredTwoWeeksBug = isTwoWeeksBug(daysEls)
    if encounteredTwoWeeksBug:
        return None

    return Schedule(parseDays(daysEls), nextWeek)


def parseDays(daysEls: list[Tag]) -> list[Day]:
    """Parses and returns Days from the given days elements"""

    return [parseDay(day) for day in daysEls]


def parseDay(day: Tag) -> Day:
    """Parses and returns Day from the given day element"""

    dayInfo = day.select_one("div.day-name > div")
    if dayInfo is None:
        raise ValueError("Couldn't find day info element")

    dayInfoGroups = re.match(r"([^\n|\r| ]+)", dayInfo.text)
    if dayInfoGroups is None:
        raise ValueError("Couldn't parse day info")

    weekDay, date = dayInfoGroups.groups()
    weekDay = Schedule.DAYS[weekDay]

    return Day(parseLessons(day), weekDay, date)


def parseLessons(dayEl: Tag) -> list[Lesson]:
    """Parses and returns Lessons from the given day element"""

    lessonsEls = dayEl.select("div.day-item > div")

    return [parseLesson(lesson, hour) for hour, lesson in enumerate(lessonsEls)]


def parseLesson(lessonEl: Tag, hour: int) -> Lesson:
    """Parses and returns Lesson from the given lesson element"""

    if "empty" in lessonEl.attrs["class"]:
        return Lesson(hour)

    lessonDetail: dict[str, str] = json.loads(lessonEl.attrs["data-detail"])
    changeInfo = lessonDetail.get("changeinfo") or lessonDetail.get("removedinfo") or None

    absentInfo = lessonDetail.get("absentinfo")
    if absentInfo:
        return Lesson(hour, absentInfo, changeInfo=changeInfo)

    if lessonDetail.get("type") == "removed":
        return Lesson(hour, changeInfo=changeInfo)

    subjectText = lessonDetail.get("subjecttext")
    subjectRegex = re.match(r"^[^\|]+?(?= \|)", subjectText) if subjectText else None
    subject = subjectRegex.group(0) if subjectRegex else None

    classroom = lessonDetail.get("room")
    teacher = lessonDetail.get("teacher")

    return Lesson(hour, subject, classroom, teacher, changeInfo)


def isTwoWeeksBug(daysEls: list[Tag]) -> bool:
    """Checks if the schedule is two weeks long, this is a rare bug that happens sometimes on bakalari"""

    return len(daysEls) > SCHOOL_DAYS_IN_WEEK
