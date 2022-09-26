import random
from typing import List

import discord
from html2img.html2img import Html2img


class Table:
    class Style:
        def __init__(self, background: int = None, backgroundAngle: int = None):
            if background is None:
                background = random.randint(0, len(self.backgrounds) - 1)
            self.background = self.backgrounds[background]

            self.backgroundAngle = backgroundAngle
            if self.backgroundAngle is None:
                self.backgroundAngle = random.randint(0, 360)

            self.set_background_angle()

        def set_background_angle(self):
            self.background = self.background.replace("{ANGLE}", str(self.backgroundAngle))

        backgrounds = [
            "linear-gradient({ANGLE}deg, #fc5c7d, #6a82fb)",
            "linear-gradient({ANGLE}deg, #ff0000, #24e912)",
        ]

    def __init__(self, columns: list):
        self.columns = columns
        self.rows = self.gen_rows()

    class Cell:
        def __init__(self, items: List, exclusive: bool = False):
            self.items = items
            self.exclusive = exclusive
            self.empty = True
            for item in items:
                if item.value:
                    self.empty = False

        class Item:
            def __init__(self, value: str):
                self.value = value

    def gen_rows(self) -> list:
        """Generates rows for the table"""
        rows = [[] for i in range(len(self.columns[0]))]
        for column in self.columns:
            for i, item in enumerate(column):
                rows[i].append(item)
        return rows

    async def render(self, file_name: str = "table.png", style: Style = None) -> discord.File:
        """Returns a rendered table as a discord.File"""
        return await Html2img.html2discord_file(self.renderHTML(style), Html2img.cssPathTable, file_name)

    def renderHTML(self, style: Style = None) -> str:
        """Returns an HTML table"""
        if style is None:
            style = self.Style()

        output = f"""<!DOCTYPE html><html><head><link rel="stylesheet" href="../styles.css"></head><body>"""

        output += f'<table class="{random.randint(0, len(style.backgrounds) - 1)}, {random.randint(0, 360)}">'
        for row in self.rows:
            output += "<tr>"
            for cell in row:
                output += '<td class="'
                output += "empty " if cell.empty else ""
                output += "exclusive " if cell.exclusive else ""
                output += '">'
                for item in cell.items:
                    output += f"<p>{item.value}</p>"
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
