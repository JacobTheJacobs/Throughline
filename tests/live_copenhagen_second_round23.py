"""Explicit second, unlabeled Copenhagen candidate; never count as the intended city without evidence."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
import live_queries
original=live_queries.matches_name
def select(query,choice):
 if query=='Copenhagen' and choice.get('type')=='destination':return choice.get('id')=='82DCD455-A5AB-42D0-B390-11218B0C7FF0'
 return original(query,choice)
live_queries.matches_name=select
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  result=await live_queries.audit(browser,9,'Copenhagen','destination',entry='form',visuals=True,visual_settle_ms=15000)
  Path('/tmp/throughline-round23-copenhagen-second.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
  print('SECOND_CONTROL',json.dumps({'status':result['status'],'chosen':result.get('chosen_identity'),'cards':[(x['name'],x.get('description')) for x in result.get('cards',[])],'errors':result['errors']}),flush=True)
  await browser.close()
asyncio.run(main())
