"""Ten fresh seeded live cases; flow pass is not a factual accuracy certificate."""
import asyncio,json,random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
POOLS=[('artist',['Joanna Newsom','St. Vincent']),('artist',['LCD Soundsystem','Sigur Rós']),('person',['Wong Kar-wai','Julia Ducournau']),('person',['N. K. Jemisin','Susanna Clarke']),('brand',['IKEA','Nintendo']),('movie',['The Grand Budapest Hotel','Spirited Away']),('book',['Annihilation','Beloved']),('video game',['Hades','Pentiment']),('tv show',['Atlanta','The Bear']),('destination',['Helsinki','Kyoto'])]
async def main():
 cases=[(random.Random(2026102922+i).choice(pool),kind) for i,(kind,pool) in enumerate(POOLS)]
 print(json.dumps({'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':'Finland|Suomi' if query=='Helsinki' else 'Japan|日本'} if kind=='destination' else None
    return await audit(browser,i,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round22-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{s:sum(x['status']==s for x in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)
if __name__=='__main__':asyncio.run(main())
