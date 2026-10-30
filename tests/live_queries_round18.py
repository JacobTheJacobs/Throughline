"""Ten fresh seeded live cases; flow status is not a semantic accuracy score."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS=[
 ('artist',['Caroline Polachek','Arlo Parks','Lauren Mayberry']),
 ('artist',['Fleet Foxes','Yo La Tengo','King Gizzard & the Lizard Wizard']),
 ('person',['Kelly Reichardt','Sean Baker','Alex Garland']),
 ('person',['Yoko Ogawa','Samanta Schweblin','Ocean Vuong']),
 ('brand',['Moleskine','Allbirds','On Running']),
 ('movie',['The Green Knight','Perfect Blue','Paterson']),
 ('book',['The Memory Police','Exhalation','We Have Always Lived in the Castle']),
 ('video game',['A Short Hike','Citizen Sleeper','Signalis']),
 ('tv show',['The Leftovers','Better Things','We Are Lady Parts']),
 ('destination',['Oslo','Bologna','Ghent']),
]
COUNTRIES={'Oslo':'Norway|Norge','Bologna':'Italy|Italia','Ghent':'Belgium|België|Belgique'}

async def main():
 rng=random.Random(2026102918)
 cases=[(rng.choice(pool),kind) for kind,pool in POOLS]
 print(json.dumps({'seed':2026102918,'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(index,case):
   async with sem:
    query,kind=case
    return await audit(browser,index,query,kind,expected={'detail_pattern':COUNTRIES[query]} if kind=='destination' else None,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round18-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{state:sum(x['status']==state for x in results) for state in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':asyncio.run(main())
