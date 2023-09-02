from __future__ import annotations

from constants import NUM_OF_LESSONS_IN_DAY
from core.schedule.lesson import Lesson
from core.schedule.schedule import Schedule
from core.table import Table


class Day:
    def __init__(self, lessons: list[Lesson], weekDay: int, date: str | None):
        self.lessons = lessons
        self.weekDay = weekDay
        self.nameShort = Schedule.DAYS_REVERSED[weekDay]
        self.date = date

    @property
    def lessons(self) -> list[Lesson]:
        return self._lessons

    @lessons.setter
    def lessons(self, lessons: list[Lesson]):
        # Adds empty lessons if there have been none given
        if lessons == []:
            lessons = [Lesson(i) for i in range(NUM_OF_LESSONS_IN_DAY)]
        self._lessons = lessons

    @property
    def empty(self) -> bool:
        return all([lesson.empty for lesson in self.lessons])

    def change_lesson(self, index: int, lesson: Lesson):
        """Changes the lesson at the given index to the given lesson. This function is needed for property setter"""
        self._lessons[index] = lesson

    def __str__(self) -> str:
        return f"Day(WeekDay: {self.weekDay}, NameShort: {self.nameShort}, Date: {self.date}, Empty: {self.empty})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Day):
            return False
        if not (
            self.weekDay == other.weekDay
            and self.nameShort == other.nameShort
            and self.date == other.date
            and self.empty == other.empty
        ):
            return False
        for lesson1, lesson2 in zip(self.lessons, other.lessons):
            if lesson1 != lesson2:
                return False
        return True

    def render(
        self,
        showDay: bool | None = None,
        showClassroom: bool | None = None,
        renderStyle: Table.Style | None = None,
        file_name: str = "day.png",
    ):
        """Renders the day as an rendered image"""
        return Schedule([self]).render(
            self.weekDay + 1,
            self.weekDay + 1,
            showDay=showDay,
            showClassroom=showClassroom,
            renderStyle=renderStyle,
            file_name=file_name,
        )

    # Gets the first non empty lesson of the day. If none then returns None
    def first_non_empty_lesson(self):
        for lesson in self.lessons:
            if not lesson.empty:
                return lesson
        return None

    # Gets the last non empty lesson of the day. If none then returns None
    def last_non_empty_lesson(self):
        for lesson in reversed(self.lessons):
            if not lesson.empty:
                return lesson
        return None
