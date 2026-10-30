"""Seeded fresh live queries; flow success does not certify factual accuracy."""
import asyncio,json,random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
POOLS=[('artist',['Björk','FKA twigs']),('artist',['Massive Attack','Beach House']),('person',['Agnès Varda','Bong Joon-ho']),('person',['Ursula K. Le Guin','Kazuo Ishiguro']),('brand',['Muji','Patagonia']),('movie',['Arrival','Fantastic Mr. Fox']),('book',['Piranesi','Invisible Cities']),('video game',['Hollow Knight','Outer Wilds']),('tv show',['Severance','Fleabag']),('destination',['Ljubljana','Tallinn'])]
async def main():
 cases=[(random.Random(2026102920+i).choice(pool),kind) for i,(kind,pool) in enumerate(POOLS)]
 print(json.dumps({'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':'Slovenia|Slovenija' if query=='Ljubljana' else 'Estonia|Eesti'} if kind=='destination' else None
    return await audit(browser,i,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round20-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{s:sum(x['status']==s for x in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)
if __name__=='__main__':asyncio.run(main())
