"""Deterministic recovery-state regressions; no provider calls or user browser data."""
import json
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")


with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in [1440, 390, 320]:
        page = browser.new_page(viewport={"width": width, "height": 640 if width == 320 else 844})
        calls = []
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def discover(route):
            body = json.loads(route.request.post_data or "{}")
            calls.append(body)
            seed = {"id": "example", "name": "Example Reference", "type": "movie"}
            if body.get("intent") == "affinity":
                return route.fulfill(json={"mode": "live", "seed": seed, "discoveries": [
                    {"id": "match", "name": "Audience Match", "type": "book", "queryType": "book", "seedName": seed["name"], "parentId": "root", "affinity": .95,
                     "reason": "Audience overlap, not a factual credit.", "reasonSource": "Qloo audience affinity"}]})
            return route.fulfill(json={"mode": "live", "seed": seed, "discoveries": [], "reason": "no_relevant_matches", "message": "No candidates passed verification. Nothing was guessed.", "canExploreAudience": True})

        page.route("**/api/discover", discover)
        page.route("**/api/suggestions", lambda r: r.fulfill(json={"directions": []}))
        page.route("**/api/card", lambda r: r.fulfill(json={}))
        page.goto(f"{BASE}/?seed=Example")
        panel = page.locator(".discovery-recovery")
        panel.wait_for()
        if width == 320:
            page.screenshot(path="/tmp/sideways-recovery-320.png")
            assert page.locator('.editorial-home h1').bounding_box()['y'] >= 64, "Recovery must not clip the heading behind the mobile header"
        assert "Nothing was guessed" in panel.inner_text()
        assert page.locator(".town-card").count() == 0
        page.wait_for_timeout(700)
        assert len(calls) == 1, "empty results must not silently switch to audience matches"
        assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
        panel.get_by_role("button", name="Try audience matches").click()
        page.wait_for_selector(".town-card")
        assert calls[-1]["intent"] == "affinity"
        page.locator(".town-card").click()
        page.locator(".rate-yes").click()
        page.wait_for_function("document.querySelector('.top-saved b')?.textContent==='1'")
        page.get_by_role("button", name="Close details", exact=True).click()
        # Failed new search keeps the current map and its save, and has useful actions.
        page.evaluate("""() => {const input=document.querySelector('.editorial-topbar input');const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;set.call(input,'Missing new thing');input.dispatchEvent(new Event('input',{bubbles:true}))}""")
        page.wait_for_timeout(100)
        page.locator('.editorial-topbar form').evaluate("form=>form.requestSubmit()")
        page.locator(".discovery-recovery.is-on-map").wait_for()
        assert page.locator(".town-card").count() == 1
        assert page.locator(".top-saved b").inner_text() == "1"
        page.locator(".discovery-recovery").get_by_role("button", name="Change search").click()
        assert "seed=" not in page.url, "Home must not leave a URL that automatically reopens a query"
        page.reload()
        page.locator(".hero-search").wait_for()
        assert page.locator(".town-card").count() == 0
        assert not errors, errors
        print(f"PASS {width}px: explicit fallback, no guessed nodes, saved map preserved", flush=True)
        page.close()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    attempts = []

    def retryable(route):
        attempts.append(json.loads(route.request.post_data or "{}"))
        seed = {"id": "retry", "name": "Retry Reference", "type": "movie"}
        if len(attempts) == 1:
            return route.fulfill(status=503, json={"mode": "live", "seed": seed, "discoveries": [], "reason": "relevance_unavailable", "message": "Checking is temporarily unavailable.", "canExploreAudience": False})
        return route.fulfill(json={"mode": "live", "seed": seed, "discoveries": [{"id": "retried", "name": "Confirmed after retry", "type": "book", "parentId": "root", "seedName": seed["name"], "queryType": "book"}]})

    page.route("**/api/discover", retryable)
    page.goto(f"{BASE}/?seed=Retry")
    retry = page.locator(".discovery-recovery").get_by_role("button", name="Try again")
    retry.wait_for()
    page.wait_for_timeout(500)
    assert len(attempts) == 1, "transient failure must not create an automatic retry loop"
    retry.click()
    page.wait_for_selector(".town-card")
    assert len(attempts) == 2
    print("PASS transient failure: explicit retry succeeds without an automatic request loop", flush=True)
    page.close()
    browser.close()
