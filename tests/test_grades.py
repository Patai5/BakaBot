from core.grades.grades import Grades
from core.grades.parse_grades import parseGrades

from tests.utils import open_html


def get_grades(filename: str) -> Grades | None:
    """Parses and returns Grades from the given filename"""
    html = open_html(filename)
    return parseGrades(html)


def test_bugged_grades():
    grades = get_grades("grades_bugged_script.html")
    assert grades is None
