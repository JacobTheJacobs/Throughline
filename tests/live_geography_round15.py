"""Regression: the selected Scotland ID must not become Indiana at another depth."""
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

BASE='https://throughline.51-21-210-47.sslip.io'

async def main():
    results=[]
    async with async_playwright() as p:
        api=await p.request.new_context(base_url=BASE,timeout=45000)
        for depth in [1,2]:
            request={'entityId':'A75E2277-6EDF-4E18-831C-096E806E51AE','name':'Edinburgh','entityType':'destination','depth':depth,'types':['place']}
            response=await api.post('/api/discover',data=request)
            data=await response.json()
            urls=[link.get('url','') for card in data.get('discoveries',[]) for link in card.get('links',[])]
            wrong=[url for url in urls if re.search(r'/in/edinburgh|in-edinburgh',url,re.I)]
            result={'depth':depth,'status':response.status,'selectedId':request['entityId'],'cards':[card['name'] for card in data.get('discoveries',[])],'wrongCountryUrls':wrong,'reason':data.get('reason'),'message':data.get('message')}
            print(json.dumps(result),flush=True)
            results.append(result)
        await api.dispose()
    Path('/tmp/throughline-round15-geography.json').write_text(json.dumps(results,indent=2))
    if any(result['wrongCountryUrls'] for result in results):raise SystemExit(1)

asyncio.run(main())
