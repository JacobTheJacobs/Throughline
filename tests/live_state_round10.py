"""Actual browser save/unlove, map isolation, gallery, agent count and mobile checks."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import BASE
from browser_wait import wait_until
from live_round3_paths import OBSERVE

async def main():
    report = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width':390,'height':844}, reduced_motion='reduce')
        await page.add_init_script('('+OBSERVE+')()')
        for name, kind in [('The Lighthouse','movie'),('Dark','tv_show')]:
            await page.goto(BASE+'/?seed='+name+'&type='+kind)
            await page.wait_for_selector('.town-card',timeout=60000)
            await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='0'")
            count = await page.locator('.town-card').count()
            await page.locator('.town-card .card-hit').first.click()
            await page.locator('.rate-yes').click()
            await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
            await page.locator('.rate-yes').click()
            await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='0'")
            await page.locator('.rate-yes').click()
            await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
            assert await page.locator('.town-card').count()==count
            await page.get_by_role('button',name='Close details',exact=True).click()
            await page.get_by_role('button',name='Gallery',exact=True).click()
            await page.locator('.gallery-open').first.click()
            assert await page.locator('.qloo-quick-action').count()==0
            await page.get_by_role('button',name='Close details',exact=True).click()
            await page.reload()
            await page.wait_for_selector('.town-card')
            await wait_until(page,"document.querySelector('.top-saved b')?.textContent==='1'")
            report.append({'query':name,'saved':1,'cards':count,'galleryExploreHidden':True,'reload':True})
            await page.get_by_role('button',name='Back to Throughline home',exact=True).click()
            await page.wait_for_selector('.editorial-home')
        await page.set_viewport_size({'width':1440,'height':900})
        await page.locator('.recent-row>button:first-child').filter(has_text='The Lighthouse').click()
        await page.wait_for_selector('.town-card')
        before=await page.locator('.town-card').count()
        await page.get_by_role('button',name='Explore for me',exact=True).click()
        await wait_until(page,"window.__liveAudit.some(x=>x.url==='/api/agent')")
        request=await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/agent').at(-1).request")
        assert request['root']['name']=='The Lighthouse'
        assert len(request['likes'])==1
        likes={x['id'] for x in request['likes']}
        assert all(x['id'] in likes for x in request.get('memory',{}).get('positiveAnchors',[]))
        await page.wait_for_selector('.log-done',timeout=70000)
        await page.wait_for_timeout(1000)
        after=await page.locator('.town-card').count()
        events=await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/agent').at(-1).data?.events||[]")
        adds=sum(len(x.get('discoveries',[])) for x in events if x.get('kind')=='add')
        assert after-before==adds
        report.append({'agentRoot':request['root']['name'],'savedSignals':len(request['likes']),'memoryScoped':True,'before':before,'after':after,'streamAdditions':adds,'log':await page.locator('.agent-log').inner_text()})
        for width in [320,390,768,1440]:
            await page.set_viewport_size({'width':width,'height':844})
            assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
            report.append({'mapWidth':width,'horizontalOverflow':False})
        await page.screenshot(path='/tmp/throughline-round10-map.png')
        await browser.close()
    Path('/tmp/throughline-round10-state.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

asyncio.run(main())
