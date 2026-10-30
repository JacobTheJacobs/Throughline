"""One real rejection/reload/agent regression in isolated browser storage."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import BASE
from live_round3_paths import OBSERVE
from browser_wait import wait_until

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
        await page.add_init_script('('+OBSERVE+')()')
        await page.goto(BASE+'/?seed=The%20Lighthouse&type=movie')
        await page.wait_for_selector('.town-card',timeout=60000)
        await wait_until(page,"JSON.parse(localStorage.getItem('sideways.discovery.v2')||'null')?.nodes?.length>0")
        snapshot=await page.evaluate("JSON.parse(localStorage.getItem('sideways.discovery.v2'))")
        first=page.locator('.town-card').first
        rejected_id=await first.get_attribute('data-node-id')
        rejected=next(node for node in snapshot['nodes'] if node['id']==rejected_id)
        before=await page.locator('.town-card').count()
        await first.click()
        await page.locator('.rate-no').click()
        await wait_until(page,f"!document.querySelector('[data-node-id=\"{rejected_id}\"]')",timeout=12000)
        await page.wait_for_timeout(500)
        await page.reload()
        await page.wait_for_selector('.town-card')
        assert await page.locator('.town-card').count()==before-1
        assert await page.locator(f'[data-node-id="{rejected_id}"]').count()==0
        await page.get_by_role('button',name='Explore for me',exact=True).click()
        await wait_until(page,"window.__liveAudit.some(x=>x.url==='/api/agent')")
        request=await page.evaluate("window.__liveAudit.filter(x=>x.url==='/api/agent').at(-1).request")
        assert rejected_id in [item['id'] for item in request['dislikes']]
        assert rejected_id in request['excludeIds']
        assert rejected_id not in [item['id'] for item in request.get('memory',{}).get('positiveAnchors',[])]
        await page.wait_for_selector('.log-done',timeout=80000)
        await page.wait_for_timeout(400)
        restored=await page.evaluate("JSON.parse(localStorage.getItem('sideways.discovery.v2'))")
        assert rejected_id not in [node['id'] for node in restored['nodes']]
        result={'rejected':rejected['name'],'rejectionSurvivesReload':True,'negativeSignalSent':True,'excludedFromAgent':True,'notPositiveMemory':True,'notReintroduced':True,'before':before,'after':len(restored['nodes'])}
        Path('/tmp/throughline-round14-rejection.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
        await browser.close()

asyncio.run(main())
