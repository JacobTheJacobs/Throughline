"""UI-only authored fixture, not a provider relevance test."""
import asyncio,base64,json
from pathlib import Path
from playwright.async_api import async_playwright
BASE='https://throughline.51-21-210-47.sslip.io'
async def main():
 nodes=[dict(id=f'ui-{i}',name=name,type='book',parentId='root',seedName='UI fixture',queryType='book',liked=i==0,description='An authored UI fixture.',reason='Written by the starting author.',relation='Written by',x=3900+i*160,y=4000,depth=1,size='md') for i,name in enumerate(['Everything Everywhere All at Once: A Very Long Title for Layout Review','The Memory Police','A New Reference'])]
 encoded=base64.urlsafe_b64encode(json.dumps(dict(root=dict(id='ui-root',name='UI fixture',type='person'),nodes=nodes)).encode()).decode().rstrip('=')
 results=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  page=await browser.new_page(reduced_motion='reduce')
  await page.goto(BASE+'/#map='+encoded)
  await page.wait_for_selector('.town-card')
  results.append({'mapCaption':await page.locator('.hover-caption').first.inner_text()})
  await page.get_by_role('button',name='Gallery',exact=True).click()
  for w,h in [(320,568),(390,844),(768,1024),(1440,900)]:
   await page.set_viewport_size(dict(width=w,height=h))
   await page.screenshot(path=f'/tmp/throughline-round19-gallery-{w}.png')
   results.append(await page.evaluate('''()=>({width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,order:[...document.querySelectorAll('.gallery-grid article footer b')].map(x=>x.textContent),smallTargets:[...document.querySelectorAll('.gallery-board button,.editorial-topbar button')].filter(x=>!x.disabled&&x.getBoundingClientRect().width>0).map(x=>({name:x.getAttribute('aria-label')||x.textContent.trim(),width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height})).filter(x=>x.width<44||x.height<44)})'''))
  await page.get_by_role('button',name='Loved',exact=False).click()
  results.append({'lovedCount':await page.locator('.gallery-grid article').count()})
  await page.locator('.gallery-open').first.click()
  results.append({'galleryExploreVisible':await page.locator('.qloo-quick-action').count()})
  await browser.close()
 Path('/tmp/throughline-round19-gallery.json').write_text(json.dumps(results,indent=2))
 print(json.dumps(results))
asyncio.run(main())
