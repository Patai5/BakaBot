from typing import Union

from bakabot.constants import SUBJECTS_REVERSED
from bakabot.core.table import Table
from bakabot.utils.utils import read_db


class Lesson:
    def __init__(
        self,
        hour: int,
        subject: Union[str, None] = None,
        classroom: Union[str, None] = None,
        teacher: Union[str, None] = None,
        changeInfo: Union[str, None] = None,
    ):
        self.hour = hour
        self.classroom = classroom
        self.teacher = teacher
        self.changeInfo = changeInfo
        self.empty = None
        self.subject = subject

    @property
    def subject(self) -> str | None:
        return self._subject

    @subject.setter
    def subject(self, name: str | None):
        self._subject = name

        self.subjectShort = SUBJECTS_REVERSED.get(name) if name else None
        if self.subjectShort is None:
            self.subjectShort = name

        self.empty = not bool(name)

    def __str__(self) -> str:
        return f"Lesson(Hour: {self.hour}, Subject: {self.subject}, Classroom: {self.classroom}, Teacher: {self.teacher}, ChangeInfo: {self.changeInfo})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Lesson):
            return False
        return (
            self.hour == other.hour
            and self.subject == other.subject
            and self.classroom == other.classroom
            and self.teacher == other.teacher
            and self.changeInfo == other.changeInfo
        )

    def render(
        self,
        shortName: bool = False,
        showClassroom: bool | None = None,
        renderStyle: Table.Style | None = None,
        file_name: str = "temp.png",
    ):
        """Returns a lesson rendered as an image"""
        if showClassroom == None:
            showClassroom = read_db("showClassroom")
            if showClassroom == None:
                raise ValueError("DB value for 'showClassroom' is None")

        lessonCell = self.buildLessonTableCell(showClassroom, shortName)

        return Table([[lessonCell]]).render(file_name=file_name, style=renderStyle)

    def buildLessonTableCell(
        self,
        showClassroom: bool,
        shortName: bool,
    ) -> Table.Cell:
        """Builds a `Table.Cell` object of the lesson."""

        lessonCell = Table.Cell([Table.Cell.Item(self.subjectShort if shortName else self.subject)])
        if showClassroom:
            lessonCell.items.append(Table.Cell.Item(self.classroom))

        return lessonCell
