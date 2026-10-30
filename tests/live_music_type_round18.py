"""Real music-card classification consistency before/after restoration."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(reduced_motion='reduce')
        await page.goto('https://throughline.51-21-210-47.sslip.io/?seed=Arlo%20Parks&type=artist')
        card=page.locator('.town-card[data-node-id="wikidata:Q96072224"]')
        await card.wait_for(timeout=60000)
        initial=await card.get_attribute('data-type')
        await page.wait_for_timeout(600)
        await page.reload()
        await card.wait_for(timeout=20000)
        restored=await card.get_attribute('data-type')
        print(json.dumps({'name':'Black Dog','initialType':initial,'restoredType':restored,'stable':initial==restored}))
        await browser.close()

asyncio.run(main())
