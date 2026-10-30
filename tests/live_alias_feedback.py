"""Live cross-provider duplicate and feedback audit, without mocked responses."""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE, snapshot


async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(viewport={"width":1440,"height":900},reduced_motion="reduce")
        page.set_default_timeout(20000)
        await page.add_init_script("("+OBSERVE+")()")
        await page.goto(BASE+'/?seed=Octavia%20E.%20Butler')
        await page.wait_for_selector('.clarify-card')
        await page.wait_for_function("window.__liveAudit.some(x=>x.data?.mode==='clarify')")
        choices=await page.evaluate("window.__liveAudit.find(x=>x.data?.mode==='clarify').data.choices")
        i=next(i for i,c in enumerate(choices) if c['id']=='6D6C7047-3CF0-463A-9114-16E015A9EB8F')
        await page.locator('.clarify-card>div>button').nth(i).click()
        await page.wait_for_selector('.town-card',timeout=45000)
        original='wikidata:Q3211325'
        await page.locator(f'.town-card[data-node-id="{original}"] .card-hit').click()
        await page.locator('.rate-yes').click()
        await page.get_by_role('button',name='Close details',exact=True).click()
        await page.locator('.town-card[data-node-id="wikidata:Q3823447"] .card-hit').click()
        await page.wait_for_timeout(6500)
        books=page.locator('.direction-chips button').filter(has_text='Books')
        if not await books.count():
            await page.locator('.qloo-all-toggle').click()
            await page.wait_for_timeout(6500)
            books=page.locator('.qloo-all-categories button').filter(has_text='Books')
        await books.click()
        duplicate='7DEDF979-7343-4B8D-BD58-D335F6B24D92'
        await page.locator(f'.town-card[data-node-id="{duplicate}"]').wait_for(timeout=25000)
        await snapshot(page,'visible-cross-provider-duplicate',saved=await page.locator('.top-saved').inner_text())
        if await page.get_by_role('button',name='Close details',exact=True).count():
            await page.get_by_role('button',name='Close details',exact=True).click()
        await page.locator(f'.town-card[data-node-id="{duplicate}"] .card-hit').click()
        await page.locator('.rate-no').click()
        await page.wait_for_timeout(1500)
        await snapshot(page,'reject-alias-of-saved-work',saved=await page.locator('.top-saved').inner_text())
        # Reach a new map through visible Home controls, preserving browser storage.
        await page.get_by_role('button',name='Back to Sideways home',exact=True).click()
        await page.get_by_role('textbox',name='What would you like to explore?',exact=True).fill('The Bear')
        await page.get_by_role('button',name='Begin exploring',exact=True).click()
        await page.wait_for_selector('.clarify-card')
        await page.wait_for_function("window.__liveAudit.some(x=>x.data?.question?.includes('The Bear'))")
        choices=await page.evaluate("window.__liveAudit.find(x=>x.data?.question?.includes('The Bear')).data.choices")
        i=next(i for i,c in enumerate(choices) if c.get('type')=='tv show' and c.get('year')==2022)
        await page.locator('.clarify-card>div>button').nth(i).click()
        await page.wait_for_function("document.querySelector('.exploration-context')?.textContent.includes('The Bear')",timeout=50000)
        await snapshot(page,'visible-home-map-isolation',saved=await page.locator('.top-saved').inner_text())
        await browser.close()


if __name__=='__main__':
    asyncio.run(main())
