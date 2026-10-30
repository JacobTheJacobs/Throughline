"""Wait-aware nested-dialog keyboard check; authored map, no provider mocks."""
import asyncio
import base64
import json
from playwright.async_api import async_playwright
from browser_wait import wait_until

async def main():
    payload={'root':{'id':'confirm-root','name':'Confirmation fixture','type':'person'},'nodes':[{'id':'confirm-book','name':'Reference','type':'book','parentId':'root','seedName':'Confirmation fixture','queryType':'book','liked':True,'x':4000,'y':4000,'depth':1,'size':'md'}]}
    encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(reduced_motion='reduce')
        await page.goto('https://throughline.51-21-210-47.sslip.io/#map='+encoded)
        await page.wait_for_selector('.town-card')
        await page.get_by_role('button',name='Saved',exact=False).first.click()
        for index in range(3):
            await page.locator('.brief-reference-actions button').first.click()
            await wait_until(page,"document.activeElement?.classList.contains('confirm-safe')")
            inside=[]
            for _ in range(8):
                await page.keyboard.press('Tab')
                inside.append(await page.evaluate("!!document.activeElement?.closest('.confirm-dialog')"))
            await page.keyboard.press('Escape')
            await wait_until(page,"!document.querySelector('.confirm-dialog')")
            restored=await page.evaluate("!!document.activeElement?.closest('.brief-reference-actions')")
            results.append({'attempt':index+1,'tabsContained':all(inside),'focusRestored':restored})
        print(json.dumps(results))
        assert all(row['tabsContained'] and row['focusRestored'] for row in results)
        await browser.close()

asyncio.run(main())
