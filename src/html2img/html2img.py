import asyncio
from io import BytesIO

import disnake
from playwright.async_api import Browser, async_playwright


class Html2img:
    @classmethod
    async def html2discord_file(cls, html: str, css: str, file_name: str = "table.png") -> disnake.File:
        """Returns a discord file of the rendered html image"""
        binaryImg = await cls.render(html, css)

        return disnake.File(fp=binaryImg, filename=file_name)

    browserInitLock = asyncio.Lock()

    @classmethod
    async def render(cls, html: str, css: str) -> BytesIO:
        """Renders the html with the css and returns a binary image"""
        async with cls.browserInitLock:
            if cls.browser is None:
                cls.browser = await cls.getBrowserInstance()

        page = await cls.browser.new_page()

        await page.set_content(html)
        await page.add_style_tag(content=css)
        await page.wait_for_function("document.fonts.ready")

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

    browser: Browser | None = None

    @classmethod
    async def getBrowserInstance(cls) -> Browser:
        """Returns an initialized browser instance"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)

        return browser
