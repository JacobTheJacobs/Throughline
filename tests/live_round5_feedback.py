"""Live current-feedback regression and full agent run using the Wong Kar-wai map."""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE


async def emit(page, stage, **extra):
    calls = await page.evaluate("window.__liveAudit")
    agents = [c for c in calls if c["url"] == "/api/agent"]
    print(json.dumps({"stage": stage, **extra, "agents": agents}, ensure_ascii=False), flush=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.set_default_timeout(15000)
        await page.add_init_script("(" + OBSERVE + ")()")
        await page.goto(BASE + "/?seed=Wong%20Kar-wai&type=person")
        await page.wait_for_selector(".town-card", timeout=45000)
        first = page.locator(".town-card").filter(has_text="In the Mood for Love")
        await first.locator(".card-hit").click()
        await page.wait_for_timeout(1200)
        await page.locator(".rate-yes").click()
        await page.wait_for_timeout(1500)
        await page.locator(".rate-yes").click()
        await page.get_by_role("button", name="Close details", exact=True).click()
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_function("window.__liveAudit.some(x=>x.url==='/api/agent')")
        await emit(page, "immediate-unsave", saved=await page.locator(".top-saved").inner_text())
        await page.get_by_role("button", name="Stop exploring", exact=True).click()
        await page.wait_for_timeout(500)
        await emit(page, "cancelled", cards=await page.locator(".town-card").count(), log=await page.locator(".agent-log").inner_text())
        await page.evaluate("window.__liveAudit=[]")
        await first.locator(".card-hit").click()
        await page.locator(".rate-yes").click()
        await page.locator(".qloo-all-toggle").click()
        await page.wait_for_function("window.__liveAudit.some(x=>x.request?.probeTypes&&x.data?.availability?.movie)", timeout=35000)
        await page.wait_for_timeout(100)
        probes = await page.evaluate("window.__liveAudit.filter(x=>x.request?.probeTypes).map(x=>({request:x.request,status:x.status,availability:x.data?.availability}))")
        await page.get_by_role("button", name="Close details", exact=True).click()
        before = await page.locator(".town-card").count()
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_selector(".log-done", timeout=70000)
        await page.wait_for_function("window.__liveAudit.some(x=>x.url==='/api/agent'&&x.data?.events)", timeout=10000)
        await page.wait_for_timeout(1000)
        await emit(page, "agent-complete", before=before, after=await page.locator(".town-card").count(), saved=await page.locator(".top-saved").inner_text(), log=await page.locator(".agent-log").inner_text(), probes=probes)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
