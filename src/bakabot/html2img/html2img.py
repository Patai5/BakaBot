import asyncio
from io import BytesIO

import disnake
from playwright.async_api import async_playwright


class Html2img:
    initialized = False

    @classmethod
    async def browser_init(cls):
        """Initializes the browser"""
        playwright = await async_playwright().start()
        cls.browser = await playwright.chromium.launch(headless=True)
        cls.initialized = True

    @classmethod
    async def render(cls, html: str, css: str) -> BytesIO:
        """Renders the html with the css and returns a binary image"""
        # Waits for the browser to initialize
        while not cls.initialized:
            await asyncio.sleep(0.1)
        page = await cls.browser.new_page()

        await page.set_content(html)
        await page.add_style_tag(content=css)

        await page.wait_for_load_state("domcontentloaded")

        size = await page.evaluate(
            """() => {
                const table = document.querySelector('table');
                return [table.offsetWidth, table.offsetHeight];
            }"""
        )
        await page.set_viewport_size({"width": size[0], "height": size[1]})

        binaryImg = await page.screenshot()

        await page.close()
        return BytesIO(binaryImg)

    @classmethod
    async def html2discord_file(cls, html: str, css: str, file_name: str = "table.png") -> disnake.File:
        """Returns a discord file of the rendered html image"""
        binaryImg = await cls.render(html, css)

        return disnake.File(fp=binaryImg, filename=file_name)
