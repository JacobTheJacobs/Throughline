"""Generic sparse-map regression: context, honest company fallback, continuation,
failure recovery, visible graph edges, and legacy local-map repair. No live providers.
Run against the dev server: python3 tests/sparse_map.py
"""
import json
import os
import time
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")


def run_case(browser, name, kind, viewport, fail=False, ambiguous=False):
    context = browser.new_context(viewport=viewport, reduced_motion="reduce")
    page = context.new_page()
    page.set_default_timeout(15000)
    calls = []
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    source_id = f"source-{kind}"
    relation = "Manufactured by" if kind == "brand" else "Directed by"
    card_name = "Example Company" if kind == "brand" else "Example Film"
    card_type = "company" if kind == "brand" else "movie"

    def discover(route):
        body = json.loads(route.request.post_data or "{}")
        calls.append(body)
        if ambiguous and body.get("text"):
            return route.fulfill(json={"mode": "clarify", "question": f"Which {name}?", "choices": [
                {"id": source_id, "name": name, "type": kind}, {"id": "namesake", "name": f"{name} Game", "type": "video_game"}]})
        if ambiguous and body.get("entityId") == source_id and not body.get("intent"):
            return route.fulfill(json={"mode": "intent", "defaultIntent": "direct", "seed": {"id": source_id, "name": name, "type": kind}})
        if body.get("intent") == "affinity":
            if fail:
                return route.fulfill(status=503, json={"message": "Audience matching is temporarily unavailable."})
            picks = [{"id": f"audience-{i}", "name": f"Audience pick {i}", "type": "book", "queryType": "book", "parentId": source_id,
                      "seedName": name, "description": "A book about culture and creative work.", "affinity": .95,
                      "reason": "Shared audience, not a factual credit.", "reasonSource": "Qloo audience affinity"} for i in range(5)]
            return route.fulfill(json={"mode": "live", "discoveries": picks})
        if body.get("entityId") and body.get("intent") != "direct":
            return route.fulfill(json={"mode": "live", "discoveries": [{"id": "child", "name": "A visible child", "type": "book", "queryType": "book", "parentId": "fact", "seedName": card_name, "affinity": .95}]})
        return route.fulfill(json={"mode": "live", "seed": {"id": source_id, "name": name, "type": kind},
                                  "discoveries": [{"id": "fact", "name": card_name, "type": card_type, "queryType": card_type, "parentId": "root", "seedName": name,
                                                   "relation": relation, "reason": f"{name} is manufactured by {card_name}." if kind == "brand" else f"Directed by {name}.", "reasonSource": "Verified direct relationship"}]})

    page.route("**/api/discover", discover)
    page.route("**/api/suggestions", lambda route: route.fulfill(json={"directions": []}))
    page.route("**/api/card**", lambda route: route.fulfill(json={}))
    page.goto(f"{BASE}/?seed={name.replace(' ', '%20')}")
    if ambiguous:
        page.locator(".clarify-card button").filter(has=page.get_by_text(name, exact=True)).click()
    page.wait_for_selector('.town-card[data-node-id="fact"]')
    assert page.locator(".intent-card").count() == 0, "confirmed creators and brands should open directly on verified connections"
    assert name in page.locator(".exploration-context").inner_text()
    assert page.locator(".world-lines path").count() == 0, "line points to a hidden starting card"
    assert page.locator(".town-card").count() == 1, "source must not become a sixth discovery"
    page.wait_for_timeout(1000)
    assert page.evaluate("""() => {
      const a=document.querySelector('.exploration-context').getBoundingClientRect(),b=document.querySelector('.town-card').getBoundingClientRect();
      return !(Math.max(a.left,b.left)<Math.min(a.right,b.right)&&Math.max(a.top,b.top)<Math.min(a.bottom,b.bottom));
    }"""), "starting-point panel must not cover the discovery"
    assert not page.evaluate("document.documentElement.scrollWidth>innerWidth"), "no horizontal overflow"
    if kind == "brand":
        assert page.locator('[data-node-id="fact"] .price-pill').inner_text() == "Company"
        assert page.locator(".entity-art-fallback svg").count() == 1
    action = page.locator(".exploration-context").get_by_role("button", name="Explore with Qloo")
    assert action.evaluate("e => {const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.left>=0&&r.right<=innerWidth}")
    page.locator('[data-node-id="fact"]').dispatch_event("click")
    page.locator(".rate-yes").click()
    page.get_by_role("button", name="Close details", exact=True).click()
    action.click()
    if fail:
        page.wait_for_function("document.querySelector('.toast')?.textContent.includes('temporarily unavailable')")
        assert page.locator(".town-card").count() == 1
        assert action.is_enabled(), "a failed request must remain retryable"
    else:
        page.wait_for_selector('[data-node-id="audience-4"]')
        assert page.locator(".town-card").count() == 6, "one existing fact plus five NEW matches"
        assert page.locator('[data-node-id="fact"]').count() == 1
        assert page.locator(".top-saved b").inner_text() == "1", "continuation must preserve saved facts"
        assert calls[-1]["entityId"] == source_id and calls[-1]["intent"] == "affinity"
        assert "fact" in calls[-1]["excludeIds"]
        assert page.locator(".world-lines path").count() == 0
        page.locator('[data-node-id="fact"]').dispatch_event("dblclick")
        page.wait_for_selector('[data-node-id="child"]')
        assert page.locator('.world-lines [data-parent-id="fact"][data-child-id="child"]').count() == 1
    assert not errors, errors
    print(f"PASS {kind}: {name}, {viewport['width']}px, {'failure recovery' if fail else 'context and continuation'}", flush=True)
    context.close()


with sync_playwright() as p:
    browser = p.chromium.launch()
    run_case(browser, "Shared Name", "brand", {"width": 390, "height": 844}, ambiguous=True)
    for name, kind, viewport in [("Northstar", "brand", {"width": 1440, "height": 900}),
                                 ("Different Brand", "brand", {"width": 390, "height": 844}),
                                 ("Casey Rivera", "person", {"width": 320, "height": 640}),
                                 ("Landscape Brand", "brand", {"width": 844, "height": 390})]:
        run_case(browser, name, kind, viewport)
    run_case(browser, "Retry Brand", "brand", {"width": 1440, "height": 900}, fail=True)
    page = browser.new_page()
    page.goto(BASE)
    page.evaluate("x=>localStorage.setItem('sideways.discovery.v2',JSON.stringify(x))", {
        "root": {"id": "legacy", "name": "Legacy Brand", "type": "brand"}, "savedAt": int(time.time() * 1000),
        "nodes": [{"id": "old-company", "name": "Legacy Company", "type": "product", "queryType": "product", "parentId": "root", "seedName": "Legacy Brand",
                   "relation": "Manufactured by", "reason": "Manufactured by Legacy Brand.", "x": 4000, "y": 4000, "size": "lg", "depth": 1, "liked": True}]})
    page.reload()
    page.wait_for_selector('.town-card[data-type="company"]')
    page.locator(".town-card").dispatch_event("click")
    assert "Legacy Brand is manufactured by Legacy Company." in page.locator(".cinematic-inspector").inner_text()
    assert page.locator(".top-saved b").inner_text() == "1"
    print("PASS legacy maps: type, relationship direction, and save preserved", flush=True)
    browser.close()
