from __future__ import annotations

import disnake
from core.subjects.subject import Subject
from core.subjects.utils import deduplicateSubjects
from disnake.ext.commands import InteractionBot

from bakabot.utils.utils import read_db, write_db


class SubjectsCache:
    """
    Caches the subjects and provides methods to work with them
    - A subject consists of both a full and a short name
    - Full name is extracted from both grades and the schedule, short names are extracted only from the schedule and
        thus we have to cache them
    """

    subjects: list[Subject] = []

    @classmethod
    def initialize(cls):
        """Initializes the SubjectsCache"""

        cls.subjects = cls._dbLoad()

    @classmethod
    def handleUpdateSubjects(cls, subjects: list[Subject]) -> bool:
        """
        Handles the update of new subjects.
        - Subjects with updated full names are updated, subjects with new short names are added.
        - Returns a boolean indicating whether any changes were made.
        """

        newSubjects = cls._getNewSubjects(subjects)
        cls.subjects.extend(newSubjects)

        toUpdateSubjects = cls._getToUpdateSubjects(subjects)
        for subject in toUpdateSubjects:
            cls._updateSubject(subject)

        hasMadeChanges = any([newSubjects, toUpdateSubjects])
        if hasMadeChanges:
            cls._dbSave()

        return hasMadeChanges

    @classmethod
    def getSubjectByName(cls, subjectName: str) -> Subject:
        subject = cls.tryGetSubjectByName(subjectName)
        if subject:
            return subject

        raise ValueError(f'No subject with the name "{subjectName}" found')

    @classmethod
    def tryGetSubjectByName(cls, subjectName: str) -> Subject | None:
        """Tries to get the subject by its name. Returns None if not found."""

        for subject in cls.subjects:
            if subject.fullName == subjectName:
                return subject

    @classmethod
    def updateCommandsWithSubjects(cls, client: InteractionBot):
        """Updates the commands with the subjects"""

        from bakabot.bot_commands.bot_commands import General

        subjectChoices = cls.getSlashCommandSubjectChoices()

        General.slashGradePrediction.options[0].choices = subjectChoices
        General.slashGradesAverage.options[0].choices = subjectChoices

        client.add_cog(General(client), override=True)

    @classmethod
    def getSlashCommandSubjectChoices(cls) -> list[disnake.OptionChoice]:
        """Returns the most recent subjects to use for options in a slash command as options"""

        choices: list[disnake.OptionChoice] = []

        for subject in cls.subjects:
            option = disnake.OptionChoice(name=subject.fullName, value=subject.fullName)
            choices.append(option)

        return choices

    @classmethod
    def _getNewSubjects(cls, subjects: list[Subject]) -> list[Subject]:
        """Returns the new subjects from the list of subjects. Ignores duplicates."""

        newSubjects = filter(
            lambda subject: cls.tryGetSubjectByName(subject.fullName) is None,
            subjects,
        )

        return deduplicateSubjects(list(newSubjects))

    @classmethod
    def _getToUpdateSubjects(cls, subjects: list[Subject]) -> list[Subject]:
        """Returns the subjects that should be updated from the list of subjects. Ignores duplicates."""

        toUpdateSubjects = filter(
            lambda subject: cls._shouldUpdateSubject(subject),
            subjects,
        )

        return deduplicateSubjects(list(toUpdateSubjects))

    @classmethod
    def _shouldUpdateSubject(cls, subject: Subject) -> bool:
        """
        Returns a boolean indicating whether the subject should be updated
        - Subjects are matched by their full names, the short names are compared.
        """

        cachedSubject = cls.tryGetSubjectByName(subject.fullName)
        if not cachedSubject:
            return False

        return cachedSubject.shortName != subject.shortName

    @classmethod
    def _updateSubject(cls, subject: Subject):
        """Updates the subject in the cache"""

        cachedSubject = cls.tryGetSubjectByName(subject.fullName)
        if not cachedSubject:
            return

        cls.subjects.remove(cachedSubject)
        cls.subjects.append(subject)

    @staticmethod
    def _dbLoad() -> list[Subject]:
        """Loads the Subject objects from the database"""

        subjects: list[Subject] | None = read_db("subjects")
        if subjects is None:
            raise Exception("Subjects database is empty")

        return subjects

    @classmethod
    def _dbSave(cls):
        """Saves the Subject objects to the database"""

        write_db("subjects", cls.subjects)
