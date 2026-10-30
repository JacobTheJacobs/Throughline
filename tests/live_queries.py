"""Seeded, provider-backed browser audit. No API mocks and no user browser state.
Run with the dev server available: python3 -u tests/live_queries.py
Prints one JSON result per query, including actual returned entities for review.
FLOW_PASS means browser/data-contract checks passed, not independently proven relevance.
Choosing the first exact name/type candidate deliberately audits first-choice ranking.
"""
import asyncio
import json
import os
import random
import re
import time
import unicodedata
from urllib.parse import quote
from playwright.async_api import async_playwright
from browser_wait import wait_until

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")
GROUPS = [
    (2, [(n, "person") for n in ["Greta Gerwig", "Bong Joon-ho", "Hayao Miyazaki", "Sofia Coppola", "Guillermo del Toro", "Denis Villeneuve"]]),
    (2, [(n, "person") for n in ["Ursula K. Le Guin", "James Baldwin", "Octavia E. Butler", "Haruki Murakami", "Toni Morrison", "Margaret Atwood"]]),
    (2, [(n, "artist") for n in ["Björk", "Daft Punk", "Radiohead", "Nina Simone", "Kendrick Lamar", "Aphex Twin"]]),
    (3, [(n, "brand") for n in ["Patagonia", "LEGO", "Adidas", "Nintendo", "IKEA", "Porsche", "Uniqlo", "Ben & Jerry's"]]),
    (2, [(n, "movie") for n in ["Arrival", "Parasite", "Moonlight", "The Grand Budapest Hotel", "Whiplash", "Everything Everywhere All at Once"]]),
    (2, [(n, "book") for n in ["1984", "Dune", "The Left Hand of Darkness", "Sapiens", "The Dispossessed"]]),
    (2, [(n, "video game") for n in ["Portal 2", "Hades", "Disco Elysium", "Stardew Valley", "Elden Ring"]]),
    (1, [(n, "tv show") for n in ["Succession", "Severance", "Fleabag"]]),
    (1, [(n, "podcast") for n in ["99% Invisible", "Radiolab", "The Moth"]]),
    (1, [(n, "destination") for n in ["Kyoto", "Lisbon", "Reykjavik"]]),
    (1, [(n, "destination") for n in ["Iceland", "Japan", "Portugal"]]),
    (1, [(n, "brand") for n in ["Apple", "Tesla"]]),
]


def key(value):
    return re.sub(r"[^\w]", "", "".join(c for c in unicodedata.normalize("NFD", value.casefold()) if not unicodedata.combining(c)))


def category(value):
    normalized = value.replace("_", " ").casefold()
    return {"videogame": "video game", "locality": "destination", "author": "person"}.get(normalized, normalized)


def matches_name(query, choice):
    name = choice.get("name", "")
    if key(name) == key(query):
        return True
    if choice.get("type") == "brand":
        suffix = r"(?:,?\s+)(?:incorporated|inc\.?|limited|ltd\.?|llc|corp(?:oration)?\.?|company|co\.?|ag|gmbh|plc)$"
        return key(re.sub(suffix, "", name, flags=re.I)) == key(re.sub(suffix, "", query, flags=re.I))
    if category(choice.get("type", "")) in ["book", "movie", "tv show", "video game", "album"]:
        unqualified = re.sub(r"\([^)]*\)|\[[^]]*\]", "", name)
        return key(unqualified) == key(re.sub(r"\([^)]*\)|\[[^]]*\]", "", query)) or key(name.split(": ")[0]) == key(query)
    return False


