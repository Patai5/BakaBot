from __future__ import annotations


class Subject:
    def __init__(self, fullName: str, shortName: str | None):
        self.fullName = fullName
        """Full name of the subject. Always set. Extracted from both grades and schedule"""
        self.shortName = shortName
        """Short name of the subject. If not set, fallbacks to the full name. Extracted only from schedule"""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Subject):
            return False

        return self.fullName == other.fullName and self.shortName == other.shortName

    @property
    def shortOrFullName(self) -> str:
        """Returns the short name if set, otherwise the full name"""

        return self.shortName or self.fullName
