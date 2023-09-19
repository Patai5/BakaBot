import os

from bs4 import BeautifulSoup
from core.schedule.lesson import Lesson
from core.schedule.parse_schedule import parseSchedule
from core.schedule.schedule import Schedule


class TestSchedules:
    emptySchedule = Schedule([], False)

    only4thLessons = Schedule([], False)
    for day in only4thLessons.days:
        day.lessons[3] = Lesson(3, f"Subject{day.weekDay}", f"Room{day.weekDay}", f"Mr.{day.weekDay}")

    normalSchedule = Schedule([], False)
    # Monday
    normalSchedule.days[0].lessons[1] = Lesson(1, "Jazyk francouzský", "123", "Mr. Fj")
    normalSchedule.days[0].lessons[2] = Lesson(2, "Český jazyk a literatura", "1", "Mr. Cj")
    normalSchedule.days[0].lessons[3] = Lesson(3, "Matematika", "2", "M")
    normalSchedule.days[0].lessons[4] = Lesson(4, "Matematika", "2", "M")
    normalSchedule.days[0].lessons[6] = Lesson(6, "Informatika a výpočetní technika", "321", "XX")
    # Tuesday is empty
    # Wednesday
    normalSchedule.days[2].lessons[0] = Lesson(0, "Green", None, None)
    normalSchedule.days[2].lessons[1] = Lesson(1, "Red", None, None, "Přesun na 3.1., 3. hod (Bi, Mr. X)")
    normalSchedule.days[2].lessons[2] = Lesson(2, "Biologie", "1", "Mr. X", "Suplování (Mr. Z, 2)")
    normalSchedule.days[2].lessons[3] = Lesson(3, "Dějepis", "abc", "Mr. X")
    # Thursday is empty but because removed
    normalSchedule.days[3].lessons[4] = Lesson(4, None, None, None, "Zrušeno (Fy, XX)")
    # Friday
    normalSchedule.days[4].lessons[0] = Lesson(0, None, None, None, "Přesun na 5.1., 1. hod (D, Mr. X)")
    normalSchedule.days[4].lessons[1] = Lesson(1, "Dějepis", "1", "Mr. X", "Přesun z 5.1., 0")

    schedules = [emptySchedule, only4thLessons, normalSchedule]
    for schedule in schedules:
        for i, day in enumerate(schedule.days, start=1):
            day.date = f"{i}.1."


templatesPath = os.path.join("tests", "schedule_response_templates")


def open_schedule(filename: str, nextWeek: bool) -> Schedule:
    with open(os.path.join(templatesPath, filename), "r", encoding="utf-8") as f:
        parsedSchedule = parseSchedule(BeautifulSoup(f.read(), "html.parser"), nextWeek)

        if parsedSchedule is None:
            raise ValueError("Schedule is None")

        return parsedSchedule


def print_schedule_differences(schedule1: Schedule, schedule2: Schedule):
    for day1, day2 in zip(schedule1.days, schedule2.days):
        if day1 != day2:
            print(f"Day {day1.weekDay} is different:")
            print(f"\tInput:    {day1}\n\tExpected: {day2}\n")
            for lesson1, lesson2 in zip(day1.lessons, day2.lessons):
                if lesson1 != lesson2:
                    print(f"\tInput:    {lesson1}\n\tExpected: {lesson2}\n")


empty_schedule = open_schedule("schedule_empty.html", False)
normal_schedule = open_schedule("schedule_normal.html", False)


def test_empty_schedule():
    print_schedule_differences(empty_schedule, TestSchedules.emptySchedule)
    assert empty_schedule == TestSchedules.emptySchedule


def test_schedule():
    print_schedule_differences(normal_schedule, TestSchedules.normalSchedule)
    assert normal_schedule == TestSchedules.normalSchedule
