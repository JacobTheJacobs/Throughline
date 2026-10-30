"""Browser verification for the anonymous local study and public evidence routes."""
import json, os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("SIDEWAYS_BASE", "http://127.0.0.1:5173")
failures = []
def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok: failures.append(name)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 850})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{BASE}/study")
    page.wait_for_timeout(1200)
    check("study is hidden but directly reachable", page.get_by_role("heading", name="Help test a better way to build creative references.").is_visible())
    begin = page.get_by_role("button", name="Begin study")
    check("consent is required", begin.is_disabled())
    page.get_by_role("checkbox").click(); page.wait_for_timeout(200); page.get_by_role("button", name="Begin study").click()
    participant = page.evaluate("JSON.parse(localStorage.getItem('sideways.study.session.v1')).participantId")
    check("participant identity is anonymous", participant.startswith("S-") and "@" not in participant)
    page.get_by_role("button", name="Start five-minute timer").click()
    page.wait_for_timeout(1100)
    before = page.evaluate("JSON.parse(localStorage.getItem('sideways.study.session.v1')).trials[0].startedAt")
    page.reload(); page.wait_for_timeout(1200)
    after = page.evaluate("JSON.parse(localStorage.getItem('sideways.study.session.v1')).trials[0].startedAt")
    task_restored = page.get_by_text("Task 1 of 2").is_visible()
    check("refresh preserves locked timing and assignment", before == after and task_restored)
    if before != after or not task_restored: print("RECOVERY", before, after, task_restored, page.inner_text("body")[:240])
    check("five structured references are required", page.locator(".study-references fieldset").count() == 5)
    withdraw = page.get_by_role("button", name="Withdraw")
    withdraw.click(); page.wait_for_selector('[role="alertdialog"]')
    check("withdraw uses the reusable custom dialog", page.get_by_role("heading", name="Withdraw from this study?").is_visible())
    check("withdraw dialog starts on the safe action", page.evaluate("document.activeElement?.textContent") == "Continue study")
    page.keyboard.press("Escape"); page.wait_for_timeout(150)
    abandoned = page.evaluate("JSON.parse(localStorage.getItem('sideways.study.session.v1')).trials[0].abandonedAt")
    check("Escape preserves the study and restores focus", abandoned is None and page.evaluate("document.activeElement?.textContent") == "Withdraw")
    downloads = []
    page.on("download", lambda item: downloads.append(item.suggested_filename))
    page.evaluate("""() => { const key='sideways.study.session.v1', s=JSON.parse(localStorage.getItem(key)), refs=Array.from({length:5},(_,i)=>({name:`Ref ${i}`,category:['film','place','artist'][i%3],rationale:'Useful connection'})), make=(condition,task,offset)=>({condition,task,startedAt:s.createdAt+offset,completedAt:s.createdAt+offset+1000,references:refs,savedEvents:condition==='sideways'?5:0,rejectedEvents:0,rating:{usefulness:5,surprise:4,confidence:5,willingness:5}}); s.trials=[make(s.assignment.firstCondition,s.assignment.firstTask,10),make(s.assignment.secondCondition,s.assignment.secondTask,2010)]; localStorage.setItem(key,JSON.stringify(s)); }""")
    page.reload(); page.wait_for_timeout(1200)
    page.get_by_role("button", name="Download JSON + CSV").click(); page.wait_for_timeout(500)
    check("completed session exports JSON and CSV", any(name.endswith(".json") for name in downloads) and any(name.endswith(".csv") for name in downloads))
    page.goto(f"{BASE}/evidence")
    body = page.inner_text("body")
    check("evidence page refuses invented outcomes", "Study in progress" in body and "Why the charts are empty" in body)
    check("public evidence exposes no participant identifiers", "S-" not in body and participant not in body)
    page.goto(f"{BASE}/study/review")
    check("research workspace starts local and locked", "0/10" in page.inner_text("body") and page.get_by_role("button", name="Export public aggregate").is_disabled())
    clean = browser.new_context(viewport={"width": 390, "height": 844})
    mobile = clean.new_page(); mobile.goto(BASE); mobile.wait_for_timeout(700)
    check("normal users create no study telemetry", mobile.evaluate("localStorage.getItem('sideways.study.session.v1')") is None)
    mobile.goto(f"{BASE}/study"); mobile.wait_for_timeout(1000)
    check("study remains usable on mobile", mobile.locator(".study-card").is_visible() and mobile.locator("body").evaluate("el => el.scrollWidth <= innerWidth"))
    mobile.get_by_role("checkbox").focus(); mobile.keyboard.press("Space"); mobile.wait_for_timeout(100)
    check("keyboard consent enables progression", mobile.get_by_role("button", name="Begin study").is_enabled())
    clean.close()

    capture_context = browser.new_context(viewport={"width": 1280, "height": 850}, permissions=["clipboard-read", "clipboard-write"])
    capture = capture_context.new_page()
    def mock_discovery(route):
        body = json.loads(route.request.post_data or "{}")
        name = body.get("text") or body.get("name") or "Alpha"
        payload = {"mode":"live","seed":{"id":"seed-alpha","name":name,"type":"brand","tags":["test"]},"alternatives":[],"discoveries":[{"id":f"auto-{i}","name":f"Automatic {i}","type":["movie","book","artist","place"][i%4],"description":"Mock study reference","affinity":.94-i*.02,"parentId":"root","seedName":name,"queryType":"test","tags":["test"],"reason":"Verified automatic study capture.","links":[]} for i in range(5)]}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))
    capture.route("**/api/discover", mock_discovery)
    capture.goto(BASE); capture.evaluate("""() => localStorage.setItem('sideways.study.session.v1', JSON.stringify({schema:'sideways.study.session.v1',protocol:'2026-10-25.v1',participantId:'S-CAPTURE1',assignment:{firstCondition:'sideways',firstTask:'nostalgic-wonder',secondCondition:'normal',secondTask:'rebellious-precision'},createdAt:Date.now()-1000,appVersion:'test',trials:[{condition:'sideways',task:'nostalgic-wonder',startedAt:Date.now()-500,references:Array.from({length:5},()=>({name:'',category:'',url:'',rationale:''})),savedEvents:0,rejectedEvents:0}] }))""")
    capture.goto(f"{BASE}/?seed=Alpha&study=S-CAPTURE1"); capture.wait_for_selector(".town-card", timeout=20000); capture.wait_for_timeout(1200)
    for index in range(3):
        capture.locator(".town-card .card-hit").nth(index).click(); capture.wait_for_timeout(180)
        capture.locator(".cinematic-inspector .rate-yes").click(); capture.wait_for_timeout(180)
    capture.locator(".town-card .card-hit").nth(3).click(); capture.wait_for_timeout(180)
    capture.locator(".cinematic-inspector .rate-no").click(); capture.wait_for_timeout(1000)
    capture.get_by_role("button", name="Open taste brief", exact=True).click(); capture.wait_for_selector(".taste-brief")
    capture.get_by_role("button", name="Copy Markdown").click(); capture.wait_for_timeout(250)
    recorded = capture.evaluate("JSON.parse(localStorage.getItem('sideways.study.session.v1')).trials[0]")
    check("Sideways automatically captures study decisions", recorded["savedEvents"] == 3 and recorded["rejectedEvents"] == 1 and len([item for item in recorded["references"] if item.get("name")]) == 3)
    check("Sideways automatically captures paths and generated brief", bool(recorded.get("generatedBrief")) and all(item.get("path") for item in recorded["references"] if item.get("name")))
    capture_context.close()
    check("no browser errors", not errors)
    browser.close()

if failures:
    raise SystemExit("; ".join(failures))
