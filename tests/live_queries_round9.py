"""Ten new seeded real-browser queries; covers, graph, identity, save/reload and gallery."""
import asyncio,json,random
from playwright.async_api import async_playwright
from live_queries import audit

SEED=2026102809
POOLS=[
 ('artist',[('Massive Attack',{}),('Fiona Apple',{}),('Burna Boy',{})]),
 ('artist',[('Solange',{}),('The Cure',{}),('Hikaru Utada',{})]),
 ('person',[('Yorgos Lanthimos',{'detail_pattern':'director|filmmaker'}),('Lynne Ramsay',{'detail_pattern':'director|filmmaker'}),('Abbas Kiarostami',{'detail_pattern':'director|filmmaker'})]),
 ('person',[('Yōko Ogawa',{'detail_pattern':'writer|author|novelist'}),('Ted Chiang',{'detail_pattern':'writer|author|novelist'}),('Olga Tokarczuk',{'detail_pattern':'writer|author|novelist'})]),
 ('brand',[('Aesop',{}),('Salomon',{}),('Moleskine',{})]),
 ('movie',[('Aftersun',{'year':2022}),('Tampopo',{'year':1985}),('Coherence',{'year':2013})]),
 ('book',[('The Memory Police',{'year':1994}),('Convenience Store Woman',{'year':2016}),('The Fifth Season',{'year':2015})]),
 ('video game',[('Inscryption',{'year':2021}),('Animal Well',{'year':2024}),('Tunic',{'year':2022})]),
 ('tv show',[('Detectorists',{'year':2014}),('Reservation Dogs',{'year':2021}),('Scavengers Reign',{'year':2023})]),
 ('destination',[('Tbilisi',{}),('Oaxaca',{}),('Tallinn',{})]),
]

async def main():
 rng=random.Random(SEED);cases=[(name,kind,expected) for kind,pool in POOLS for name,expected in [rng.choice(pool)]]
 print(json.dumps({'sample_seed':SEED,'selected_queries':cases,'real_providers':True,'entry':'hydrated native form','concurrency':2},ensure_ascii=False),flush=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch();sem=asyncio.Semaphore(2)
  async def run(index,case):
   async with sem:return await audit(browser,index,*case,visuals=True,entry='form',visual_settle_ms=20000)
  results=await asyncio.gather(*(run(i,c) for i,c in enumerate(cases)));await browser.close()
 print(json.dumps({'summary':{s:sum(r['status']==s for r in results) for s in ['FLOW_PASS','FALLBACK','FAIL']},'visuals':{'checked':sum('visuals' in r for r in results),'with_issues':sum(bool(r.get('visual_issues')) for r in results)}},ensure_ascii=False),flush=True)
 if any(r['status']=='FAIL' or r.get('visual_issues') for r in results):raise SystemExit(1)

asyncio.run(main())
