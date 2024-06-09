import disnake
import pytest
from core.subjects.subject import Subject
from core.subjects.subjects_cache import SubjectsCache
from pytest_mock import MockerFixture


def test_initialize(mocker: MockerFixture):
    """Should initialize from the database"""

    spy = mocker.spy(SubjectsCache, "_dbLoad")
    spy.attach_mock(mocker.Mock(), "_dbLoad")
    SubjectsCache.initialize()

    spy.assert_called_once()


def test_getSubjectByName():
    """Should return the subject by its name and raise an error if not found"""

    SubjectsCache.subjects = [Subject("subject1", None)]

    assert SubjectsCache.getSubjectByName("subject1").fullName == "subject1"

    pytest.raises(ValueError, SubjectsCache.getSubjectByName, "subject2")


def test_tryGetSubjectByName():
    """Should return the subject by its name and None if not found"""

    SubjectsCache.subjects = [Subject("subject1", None)]

    firstSubject = SubjectsCache.tryGetSubjectByName("subject1")
    assert isinstance(firstSubject, Subject)
    assert firstSubject.fullName == "subject1"

    assert SubjectsCache.tryGetSubjectByName("subject2") is None


class Test_HandleUpdateSubjects:
    def test_ignore_existing_subjects(self, mocker: MockerFixture):
        """Should ignore already existing subjects"""

        SubjectsCache.subjects = [Subject("subject1", None)]

        spy = mocker.spy(SubjectsCache, "_dbSave")
        spy.attach_mock(mocker.Mock(), "_dbSave")
        changed = SubjectsCache.handleUpdateSubjects([Subject("subject1", None)])

        assert changed == False
        assert SubjectsCache.subjects == [Subject("subject1", None)]
        spy.assert_not_called()

    def test_add_new_subjects(self, mocker: MockerFixture):
        """Should add new subjects"""

        SubjectsCache.subjects = [Subject("subject1", None)]

        spy = mocker.spy(SubjectsCache, "_dbSave")
        spy.attach_mock(mocker.Mock(), "_dbSave")
        changed = SubjectsCache.handleUpdateSubjects([Subject("subject2", None)])

        assert changed == True
        assert SubjectsCache.subjects == [
            Subject("subject1", None),
            Subject("subject2", None),
        ]
        spy.assert_called_once()

    def test_update_subjects(self, mocker: MockerFixture):
        """Should update subjects"""

        SubjectsCache.subjects = [Subject("subject1", None)]

        spy = mocker.spy(SubjectsCache, "_dbSave")
        spy.attach_mock(mocker.Mock(), "_dbSave")
        changed = SubjectsCache.handleUpdateSubjects([Subject("subject1", "short1")])

        assert changed == True
        assert SubjectsCache.subjects == [Subject("subject1", "short1")]
        spy.assert_called_once()

    def test_multiple_changes(self, mocker: MockerFixture):
        """Should handle ignoring, adding and updating deduplicating subjects"""

        SubjectsCache.subjects = [Subject("subject1", None), Subject("subject2", None)]

        spy = mocker.spy(SubjectsCache, "_dbSave")
        spy.attach_mock(mocker.Mock(), "_dbSave")
        changed = SubjectsCache.handleUpdateSubjects(
            [
                Subject("subject1", None),
                Subject("subject2", None),
                Subject("subject2", None),
                Subject("subject3", "short3"),
                Subject("subject1", "short1"),
                Subject("subject1", "short1"),
            ]
        )

        assert changed == True
        assert len(SubjectsCache.subjects) == 3
        assert Subject("subject1", "short1") in SubjectsCache.subjects
        assert Subject("subject2", None) in SubjectsCache.subjects
        assert Subject("subject3", "short3") in SubjectsCache.subjects
        spy.assert_called_once()


def test_getSlashCommandSubjectChoices():
    """Should return the subject choices for the slash commands"""

    SubjectsCache.subjects = [
        Subject("subject1", "short1"),
        Subject("subject2", "short2"),
    ]

    choices = SubjectsCache.getSlashCommandSubjectChoices()

    assert choices == [
        disnake.OptionChoice(name="subject1", value="subject1"),
        disnake.OptionChoice(name="subject2", value="subject2"),
    ]
