import asyncio
import os

import pytest
from bs4 import BeautifulSoup

from bakabot.core.schedule import Schedule


class TestSchedules:
    emptySchedule = Schedule([], False)

    only4thLessons = Schedule([], False)
    for day in only4thLessons.days:
        day.empty = False
        lesson = day.lessons[3]
        lesson.empty = False
        lesson.subject = f"Subject{day.weekDay}"
        lesson.classroom = f"Room{day.weekDay}"
        lesson.teacher = f"Mr.{day.weekDay}"

    schedules = [emptySchedule, only4thLessons]
    for schedule in schedules:
        for i, day in enumerate(schedule.days, start=1):
            day.date = f"{i}.1."


templatesPath = os.path.join("tests", "schedule_response_templates")


def open_schedule(filename: str, nextWeek: bool) -> Schedule:
    with open(os.path.join(templatesPath, filename), "r", encoding="utf-8") as f:
        return Schedule.parse_schedule(BeautifulSoup(f.read(), "html.parser"), nextWeek)


empty_schedule = open_schedule("schedule_empty.html", False)


@pytest.mark.parametrize(
    "lesson, expected",
    [
        (empty_schedule.days[0].lessons[0], TestSchedules.emptySchedule.days[0].lessons[0]),
        (empty_schedule.days[0].lessons[4], TestSchedules.emptySchedule.days[0].lessons[4]),
        (empty_schedule.days[4].lessons[10], TestSchedules.emptySchedule.days[4].lessons[10]),
    ],
)
def test_multi_empty_schedule_lessons(lesson: Schedule.Lesson, expected: Schedule.Lesson):
    print(f"Input: {lesson}\nExpected: {expected}")
    assert lesson == expected


@pytest.mark.parametrize(
    "day, expected",
    [
        (empty_schedule.days[0], TestSchedules.emptySchedule.days[0]),
        (empty_schedule.days[2], TestSchedules.emptySchedule.days[2]),
        (empty_schedule.days[4], TestSchedules.emptySchedule.days[4]),
    ],
)
def test_multi_empty_schedule_days(day: Schedule.Day, expected: Schedule.Day):
    print(f"Input: {day}\nExpected: {expected}")
    assert day == expected


def test_empty_schedule():
    print(f"Input: {empty_schedule}\nExpected: {TestSchedules.emptySchedule}")
    assert empty_schedule == TestSchedules.emptySchedule
