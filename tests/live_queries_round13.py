"""Ten fresh stratified live searches; no provider mocks. Flow != relevance proof."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ('artist', ['Massive Attack', 'PJ Harvey', 'Cocteau Twins']),
    ('artist', ['David Bowie', 'Beyoncé', 'Talking Heads']),
    ('person', ['David Lynch', 'Wong Kar-wai', 'Agnès Varda']),
    ('person', ['Ted Chiang', 'George Orwell', 'Virginia Woolf']),
    ('brand', ['Aesop', 'New Balance', 'Lacoste']),
    ('movie', ['Aftersun', 'Amélie', 'Pan’s Labyrinth']),
    ('book', ['The Road', 'The Name of the Rose', 'The Hobbit']),
    ('video game', ['Hollow Knight', 'Undertale', 'Journey']),
    ('tv show', ['Twin Peaks', 'The Wire', 'Black Mirror']),
    ('destination', ['Tallinn', 'Bergen', 'Porto']),
]

async def main():
    rng = random.Random(2026102913)
    cases = [(rng.choice(pool), kind) for kind, pool in POOLS]
    print(json.dumps({'seed': 2026102913, 'queries': cases}), flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        sem = asyncio.Semaphore(2)
        async def run(index, case):
            async with sem:
                return await audit(browser, index, *case, visuals=True, entry='form', visual_settle_ms=10000)
        results = await asyncio.gather(*(run(i, c) for i, c in enumerate(cases)))
        await browser.close()
    Path('/tmp/throughline-round13-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps({'summary': {s: sum(r['status'] == s for r in results) for s in ['FLOW_PASS', 'FALLBACK', 'FAIL']}}), flush=True)

if __name__ == '__main__':
    asyncio.run(main())
