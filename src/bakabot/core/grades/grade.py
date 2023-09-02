import datetime

import discord
from core.grades.grades import Grades


class Grade:
    def __init__(
        self, id: str, caption: str, subject: str, weight: int, note: str, date: list[int], grade: float | str
    ):
        self.id = id
        self.caption = caption
        self.subject = subject
        self.weight = weight
        self.note = note
        self.date = date
        self.grade = grade

    def grade_string(self):
        """Returns the grade as a string with a minus if it's a decimal number"""
        # If the grade is a string, we can just return it
        if isinstance(self.grade, str):
            return self.grade

        # If the grade is a decimal number, we add a minus to it
        if self.grade % 1 != 0:
            return str(int(self.grade)) + "-"
        else:
            return str(int(self.grade))

    def show(self, grades: Grades):
        # Creation of the embed
        embed = discord.Embed()

        # Subject
        embed.set_author(name=Grades.SUBJECTS.get(self.subject))

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
        if isinstance(self.grade, str):
            # If the grade is not a number, the color is simply gray
            embed.color = discord.Color.from_rgb(128, 128, 128)
        else:
            # Color of the embed from green (good) to red (bad) determining how bad the grade is
            green = int(255 / 4 * (self.grade - 1))
            red = int(255 - 255 / 4 * (self.grade - 1))
            embed.color = discord.Color.from_rgb(green, red, 0)

        # Returns the embed
        return embed
