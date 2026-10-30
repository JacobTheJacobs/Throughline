"""Ten new reproducible live cases. Browser success is not a relevance verdict."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ('artist', ['Mitski', 'Khruangbin', 'Beach House']),
    ('artist', ['Nick Cave & The Bad Seeds', 'LCD Soundsystem', 'Sade']),
    ('person', ['Alfonso Cuarón', 'Pedro Almodóvar', 'Yorgos Lanthimos']),
    ('person', ['Terry Pratchett', 'Jorge Luis Borges', 'Diana Wynne Jones']),
    ('brand', ['Oatly', 'Carhartt', 'Bang & Olufsen']),
    ('movie', ['Portrait of a Lady on Fire', 'The Florida Project', 'Good Will Hunting']),
    ('book', ['The Handmaid’s Tale', 'The Master and Margarita', 'American Gods']),
    ('video game', ['Subnautica', 'Baldur’s Gate 3', 'Spiritfarer']),
    ('tv show', ['Reservation Dogs', 'Station Eleven', 'BoJack Horseman']),
    ('destination', ['Copenhagen', 'Edinburgh', 'Dubrovnik']),
]

async def main():
    rng=random.Random(2026102914)
    cases=[(rng.choice(pool),kind) for kind,pool in POOLS]
    print(json.dumps({'seed':2026102914,'queries':cases},ensure_ascii=False),flush=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        semaphore=asyncio.Semaphore(2)
        async def run(index,case):
            async with semaphore:
                return await audit(browser,index,*case,entry='form',visuals=True,visual_settle_ms=10000)
        results=await asyncio.gather(*(run(i,case) for i,case in enumerate(cases)))
        await browser.close()
    Path('/tmp/throughline-round14-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
    print(json.dumps({'summary':{status:sum(x['status']==status for x in results) for status in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)

if __name__=='__main__':
    asyncio.run(main())
