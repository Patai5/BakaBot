from core.reminder import (
    REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC,
    REMIND_WHOLE_DAY_SCHEDULE_TIME,
    getLessonToRemind,
    getNextRemindTime,
)

from tests.test_schedule import TestSchedules


class Test_getNextRemindTime:
    def test_remind_whole_day(self):
        """Should remind about the whole day schedule with the first lesson"""
        schedule = TestSchedules.emptySchedule
        remindTime = getNextRemindTime(schedule, currentTimeSec=50)

        assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME
        assert remindTime.lessonTimeIndex == 0
        assert remindTime.remindWholeDaySchedule is True

    def test_remind_about_upcoming_lessons(self):
        """Should remind about the upcoming lessons"""
        schedule = TestSchedules.only4thAnd5thLessons
        firstLessonRemindTime = TestSchedules.defaultLessonTimes[0] + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC

        remindTime1 = getNextRemindTime(schedule, firstLessonRemindTime - 10)
        assert remindTime1.timeSec == firstLessonRemindTime
        assert remindTime1.lessonTimeIndex == 1
        assert remindTime1.remindWholeDaySchedule is False

        remindTime2 = getNextRemindTime(schedule, firstLessonRemindTime + 10)
        assert remindTime2.timeSec == TestSchedules.defaultLessonTimes[1] + REMIND_AFTER_PREVIOUS_CLASS_TIME_SEC
        assert remindTime2.lessonTimeIndex == 2
        assert remindTime2.remindWholeDaySchedule is False

    def test_should_go_over_to_next_day(self):
        """Should go over to the next day if there are no more lessons"""
        schedule = TestSchedules.only4thLessons
        currentTimeSec = TestSchedules.defaultLessonTimes[-1]
        remindTime = getNextRemindTime(schedule, currentTimeSec)

        assert remindTime.timeSec == REMIND_WHOLE_DAY_SCHEDULE_TIME + 86400
        assert remindTime.lessonTimeIndex == 0
        assert remindTime.remindWholeDaySchedule is True


class Test_getLessonToRemind:
    def test_should_get_correct_lesson(self):
        """Should get the correct lesson to remind"""
        schedule = TestSchedules.only4thAnd5thLessons

        lesson = getLessonToRemind(schedule.days[0], lessonTimeIndex=3, lastRemindedLesson=None)
        assert lesson == schedule.days[0].lessons[3]

        lesson2 = getLessonToRemind(schedule.days[0], lessonTimeIndex=4, lastRemindedLesson=None)
        assert lesson2 == schedule.days[0].lessons[4]

    def test_should_skip_empty_lessons(self):
        """Should skip over empty lessons"""
        schedule = TestSchedules.only4thAnd5thLessons

        lesson = getLessonToRemind(schedule.days[0], lessonTimeIndex=0, lastRemindedLesson=None)
        assert lesson == schedule.days[0].lessons[3]

    def test_should_return_none_for_last_reminded_lesson(self):
        """Should return `None` if the last reminded lesson was the last lesson"""
        schedule = TestSchedules.only4thAnd5thLessons

        lastRemindedLesson = schedule.days[0].lessons[3]
        lesson = getLessonToRemind(schedule.days[0], lessonTimeIndex=0, lastRemindedLesson=lastRemindedLesson)
        assert lesson == None

    def test_should_remind_after_the_last_reminded_lesson(self):
        """Should remind after the last reminded lesson, if we are past it"""
        schedule = TestSchedules.only4thAnd5thLessons

        lastRemindedLesson = schedule.days[0].lessons[3]
        lesson = getLessonToRemind(schedule.days[0], lessonTimeIndex=4, lastRemindedLesson=lastRemindedLesson)
        assert lesson == schedule.days[0].lessons[4]
