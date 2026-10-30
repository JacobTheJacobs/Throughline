"""Live single-action inspector checks: no category grid/ranking calls, real match insertion."""
import asyncio,json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
  await page.add_init_script('('+OBSERVE+')()')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/?seed=Wong%20Kar-wai&type=person')
  await page.wait_for_selector('.town-card',timeout=60000)
  await page.locator('.town-card').filter(has_text='In the Mood for Love').locator('.card-hit').click()
  await page.wait_for_selector('.qloo-quick-action')
  await page.wait_for_timeout(1500)
  action=page.locator('.cinematic-inspector .qloo-quick-action')
  assert await action.get_by_role('button').count()==1
  assert await action.inner_text()=='Explore with Qloo'
  assert not await page.locator('.direction-chips,.qloo-all-toggle,.qloo-all-categories').count()
  calls=await page.evaluate('window.__liveAudit')
  assert not any(c['url']=='/api/suggestions' or c.get('request',{} ) and c['request'].get('probeTypes') for c in calls),'Inspector opening triggered category discovery'
  before=await page.locator('.town-card').count()
  await action.get_by_role('button',name='Explore with Qloo',exact=True).click()
  await page.wait_for_function("document.querySelector('.qloo-quick-action button')?.getAttribute('aria-busy')==='false'",timeout=60000)
  after=await page.locator('.town-card').count()
  assert before<after<=before+5,{'before':before,'after':after,'body':await page.locator('.toast').inner_text() if await page.locator('.toast').count() else ''}
  probes=await page.evaluate("window.__liveAudit.filter(c=>c.request?.probeTypes)")
  assert len(probes)==1,'One click triggered multiple browser discovery requests'
  inserted=await page.locator('.town-card').evaluate_all('els=>els.map(e=>({id:e.dataset.nodeId,type:e.dataset.type}))')
  await page.screenshot(path='/tmp/sideways-single-qloo-desktop.png')
  for width in [390,768]:
   await page.set_viewport_size({'width':width,'height':844})
   await action.get_by_role('button').scroll_into_view_if_needed()
   box=await action.get_by_role('button').bounding_box()
   assert box['height']>=44 and box['x']>=0 and box['x']+box['width']<=width
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
  await page.screenshot(path='/tmp/sideways-single-qloo-tablet.png')
  assert not errors,errors
  print(json.dumps({'stage':'single-action','before':before,'after':after,'probeCount':len(probes),'requestTypes':probes[0]['request']['types'],'inserted':inserted,'actionText':await action.inner_text(),'errors':errors},ensure_ascii=False),flush=True)
  await page.close()
  page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
  await page.add_init_script('('+OBSERVE+')()')
  await page.goto(BASE+'/?s=1BC51D7C-4E53-4D8F-B381-C5112D1B5133&n=Bel-Air&t=destination')
  await page.wait_for_selector('.town-card',timeout=45000)
  await page.locator('.town-card').filter(has_text='Carrefour Rambouillet').locator('.card-hit').click()
  action=page.locator('.cinematic-inspector .qloo-quick-action')
  await action.get_by_role('button',name='Explore with Qloo',exact=True).click()
  await page.wait_for_function("document.querySelector('.qloo-quick-action small')?.textContent==='From Bel-Air'",timeout=60000)
  assert await action.get_by_role('button').count()==1
  assert await action.inner_text()=='Explore with Qloo\nFrom Bel-Air'
  assert await page.locator('.town-card').count()==5,'Unsupported card silently switched anchor'
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':900 if width==1440 else 844})
   await action.get_by_role('button').scroll_into_view_if_needed()
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
   await page.screenshot(path=f'/tmp/sideways-single-qloo-fallback-{width}.png')
  print(json.dumps({'stage':'compact-fallback','text':await action.inner_text(),'beforeExplicitFallback':await page.locator('.town-card').count(),'calls':await page.evaluate("window.__liveAudit.filter(c=>c.request?.probeTypes).map(c=>({status:c.status,reason:c.data?.reason,anchor:c.request.name}))")},ensure_ascii=False),flush=True)
  await browser.close()

asyncio.run(main())
