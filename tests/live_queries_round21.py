"""Fresh seeded production cases. Flow success is not factual certification."""
import asyncio,json,random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
POOLS=[('artist',['Sufjan Stevens','Japanese Breakfast']),('artist',['Slowdive','Big Thief']),('person',['Park Chan-wook','Céline Song']),('person',['Octavia Butler','Ted Chiang']),('brand',['LEGO','Uniqlo']),('movie',['Moonlight','Pan’s Labyrinth']),('book',['The Dispossessed','The Secret History']),('video game',['Disco Elysium','Tunic']),('tv show',['Reservation Dogs','Derry Girls']),('destination',['Reykjavík','Kraków'])]
async def main():
 cases=[(random.Random(2026102921+i).choice(pool),kind) for i,(kind,pool) in enumerate(POOLS)]
 print(json.dumps({'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':'Iceland|Ísland' if query=='Reykjavík' else 'Poland|Polska'} if kind=='destination' else None
    return await audit(browser,i,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round21-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{s:sum(x['status']==s for x in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)
if __name__=='__main__':asyncio.run(main())
