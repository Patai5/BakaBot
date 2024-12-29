from src.core.subjects.subject import Subject
from src.core.subjects.utils import deduplicateSubjects


def test_deduplicateSubjects() -> None:
    """Should deduplicate subjects"""

    subjects = [
        Subject("subject1", None),
        Subject("subject2", None),
        Subject("subject1", None),
    ]

    deduplicatedSubjects = deduplicateSubjects(subjects)

    assert len(deduplicatedSubjects) == 2
    assert Subject("subject1", None) in deduplicatedSubjects
    assert Subject("subject2", None) in deduplicatedSubjects
