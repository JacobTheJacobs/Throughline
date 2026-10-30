"""Ten fresh real-provider cases, with a country-qualified destination."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS=[
 ('artist',['Ethel Cain','Tamino','Weyes Blood']),
 ('artist',['Black Country, New Road','Fontaines D.C.','Wet Leg']),
 ('person',['Celine Song','Charlotte Wells','Alice Rohrwacher']),
 ('person',['Annie Ernaux','Olga Tokarczuk','Sally Rooney']),
 ('brand',['Ganni','Acne Studios',"Arc’teryx"]),
 ('movie',['The Worst Person in the World','After Yang','Leave No Trace']),
 ('book',['Sea of Tranquility','Convenience Store Woman','The Overstory']),
 ('video game',['Pentiment','Night in the Woods','Kentucky Route Zero']),
 ('tv show',['Pachinko','Slow Horses','Detectorists']),
 ('destination',['Valencia','Granada','Québec City']),
]
COUNTRIES={'Valencia':'Spain|España','Granada':'Spain|España','Québec City':'Canada|Québec|Quebec'}

async def main():
 rng=random.Random(2026102917)
 cases=[(rng.choice(pool),kind) for kind,pool in POOLS]
 print(json.dumps({'seed':2026102917,'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(index,case):
   async with sem:
    query,kind=case
    return await audit(browser,index,query,kind,expected={'detail_pattern':COUNTRIES[query]} if kind=='destination' else None,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round17-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{state:sum(x['status']==state for x in results) for state in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':asyncio.run(main())
