"""Ten fresh seeded live queries. Flow status does not certify every fact."""
import asyncio,json,random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
POOLS=[('artist',['Lorde','PJ Harvey']),('artist',['Talking Heads','Gorillaz']),('person',['Sofia Coppola','Guillermo del Toro']),('person',['Terry Pratchett','James Baldwin']),('brand',['Puma','Ben & Jerry’s']),('movie',['Her','The Truman Show']),('book',['A Wizard of Earthsea','The Name of the Wind']),('video game',['Portal 2','Spiritfarer']),('tv show',['Black Mirror','What We Do in the Shadows']),('destination',['Vienna','Stockholm'])]
async def main():
 cases=[(random.Random(2026102924+i).choice(pool),kind) for i,(kind,pool) in enumerate(POOLS)]
 print(json.dumps({'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':'Austria|Österreich' if query=='Vienna' else 'Sweden|Sverige'} if kind=='destination' else None
    return await audit(browser,i,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round24-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{s:sum(x['status']==s for x in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)
if __name__=='__main__':asyncio.run(main())
