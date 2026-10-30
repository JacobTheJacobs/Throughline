"""Real browser regression: a rejected Wikidata work must not return under a Qloo alias.
Also records live fallback-category UI. No request or response mocking.
"""
import asyncio
import json
import sys
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE


async def emit(page, stage, **extra):
    calls = await page.evaluate("window.__liveAudit")
    for call in calls:
        data = call.get("data")
        if isinstance(data, dict):
            call["data"] = {k: data[k] for k in ["mode", "message", "reason", "availability", "coverage", "error"] if k in data}
            if "discoveries" in data:
                call["data"]["discoveries"] = [{k: c.get(k) for k in ["id", "name", "type", "relation"]} for c in data["discoveries"]]
    print(json.dumps({"stage": stage, **extra, "calls": calls}, ensure_ascii=False), flush=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.set_default_timeout(15000)
        await page.add_init_script("(" + OBSERVE + ")()")
        await page.goto(BASE + "/?seed=Octavia%20E.%20Butler")
        await page.wait_for_selector(".clarify-card")
        await page.wait_for_function("window.__liveAudit.some(x=>x.data?.mode==='clarify')")
        choices = await page.evaluate("window.__liveAudit.filter(x=>x.data?.mode==='clarify').at(-1).data.choices")
        writer = next(i for i, c in enumerate(choices) if c.get("type") == "person" and "writer" in c.get("detail", "").lower())
        await page.locator(".clarify-card>div>button").nth(writer).click()
        await page.wait_for_selector(".town-card", timeout=45000)
        await page.locator(".town-card").filter(has_text="Parable of the Talents").locator(".card-hit").click()
        await page.wait_for_selector(".cinematic-inspector")
        await page.locator(".rate-no").click()
        await page.wait_for_timeout(1200)
        if await page.get_by_role("button", name="Close details", exact=True).count():
            await page.get_by_role("button", name="Close details", exact=True).click()
        await page.locator(".town-card").filter(has_text="Parable of the Sower").locator(".card-hit").click()
        await page.wait_for_timeout(1500)
        await emit(page, "rejected-work-before-expansion", cards=await page.locator(".town-card").all_text_contents(), inspector=await page.locator(".cinematic-inspector").inner_text())
        books = page.locator(".direction-chips").get_by_role("button", name="Books", exact=False)
        if not await books.count():
            await page.locator(".qloo-all-toggle").click()
            if "--wait-for-availability" in sys.argv:
                await page.wait_for_function("window.__liveAudit.some(x=>x.request?.probeTypes&&x.request?.types?.includes('book')&&x.data?.availability?.book==='available')", timeout=35000)
            books = page.locator(".qloo-all-categories").get_by_role("button", name="Books", exact=True)
        if await books.count():
            await books.click()
            await page.wait_for_timeout(8000)
            await emit(page, "rejected-work-after-expansion", cards=await page.locator(".town-card").all_text_contents(), notice=await page.locator(".toast").inner_text() if await page.locator(".toast").count() else "")
        else:
            await emit(page, "books-unavailable", inspector=await page.locator(".cinematic-inspector").inner_text())
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
