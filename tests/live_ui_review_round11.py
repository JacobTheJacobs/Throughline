"""Production UI review using an explicitly authored shared-map fixture.
No provider responses mocked; clipboard/window.open intercepted to avoid external writes.
"""
import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE='https://throughline.51-21-210-47.sslip.io'

async def main():
    root={'id':'review-root','name':'Review fixture','type':'person'}
    nodes=[{'id':f'review-{i}','name':f'Saved reference {i}','type':'book','parentId':'root','seedName':'Review fixture','queryType':'book','liked':True,'description':'Identity evidence that should survive exact sharing.','reason':'An authored relationship explanation for this browser fixture. '*4,'relation':'Written by','x':3800+i*200,'y':3900,'depth':1,'size':'md'} for i in range(12)]
    encoded=base64.urlsafe_b64encode(json.dumps({'root':root,'nodes':nodes}).encode()).decode().rstrip('=')
    result={'fixture':True,'liveProvidersTested':False}
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
        await page.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.__copied=text}}});window.open=(url)=>{window.__opened=url;return {}}")
        await page.goto(BASE+'/#map='+encoded)
        await page.wait_for_selector('.town-card')
        await page.get_by_role('button',name='Share',exact=True).click()
        result['shareInitialFocusInside']=await page.evaluate("!!document.activeElement?.closest('.share-studio')")
        await page.locator('.share-networks button').last.focus()
        await page.keyboard.press('Tab')
        result['shareTabWrapInside']=await page.evaluate("!!document.activeElement?.closest('.share-studio')")
        await page.get_by_role('button',name='Copy exact link',exact=False).click()
        copied=await page.evaluate('window.__copied')
        result['exactLinkLength']=len(copied)
        data=json.loads(base64.urlsafe_b64decode(copied.split('#map=')[1]+'==='))
        result['descriptionSurvivesSharing']='description' in data['nodes'][0]
        await page.locator('.share-networks button').first.click()
        opened=await page.evaluate('window.__opened')
        result['socialPreservesMap']='%23map%3D' in opened
        result['socialUsesSeedOnly']='%3Fs%3D' in opened
        await page.keyboard.press('Escape')
        await page.get_by_role('button',name='Saved',exact=False).first.click()
        await page.wait_for_selector('.taste-brief')
        result['factualBadge']=await page.locator('.brief-reference-actions em').first.inner_text()
        await page.locator('.brief-reference-actions button').first.click()
        await page.wait_for_selector('.confirm-dialog')
        await page.keyboard.press('Tab')
        await page.keyboard.press('Tab')
        result['nestedConfirmFocusInside']=await page.evaluate("!!document.activeElement?.closest('.confirm-dialog')")
        result['focusedElement']=await page.evaluate("document.activeElement?.outerHTML.slice(0,180)")
        await page.keyboard.press('Escape')
        await page.keyboard.press('Escape')
        await page.get_by_role('button',name='Gallery',exact=True).click()
        await page.locator('.gallery-open').first.click()
        await page.get_by_role('button',name='Close details',exact=True).click()
        await page.wait_for_timeout(150)
        result['galleryFocusRestored']=await page.evaluate("!!document.activeElement?.closest('.gallery-grid')")
        await page.get_by_role('button',name='Back to Throughline home',exact=True).click()
        await page.set_viewport_size({'width':390,'height':844})
        await page.get_by_role('button',name='Open recent explorations',exact=True).click()
        result['recentsCloseSize']=await page.get_by_role('button',name='Close saved explorations',exact=True).bounding_box()
        await browser.close()
    Path('/tmp/throughline-round11-ui.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

asyncio.run(main())
