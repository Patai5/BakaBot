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
    def shortName(self) -> str:
        """Short name of the subject. If not set, fallbacks to the full name"""

        return self._shortName or self.fullName

    @shortName.setter
    def shortName(self, shortName: str | None):
        self._shortName = shortName

    @property
    def hasShortName(self) -> bool:
        """Returns True if the subject has a short name"""

        return self._shortName is not None
