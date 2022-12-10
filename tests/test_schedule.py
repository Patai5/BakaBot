from bakabot.core.schedule import Schedule


class TestSchedules:
    emptySchedule = Schedule([], False)

    only4thLessons = Schedule([], False)
    for day in only4thLessons.days:
        day.empty = False
        lesson = day.lessons[3]
        lesson.empty = False
        lesson.subject = f"Subject{day.weekDay}"
        lesson.classroom = f"Room{day.weekDay}"
        lesson.teacher = f"Mr.{day.weekDay}"
