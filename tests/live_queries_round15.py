"""Fresh seeded live search review, no mocked providers."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS=[
 ('artist',['Fiona Apple','Norah Jones','Bon Iver']),
 ('artist',['Slowdive','The National','Florence + the Machine']),
 ('person',['Park Chan-wook','Sergio Leone','Wes Craven']),
 ('person',['N. K. Jemisin','Susanna Clarke','Neil Gaiman']),
 ('brand',['Muji','Dyson','Oatly']),
 ('movie',['Pan’s Labyrinth','Good Will Hunting','Moonrise Kingdom']),
 ('book',['Piranesi','The Road','American Gods']),
 ('video game',['Spiritfarer','Celeste','Outer Wilds']),
 ('tv show',['Reservation Dogs','The Wire','BoJack Horseman']),
 ('destination',['Vancouver','Cambridge','Bergen']),
]

async def main():
 rng=random.Random(2026102915)
 cases=[(rng.choice(pool),kind) for kind,pool in POOLS]
 print(json.dumps({'seed':2026102915,'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(index,case):
   async with sem:return await audit(browser,index,*case,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round15-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{state:sum(x['status']==state for x in results) for state in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':asyncio.run(main())
