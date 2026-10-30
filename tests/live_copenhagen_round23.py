"""Inspect destination evidence before retrying an overly narrow country-text assertion."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
async def main():
 async with async_playwright() as p:
  api=await p.request.new_context(base_url='https://throughline.51-21-210-47.sslip.io')
  response=await api.post('/api/discover',data={'text':'Copenhagen'},timeout=30000)
  data=await response.json()
  choices=[x for x in data.get('choices',[]) if x.get('type')=='destination']
  print('DESTINATION_CHOICES',json.dumps(choices,ensure_ascii=False),flush=True)
  await api.dispose()
  browser=await p.chromium.launch()
  result=await audit(browser,9,'Copenhagen','destination',entry='form',visuals=True,visual_settle_ms=15000)
  Path('/tmp/throughline-round23-copenhagen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
  print('CONTROL',json.dumps({'status':result['status'],'chosen':result.get('chosen_identity'),'cards':[x['name'] for x in result.get('cards',[])],'errors':result['errors']}),flush=True)
  await browser.close()
asyncio.run(main())
