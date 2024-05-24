SCHOOL_DAYS_IN_WEEK = 5
NUM_OF_LESSONS_IN_DAY = 13

# TODO: Ideally not have this hardcoded, instead somehow scrape this
SUBJECTS = {
    "Aj": "Jazyk anglický",
    "Bi": "Biologie",
    "Ch": "Chemie",
    "Čj": "Český jazyk a literatura",
    "D": "Dějepis",
    "Evh": "Estetická výchova - hudební",
    "Evv": "Estetická výchova - výtvarná",
    "Fj": "Jazyk francouzský",
    "Fy": "Fyzika",
    "Inf": "Informatika a výpočetní technika",
    "LpBi": "Laboratorní práce z biologie",
    "LpCh": "Laboratorní práce z chemie",
    "LpFy": "Laboratorní práce z fyziky",
    "M": "Matematika",
    "TH": "Třídnická hodina",
    "Tv": "Tělesná výchova",
    "Z": "Zeměpis",
    "Zsv": "Základy společenských věd",
}

SUBJECTS_REVERSED: dict[str, str] = {}
for key, value in zip(SUBJECTS.keys(), SUBJECTS.values()):
    SUBJECTS_REVERSED.update({value: key})

SUBJECTS_LOWER: dict[str, str] = {}
for key in SUBJECTS.keys():
    SUBJECTS_LOWER.update({key.lower(): key})


DAYS = {"po": 0, "út": 1, "st": 2, "čt": 3, "pá": 4}

DAYS_REVERSED: dict[int, str] = {}
for key, value in zip(DAYS.keys(), DAYS.values()):
    DAYS_REVERSED.update({value: key})

TABLE_CSS_PATH = "src/bakabot/html2img/css/table.css"
