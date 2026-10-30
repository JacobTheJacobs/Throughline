"""Explicit known alias control: On Running -> On, with Swiss running-brand evidence."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import live_queries

original=live_queries.matches_name
def alias(query,choice):
    return original(query,choice) or (query=='On Running' and choice.get('name')=='On' and choice.get('type')=='brand')
live_queries.matches_name=alias

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        result=await live_queries.audit(browser,4,'On Running','brand',expected={'detail_pattern':'Swiss.*running|running.*Swiss'},entry='form',visuals=True,visual_settle_ms=15000)
        Path('/tmp/throughline-round18-on-alias.json').write_text(json.dumps(result,indent=2))
        print('ALIAS_CONTROL',json.dumps({'status':result['status'],'identity':result.get('chosen_identity'),'cards':[card['name'] for card in result.get('cards',[])],'errors':result['errors']}))
        await browser.close()

asyncio.run(main())
