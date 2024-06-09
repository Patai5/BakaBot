import json
import re

from bs4 import BeautifulSoup
from core.grades.grade import Grade
from core.grades.grades import Grades


def parseGrades(gradesHtml: str) -> Grades:
    """Returns a Grades object with the extracted information from the server"""
    gradesSoup = BeautifulSoup(gradesHtml, "html.parser")

    jsonDataScript = gradesSoup.select_one("div#cphmain_DivByTime > script")
    if jsonDataScript is None:
        raise ValueError("Could not find main data script for grades")

    parsedJsonData = re.search(r"\[\{.*](?=;)", jsonDataScript.text)
    if parsedJsonData is None:
        raise ValueError("Could not parse main data script for grades")

    jsonGradesData: list[dict[str, str]] = json.loads(parsedJsonData.group(0))
    return parseGradesJson(jsonGradesData)


def parseGradesJson(jsonGradesData: list[dict[str, str]]) -> Grades:
    """Returns a Grades object with the extracted information from the server"""
    gradesObject = Grades([])

    for jsonGrade in jsonGradesData:
        parsedGradeObject = parseGradeJson(jsonGrade)
        gradesObject.grades.append(parsedGradeObject)

    return gradesObject


def parseGradeJson(jsonGrade: dict[str, str]) -> Grade:
    """Returns a Grade object from the parsed json data"""

    caption = jsonGrade["caption"]
    id = jsonGrade["id"]
    subjectName = jsonGrade["nazev"]
    weight = int(jsonGrade["vaha"])
    note = jsonGrade["poznamkakzobrazeni"]
    date = jsonGrade["datum"]
    gradeText = jsonGrade["MarkText"]

    cleanNote = note.replace(" <br>", "")

    # Parses the date into list of [Year, Month, Day]
    # TODO: reformat: wth is this, use a datetime object not a list
    parsedDate = re.search(r"(\d{4})-0?(\d{1,2})-0?(\d{1,2})", date)
    if parsedDate is None:
        raise ValueError("Could not parse date for grade")

    dateList = [int(date) for date in parsedDate.group(1, 2, 3)]

    # Parses the grade as string or a float
    # TODO: reformat: move this logic somewhere else
    gradeValue = None
    if re.search(r"^\d-?$", gradeText):
        if "-" in gradeText:
            gradeValue = int(gradeText[0]) + 0.5
        else:
            gradeValue = int(gradeText)

    return Grade(id, caption, subjectName, weight, cleanNote, dateList, gradeText, gradeValue)
