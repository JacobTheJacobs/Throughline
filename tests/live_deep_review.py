"""Provider-backed follow-up: identity preservation, expansion and map isolation."""
import asyncio
import json
from urllib.parse import quote
from playwright.async_api import async_playwright
from live_queries import BASE


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.set_default_timeout(15000)
        seen = []

        async def record(response):
            if "/api/" not in response.url:
                return
            try:
                body = response.request.post_data_json
                data = await response.json() if "/api/agent" not in response.url else {"events": [json.loads(line) for line in (await response.text()).splitlines() if line.strip()]}
                seen.append({"route": response.url.split("/api/")[-1], "http": response.status, "request": body, "data": data})
            except Exception as e:
                seen.append({"route": response.url, "error": str(e)})

        page.on("response", record)
        await page.goto(f"{BASE}/?seed=Haruki%20Murakami")
        await page.wait_for_selector(".clarify-card")
        await page.wait_for_timeout(250)
        choice = next(x for x in reversed(seen) if x.get("data", {}).get("mode") == "clarify")
        choices = choice["data"]["choices"]
        selected = next(i for i, x in enumerate(choices) if x["id"] == "62A8F44C-CD8F-4BDB-878E-4634F2D97074")
        await page.locator(".clarify-card>div>button").nth(selected).click()
        await page.wait_for_selector(".town-card")
        await page.locator(".town-card").filter(has_text="Norwegian Wood").click()
        await page.locator(".rate-yes").click()
        await page.wait_for_timeout(5500)
        print(json.dumps({"stage": "fallback-card-open", "calls": seen, "inspector": await page.locator(".cinematic-inspector").inner_text()}, ensure_ascii=False), flush=True)
        buttons = page.locator(".direction-chips button")
        if await buttons.count():
            before = len(seen)
            await buttons.first.click()
            await page.wait_for_timeout(5000)
            print(json.dumps({"stage": "fallback-category-click", "calls": seen[before:], "notice": await page.locator(".toast").inner_text() if await page.locator(".toast").count() else "", "canvas_count": await page.locator(".town-card").count()}, ensure_ascii=False), flush=True)
        await page.get_by_role("button", name="Close details", exact=True).click()
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_selector(".log-done", timeout=65000)
        await page.wait_for_timeout(300)
        print(json.dumps({"stage": "fallback-agent", "log": await page.locator(".agent-log").inner_text(), "agent_calls": [x for x in seen if x["route"] == "agent"]}, ensure_ascii=False), flush=True)
        # A new map in the SAME browser must not inherit the saved count or likes.
        seen.clear()
        await page.goto(f"{BASE}/?seed=Arrival&type=movie")
        await page.wait_for_selector(".town-card", timeout=50000)
        await page.wait_for_timeout(1000)
        print(json.dumps({"stage": "new-map-isolation", "saved": await page.locator(".top-saved").inner_text(), "calls": seen}, ensure_ascii=False), flush=True)
        await browser.close()

        # Inspect ambiguous identity results, without selecting a substitute silently.
        api = await p.request.new_context(base_url=BASE, timeout=50000)
        for text in ["IKEA", "IKEA brand", "The Dispossessed", "The Dispossessed Ursula K. Le Guin"]:
            response = await api.post("/api/discover", data={"text": text})
            data = await response.json()
            print(json.dumps({"stage": "identity-inspection", "query": text, "http": response.status, "data": data}, ensure_ascii=False), flush=True)
        await api.dispose()


if __name__ == "__main__":
    asyncio.run(main())
