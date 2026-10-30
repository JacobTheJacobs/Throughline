"""Two bounded real API calls with authored metadata; no mocked scoring."""
import asyncio,json,time
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  api=await p.request.new_context(base_url='https://throughline.51-21-210-47.sslip.io')
  card={'id':'review-cache-'+str(time.time_ns()),'name':'Dune','type':'book'}
  a=await api.post('/api/card',data={'card':card},timeout=20000)
  b=await api.post('/api/card',data={'card':{**card,'description':'1965 novel by Frank Herbert','tags':['Science Fiction']}},timeout=20000)
  first,second=await a.json(),await b.json()
  result={'authoredMetadataControl':True,'statuses':[a.status,b.status],'firstSource':first.get('source'),'secondSource':second.get('source'),'sameQueryOptions':first.get('options')==second.get('options'),'second':second}
  Path('/tmp/throughline-round23-card-cache.json').write_text(json.dumps(result,indent=2))
  print(json.dumps(result))
  await api.dispose()
asyncio.run(main())
