"""Untrusted shared-map sanitization and short-screen home checks."""
import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import BASE

async def main():
    name='<img src=x onerror="window.__xss=1">'
    payload={'root':{'id':'safety-root','name':name,'type':'movie'},'nodes':[{'id':'safety-child','name':name,'type':'book','parentId':'root','seedName':name,'queryType':'book','liked':True,'x':4100,'y':4000,'depth':1,'size':'md','image':'http://169.254.169.254/x','links':[{'label':'Bad link','url':'javascript:window.__xss=1'}]}]}
    encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(reduced_motion='reduce')
        await page.goto(BASE+'/#map='+encoded)
        await page.wait_for_selector('.town-card')
        assert not await page.evaluate('window.__xss')
        assert await page.locator('a[href^="javascript:"]').count()==0
        assert await page.locator('img[src^="http://169.254"]').count()==0
        results.append({'sharedHtmlEscaped':True,'unsafeLinksDropped':True,'httpImageDropped':True})
        await page.get_by_role('button',name='Back to Throughline home',exact=True).click()
        assert await page.locator('.coach-mark').count()==0
        assert await page.locator('.toast').count()==0
        for w,h in [(320,568),(390,844),(768,1024),(1440,900),(844,390)]:
            await page.set_viewport_size({'width':w,'height':h})
            search=page.locator('.hero-search')
            await search.scroll_into_view_if_needed()
            assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
            bounds=await search.bounding_box()
            assert bounds and bounds['y']>=0 and bounds['y']+bounds['height']<=h
            if w<=700:assert await page.get_by_role('button',name='Open recent explorations',exact=True).is_visible()
            await page.screenshot(path=f'/tmp/throughline-round10-home-{w}.png')
            results.append({'width':w,'height':h,'inputReachable':True,'horizontalOverflow':False})
        await browser.close()
    Path('/tmp/throughline-round10-shared-safety.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))

asyncio.run(main())
