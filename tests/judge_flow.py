"""End-to-end judge path. Needs the dev server on :5173 and `pip install playwright && playwright install chromium`.
Run: python tests/judge_flow.py"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")
failures = []

def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
    if not ok:
        failures.append(name)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 860})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.evaluate("localStorage.clear()")
    # A starter with a named category opens directly; no clarification or intent step.
    page.goto(f"{BASE}/?seed=Spirited%20Away&type=movie")
    page.wait_for_selector(".town-card", timeout=40000)
    page.wait_for_timeout(12000)
    check("new map starts focused", 1 <= len(page.query_selector_all(".town-card")) <= 5)

    cards = [c for c in page.query_selector_all(".town-card") if 450 < (c.bounding_box() or {"x": 0})["x"] < 1000 and 100 < (c.bounding_box() or {"y": 0})["y"] < 500]
    card = cards[0]
    card.hover(); page.wait_for_timeout(400)
    check("starting reference stays visible as context", page.locator(".exploration-context").is_visible())
    check("hover mutes unrelated branches", len(page.query_selector_all(".node-muted")) > 0)

    stage = lambda: page.eval_on_selector(".world-stage", "e=>e.style.transform")
    before = stage()
    card.click(position={"x": 40, "y": 20}); page.wait_for_timeout(1500)
    check("click opens inspector", page.query_selector(".cinematic-inspector") is not None)
    check("no connectors point at an invisible source card", page.locator('.world-lines [data-parent-id="root"]').count() == 0)
    check("camera does not jump on open", stage() == before)

    n0 = len(page.query_selector_all(".town-card"))
    page.locator(".rate-yes").first.click(); page.wait_for_timeout(600)
    check("save curates without a surprise API expansion", len(page.query_selector_all(".town-card")) == n0 and "saved to your brief" in page.inner_text(".toast").lower())
    check("brief progress reflects the save", "1" in page.inner_text(".top-saved"))

    page.mouse.click(1420, 450); page.wait_for_timeout(600)
    check("outside click ungrays", len(page.query_selector_all(".node-muted")) == 0)

    page.get_by_role("button", name="Explore for me").click()
    try:
        page.wait_for_selector(".log-done", timeout=65000)
        check("agent finishes with a result", any(w in page.inner_text(".log-done") for w in ("Added", "added", "No verified", "No strong", "unavailable", "limit")))
    except Exception:
        activity = page.locator(".agent-log")
        detail = activity.inner_text() if activity.count() else "activity panel missing"
        check("agent finishes with a result", False, detail[:300])
    check("no page errors", not errors, "; ".join(errors[:2]))
    browser.close()

sys.exit(1 if failures else 0)
