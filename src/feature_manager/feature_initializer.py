from ..core.grades.grades import Grades
from ..core.reminder import startReminder
from ..core.schedule.schedule import ChangeDetector
from ..utils.utils import read_db
from .feature_manager import Feature, FeatureManager


def getFeatureManager() -> FeatureManager:
    """Returns a FeatureManager with all features registered."""
    featureManager = FeatureManager()

    gradesFeature = Feature(
        "grades",
        lambda: bool(read_db("channelGrades")),
        lambda client: Grades.start_detecting_changes(60, client),
    )
    featureManager.register_feature(gradesFeature)

    scheduleFeature = Feature(
        "schedule",
        lambda: bool(read_db("channelSchedule")),
        lambda client: ChangeDetector.start_detecting_changes(60, featureManager, client),
    )
    featureManager.register_feature(scheduleFeature)

    reminderFeature = Feature(
        "reminder",
        lambda: bool(read_db("channelReminder") and read_db("schedule1")),
        lambda client: startReminder(client),
    )
    featureManager.register_feature(reminderFeature)

    return featureManager
