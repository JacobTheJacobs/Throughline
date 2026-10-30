"""Deterministic UI test against the current interface, with mocked /api/discover and /api/suggestions
(no Qloo or JEV needed). Covers save, brief removal/undo, share round-trip, Taste GraphRAG events,
reload persistence (links, Discover provenance) and map-bound undo.
Run: python3 tests/ui_mock.py   (dev server on :5173, playwright installed)"""
import json, os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")
TYPES = ["movie", "book", "artist", "place"]
failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def item(prefix, name, i, parent):
    kind = TYPES[i % 4]
    return {"id": f"{prefix}-{i}", "name": f"{name} {i}", "type": kind, "queryType": kind, "parentId": parent,
            "seedName": name, "description": "Mock entity with enough descriptive evidence.", "affinity": 0.9 - i * 0.02,
            "image": f"https://images.qloo.com/i/mock-{prefix}-{i}.jpg", "tags": ["test", f"tag{i}"], "reason": "Mock reason.",
            "links": [{"label": "IMDb", "url": f"https://www.imdb.com/title/tt{i:07d}/"}]}


def handle(route):
    body = json.loads(route.request.post_data or "{}")
    if body.get("entityId") and len(body.get("types") or []) > 4 and not body.get("probeTypes"):  # Discover feed request from an anchor
        anchor = body["entityId"]
        data = [item(f"feed-{anchor}", "Feed pick", i, anchor) for i in range(4)]
    elif body.get("entityId"):
        anchor = body["entityId"]
        data = [item(f"{anchor}-c", "Child", i, anchor) for i in range(3)]
        if anchor == "alpha-1":  # graph expansion reaches the pick already saved from Discover
            data[0] = {**item("feed-alpha-0", "Feed pick", 0, anchor), "id": "feed-alpha-0-0"}
    else:
        name = body.get("text", "Seed")
        key = name.lower()
        if key == "limited":
            return route.fulfill(status=429, content_type="application/json", body=json.dumps({"error": "Daily limit reached for this feature — come back tomorrow."}))
        return route.fulfill(status=200, content_type="application/json", body=json.dumps({
            "mode": "live", "seed": {"id": f"seed-{key}", "name": name, "type": "brand", "tags": ["test"]}, "alternatives": [],
            "discoveries": [item(key, f"{name} reference", i, "root") for i in range(1 if key == "solo" else 5)], "coverage": {}}))
    return route.fulfill(status=200, content_type="application/json", body=json.dumps({"mode": "live", "discoveries": data, "coverage": {}}))


def suggestions(route):
    route.fulfill(status=200, content_type="application/json", body=json.dumps({"directions": [{"label": "More movies like this", "type": "movie"}]}))


def idb_events(page):
    return page.evaluate("""async () => { const db=await new Promise((res,rej)=>{const r=indexedDB.open('sideways-memory');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
      const tx=db.transaction('events','readonly'); return await new Promise((res,rej)=>{const r=tx.objectStore('events').getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)}); }""")


def saved_count(page):
    return int(page.inner_text(".top-saved b"))


