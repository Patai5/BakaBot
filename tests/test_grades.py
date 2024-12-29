from src.core.grades.grades import Grades
from src.core.grades.parse_grades import parseGrades

from .utils import open_html


def get_grades(filename: str) -> Grades | None:
    """Parses and returns Grades from the given filename"""
    html = open_html(filename)
    return parseGrades(html)


def test_bugged_grades() -> None:
    grades = get_grades("grades_bugged_script.html")
    assert grades is None
