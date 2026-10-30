"""Live Discover separation: Save and Reject do not add graph nodes; Add to map does."""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.set_default_timeout(15000)
        await page.add_init_script("(" + OBSERVE + ")()")
        await page.goto(BASE + "/?seed=In%20the%20Mood%20for%20Love&type=movie")
        await page.wait_for_selector(".town-card", timeout=45000)
        before = await page.locator(".town-card").count()
        responsive = []
        for width in [390,768,900,901,1440]:
            await page.set_viewport_size({"width":width,"height":844})
            await page.wait_for_timeout(100)
            responsive.append({"width":width,"accessible_discover_buttons":await page.get_by_role("button",name="Discover",exact=True).count(),"header_buttons":await page.locator('.editorial-topbar .top-share').evaluate_all("els=>els.map(el=>({text:el.textContent,display:getComputedStyle(el).display}))")})
        print(json.dumps({"stage":"discover-responsive-access","measurements":responsive},ensure_ascii=False),flush=True)
        await page.get_by_role("button", name="Discover", exact=True).click()
        await page.wait_for_function("window.__liveAudit.some(x=>x.request?.agent&&x.request?.limit===9&&x.data)", timeout=45000)
        cards = page.locator(".discover-masonry>article")
        if not await cards.count():
            print(json.dumps({"stage":"discover-empty","graph":before,"visible":await page.locator('.discover-board').inner_text(),"calls":await page.evaluate('window.__liveAudit')},ensure_ascii=False),flush=True)
            await browser.close()
            return
        first = cards.first
        name = await first.locator("h2").inner_text()
        await first.get_by_role("button", name="Save to brief", exact=False).click()
        await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
        after_save = await page.locator(".town-card").count()
        rejected = None
        if await cards.count() > 1:
            rejected = await cards.nth(1).locator("h2").inner_text()
            await cards.nth(1).locator("button.reject").click()
            await page.wait_for_timeout(100)
        after_reject = await page.locator(".town-card").count()
        await first.get_by_role("button", name="Add to map", exact=False).click()
        await page.wait_for_function("document.querySelectorAll('.town-card').length>"+str(before))
        close = page.get_by_role("button", name="Close discovery feed", exact=True)
        close_hit = await close.evaluate("el=>{const r=el.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return{rect:{x:r.x,y:r.y,width:r.width,height:r.height},hit:hit?.outerHTML?.slice(0,500),clickable:!!hit&&(hit===el||el.contains(hit))}}")
        if close_hit["clickable"]:
            await close.click()
        await page.wait_for_timeout(1300)
        state = await page.evaluate("({calls:window.__liveAudit,stored:JSON.parse(localStorage.getItem('sideways.discovery.v2')||'null'),tastes:Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('sideways.taste.map.')).map(k=>[k,JSON.parse(localStorage.getItem(k))]))})")
        print(json.dumps({"stage":"discover-actions","saved_name":name,"rejected_name":rejected,"before":before,"after_save":after_save,"after_reject":after_reject,"after_add":await page.locator('.town-card').count(),"saved":await page.locator('.top-saved').inner_text(),"overflow":await page.evaluate('document.documentElement.scrollWidth>innerWidth'),"close_hit":close_hit,**state},ensure_ascii=False),flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
