from src.core.schedule.lesson import Lesson
from src.core.schedule.parse_schedule import parseSchedule
from src.core.schedule.schedule import Schedule
from src.core.subjects.subject import Subject

from .utils import open_html


class TestSchedules:
    defaultLessonTimes = [
        25500,
        28800,
        32100,
        36000,
        39300,
        42600,
        43800,
        45900,
        47100,
        50400,
        53400,
        56400,
        59400,
    ]
    emptySchedule = Schedule([], defaultLessonTimes, False)

    only4thLessons = Schedule([], defaultLessonTimes, False)
    for day in only4thLessons.days:
        subject = Subject(f"SubjectLong{day.weekDay}", f"SubjectShort{day.weekDay}")
        day.lessons[3] = Lesson(3, subject, f"Room{day.weekDay}", f"Mr.{day.weekDay}")

    only4thAnd5thLessons = Schedule([], defaultLessonTimes, False)
    for day in only4thAnd5thLessons.days:
        subject = Subject(f"SubjectLong{day.weekDay}1", f"SubjectShort{day.weekDay}1")
        day.lessons[3] = Lesson(3, subject, f"Room{day.weekDay}", f"Mr.{day.weekDay}")
        subject = Subject(f"SubjectLong{day.weekDay}2", f"SubjectShort{day.weekDay}2")
        day.lessons[4] = Lesson(4, subject, f"Room{day.weekDay}", f"Mr.{day.weekDay}")

    schedules = [emptySchedule, only4thLessons]
    for schedule in schedules:
        for i, day in enumerate(schedule.days, start=1):
            day.date = f"{i}.1."


def handle_open_schedule(filename: str, nextWeek: bool) -> Schedule:
    schedule = open_schedule(filename, nextWeek)
    if not schedule:
        raise ValueError("Schedule is None")

    return schedule


def open_schedule(filename: str, nextWeek: bool) -> Schedule | None:
    html = open_html(filename)
    return parseSchedule(html, nextWeek)


def print_schedule_differences(schedule1: Schedule, schedule2: Schedule) -> None:
    for day1, day2 in zip(schedule1.days, schedule2.days):
        if day1 != day2:
            print(f"Day {day1.weekDay} is different:")
            print(f"\tInput:    {day1}\n\tExpected: {day2}\n")
            for lesson1, lesson2 in zip(day1.lessons, day2.lessons):
                if lesson1 != lesson2:
                    print(f"\tInput:    {lesson1}\n\tExpected: {lesson2}\n")


empty_schedule = handle_open_schedule("schedule_empty.html", False)
normal_schedule = handle_open_schedule("schedule_normal.html", False)
empty_holiday_day_schedule = handle_open_schedule("schedule_holiday_day.html", False)
one_time_lesson_schedule = handle_open_schedule("schedule_one_time_lesson.html", False)
bugged_schedule = open_schedule("schedule_bugged_script.html", False)


def test_bugged_schedule() -> None:
    assert bugged_schedule == None


def test_empty_schedule() -> None:
    print_schedule_differences(empty_schedule, TestSchedules.emptySchedule)
    assert empty_schedule == TestSchedules.emptySchedule


def test_holiday_day_extraction() -> None:
    """Should extract an empty holiday day correctly"""

    holidayDay = empty_holiday_day_schedule.days[2]
    assert holidayDay.weekDay == 2
    assert holidayDay.date == "8.5."
    assert len(holidayDay.lessons) == 13

    assert holidayDay.lessons[0].empty == True
    assert holidayDay.lessons[0].subject == None


def test_one_time_lesson_extraction() -> None:
    """Should extract a one time special lesson correctly"""

    lesson = one_time_lesson_schedule.days[0].lessons[4]
    assert lesson.hour == 4
    assert lesson.empty == False
    assert lesson.subject == Subject("Před", "Před")
    assert lesson.classroom == None
    assert lesson.teacher == None
    assert lesson.changeInfo == None


def test_days_extraction() -> None:
    """Tests if the days are parsed correctly"""

    days = normal_schedule.days
    assert len(days) == 5

    assert days[0].date == "3.6."
    assert days[0].nameShort == "po"
    assert days[0].weekDay == 0

    assert days[4].date == "7.6."
    assert days[4].nameShort == "pá"
    assert days[4].weekDay == 4


def test_lessons_extraction() -> None:
    """Should extract lessons correctly"""

    lessons = normal_schedule.days[0].lessons
    assert len(lessons) == 13


def test_regular_lesson() -> None:
    """Should extract a regular lesson correctly"""

    lesson = normal_schedule.days[4].lessons[8]
    assert lesson.hour == 8
    assert lesson.empty == False
    assert lesson.subject == Subject("Jazyk anglický", "Aj")
    assert lesson.classroom == "129"
    assert lesson.teacher == "Mgr. Marcela Tesařová"
    assert lesson.changeInfo == None


def test_empty_lessons() -> None:
    """Should extract an empty lesson correctly"""

    lesson = normal_schedule.days[0].lessons[0]
    assert lesson.hour == 0
    assert lesson.empty == True
    assert lesson.subject == None
    assert lesson.classroom == None
    assert lesson.teacher == None
    assert lesson.changeInfo == None


def test_changed_lesson() -> None:
    """Should extract a changed lesson correctly"""

    lesson = normal_schedule.days[0].lessons[3]
    assert lesson.hour == 3
    assert lesson.empty == False
    assert lesson.subject == Subject("Chemie", "Ch")
    assert lesson.classroom == "104"
    assert lesson.teacher == "Mgr. Kateřina Hubková"
    assert lesson.changeInfo == "Zrušeno (Bi, Pecová Barbora)"


def test_removed_lesson() -> None:
    """Should extract a removed lesson correctly"""

    lesson = normal_schedule.days[0].lessons[4]
    assert lesson.hour == 4
    assert lesson.empty == True
    assert lesson.subject == None
    assert lesson.classroom == None
    assert lesson.teacher == None
    assert lesson.changeInfo == "Zrušeno (Zsv, Coufalová Lucie)"


def test_lesson_times() -> None:
    """Should extract lesson times correctly"""

    lessonTimes = normal_schedule.lessonTimes
    assert len(lessonTimes) == 13

    assert lessonTimes[0] == 25500
    assert lessonTimes[1] == 28800
    assert lessonTimes[12] == 59400
