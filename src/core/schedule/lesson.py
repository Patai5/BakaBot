from typing import Union

import disnake

from ...utils.utils import read_db
from ..subjects.subject import Subject
from ..table import Table


class Lesson:
    def __init__(
        self,
        hour: int,
        subject: Subject | None = None,
        classroom: Union[str, None] = None,
        teacher: Union[str, None] = None,
        changeInfo: Union[str, None] = None,
    ):
        self.hour = hour
        self.classroom = classroom
        self.teacher = teacher
        self.changeInfo = changeInfo
        self.subject = subject

        self.empty = subject is None

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

    async def render(
        self,
        shortName: bool = False,
        showClassroom: bool | None = None,
        renderStyle: Table.Style | None = None,
        file_name: str = "temp.png",
    ) -> disnake.File:
        """Returns a lesson rendered as an image"""
        if showClassroom == None:
            showClassroom = read_db("showClassroom")
            if showClassroom == None:
                raise ValueError("DB value for 'showClassroom' is None")

        lessonCell = self.buildLessonTableCell(showClassroom, shortName)

        return await Table([[lessonCell]]).render(file_name=file_name, style=renderStyle)

    def buildLessonTableCell(
        self,
        showClassroom: bool,
        shortName: bool,
    ) -> Table.Cell:
        """Builds a `Table.Cell` object of the lesson."""

        lessonNameText = self.getLessonName(shortName)
        lessonCell = Table.Cell([Table.Cell.Item(lessonNameText)])

        if showClassroom:
            lessonCell.items.append(Table.Cell.Item(self.classroom))

        return lessonCell

    def getLessonName(self, shortName: bool = False) -> str | None:
        """
        Returns the lesson name.
        - If the lesson is empty, returns None, otherwise returns either the short name or the full name of the subject.
        """
        if not self.subject:
            return None

        return shortName and self.subject.shortOrFullName or self.subject.fullName
