from constants import DAYS_REVERSED, NUM_OF_LESSONS_IN_DAY
from core.schedule.lesson import Lesson
from core.table import Table
from utils.utils import read_db


class Day:
    def __init__(self, lessons: list[Lesson], weekDay: int, date: str | None):
        self.lessons = lessons
        self.weekDay = weekDay
        self.nameShort = DAYS_REVERSED[weekDay]
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
        shortName: bool = True,
        showDay: bool | None = None,
        showClassroom: bool | None = None,
        renderStyle: Table.Style | None = None,
        file_name: str = "day.png",
    ):
        """Renders the day as an rendered image"""
        if showClassroom == None:
            # TODO: Add mongo db and db typing support
            showClassroom = read_db("showClassroom")
            if showClassroom == None:
                raise ValueError("DB value for 'showClassroom' is None")
        if showDay == None:
            # TODO: Add mongo db and db typing support
            showDay = read_db("showDay")
            if showDay == None:
                raise ValueError("DB value for 'showDay' is None")

        if self.empty:
            raise ValueError("Cannot render an empty day")

        dayTableToRender = self.buildDayTable(showClassroom, shortName, showDay)

        return Table([dayTableToRender]).render(file_name=file_name, style=renderStyle)

    def buildDayTable(self, showClassroom: bool, shortName: bool, showDay: bool) -> list[Table.Cell]:
        """Builds a `Table` object of the day."""

        startHour, endHour = self.getStartEndHours()
        if startHour is None or endHour is None:
            raise ValueError("Cannot render an empty day")

        lessonCells: list[Table.Cell] = []
        if showDay:
            lessonCells.append(Table.Cell([Table.Cell.Item(self.nameShort)]))

        for lesson in self.lessons[startHour : endHour + 1]:
            lessonCell = lesson.buildLessonTableCell(showClassroom, shortName)
            lessonCells.append(lessonCell)

        return lessonCells

    def getStartEndHours(self) -> tuple[int | None, int | None]:
        """Gets the start and end hours of the day. Empty lessons are not counted"""
        startHour = None
        endHour = None
        for lesson in self.lessons:
            if not lesson.empty:
                if startHour is None:
                    startHour = lesson.hour
                endHour = lesson.hour
        return startHour, endHour

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
