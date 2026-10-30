"""Browser-local deletion semantics using an authored disposable map, no user profile."""
import asyncio,base64,json
from pathlib import Path
from playwright.async_api import async_playwright
from browser_wait import wait_until
READ="""async()=>{const db=await new Promise((ok,no)=>{const r=indexedDB.open('sideways-memory');r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});const tx=db.transaction(['sessions','events','edges'],'readonly');const read=s=>new Promise(ok=>{const r=tx.objectStore(s).getAll();r.onsuccess=()=>ok(r.result)});const [sessions,events,edges]=await Promise.all(['sessions','events','edges'].map(read));return {session:sessions.some(x=>x.id==='delete-review-root'),events:events.filter(x=>x.sessionId==='delete-review-root').length,edges:edges.filter(x=>x.sessionId==='delete-review-root').length}}"""
async def main():
 payload={'root':{'id':'delete-review-root','name':'Disposable deletion review','type':'person'},'nodes':[{'id':'delete-review-child','name':'Disposable reference','type':'book','parentId':'root','seedName':'Disposable deletion review','queryType':'book','x':4000,'y':4000,'depth':1,'size':'md','reason':'Authored UI fixture.'}]}
 encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
  await page.goto('https://throughline.51-21-210-47.sslip.io/#map='+encoded)
  await page.wait_for_selector('.town-card')
  heart=page.locator('.card-taste button')
  await page.locator('.town-card').hover()
  bounds=await heart.bounding_box()
  hit=await page.evaluate("r=>document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.className",bounds)
  print('HEART_HIT_TEST',json.dumps({'target':hit}),flush=True)
  await heart.click()
  await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
  await heart.click()
  await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='0'")
  # The details save action lets the deletion check proceed independently of map overlay stacking.
  await page.locator('.town-card .card-hit').click()
  await page.locator('.rate-yes').click()
  await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
  await page.wait_for_timeout(900)
  before=await page.evaluate(READ)
  await page.get_by_role('button',name='Close details',exact=True).click()
  await page.get_by_role('button',name='Back to Throughline home',exact=True).click()
  await page.get_by_role('button',name='More actions for Disposable deletion review',exact=True).click()
  await page.get_by_role('menuitem',name='Remove',exact=True).click()
  await page.locator('.confirm-danger').click()
  await wait_until(page,"!document.querySelector('.recent-row')")
  after=await page.evaluate(READ)
  result={'fixtureOnly':True,'heartPointerTarget':hit,'heartPointerSaveUnsavePassed':True,'before':before,'afterRemoveExploration':after,'historyEntryGone':True}
  Path('/tmp/throughline-round22-deletion.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result))
  await browser.close()
asyncio.run(main())
