from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import disnake

from ..subjects.subjects_cache import SubjectsCache

if TYPE_CHECKING:
    from ..grades.grades import Grades


class Grade:
    def __init__(
        self,
        id: str,
        caption: str,
        subjectName: str,
        weight: int,
        note: str,
        date: list[int],
        gradeText: str,
        gradeValue: float | None,
    ):
        self.id = id
        self.caption = caption
        self.subjectName = subjectName
        """The full name of the subject. Short name has to be fetched from the subjects cache"""
        self.weight = weight
        self.note = note
        self.date = date
        self.gradeText = gradeText
        self.gradeValue = gradeValue

    @staticmethod
    def empty_grade(subjectName: str = "", weight: int = 1, gradeValue: float = 1) -> Grade:
        """Makes a Grade object with as little parameters as possible"""
        return Grade("", "", subjectName, weight, "", [0, 0, 0], "", gradeValue)

    def grade_string(self) -> str:
        """Returns the `gradeValue` as a string. If the grade is a decimal number, adds a minus to it.
        - `gradeValue` can also be non-number, in which case we return the `gradeText`
        """
        if self.gradeValue is None:
            return self.gradeText

        # If the grade is a decimal number, we add a minus to it
        if self.gradeValue % 1 != 0:
            return str(int(self.gradeValue)) + "-"
        else:
            return str(int(self.gradeValue))

    def show(self, grades: Grades) -> disnake.Embed:
        """
        Returns an embed with the grade information
        - The full subject name is fetched from the subjects cache, if it's not found, fallbacks to the short name
        """

        title = self.grade_string()

        # Captions and notes into the same field (Same thing really)
        captionsNotes = ""
        if self.caption:
            captionsNotes += "\n" + self.caption
        if self.note:
            captionsNotes += "\n" + self.note
        description = f"Váha: {self.weight}{captionsNotes}"

        # Color of the embed
        if self.gradeValue is None:
            # If the grade is not a number, the color is simply gray
            color = disnake.Color.from_rgb(128, 128, 128)
        else:
            # Color of the embed from green (good) to red (bad) determining how bad the grade is
            green = int(255 / 4 * (self.gradeValue - 1))
            red = int(255 - 255 / 4 * (self.gradeValue - 1))
            color = disnake.Color.from_rgb(green, red, 0)

        # Date
        timestamp = datetime.datetime(self.date[0], self.date[1], self.date[2])

        # Creation of the embed
        embed = disnake.Embed(title=title, description=description, color=color, timestamp=timestamp)

        # Subject
        embed.set_author(name=self.subjectName)

        # Current average
        maybeSubject = SubjectsCache.tryGetSubjectByName(self.subjectName)
        subjectShortName = maybeSubject.shortOrFullName if maybeSubject else self.subjectName

        gradesFromSubject = grades.by_subject_name(self.subjectName)
        subjectAverage = gradesFromSubject.average()
        if subjectAverage is None:
            # If there are no grades for the subject with a number grade
            content = f"Průměr z {subjectShortName}: *nelze spočítat (žádné známky s číselným ohodnocením)*"
        else:
            # Normal average calculation
            content = f"Průměr z {subjectShortName}: {subjectAverage}"
        embed.add_field(name="\u200b", value=content, inline=False)

        # Returns the embed
        return embed
