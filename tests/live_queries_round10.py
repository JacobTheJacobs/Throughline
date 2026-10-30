"""Reproducible production browser audit: ten new queries, real providers."""
import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ('artist', ['Portishead', 'FKA twigs', 'Sufjan Stevens']),
    ('artist', ['Kate Bush', 'Ryuichi Sakamoto', 'Janelle Monáe']),
    ('person', ['Céline Sciamma', 'Akira Kurosawa', 'Park Chan-wook']),
    ('person', ['Kazuo Ishiguro', 'Italo Calvino', 'N. K. Jemisin']),
    ('brand', ['Muji', 'Fjällräven', 'Dyson']),
    ('movie', ['Perfect Days', 'Past Lives', 'The Lighthouse']),
    ('book', ['Piranesi', 'The Secret History', 'Never Let Me Go']),
    ('video game', ['Outer Wilds', 'Return of the Obra Dinn', 'Celeste']),
    ('tv show', ['Atlanta', 'The Bear', 'Dark']),
    ('destination', ['Helsinki', 'Ljubljana', 'Valparaíso']),
]

async def main():
    rng = random.Random(2026102910)
    cases = [(rng.choice(pool), kind) for kind, pool in POOLS]
    print(json.dumps({'seed': 2026102910, 'queries': cases}), flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        sem = asyncio.Semaphore(2)
        async def run(index, case):
            async with sem:
                return await audit(browser, index, *case, visuals=True, entry='form', visual_settle_ms=15000)
        results = await asyncio.gather(*(run(i, c) for i, c in enumerate(cases)))
        await browser.close()
    Path('/tmp/throughline-round10-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps({'summary': {s: sum(r['status'] == s for r in results) for s in ['FLOW_PASS', 'FALLBACK', 'FAIL']}, 'art_issues': sum(bool(r.get('visual_issues')) for r in results)}), flush=True)
    if any(r['status']=='FAIL' for r in results):
        raise SystemExit(1)

if __name__ == '__main__':
    asyncio.run(main())
