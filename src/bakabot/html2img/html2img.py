import asyncio
import os
from io import BytesIO

import disnake
from PIL import Image
from playwright.async_api import async_playwright


class Html2img:
    initialized = False

    @classmethod
    async def browser_init(cls):
        """Initializes the browser"""
        playwright = await async_playwright().start()
        cls.browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox"],
        )
        cls.initialized = True

    html2imgDir = os.path.join(os.getcwd(), "src", "bakabot", "html2img")

    tempPNGPath = os.path.join(html2imgDir, "temp", "temp.png")
    cssPathTable = os.path.join(html2imgDir, "css", "table")

    @classmethod
    async def render(cls, html: str, css_path: str):
        """Renders the html and saves it as a png"""
        path = os.path.join(css_path, "temp")
        if not os.path.isdir(path):
            os.mkdir(path)
        path = os.path.join(path, "index.html")

        # Waits for the browser to initialize
        while not cls.initialized:
            await asyncio.sleep(0.1)
        page = await cls.browser.new_page()

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        await page.goto("file://" + path)
        os.remove(path)

        size = await page.evaluate(
            """() => {
                const table = document.querySelector('table');
                return [table.offsetWidth, table.offsetHeight];
            }"""
        )
        await page.set_viewport_size({"width": size[0], "height": size[1]})

        tempDir = os.path.join(cls.html2imgDir, "temp")
        if not os.path.isdir(tempDir):
            os.mkdir(tempDir)
        await page.screenshot(path=cls.tempPNGPath)

    @classmethod
    async def html2discord_file(cls, html: str, css: str, file_name: str = "table.png") -> disnake.File:
        """Returns a discord file of the rendered html image"""
        await cls.render(html, css)

        img = Image.open(cls.tempPNGPath)
        binaryImg = BytesIO()
        img.save(binaryImg, "PNG")
        os.remove(cls.tempPNGPath)
        binaryImg.seek(0)

        return disnake.File(fp=binaryImg, filename=file_name)
