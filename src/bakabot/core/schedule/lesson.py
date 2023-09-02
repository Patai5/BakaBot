from __future__ import annotations

from typing import Union

from core.grades import Grades
from core.table import Table
from utils.utils import read_db


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

        self.subjectShort = Grades.SUBJECTS_REVERSED.get(name) if name else None
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
        showClassroom: bool | None = None,
        shortName: bool | None = False,
        renderStyle: Table.Style | None = None,
        file_name: str = "temp.png",
    ):
        """Returns a lesson redered as an image"""
        if showClassroom == None:
            showClassroom = read_db("showClassroom")

        cell = Table.Cell([Table.Cell.Item(self.subjectShort if shortName else self.subject)])
        if showClassroom:
            cell.items.append(Table.Cell.Item(self.classroom))
        return Table([[cell]]).render(file_name=file_name, style=renderStyle)
