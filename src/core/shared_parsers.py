import re

IS_SCRIPT_BUGGED_REGEX = r'<script type="text\/javascript">\s*\Z'
"""
Check if the script is missing and bugged.
- If it's missing, then the body will end right after (with some empty lines).
    1. `<script type="text\\/javascript">` checks for the script
    2. `\\s*\\Z` checks for the end of the body with empty lines
"""


def isBuggedBakalariScript(html: str) -> bool:
    """Returns True if the bakalari's script is bugged with missing "app root" script"""

    isBugged = re.search(IS_SCRIPT_BUGGED_REGEX, html, re.MULTILINE)

    return bool(isBugged)
