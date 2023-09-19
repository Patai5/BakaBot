import json
import re

from bs4 import BeautifulSoup, Tag

from bakabot.constants import DAYS, SCHOOL_DAYS_IN_WEEK
from bakabot.core.schedule.day import Day
from bakabot.core.schedule.lesson import Lesson
from bakabot.core.schedule.schedule import Schedule


def parseSchedule(body: BeautifulSoup, nextWeek: bool) -> Schedule | None:
    """Parses a schedule object from the html. Returns None on bakalari's bugs. Throws ValueError on parsing errors"""

    scheduleEl = body.select_one("div#schedule")
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

    dayInfoGroups: list[str] = re.findall(r"([^(\\n)(\\r)\s]+)", dayInfo.text)
    if len(dayInfoGroups) != 2:
        raise ValueError("Couldn't parse day info")

    weekDay, date = dayInfoGroups
    weekDay = DAYS[weekDay]

    return Day(parseLessons(day), weekDay, date)


def parseLessons(dayEl: Tag) -> list[Lesson]:
    """Parses and returns Lessons from the given day element"""

    lessonsEls = dayEl.select("div.day-item")

    return [parseLesson(lesson, hour) for hour, lesson in enumerate(lessonsEls)]


def parseLesson(lessonEl: Tag, hour: int) -> Lesson:
    """Parses and returns Lesson from the given lesson element"""

    lessonDetailEl = getLessonDetailEl(lessonEl)
    if lessonDetailEl is None:
        raise ValueError("Couldn't find lesson detail element")

    if "empty" in lessonDetailEl.attrs["class"]:
        return Lesson(hour)

    lessonDetail: dict[str, str] = json.loads(lessonDetailEl.attrs["data-detail"])
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


def getLessonDetailEl(lessonEl: Tag) -> Tag | None:
    """Returns the lesson detail element. This element is found differently for these lesson types:
    - Normal lessons have this element placed in a div under the lesson element
    - Removed lessons have it placed directly in the lesson element"""

    isRemovedLesson = "day-item-hover" in lessonEl.attrs["class"]

    return lessonEl if isRemovedLesson else lessonEl.select_one(":first-child")


def isTwoWeeksBug(daysEls: list[Tag]) -> bool:
    """Checks if the schedule is two weeks long, this is a rare bug that happens sometimes on bakalari"""

    return len(daysEls) > SCHOOL_DAYS_IN_WEEK
