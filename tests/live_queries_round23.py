"""Fresh stratified seeded production queries; flow pass is not semantic certification."""
import asyncio,json,random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit
POOLS=[('artist',['Weyes Blood','Adrianne Lenker']),('artist',['Stereolab','Khruangbin']),('person',['Denis Villeneuve','Greta Gerwig']),('person',['Jorge Luis Borges','Shirley Jackson']),('brand',['Converse','Lush']),('movie',['Whiplash','Amélie']),('book',['The Fifth Season','The Handmaid’s Tale']),('video game',['Baldur’s Gate 3','Stardew Valley']),('tv show',['Russian Doll','Succession']),('destination',['Lisbon','Copenhagen'])]
async def main():
 cases=[(random.Random(2026102923+i).choice(pool),kind) for i,(kind,pool) in enumerate(POOLS)]
 print(json.dumps({'queries':cases},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  sem=asyncio.Semaphore(2)
  async def run(i,case):
   async with sem:
    query,kind=case
    expected={'detail_pattern':'Portugal' if query=='Lisbon' else 'Denmark|Danmark'} if kind=='destination' else None
    return await audit(browser,i,query,kind,expected=expected,entry='form',visuals=True,visual_settle_ms=15000)
  results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
  await browser.close()
 Path('/tmp/throughline-round23-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 print(json.dumps({'summary':{s:sum(x['status']==s for x in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)
if __name__=='__main__':asyncio.run(main())
