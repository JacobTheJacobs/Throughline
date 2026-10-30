"""Live same-title adaptation/save/map-isolation checks. No API interception or mocks."""
import asyncio
import json
from urllib.parse import quote
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.set_default_timeout(15000)
        await page.add_init_script("(" + OBSERVE + ")()")
        for name, kind in [("Children of Men", "movie"), ("Station Eleven", "tv_show")]:
            await page.goto(BASE + "/?seed=" + quote(name) + "&type=" + kind)
            await page.wait_for_selector(".town-card", timeout=45000)
            await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='0'")
            count = await page.locator(".town-card").count()
            await page.locator(".town-card").first.locator(".card-hit").click()
            await page.wait_for_selector(".taste-reason")
            explanation = await page.locator(".taste-reason").inner_text()
            calls_before = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/discover').length")
            await page.locator(".rate-yes").click()
            await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
            await page.wait_for_timeout(500)
            calls_after = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/discover').length")
            assert await page.locator(".town-card").count() == count
            assert calls_before == calls_after
            await page.reload(wait_until="domcontentloaded")
            await page.wait_for_selector(".town-card")
            await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
            print(json.dumps({"stage": "adaptation-save-reload", "query": name, "explanation": explanation, "cards": count, "saved": await page.locator('.top-saved').inner_text(), "save_discovery_calls": calls_after-calls_before, "overflow": await page.evaluate('document.documentElement.scrollWidth>innerWidth')}, ensure_ascii=False), flush=True)
            # Let this map's normal debounced memory finish before switching maps.
            await page.wait_for_timeout(1200)
            await page.get_by_role("button", name="Back to Sideways home", exact=True).click()
            await page.wait_for_selector(".editorial-home")
        await page.set_viewport_size({"width":1440,"height":900})
        await page.locator('.recent-row>button:first-child').filter(has_text="Children of Men").click()
        await page.wait_for_selector(".town-card")
        await page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_function("window.__liveAudit.some(x=>x.url==='/api/agent')")
        agent = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/agent').at(-1)")
        await page.get_by_role("button", name="Stop exploring", exact=True).click()
        request = agent.get("request", {})
        print(json.dumps({"stage":"restored-map-memory", "saved":await page.locator('.top-saved').inner_text(), "root":request.get('root'), "likes":request.get('likes'), "dislikes":request.get('dislikes'), "memory":request.get('memory')}, ensure_ascii=False), flush=True)
        await page.wait_for_timeout(1200)
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_function("window.__liveAudit.filter(x=>x.url==='/api/agent').length>=2")
        settled = await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/agent').at(-1).request")
        await page.get_by_role("button", name="Stop exploring", exact=True).click()
        print(json.dumps({"stage":"restored-map-memory-settled", "root":settled.get('root'), "likes":settled.get('likes'), "memory":settled.get('memory')}, ensure_ascii=False), flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
