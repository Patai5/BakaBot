SCHOOL_DAYS_IN_WEEK = 5
NUM_OF_LESSONS_IN_DAY = 13

# TODO: Ideally not have this hardcoded, instead somehow scrape this
SUBJECTS = {
    "ANJ": "Anglický jazyk",
    "BIO": "Biologie",
    "CHE": "Chemie",
    "CEJ": "Český jazyk",
    "DEJ": "Dějepis",
    "EHV": "Estetická výchova - hudební",
    "EVV": "Estetická výchova - výtvarná",
    "FRJ": "Francouzský jazyk",
    "FYZ": "Fyzika",
    "IVT": "Informatika a výpočetní technika",
    "LpBi": "Laboratorní práce z biologie",
    "LpCh": "Laboratorní práce z chemie",
    "LpFy": "Laboratorní práce z fyziky",
    "MAT": "Matematika",
    "TH": "Třídnická hodina",
    "TEV": "Tělesná výchova",
    "ZEM": "Zeměpis",
    "ZSV": "Základy společenských věd",
    "LIT": "Literatura"
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
