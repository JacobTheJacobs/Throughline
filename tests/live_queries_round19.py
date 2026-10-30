"""Fresh live UI checks; FLOW_PASS is not a semantic accuracy score."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

CASES=[('Caroline Polachek','artist'),('Fleet Foxes','artist'),('Kelly Reichardt','person'),('Yoko Ogawa','person'),('Moleskine','brand'),('Perfect Blue','movie'),('The Memory Police','book'),('Citizen Sleeper','video game'),('We Are Lady Parts','tv show'),('Bologna','destination')]

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    return await audit(browser,i,query,kind,expected={'detail_pattern':'Italy|Italia'} if kind=='destination' else None,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(CASES)))
  await browser.close()
 Path('/tmp/throughline-round19-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{state:sum(x['status']==state for x in results) for state in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':asyncio.run(main())