def start(page, name):
    page.goto(f"{BASE}/?seed={name}")
    page.wait_for_selector(".town-card", timeout=20000)
    page.wait_for_timeout(1500)


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 1440, "height": 860})
    context.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route("**/api/discover", handle)
    page.route("**/api/suggestions", suggestions)
    page.goto(BASE); page.evaluate("localStorage.clear(); indexedDB.deleteDatabase('sideways-memory')")

    # First map
    start(page, "Alpha")
    check("new search starts with five discoveries", len(page.query_selector_all(".town-card")) == 5)
    check("cards show readable type pills", "tv_show" not in page.inner_text(".world-stage"))

    # Save from the inspector and remember the feedback
    page.locator(".town-card .card-hit").first.click(); page.wait_for_timeout(500)
    check("inspector opens", page.query_selector(".cinematic-inspector") is not None)
    page.locator(".cinematic-inspector .rate-yes").click(); page.wait_for_timeout(400)
    check("save updates the Saved counter", saved_count(page) == 1)
    check("save is remembered as a weighted love event", any(e.get("kind") == "love" and e.get("weight") == 5 and e.get("seq") for e in idb_events(page)))

    # Brief removal: confirm, cancel, remove, undo
    page.locator(".top-saved").click(); page.wait_for_selector(".taste-brief")
    check("brief lists the saved reference", "Alpha reference 0" in page.inner_text(".taste-brief"))
    page.locator(".taste-brief").get_by_role("button", name="Remove Alpha reference 0 from brief").click()
    page.wait_for_selector(".confirm-dialog")
    page.wait_for_timeout(150)
    focused = page.evaluate("document.activeElement?.textContent?.trim()")
    check("confirmation starts on the safe action", focused == "Keep reference", repr(focused))
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    check("Escape cancels removal", page.query_selector(".confirm-dialog") is None and saved_count(page) == 1)
    page.locator(".taste-brief").get_by_role("button", name="Remove Alpha reference 0 from brief").click()
    page.get_by_role("button", name="Remove from brief", exact=True).click(); page.wait_for_timeout(400)
    check("confirmed removal clears the brief", saved_count(page) == 0)
    check("removal records an unlove event", any(e.get("kind") == "unlove" for e in idb_events(page)))
    page.get_by_role("button", name="Undo", exact=True).click(); page.wait_for_timeout(400)
    check("undo restores the reference", saved_count(page) == 1)
    page.keyboard.press("Escape"); page.wait_for_timeout(200)

    # Share round-trip
    if page.query_selector(".cinematic-inspector .panel-close"):
        page.locator(".cinematic-inspector .panel-close").click(); page.wait_for_timeout(200)
    page.locator(".top-share", has_text="Share").click(); page.wait_for_selector(".share-studio")
    page.get_by_role("button", name="Copy exact link").click(); page.wait_for_timeout(300)
    shared_url = page.evaluate("navigator.clipboard.readText().catch(()=> '')")
    check("share copies an exact map link", "#map=" in shared_url)
    page.locator(".share-close").click(); page.wait_for_timeout(200)
    shared = browser.new_context(viewport={"width": 1200, "height": 800}).new_page()
    shared.route("**/api/discover", handle); shared.route("**/api/suggestions", suggestions)
    shared.goto(shared_url); shared.wait_for_selector(".town-card", timeout=10000)
    check("shared link restores the map without a new search", len(shared.query_selector_all(".town-card")) == 5)
    shared.context.close()

    # Discover board (removed in the Throughline redesign): run these checks only when it exists
    if page.locator(".top-share", has_text="Discover").count():
        # Discover feed: save a pick reached through a parent discovery, then reload
        page.locator(".top-share", has_text="Discover").click(); page.wait_for_selector(".discover-board")
        page.wait_for_selector(".discover-masonry article", timeout=10000)
        check("Discover opens from the top bar and loads picks", len(page.query_selector_all(".discover-masonry article")) >= 1)
        page.locator(".discover-masonry article").first.click(); page.wait_for_timeout(300)
        page.locator(".discover-detail").get_by_role("button", name="♡ Save to brief").click(); page.wait_for_timeout(400)
        stored = page.evaluate("JSON.parse(localStorage.getItem('sideways.discover-saved.seed-alpha')||'[]')")
        check("Discover save stores its parent discovery", bool(stored) and stored[0].get("parentId") == "alpha-0", str([s.get("parentId") for s in stored]))
        page.reload(); page.wait_for_selector(".town-card", timeout=20000); page.wait_for_timeout(1500)
        stored = page.evaluate("JSON.parse(localStorage.getItem('sideways.discover-saved.seed-alpha')||'[]')")
        check("reload keeps the Discover save's parent", bool(stored) and stored[0].get("parentId") == "alpha-0", str([s.get("parentId") for s in stored]))
        check("reload keeps source links", bool(stored) and any("imdb.com" in l.get("url", "") for l in stored[0].get("links", [])))
        check("reload keeps map-card source links", "imdb.com" in page.evaluate("localStorage.getItem('sideways.discovery.v2')||''"))
        page.locator(".top-saved").click(); page.wait_for_selector(".taste-brief")
        check("brief shows the saved pick", "Feed pick 0" in page.inner_text(".taste-brief"))
        page.keyboard.press("Escape"); page.wait_for_timeout(200)

        # Reaching a saved Discover pick through the graph keeps it saved
        before = saved_count(page)
        page.locator('.town-card[data-node-id="alpha-1"] .card-hit').click(); page.wait_for_timeout(500)
        page.locator(".qloo-quick-action button").first.click()
        page.wait_for_selector('.town-card[data-node-id="feed-alpha-0-0"]', timeout=10000); page.wait_for_timeout(600)
        check("rediscovered saved pick stays saved", saved_count(page) == before, f"{before} -> {saved_count(page)}")
        page.keyboard.press("Escape"); page.wait_for_timeout(200)
        page.locator('.town-card[data-node-id="feed-alpha-0-0"] .card-hit').click(); page.wait_for_timeout(400)
        page.locator(".cinematic-inspector .rate-no").click(); page.wait_for_timeout(2500)
        stored = page.evaluate("JSON.parse(localStorage.getItem('sideways.discover-saved.seed-alpha')||'[]')")
        check("rejecting a saved pick unsaves it everywhere", saved_count(page) == before - 1 and not any(i.get("id") == "feed-alpha-0-0" for i in stored), f"{saved_count(page)} {[i.get('id') for i in stored]}")

    # Undo is bound to its map: remove on Alpha, start Beta, Undo must not touch Beta
    page.locator(".top-saved").click(); page.wait_for_selector(".taste-brief")
    page.locator(".taste-brief").get_by_role("button", name="Remove Alpha reference 0 from brief").click()
    page.get_by_role("button", name="Remove from brief", exact=True).click(); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    page.locator(".editorial-brand").click(); page.wait_for_selector(".hero-search input")
    page.fill(".hero-search input", "Beta"); page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('.town-card')?.innerText.includes('Beta')", timeout=20000); page.wait_for_timeout(800)
    undo = page.get_by_role("button", name="Undo", exact=True)
    if undo.count():
        undo.first.click(); page.wait_for_timeout(300)
    check("undo from another map cannot change this map", saved_count(page) == 0)

    # A rejection's removal timer must not delete a same-id card from the next map
    start(page, "Gamma")
    page.locator(".town-card .card-hit").nth(1).click(); page.wait_for_timeout(300)
    page.locator(".cinematic-inspector .rate-no").click()
    page.locator(".editorial-brand").click(); page.wait_for_selector(".hero-search input")
    page.fill(".hero-search input", "Gamma"); page.keyboard.press("Enter")
    page.wait_for_selector(".town-card", timeout=20000); page.wait_for_timeout(2500)
    n = len(page.query_selector_all(".town-card")); check("rejection on an old map cannot remove cards from the new one", n == 5, str(n))

    page.locator(".town-card .card-hit").nth(1).click(); page.wait_for_timeout(300)
    page.locator(".cinematic-inspector .rate-no").click(); page.wait_for_timeout(2500)
    n = len(page.query_selector_all(".town-card")); check("rejection on the current map removes the card", n == 4, str(n))

    # Rejecting an intermediate card keeps the child's real provenance and invents no direct RAG edge
    page.locator('.town-card[data-node-id="gamma-0"] .card-hit').click(); page.wait_for_timeout(500)
    page.locator(".qloo-quick-action button").first.click()
    page.wait_for_selector('.town-card[data-node-id="gamma-0-c-0"]', timeout=10000); page.wait_for_timeout(600)
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    page.locator('.town-card[data-node-id="gamma-0-c-0"] .card-hit').click(); page.wait_for_timeout(400)
    page.locator(".cinematic-inspector .rate-yes").click(); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    page.locator('.town-card[data-node-id="gamma-0"] .card-hit').click(); page.wait_for_timeout(400)
    page.locator(".cinematic-inspector .rate-no").click(); page.wait_for_timeout(2500)
    stored = json.loads(page.evaluate("localStorage.getItem('sideways.discovery.v2')") or "{}")
    child = next((n for n in stored.get("nodes", []) if n.get("id") == "gamma-0-c-0"), {})
    check("removed parent stays in the child's path", "Gamma reference 0" in (child.get("via") or []), str(child.get("via")))
    page.wait_for_timeout(1500)
    edges = page.evaluate("""async () => { const db=await new Promise(r=>{const q=indexedDB.open('sideways-memory');q.onsuccess=()=>r(q.result)});
      const tx=db.transaction('edges','readonly'); return await new Promise(r=>{const q=tx.objectStore('edges').getAll();q.onsuccess=()=>r(q.result)}); }""")
    check("no invented root-to-child memory edge", not any(e.get("from") == "seed-gamma" and e.get("to") == "gamma-0-c-0" for e in edges))

    # Rejecting the last card is saved: reload must not resurrect it
    page.locator(".editorial-brand").click(); page.wait_for_selector(".hero-search input")
    page.fill(".hero-search input", "Solo"); page.keyboard.press("Enter")
    page.wait_for_selector('.town-card[data-node-id="solo-0"]', timeout=20000); page.wait_for_timeout(800)
    page.locator('.town-card[data-node-id="solo-0"] .card-hit').click(); page.wait_for_timeout(400)
    page.locator(".cinematic-inspector .rate-no").click(); page.wait_for_timeout(2500)
    page.goto(f"{BASE}/?seed=Solo"); page.wait_for_timeout(3000)
    check("rejected last card stays gone after reload", len(page.query_selector_all(".town-card")) == 0, str(len(page.query_selector_all(".town-card"))))

    # A quota refusal is reported as a quota refusal, not as an empty discovery
    page.locator(".editorial-brand").click(); page.wait_for_selector(".hero-search input")
    page.fill(".hero-search input", "Limited"); page.keyboard.press("Enter"); page.wait_for_timeout(1500)
    body_text = page.inner_text("body")
    check("daily limit is shown as a limit", "Daily limit" in body_text and "Nothing new from here" not in body_text)

    # Recent explorations: pin to top, remove after confirmation
    page.locator(".editorial-brand").click(); page.wait_for_selector(".home-sidebar .recent-row", timeout=10000)
    last = page.locator(".home-sidebar .recent-row").last; last_name = last.locator("b").inner_text()
    last.locator(".recent-more").click(); page.get_by_role("menuitem", name="Pin to top").click(); page.wait_for_timeout(300)
    check("pinned exploration moves to the top", page.locator(".home-sidebar .recent-row b").first.inner_text() == last_name)
    first = page.locator(".home-sidebar .recent-row").first; count = page.locator(".home-sidebar .recent-row").count()
    first.locator(".recent-more").click(); page.get_by_role("menuitem", name="Remove").click()
    page.wait_for_selector(".confirm-dialog"); page.get_by_role("button", name="Remove exploration").click(); page.wait_for_timeout(400)
    check("confirmed removal deletes the exploration", page.locator(".home-sidebar .recent-row").count() == count - 1 and last_name not in page.inner_text(".home-sidebar"))

    # Reload of a very large map keeps the newest saved card
    big = {"root": {"id": "seed-big", "name": "Big", "type": "brand"}, "nodes": [
        {**item("big", "Big card", i, "root"), "x": 2000, "y": 1500, "depth": 1, "liked": i == 699} for i in range(700)]}
    page.close(); page = context.new_page(); page.on("pageerror", lambda e: errors.append(str(e)))
    page.route("**/api/discover", handle); page.route("**/api/suggestions", suggestions)
    page.goto(BASE); page.evaluate("v => localStorage.setItem('sideways.discovery.v2', v)", json.dumps(big))
    page.goto(f"{BASE}/?seed=Big"); page.wait_for_selector(".town-card", timeout=20000); page.wait_for_timeout(1500)
    check("large-map reload keeps the saved card", saved_count(page) == 1, str(saved_count(page)))

    check("no page errors", not errors, "; ".join(errors[:3]))
    browser.close()

print(f"\n{len(failures)} failed" if failures else "\nAll UI checks passed")
sys.exit(1 if failures else 0)
