"""Ten additional, stratified random live cases; never replace a failed sample."""
import asyncio
import json
import random
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ("person", ["Greta Gerwig", "Bong Joon-ho", "Sofia Coppola"]),
    ("person", ["Octavia E. Butler", "James Baldwin", "Haruki Murakami"]),
    ("artist", ["Nina Simone", "Radiohead", "Daft Punk"]),
    ("brand", ["LEGO", "Adidas", "IKEA", "Porsche"]),
    ("movie", ["Moonlight", "Arrival", "The Grand Budapest Hotel"]),
    ("book", ["Dune", "Sapiens", "The Dispossessed"]),
    ("video game", ["Portal 2", "Disco Elysium", "Elden Ring"]),
    ("tv show", ["Severance", "Succession"]),
    ("podcast", ["Radiolab", "The Moth"]),
    ("destination", ["Kyoto", "Lisbon", "Japan", "Iceland"]),
]


async def main():
    rng = random.Random(2026102802)
    cases = [(rng.choice(pool), kind) for kind, pool in POOLS]
    print(json.dumps({"sample_seed": 2026102802, "selected_queries": cases, "live_providers": True, "concurrency": 2}), flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        sem = asyncio.Semaphore(2)

        async def run(i, case):
            async with sem:
                return await audit(browser, i, *case)

        results = await asyncio.gather(*(run(i, case) for i, case in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary": {s: sum(r["status"] == s for r in results) for s in ["FLOW_PASS", "FALLBACK", "FAIL"]}}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
