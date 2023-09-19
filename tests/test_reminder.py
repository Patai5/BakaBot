from typing import Tuple

import pytest
from core.reminder import Reminder
from core.schedule.day import Day
from core.schedule.lesson import Lesson
from core.schedule.schedule import Schedule
from test_schedule import TestSchedules

almostFullDayS = 60**2 * 23


@pytest.mark.parametrize(
    "day, time, current, expected",
    [
        (TestSchedules.emptySchedule.days[0], 0, False, None),
        (TestSchedules.emptySchedule.days[0], Reminder.REMIND[4], True, None),
        (TestSchedules.emptySchedule.days[0], almostFullDayS, False, None),
        (TestSchedules.only4thLessons.days[0], 0, False, TestSchedules.only4thLessons.days[0].lessons[3]),
        (
            TestSchedules.only4thLessons.days[0],
            Reminder.REMIND[2],
            False,
            TestSchedules.only4thLessons.days[0].lessons[3],
        ),
        (TestSchedules.only4thLessons.days[0], Reminder.REMIND[3], False, None),
        (
            TestSchedules.only4thLessons.days[0],
            Reminder.REMIND[3],
            True,
            TestSchedules.only4thLessons.days[0].lessons[3],
        ),
    ],
)
def test_multi_reminders(day: Day, time: int, current: bool, expected: Lesson | None):
    assert Reminder.next_reminder_lesson(day, time, current) == expected


@pytest.mark.parametrize(
    "schedule, weekDaySec, expected",
    [
        (TestSchedules.only4thLessons, (0, 0), Reminder.REMIND[0]),
        (TestSchedules.only4thLessons, (0, 10000), Reminder.REMIND[0] - 10000),
        (TestSchedules.only4thLessons, (0, Reminder.REMIND[0] - 1), 1),
        (TestSchedules.only4thLessons, (0, Reminder.REMIND[0]), Reminder.REMIND[1] - Reminder.REMIND[0]),
        (
            TestSchedules.only4thLessons,
            (0, Reminder.REMIND[3]),
            Reminder.FULL_DAY + Reminder.REMIND[0] - Reminder.REMIND[3],
        ),
        (TestSchedules.only4thLessons, (0, almostFullDayS), Reminder.FULL_DAY + Reminder.REMIND[0] - almostFullDayS),
        (TestSchedules.only4thLessons, (4, 0), Reminder.REMIND[0]),
        (
            TestSchedules.only4thLessons,
            (4, Reminder.REMIND[1]),
            Reminder.REMIND[2] - Reminder.REMIND[1],
        ),
        (
            TestSchedules.only4thLessons,
            (4, Reminder.REMIND[4]),
            Reminder.FULL_DAY * 3 + Reminder.REMIND[0] - Reminder.REMIND[4],
        ),
        (
            TestSchedules.only4thLessons,
            (4, almostFullDayS),
            Reminder.FULL_DAY * 3 + Reminder.REMIND[0] - almostFullDayS,
        ),
        (TestSchedules.only4thLessons, (5, 0), Reminder.FULL_DAY * 2 + Reminder.REMIND[0]),
        (TestSchedules.only4thLessons, (6, 0), Reminder.FULL_DAY + Reminder.REMIND[0]),
    ],
)
def test_multi_get_remind_times(schedule: Schedule, weekDaySec: Tuple[int, int], expected: int):
    assert Reminder.get_remind_time(schedule, weekDaySec) == expected
