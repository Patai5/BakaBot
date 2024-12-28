from typing import Literal

SCHOOL_DAYS_IN_WEEK = 5
NUM_OF_LESSONS_IN_DAY = 13

DAYS = {"po": 0, "út": 1, "st": 2, "čt": 3, "pá": 4}

DAYS_REVERSED: dict[int, str] = {}
for key, value in zip(DAYS.keys(), DAYS.values()):
    DAYS_REVERSED.update({value: key})

TABLE_CSS_PATH = "src/bakabot/html2img/css/table.css"

CHANNELS = {
    "grades": "channelGrades",
    "schedule": "channelSchedule",
    "reminder": "channelReminder",
    "status": "channelStatus",
}

FeaturesType = Literal["grades", "schedule", "reminder"]
FEATURES: list[FeaturesType] = ["grades", "schedule", "reminder"]

PREDICTOR_EMOJI = "📊"
