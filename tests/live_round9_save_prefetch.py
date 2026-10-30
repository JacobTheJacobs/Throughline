"""Compare save versus no-save timing of the inspector's real delayed prefetch."""
import asyncio,json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for save in [False,True]:
   context=await browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce')
   page=await context.new_page()
   await page.add_init_script('('+OBSERVE.replace('const entry={url,','const entry={at:performance.now(),url,')+')()')
   await page.goto(BASE+'/?seed=Animal%20Well')
   await page.wait_for_selector('.town-card',timeout=60000)
   await page.locator('.town-card').first.locator('.card-hit').click()
   await page.wait_for_selector('.cinematic-inspector')
   opened=await page.evaluate('performance.now()')
   if save:await page.locator('.rate-yes').click()
   await page.wait_for_function('window.__liveAudit.some(c=>c.request?.probeTypes)',timeout=15000)
   await page.wait_for_timeout(800)
   calls=await page.evaluate('window.__liveAudit')
   print(json.dumps({'save':save,'opened':opened,'saved':await page.locator('.top-saved').inner_text(),'graphCards':await page.locator('.town-card').count(),'calls':calls},ensure_ascii=False),flush=True)
   await context.close()
  await browser.close()

asyncio.run(main())
