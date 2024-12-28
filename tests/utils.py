import os

htmlResponsesPath = os.path.join("tests", "html_responses")


def open_html(filename: str) -> str:
    path = os.path.join(htmlResponsesPath, filename)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
