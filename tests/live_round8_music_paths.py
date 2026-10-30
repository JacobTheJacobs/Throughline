"""Real music-work inspector/category diagnostics, without guessed provider crosswalks."""
import asyncio,json,time,unicodedata
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE

def key(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if c.isalnum())

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for artist,work in [('Katy Perry','Witness'),('Kraftwerk','Trans-Europe Express')]:
   context=await browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce')
   page=await context.new_page()
   await page.add_init_script('('+OBSERVE+')()')
   await page.goto(BASE)
   await page.wait_for_function("Object.keys(document.querySelector('.hero-search input')||{}).some(k=>k.startsWith('__reactProps'))",timeout=30000)
   await page.get_by_role('textbox',name='What would you like to explore?',exact=True).fill(artist)
   await page.get_by_role('button',name='Begin exploring',exact=True).click()
   deadline=time.monotonic()+60
   while not await page.locator('.town-card').count():
    if time.monotonic()>deadline:raise AssertionError('No map for '+artist)
    if await page.locator('.clarify-card:not(.intent-card)').count():
     choices=await page.evaluate("window.__liveAudit.filter(c=>c.data?.mode==='clarify').at(-1)?.data.choices||[]")
     exact=[(i,c) for i,c in enumerate(choices) if c.get('type')=='artist' and key(c.get('name',''))==key(artist)]
     if not exact:raise AssertionError('Artist identity unavailable')
     await page.locator('.clarify-card>div>button').nth(exact[0][0]).click()
    await page.wait_for_timeout(100)
   await page.locator('.town-card').filter(has_text=work).locator('.card-hit').click()
   await page.wait_for_function("window.__liveAudit.some(c=>c.request?.probeTypes&&c.data)",timeout=45000)
   await page.wait_for_timeout(250)
   calls=await page.evaluate("window.__liveAudit.filter(c=>c.url==='/api/suggestions'||c.request?.probeTypes)")
   print(json.dumps({'artist':artist,'work':work,'inspector':await page.locator('.cinematic-inspector').inner_text(),'calls':calls},ensure_ascii=False),flush=True)
   await context.close()
  await browser.close()

asyncio.run(main())
