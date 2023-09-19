from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import disnake
from constants import SUBJECTS

if TYPE_CHECKING:
    from core.grades.grades import Grades


class Grade:
    def __init__(
        self,
        id: str,
        caption: str,
        subject: str,
        weight: int,
        note: str,
        date: list[int],
        gradeText: str,
        gradeValue: float | None,
    ):
        self.id = id
        self.caption = caption
        self.subject = subject
        self.weight = weight
        self.note = note
        self.date = date
        self.gradeText = gradeText
        self.gradeValue = gradeValue

    @staticmethod
    def empty_grade(subject: str = "", weight: int = 1, gradeValue: float = 1):
        """Makes a Grade object with as little parameters as possible"""
        return Grade("", "", subject, weight, "", [0, 0, 0], "", gradeValue)

    def grade_string(self):
        """Returns the `gradeValue` as a string. If the grade is a decimal number, adds a minus to it.
        - `gradeValue` can also be non-number, in which case we return the `gradeText`"""
        if self.gradeValue is None:
            return self.gradeText

        # If the grade is a decimal number, we add a minus to it
        if self.gradeValue % 1 != 0:
            return str(int(self.gradeValue)) + "-"
        else:
            return str(int(self.gradeValue))

    def show(self, grades: Grades):
        # Creation of the embed
        embed = disnake.Embed()

        # Subject
        embed.set_author(name=SUBJECTS.get(self.subject))

        # Grade
        embed.title = self.grade_string()

        # Captions and notes into the same field (Same thing really)
        captionsNotes = ""
        if self.caption:
            captionsNotes += "\n" + self.caption
        if self.note:
            captionsNotes += "\n" + self.note

        # Weight
        embed.description = f"Váha: {self.weight}{captionsNotes}"

        # Current average
        gradesFromSubject = grades.by_subject(self.subject)
        subjectAverage = gradesFromSubject.average()
        if subjectAverage is None:
            # If there are no grades for the subject with a number grade
            content = f"Průměr z {self.subject}: *nelze spočítat (žádné známky s číselným ohodnocením)*"
        else:
            # Normal average calculation
            content = f"Průměr z {self.subject}: {subjectAverage}"
        embed.add_field(name="\u200b", value=content, inline=False)

        # Date
        embed.timestamp = datetime.datetime(self.date[0], self.date[1], self.date[2])

        # Color of the embed
        if self.gradeValue is None:
            # If the grade is not a number, the color is simply gray
            embed.color = disnake.Color.from_rgb(128, 128, 128)
        else:
            # Color of the embed from green (good) to red (bad) determining how bad the grade is
            green = int(255 / 4 * (self.gradeValue - 1))
            red = int(255 - 255 / 4 * (self.gradeValue - 1))
            embed.color = disnake.Color.from_rgb(green, red, 0)

        # Returns the embed
        return embed
