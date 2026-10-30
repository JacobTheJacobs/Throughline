"""Read-only live audit of canonical identities, feedback, and agent additions.
Fetch responses are cloned for observation only; no requests/responses are mocked.
"""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE

OBSERVE = """() => {
 window.__liveAudit=[];
 const original=window.fetch.bind(window);
 window.fetch=async (...args)=>{
  const url=String(args[0] instanceof Request?args[0].url:args[0]);
  const entry={url,request:args[1]?.body?JSON.parse(args[1].body):null};
  if(url.startsWith('/api/'))window.__liveAudit.push(entry);
  const response=await original(...args);
  entry.status=response.status;
  if(url.startsWith('/api/'))response.clone().text().then(text=>{
   try{entry.data=url==='/api/agent'?{events:text.trim().split('\\n').filter(Boolean).map(JSON.parse)}:JSON.parse(text)}catch{entry.text=text.slice(0,200)}
  }).catch(e=>{entry.captureError=String(e)});
  return response;
 };
}"""


async def snapshot(page, stage, **extra):
    await page.wait_for_timeout(350)
    state = await page.evaluate("""() => ({calls:window.__liveAudit,stored:JSON.parse(localStorage.getItem('sideways.discovery.v2')||'null')})""")
    print(json.dumps({"stage": stage, **extra, **state}, ensure_ascii=False), flush=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = await context.new_page()
        page.set_default_timeout(20000)
        await page.add_init_script("(" + OBSERVE + ")()")
        await page.goto(BASE + "/?seed=Haruki%20Murakami")
        await page.wait_for_selector(".clarify-card")
        await page.wait_for_function("window.__liveAudit.some(x=>x.data?.mode==='clarify')")
        choices = await page.evaluate("window.__liveAudit.find(x=>x.data?.mode==='clarify').data.choices")
        i = next(i for i, c in enumerate(choices) if c["id"] == "62A8F44C-CD8F-4BDB-878E-4634F2D97074")
        await page.locator(".clarify-card>div>button").nth(i).click()
        await page.wait_for_selector(".town-card", timeout=45000)
        await page.locator(".town-card").filter(has_text="Norwegian Wood").click()
        await page.locator(".rate-yes").click()
        await page.wait_for_timeout(7000)
        await snapshot(page, "murakami-open", inspector=await page.locator(".cinematic-inspector").inner_text())
        books = page.locator(".direction-chips button").filter(has_text="Books")
        if await books.count() and await books.is_enabled():
            await page.evaluate("window.__liveAudit=[]")
            await books.click()
            await page.wait_for_timeout(7500)
            await snapshot(page, "murakami-books", notice=await page.locator(".toast").inner_text() if await page.locator(".toast").count() else "")
        else:
            print(json.dumps({"stage": "murakami-books", "outcome": "No confirmed Books button offered"}), flush=True)
        if await page.get_by_role("button", name="Close details", exact=True).count():
            await page.get_by_role("button", name="Close details", exact=True).click()
        await page.evaluate("window.__liveAudit=[]")
        await page.get_by_role("button", name="Explore for me", exact=True).click()
        await page.wait_for_selector(".log-done", timeout=65000)
        await page.wait_for_function("window.__liveAudit.some(x=>x.url==='/api/agent'&&x.data?.events)", timeout=10000)
        await snapshot(page, "murakami-agent", log=await page.locator(".agent-log").inner_text())
        # The map header search is hidden by design; visible Home navigation and
        # same-browser map isolation are exercised in live_alias_feedback.py.
        await browser.close()
        api = await p.request.new_context(base_url=BASE, timeout=50000)
        for query in ["Iceland", "Iceland country", "IKEA", "The Dispossessed", "Scary Movie", "The Jungle Book", "The Artist"]:
            r=await api.post('/api/discover',data={"text":query})
            print(json.dumps({"stage":"identity-recheck","query":query,"http":r.status,"data":await r.json()},ensure_ascii=False),flush=True)
        await api.dispose()


if __name__ == "__main__":
    asyncio.run(main())
