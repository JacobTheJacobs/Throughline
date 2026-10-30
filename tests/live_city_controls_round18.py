"""Real literal-city-name controls; preserve choices/details for semantic review."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
 rows=[]
 async with async_playwright() as p:
  api=await p.request.new_context(base_url='https://throughline.51-21-210-47.sslip.io',timeout=45000)
  for text in ['Québec City','Berlin city','Edinburgh city','Freitag brand']:
   response=await api.post('/api/discover',data={'text':text})
   data=await response.json()
   row={'query':text,'http':response.status,'mode':data.get('mode'),'reason':data.get('reason'),'question':data.get('question'),'message':data.get('message'),'seed':data.get('seed'),'choices':data.get('choices',[]),'cards':[{'name':card['name'],'description':card.get('description'),'links':card.get('links')} for card in data.get('discoveries',[])]}
   rows.append(row)
   print(json.dumps(row,ensure_ascii=False),flush=True)
  await api.dispose()
 Path('/tmp/throughline-round18-city-controls.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))

asyncio.run(main())
