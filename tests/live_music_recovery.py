"""Real music identity, explicit artist recovery and stale-state regression. No mocked responses."""
import asyncio,json
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE

async def search(page,text):
 await page.wait_for_function("Object.keys(document.querySelector('.hero-search input')||{}).some(k=>k.startsWith('__reactProps'))")
 await page.get_by_role('textbox',name='What would you like to explore?',exact=True).fill(text)
 await page.get_by_role('button',name='Begin exploring',exact=True).click()

async def choose(page,qid):
 await page.wait_for_selector('.clarify-card',timeout=45000)
 choices=await page.evaluate("window.__liveAudit.filter(c=>c.data?.mode==='clarify').at(-1).data.choices")
 index=next(i for i,c in enumerate(choices) if c['id']==qid)
 await page.locator('.clarify-card>div>button').nth(index).click()
 return choices

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
  await page.add_init_script('('+OBSERVE+')()')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE)
  await search(page,'Dragostea Din Tei')
  choices=await choose(page,'wikidata:Q161407')
  assert any(c['id']=='wikidata:Q121862982' and 'Haiducii' in c.get('detail','') for c in choices)
  await page.get_by_role('button',name='Find matches from O-Zone',exact=True).wait_for(timeout=45000)
  assert not await page.locator('.town-card').count(),'Recovery silently changed anchor'
  await page.get_by_role('button',name='Find matches from O-Zone',exact=True).click()
  await page.wait_for_selector('.town-card',timeout=60000)
  assert 'O-Zone' in await page.locator('.exploration-context').inner_text()
  assert not await page.locator('.discovery-recovery').count()
  print(json.dumps({'stage':'verified-song-to-explicit-artist','choices':choices,'cards':await page.locator('.town-card').count(),'context':await page.locator('.exploration-context').inner_text()}),flush=True)
  await page.get_by_role('button',name='Back to Sideways home',exact=True).click()
  await search(page,'Dragostea Din Tei')
  await choose(page,'C71D143E-76CC-4FB3-BFF8-ED2DAD69241B')
  await page.wait_for_selector('.discovery-recovery')
  await page.get_by_role('button',name='Choose another meaning',exact=True).wait_for()
  recent=page.locator('.home-sidebar button').filter(has_text='O-Zone').first
  await recent.wait_for()
  await recent.click()
  await page.wait_for_selector('.town-card')
  assert not await page.locator('.discovery-recovery').count(),'Stale search recovery survived map resume'
  print(json.dumps({'stage':'resume-clears-unrelated-error','context':await page.locator('.exploration-context').inner_text()}),flush=True)
  await page.get_by_role('button',name='Back to Sideways home',exact=True).click()
  await search(page,'Katy Perry')
  await page.wait_for_selector('.clarify-card, .town-card',timeout=45000)
  if await page.locator('.clarify-card').count():
   choices=await page.evaluate("window.__liveAudit.filter(c=>c.data?.mode==='clarify').at(-1).data.choices")
   artist=next(c for c in choices if c['type']=='artist' and c['name']=='Katy Perry')
   await choose(page,artist['id'])
  await page.wait_for_selector('.town-card',timeout=60000)
  await page.locator('.town-card').filter(has_text='Hot n Cold').locator('.card-hit').click()
  await page.wait_for_function("document.querySelector('.qloo-quick-action small')?.textContent==='From Katy Perry'",timeout=45000)
  assert await page.locator('.cinematic-inspector .direction-chips button').count()==0
  before=await page.locator('.town-card').count()
  calls=await page.evaluate("window.__liveAudit.filter(c=>c.request?.probeTypes&&c.request?.name==='Hot n Cold')")
  assert len(calls)==1,'Repeated unsupported-card probes'
  await page.locator('.cinematic-inspector').get_by_role('button',name='Explore with Qloo',exact=True).click()
  await page.wait_for_function('(n)=>document.querySelectorAll(".town-card").length>n',arg=before,timeout=45000)
  assert not await page.locator('.discovery-recovery').count()
  assert not errors,errors
  await page.set_viewport_size({'width':390,'height':844})
  assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
  await page.screenshot(path='/tmp/sideways-music-recovery-fixed.png')
  print(json.dumps({'stage':'blocked-work-to-explicit-source','before':before,'after':await page.locator('.town-card').count(),'blockedProbes':len(calls),'errors':errors,'calls':await page.evaluate('window.__liveAudit')},ensure_ascii=False),flush=True)
  await browser.close()

asyncio.run(main())
