"""Save a Discover-only card, let IndexedDB settle, inspect the next real feed request."""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width":1440,"height":900}, reduced_motion="reduce")
        await page.add_init_script("(" + OBSERVE + ")()")
        await page.goto(BASE + '/?seed=In%20the%20Mood%20for%20Love&type=movie')
        await page.wait_for_selector('.town-card', timeout=45000)
        await page.get_by_role('button', name='Discover', exact=True).click()
        await page.wait_for_selector('.discover-masonry>article', timeout=45000)
        first = page.locator('.discover-masonry>article').first
        name = await first.locator('h2').inner_text()
        before = await page.locator('.town-card').count()
        await first.get_by_role('button', name='Save to brief', exact=False).click()
        await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
        await page.wait_for_timeout(1500)
        events = await page.evaluate("""async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('sideways-memory');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});return await new Promise((resolve,reject)=>{const r=db.transaction('events','readonly').objectStore('events').getAll();r.onsuccess=()=>resolve(r.result.filter(x=>x.kind==='love'));r.onerror=()=>reject(r.error)})}""")
        previous = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/discover'&&x.request?.limit===9).length")
        await page.get_by_role('button', name='Load more picks', exact=True).click()
        await page.wait_for_function("window.__liveAudit.filter(x=>x.url==='/api/discover'&&x.request?.limit===9).length>"+str(previous))
        call = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/discover'&&x.request?.limit===9).at(-1)")
        print(json.dumps({"stage":"discover-save-memory", "saved_name":name, "saved":await page.locator('.top-saved').inner_text(), "graph_before":before, "graph_after_save":await page.locator('.town-card').count(), "persisted_loves":events, "request":call['request']},ensure_ascii=False),flush=True)
        await browser.close()


if __name__=='__main__':
    asyncio.run(main())