async def audit(browser, index, query, kind, expected=None, visuals=False, entry="url", visual_settle_ms=0):
    started = time.monotonic()
    viewport = {"width": 390, "height": 844} if index % 3 == 1 else {"width": 1440, "height": 900}
    context = await browser.new_context(viewport=viewport, reduced_motion="reduce")
    page = await context.new_page()
    page.set_default_timeout(12000)
    result = {"index": index + 1, "query": query, "intended_type": kind, "viewport": viewport["width"],
              "status": "FAIL", "checks": [], "warnings": [], "errors": [], "responses": []}
    requests = []
    request_details = []
    def request_seen(request):
        if "/api/" not in request.url:
            return
        requests.append(request.url)
        try:
            payload = request.post_data_json if request.method == "POST" else {}
        except Exception:
            payload = {}
        request_details.append({"url": request.url, "probeTypes": bool((payload or {}).get("probeTypes"))})
    page.on("request", request_seen)
    if expected:
        result["expected_identity"] = expected
    page.on("pageerror", lambda error: result["errors"].append(str(error)))

    async def response_seen(response):
        if "/api/" not in response.url:
            return
        entry = {"route": response.url.split("/api/")[-1].split("?")[0], "status": response.status}
        try:
            data = await response.json()
            if entry["route"] == "discover":
                entry.update({"mode": data.get("mode"), "message": data.get("message"), "seed": data.get("seed"),
                              "discoveries": data.get("discoveries", []), "choices": data.get("choices", [])})
        except Exception:
            if response.status >= 400:
                entry["error"] = (await response.text())[:500]
        result["responses"].append(entry)

    page.on("response", response_seen)
    try:
        if entry == "form":
            await page.goto(BASE, wait_until="domcontentloaded")
            # SSR markup can be visible before React attaches input handlers.
            await wait_until(page,"Object.keys(document.querySelector('.hero-search input')||{}).some(k=>k.startsWith('__reactProps'))", timeout=30000)
            await page.get_by_role("textbox", name="What would you like to explore?", exact=True).fill(query)
            await page.get_by_role("button", name="Begin exploring", exact=True).click()
        else:
            await page.goto(f"{BASE}/?seed={quote(query)}", wait_until="domcontentloaded")
        deadline = time.monotonic() + 105
        choices_made = 0
        fallback = False
        while time.monotonic() < deadline:
            if await page.locator(".town-card").count():
                break
            if await page.locator(".clarify-card:not(.intent-card)").count():
                await page.wait_for_timeout(150)
                choice_response = next((r for r in reversed(result["responses"]) if r.get("mode") == "clarify"), {})
                choices = choice_response.get("choices", [])
                desired = [c for c in choices if matches_name(query, c)
                           and category(c.get("type", "")) == category(kind)]
                if expected:
                    desired = [c for c in desired if
                               (not expected.get("year") or c.get("year") == expected["year"]) and
                               (not expected.get("detail_pattern") or re.search(expected["detail_pattern"], c.get("detail", ""), re.I))]
                if not desired:
                    raise AssertionError(f"Intended entity is missing or not uniquely identified: {[(c.get('name'),c.get('type')) for c in choices]}")
                if len(desired) > 1:
                    result["warnings"].append("Multiple same-name/same-type entities; first visible exact candidate selected")
                choice_index = choices.index(desired[0])
                result["chosen_identity"] = desired[0]
                await page.locator(".clarify-card>div>button").nth(choice_index).click()
                choices_made += 1
                if choices_made > 3:
                    raise AssertionError("Repeated clarification loop")
            elif await page.locator(".intent-card").count():
                if fallback:
                    raise AssertionError("Discovery returned to the intent chooser twice")
                result["warnings"].append((await page.locator(".intent-card h2").inner_text()))
                fallback = True
                await page.locator(".intent-card").get_by_role("button", name="Related tastes").click()
            elif await page.locator(".discovery-recovery").count():
                recovery = page.locator(".discovery-recovery")
                notice = await recovery.inner_text()
                result["warnings"].append(notice)
                audience = recovery.get_by_role("button", name="Try audience matches", exact=True)
                if fallback or not await audience.count():
                    raise AssertionError("Explicit recovery without a usable primary map: " + notice)
                fallback = True
                await audience.click()
            elif await page.locator(".toast").count():
                notice = await page.locator(".toast").inner_text()
                if any(term in notice.lower() for term in ["unavailable", "failed", "nothing found", "limit reached", "slow down", "has no audience data", "could not verify", "end of this trail", "no description or tags"]):
                    raise AssertionError(notice)
            await page.wait_for_timeout(200)
        else:
            raise AssertionError("No usable map within 105 seconds")

        await page.wait_for_timeout(1000)
        successful = [r for r in result["responses"] if r["route"] == "discover" and r.get("mode") == "live" and r.get("discoveries")]
        assert successful, "No live discovery response recorded"
        initial = successful[-1]
        cards = initial["discoveries"]
        seed = initial.get("seed") or {}
        result["seed"] = {k: seed.get(k) for k in ["id", "name", "type"]}
        result["cards"] = [{k: card.get(k) for k in ["id", "name", "type", "description", "relation", "reason", "reasonSource", "affinity", "links"]} for card in cards]
        if visuals:
            from live_visuals import capture_visuals
            result["visuals"] = await capture_visuals(page, settle_ms=visual_settle_ms)
            result["visual_issues"] = []
            if not result["visuals"]["visibleEdgeCount"]:
                result["visual_issues"].append("No visible graph connections in the initial map")
            missing_art = [c["name"] for c in result["visuals"]["cards"] if not any(i["complete"] and i["width"] > 0 for i in c["images"])]
            if missing_art:
                result["visual_issues"].append("Cards without loaded artwork: " + "; ".join(missing_art))
            if kind == "artist":
                await page.screenshot(path=f"/tmp/sideways-round8-artist-{index}.png")
        count = await page.locator(".town-card").count()
        assert 1 <= count <= 5, f"Unexpected initial card count: {count}"
        assert len({c["id"] for c in cards}) == len(cards), "Duplicate result IDs"
        assert all(c["id"] != seed.get("id") for c in cards), "Source returned as its own discovery"
        assert seed.get("name") in await page.locator(".exploration-context").inner_text(), "Starting point is missing"
        assert all(c.get("reason") for c in cards), "Missing relationship explanation"
        assert not await page.evaluate("document.documentElement.scrollWidth>innerWidth"), "Horizontal overflow"
        for card in cards:
            if card.get("relation") == "Manufactured by":
                assert card["type"] == "company", "Manufacturer incorrectly typed"
                assert card["reason"] == f"{seed['name']} is manufactured by {card['name']}.", "Reversed manufacturer relation"
            if card.get("relation"):
                assert not card.get("affinity"), "Factual credit incorrectly has an audience score"
            description = card.get("description", "")
            if card.get("relation") == "Performed by" and re.search(r"\balbum\b", description, re.I):
                assert card["type"] == "album", f"Album mislabeled as {card['type']}: {card['name']}"
            if re.search(r"\b(?:video game|game|handheld|home) console\b", description, re.I):
                assert card["type"] == "product", f"Hardware mislabeled as {card['type']}: {card['name']}"
        result["checks"].extend(["resolved", "1–5 unique non-source cards", "visible source context", "relationship labels", "no horizontal overflow"])

        await page.locator(".town-card").first.click(timeout=6000)
        await page.wait_for_selector(".cinematic-inspector")
        result["inspector_explanation"] = await page.locator(".taste-reason").inner_text()
        assert f"{seed['name']} {seed['name']}" not in result["inspector_explanation"], "Connection explanation repeats the reference title"
        before = len(request_details)
        await page.locator(".rate-yes").click()
        await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
        await page.wait_for_timeout(600)
        assert await page.locator(".town-card").count() == count, "Saving unexpectedly expanded the map"
        result["save_window_requests"] = [r for r in request_details[before:] if "/api/discover" in r["url"]]
        assert not any(not r["probeTypes"] for r in result["save_window_requests"]), "Save launched a non-probe discovery request"
        if result["save_window_requests"]:
            result["warnings"].append("The inspector's scheduled category probe overlapped Save; graph stayed unchanged. Save/no-save control is tested separately.")
        await page.get_by_role("button", name="Close details", exact=True).click()
        before_reload = sum("/api/discover" in url for url in requests)
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_selector(".town-card")
        await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
        assert sum("/api/discover" in url for url in requests) == before_reload, "Reload repeated the search instead of restoring the resolved map"
        await page.get_by_role("button", name="Gallery", exact=True).click()
        assert await page.locator(".gallery-board").is_visible(), "Gallery does not open"
        assert not await page.evaluate("document.documentElement.scrollWidth>innerWidth"), "Gallery overflows horizontally"
        result["checks"].extend(["card opens", "save does not expand or launch non-probe discovery", "save survives reload", "gallery opens"])
        assert not result["errors"], result["errors"]
        failed_http = [r for r in result["responses"] if r["status"] >= 400]
        if failed_http:
            result["warnings"].append(f"HTTP errors: {[(r['route'],r['status']) for r in failed_http]}")
        result["status"] = "FALLBACK" if fallback else "FLOW_PASS"
    except Exception as error:
        result["errors"].append(str(error))
        try:
            result["visible_state"] = (await page.locator("body").inner_text())[-1600:]
        except Exception:
            pass
    finally:
        result["seconds"] = round(time.monotonic() - started, 1)
        await context.close()
    result["responses"] = [{k: r[k] for k in ["route", "status", "mode", "message", "error"] if k in r} for r in result["responses"]]
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


async def main():
    rng = random.Random(20261028)
    cases = [case for size, pool in GROUPS for case in rng.sample(pool, size)]
    print(json.dumps({"selected_queries": cases, "live_providers": True, "concurrency": 2}, ensure_ascii=False), flush=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        semaphore = asyncio.Semaphore(2)

        async def run(index, case):
            async with semaphore:
                return await audit(browser, index, *case)

        results = await asyncio.gather(*(run(i, case) for i, case in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary": {status: sum(r["status"] == status for r in results) for status in ["FLOW_PASS", "FALLBACK", "FAIL"]},
                      "queries": [{"query": r["query"], "status": r["status"], "seconds": r["seconds"], "warnings": r["warnings"], "errors": r["errors"]} for r in results]}, ensure_ascii=False), flush=True)
    raise SystemExit(1 if any(r["status"] == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    asyncio.run(main())
