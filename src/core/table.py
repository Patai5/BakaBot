from __future__ import annotations

import functools
import random

import disnake

from ..constants import TABLE_CSS_PATH
from ..html2img.html2img import Html2img


class Table:
    class Style:
        def __init__(self, background: int | None = None, backgroundAngle: int | None = None):
            if background is None:
                background = random.randint(0, len(self.backgrounds) - 1)
            self.background = self.backgrounds[background]

            self.backgroundAngle = backgroundAngle
            if self.backgroundAngle is None:
                self.backgroundAngle = random.randint(0, 360)

            self.set_background_angle()

        def set_background_angle(self) -> None:
            self.background = self.background.replace("{ANGLE}", str(self.backgroundAngle))

        backgrounds = [
            "linear-gradient({ANGLE}deg, #fc5c7d, #6a82fb)",
            "linear-gradient({ANGLE}deg, #8360c3, #2ebf91)",
            "linear-gradient({ANGLE}deg, #ff512f, #f09819)",
            "linear-gradient({ANGLE}deg, #0099f7, #f11712)",
            "linear-gradient({ANGLE}deg, #ff9966, #ff5e62)",
            "linear-gradient({ANGLE}deg, #00DBDE, #FC00FF)",
            "linear-gradient({ANGLE}deg, #FBDA61, #FF5ACD)",
            "linear-gradient({ANGLE}deg, #21D4FD, #B721FF)",
            "linear-gradient({ANGLE}deg, #d64c7f, #ee4758 50%)",
            "radial-gradient(circle farthest-side, #fceabb, #f8b500)",
            "linear-gradient({ANGLE}deg, #4158D0, #C850C0 46%, #FFCC70)",
            "linear-gradient({ANGLE}deg, rgb(182, 244, 146), rgb(51, 139, 147))",
            "linear-gradient({ANGLE}deg, rgb(242, 112, 156), rgb(255, 148, 114))",
            "linear-gradient({ANGLE}deg, rgba(255,174,0,1) 11.2%, rgba(255,0,0,1) 100.2%)",
            "linear-gradient({ANGLE}deg, rgba(156,252,248,1) 11.2%, rgba(110,123,251,1) 91.1% )",
        ]

    def __init__(self, columns: ColumnType):
        self.columns = columns
        self.rows = self.gen_rows()

    @staticmethod
    @functools.lru_cache
    def tableCss() -> str:
        with open(TABLE_CSS_PATH, "r") as f:
            return f.read()

    class Cell:
        def __init__(self, items: list[Table.Cell.Item], exclusive: bool = False):
            self.items = items
            self.exclusive = exclusive
            self.empty = True
            for item in items:
                if item.value:
                    self.empty = False

        class Item:
            def __init__(self, value: str | None):
                self.value = value

    def gen_rows(self) -> RowType:
        """Generates rows for the table"""
        rows: RowType = [[] for _ in range(len(self.columns[0]))]
        for column in self.columns:
            for i, item in enumerate(column):
                rows[i].append(item)
        return rows

    async def render(self, file_name: str = "table.png", style: Style | None = None) -> disnake.File:
        """Returns a rendered table as a disnake.File"""

        return await Html2img.html2discord_file(self.renderHTML(style), Table.tableCss(), file_name)

    def renderHTML(self, style: Style | None = None) -> str:
        """Returns an HTML table"""
        if style is None:
            style = self.Style()

        output = f"""<!DOCTYPE html><html><body>"""

        output += f'<table class="{random.randint(0, len(style.backgrounds) - 1)}, {random.randint(0, 360)}">'
        for row in self.rows:
            output += "<tr>"
            for cell in row:
                output += '<td class="'
                output += "empty " if cell.empty else ""
                output += "exclusive " if cell.exclusive else ""
                output += '">'
                for item in cell.items:
                    output += f"<p>{'' if item.value is None else item.value}</p>"
                output += "</td>"
            output += "</tr>"
        output += "</table>"
        output += f"""<script>
            window.onload = function () {{
                var background = "{style.background}";
                var query = [...document.querySelectorAll("td p")];
                query.push(document.querySelector("table"));
                query.forEach((element) => {{
                    element.style.backgroundImage = background;
                }});
            }};
        </script></body></html>"""

        return output


ColumnType = list[list[Table.Cell]]
RowType = ColumnType
