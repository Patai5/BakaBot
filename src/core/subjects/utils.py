from .subject import Subject


def deduplicateSubjects(subjects: list[Subject]) -> list[Subject]:
    """Deduplicate the given list of subjects"""

    deduplicatedSubjects: list[Subject] = []

    for subject in subjects:
        if subject not in deduplicatedSubjects:
            deduplicatedSubjects.append(subject)

    return deduplicatedSubjects
