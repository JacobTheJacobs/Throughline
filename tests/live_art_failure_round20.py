"""Authored UI fixture with intentionally aborted artwork, not a provider outage."""
import asyncio,base64,json
from pathlib import Path
from playwright.async_api import async_playwright
from browser_wait import wait_until
async def main():
 payload={'root':{'id':'ui-root','name':'Artwork failure fixture','type':'person'},'nodes':[{'id':'ui-art','name':'Artwork failure fixture book','type':'book','parentId':'root','seedName':'Artwork failure fixture','queryType':'book','liked':True,'x':4000,'y':4000,'depth':1,'size':'md','image':'https://images.qloo.com/i/42AF15D5-E1BD-4291-9B0F-C829A8274843-420x-auto.jpg','reason':'An authored test relationship.'}]}
 encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(viewport={'width':390,'height':844})
  await page.route('https://images.qloo.com/**',lambda route:route.abort())
  await page.goto('https://throughline.51-21-210-47.sslip.io/#map='+encoded)
  await page.wait_for_selector('.town-card')
  await page.get_by_role('button',name='Gallery',exact=True).click()
  await wait_until(page,"!!document.querySelector('.gallery-open i') || (!!document.querySelector('.gallery-open img') && getComputedStyle(document.querySelector('.gallery-open img')).display==='none')")
  gallery=await page.locator('.gallery-open').evaluate("e=>({failedImageRetained:!!e.querySelector('img')&&e.querySelector('img').naturalWidth===0,fallback:!!e.querySelector('i'),imageDisplay:e.querySelector('img')?getComputedStyle(e.querySelector('img')).display:null,missingStyle:e.classList.contains('art-missing')})")
  await page.screenshot(path='/tmp/throughline-round20-art-failure.png')
  await page.get_by_role('button',name='Saved',exact=False).first.click()
  await page.wait_for_selector('.brief-reference')
  await wait_until(page,"!!document.querySelector('.brief-art-fallback') || (!!document.querySelector('.brief-reference img') && getComputedStyle(document.querySelector('.brief-reference img')).display==='none')")
  brief=await page.locator('.brief-reference').evaluate("e=>({failedImageRetained:!!e.querySelector('img')&&e.querySelector('img').naturalWidth===0,fallback:!!e.querySelector('.brief-art-fallback,.art-initials'),imageDisplay:e.querySelector('img')?getComputedStyle(e.querySelector('img')).display:null,missingStyle:e.classList.contains('art-missing')})")
  result={'controlledFailure':True,'gallery':gallery,'brief':brief}
  Path('/tmp/throughline-round20-art-failure.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result))
  await browser.close()
asyncio.run(main())
