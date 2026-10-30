"""Explicit alias and URL-entry diagnostic controls; no provider mocking."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
import live_queries
from browser_wait import wait_until
original=live_queries.matches_name
def alias(query,choice):
 return original(query,choice) or (query=='Octavia Butler' and choice.get('name')=='Octavia E. Butler' and choice.get('type')=='person')
live_queries.matches_name=alias
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  result=await live_queries.audit(browser,3,'Octavia Butler','person',entry='form',visuals=True,visual_settle_ms=15000)
  Path('/tmp/throughline-round21-alias.json').write_text(json.dumps(result,indent=2))
  print('ALIAS',json.dumps({'status':result['status'],'chosen':result.get('chosen_identity'),'cards':len(result.get('cards',[])),'errors':result['errors']}),flush=True)
  page=await browser.new_page()
  await page.goto('https://throughline.51-21-210-47.sslip.io/?seed=The%20Lighthouse&type=movie')
  await wait_until(page,"!!document.querySelector('.town-card,.clarify-card,.discovery-recovery')",timeout=65000)
  print('URL_ENTRY',await page.locator('body').inner_text(),flush=True)
  await browser.close()
asyncio.run(main())
