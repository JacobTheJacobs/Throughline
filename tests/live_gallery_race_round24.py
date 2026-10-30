"""Authored two-map fixture tests delayed Loved unsave across a root switch."""
import asyncio,base64,json,time
from pathlib import Path
from playwright.async_api import async_playwright
from browser_wait import wait_until
async def main():
 def record(rootid,name):
  return {'root':{'id':rootid,'name':name,'type':'person'},'nodes':[{'id':'race-shared-book','name':'Shared saved reference','type':'book','parentId':'root','seedName':name,'queryType':'book','liked':True,'x':4000,'y':4000,'depth':1,'size':'md','reason':'Authored fixture.'}],'alternatives':[],'savedAt':int(time.time()*1000)}
 a,b=record('race-a','Race A'),record('race-b','Race B')
 encoded=base64.urlsafe_b64encode(json.dumps(a).encode()).decode().rstrip('=')
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='no-preference')
  await page.add_init_script('localStorage.setItem("sideways.maps.v1",'+json.dumps(json.dumps({'race-b':b}))+')')
  await page.goto('https://throughline.51-21-210-47.sslip.io/#map='+encoded)
  await page.wait_for_selector('.town-card')
  await page.get_by_role('button',name='Gallery',exact=True).click()
  await page.get_by_role('button',name='Loved',exact=False).click()
  start=time.monotonic()
  await page.get_by_role('button',name='Remove from saved Shared saved reference',exact=True).click()
  await page.get_by_role('button',name='Back to Throughline home',exact=True).click()
  await page.locator('.recent-row>button:first-child').filter(has_text='Race B').click()
  switched_ms=round((time.monotonic()-start)*1000)
  await page.wait_for_selector('.town-card')
  immediately=await page.locator('.top-saved b').inner_text()
  await page.wait_for_timeout(1200)
  result=await page.evaluate("()=>({saved:document.querySelector('.top-saved b')?.textContent,snapshot:JSON.parse(localStorage.getItem('sideways.discovery.v2')||'null')})")
  events=await page.evaluate("async()=>{const db=await new Promise(ok=>{const r=indexedDB.open('sideways-memory');r.onsuccess=()=>ok(r.result)});return await new Promise(ok=>{const r=db.transaction('events','readonly').objectStore('events').getAll();r.onsuccess=()=>ok(r.result.filter(x=>x.kind==='unlove').map(x=>({kind:x.kind,sessionId:x.sessionId,entityId:x.entityId})))})}")
  result={'fixtureOnly':True,'switchElapsedMs':switched_ms,'root':result['snapshot']['root']['id'],'savedImmediatelyAfterSwitch':immediately,'savedCount':result['saved'],'nodeLiked':result['snapshot']['nodes'][0].get('liked'),'unloveEvents':events}
  Path('/tmp/throughline-round24-gallery-race.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result))
  await browser.close()
asyncio.run(main())
