"""Live short-query, quota-degradation and immediate-feedback consistency audit.
Uses fresh browser state, real API responses and one explicitly cancelled agent run.
"""
import asyncio
import json
from urllib.parse import quote
from playwright.async_api import async_playwright
from live_round3_paths import OBSERVE
from live_queries import BASE


async def emit(page,stage,**extra):
    print(json.dumps({"stage":stage,**extra,"calls":await page.evaluate("window.__liveAudit")},ensure_ascii=False),flush=True)


async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        for query in ['Up','U2']:
            page=await browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
            await page.add_init_script('('+OBSERVE+')()')
            await page.goto(BASE+'/?seed='+quote(query))
            await page.wait_for_selector('.clarify-card',timeout=30000)
            await page.wait_for_timeout(300)
            await emit(page,'short-query-ui',query=query,choices=await page.locator('.clarify-card>div>button').count(),visible=await page.locator('.clarify-card').inner_text())
            await page.close()
        page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
        await page.add_init_script('('+OBSERVE+')()')
        await page.goto(BASE+'/?seed=Her&type=movie')
        await page.wait_for_selector('.town-card',timeout=45000)
        await page.locator('.town-card .card-hit').first.click()
        await page.wait_for_timeout(1800)
        await emit(page,'quota-ui',primary_categories=await page.locator('.direction-chips button').count(),inspector=await page.locator('.cinematic-inspector').inner_text())
        await page.locator('.rate-yes').click()
        await page.wait_for_timeout(1400)
        await page.locator('.rate-yes').click()
        await page.get_by_role('button',name='Close details',exact=True).click()
        await page.get_by_role('button',name='Explore for me',exact=True).click()
        await page.wait_for_function("window.__liveAudit.some(x=>x.url==='/api/agent')")
        await emit(page,'immediate-unlove-agent',saved=await page.locator('.top-saved').inner_text())
        stop=page.get_by_role('button',name='Stop exploring',exact=True)
        if await stop.count():
            await stop.click()
            await page.wait_for_timeout(500)
        await emit(page,'agent-cancelled',cards=await page.locator('.town-card').count(),log=await page.locator('.agent-log').inner_text() if await page.locator('.agent-log').count() else '')
        await browser.close()


if __name__=='__main__':
    asyncio.run(main())
