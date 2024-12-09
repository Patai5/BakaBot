from core.reminder import (
    REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC,
    REMIND_WHOLE_DAY_SCHEDULE_TIME,
    getWaitUntilNextRemindTime,
)
from test_schedule import TestSchedules


def test_remind_whole_day():
    """Should remind about the whole day schedule with the first lesson"""
    schedule = TestSchedules.emptySchedule
    currentTimeSec = 50

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME - currentTimeSec
    assert remindTime.remindWholeDaySchedule is True


def test_remind_second_class():
    """Should remind about the second class"""
    schedule = TestSchedules.only4thLessons
    currentTimeSec = TestSchedules.defaultLessonTimes[0] + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC + 1

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    expectedLessonTime = TestSchedules.defaultLessonTimes[1] + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC - currentTimeSec

    assert remindTime.timeSec == expectedLessonTime
    assert remindTime.remindWholeDaySchedule is False


def test_should_go_over_to_next_day():
    """Should go over to the next day if there are no more lessons"""
    schedule = TestSchedules.only4thLessons
    currentTimeSec = TestSchedules.defaultLessonTimes[-1]

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME + 86400 - currentTimeSec
    assert remindTime.remindWholeDaySchedule is True
