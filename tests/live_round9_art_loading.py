"""Observe real cover loading after a bounded settle period; distinguish pending, failed and missing."""
import asyncio,json,sys
from playwright.async_api import async_playwright
from live_queries import BASE
from live_visuals import capture_visuals

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  cases=[('Katy Perry','artist'),('The Cure','artist'),('Abbas Kiarostami','person')]
  if '--remaining' in sys.argv:cases=[('Massive Attack','artist'),('Yōko Ogawa','person'),('Aesop','brand'),('Tbilisi','destination')]
  if '--cure' in sys.argv:cases=[('The Cure','artist')]
  for index,(name,kind) in enumerate(cases):
   page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
   responses=[];failures=[];console=[]
   page.on('response',lambda r: responses.append({'url':r.url,'http':r.status}) if r.request.resource_type=='image' else None)
   page.on('requestfailed',lambda r: failures.append({'url':r.url,'error':r.failure}) if r.resource_type=='image' else None)
   page.on('console',lambda m: console.append(m.text[:350]) if m.type=='error' else None)
   await page.goto(BASE+'/?seed='+name.replace(' ','%20')+'&type='+kind)
   await page.wait_for_selector('.town-card, .discovery-recovery',timeout=60000)
   recovery=page.locator('.discovery-recovery').get_by_role('button',name='Try audience matches',exact=True)
   if await recovery.count():await recovery.click()
   await page.wait_for_selector('.town-card',timeout=60000)
   visual=await capture_visuals(page,settle_ms=20000)
   attrs=await page.locator('.town-image img').evaluate_all("els=>els.map(i=>({src:i.getAttribute('src'),srcset:i.getAttribute('srcset'),current:i.currentSrc,complete:i.complete,width:i.naturalWidth,loading:i.loading,display:getComputedStyle(i).display}))")
   print(json.dumps({'query':name,'stage':'bounded-image-settle-20s','visuals':visual,'images':attrs,'responses':responses,'failures':failures,'console':console},ensure_ascii=False),flush=True)
   prefix='cure-' if '--cure' in sys.argv else 'remaining-' if '--remaining' in sys.argv else ''
   await page.screenshot(path=f'/tmp/sideways-round9-art-{prefix}{index}.png')
   await page.close()
  await browser.close()

asyncio.run(main())
