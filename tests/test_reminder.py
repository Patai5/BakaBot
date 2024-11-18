from core.reminder import REMIND_BEFORE_CLASS_TIME_SEC, REMIND_WHOLE_DAY_SCHEDULE_TIME, getWaitUntilNextRemindTime
from test_schedule import TestSchedules


def test_remind_whole_day():
    """Should remind about the whole day schedule before any classes"""
    schedule = TestSchedules.emptySchedule
    currentTimeSec = 50

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME - currentTimeSec
    assert remindTime.remindWholeDaySchedule is True


def test_remind_first_class():
    """Should remind about the first class"""
    schedule = TestSchedules.only4thLessons
    currentTimeSec = REMIND_WHOLE_DAY_SCHEDULE_TIME + 1

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    assert remindTime.timeSec == TestSchedules.defaultLessonTimes[0] - REMIND_BEFORE_CLASS_TIME_SEC - currentTimeSec
    assert remindTime.remindWholeDaySchedule is False


def test_should_go_over_to_next_day():
    """Should go over to the next day if there are no more lessons"""
    schedule = TestSchedules.only4thLessons
    currentTimeSec = TestSchedules.defaultLessonTimes[-1] + 1

    remindTime = getWaitUntilNextRemindTime(schedule, currentTimeSec)
    assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME + 86400 - currentTimeSec
    assert remindTime.remindWholeDaySchedule is True
