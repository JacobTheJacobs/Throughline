"""Fresh stratified searches with explicit geographic identity expectations."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS=[
 ('artist',['Japanese Breakfast','Angel Olsen','SAULT']),
 ('artist',['Big Thief','Alvvays','The War on Drugs']),
 ('person',['Lynne Ramsay','Robert Eggers','Jim Jarmusch']),
 ('person',['Elena Ferrante','Han Kang','Mariana Enriquez']),
 ('brand',['A24','Veja','Freitag']),
 ('movie',['Sound of Metal','Decision to Leave','Minari']),
 ('book',['Annihilation','House of Leaves','Klara and the Sun']),
 ('video game',['Tunic','Inscryption','Control']),
 ('tv show',['Somebody Somewhere','Scavengers Reign','Andor']),
 ('destination',['Wellington','Victoria','Salem']),
]
COUNTRIES={'Wellington':'New Zealand','Victoria':'Canada|British Columbia','Salem':'Massachusetts'}

async def main():
 rng=random.Random(2026102916)
 cases=[(rng.choice(pool),kind) for kind,pool in POOLS]
 print(json.dumps({'seed':2026102916,'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(index,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':COUNTRIES[query]} if kind=='destination' else None
    return await audit(browser,index,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round16-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{state:sum(x['status']==state for x in results) for state in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':asyncio.run(main())
