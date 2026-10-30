"""Third ten-query sample. Seed and identity expectations fixed before requests."""
import asyncio
import json
import random
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ("person", [("Greta Gerwig", {"detail_pattern": "director|filmmaker|actress"}), ("Sofia Coppola", {"detail_pattern": "director|filmmaker|screenwriter"})]),
    ("person", [("Octavia E. Butler", {"detail_pattern": "writer|author"}), ("James Baldwin", {"detail_pattern": "writer|author|essayist|novelist"})]),
    ("artist", [("Radiohead", {"detail_pattern": "band"}), ("Daft Punk", {"detail_pattern": "duo|electronic"}), ("Aphex Twin", {"detail_pattern": "musician|electronic|producer"})]),
    ("brand", [("LEGO", {}), ("Adidas", {}), ("Porsche", {}), ("Uniqlo", {})]),
    ("movie", [("Moonlight", {"year": 2016}), ("The Grand Budapest Hotel", {"year": 2014}), ("Everything Everywhere All at Once", {"year": 2022})]),
    ("book", [("Dune", {"year": 1965}), ("Sapiens", {"year": 2011}), ("Neuromancer", {"year": 1984})]),
    ("video game", [("Disco Elysium", {"year": 2019}), ("Elden Ring", {"year": 2022}), ("Celeste", {"year": 2018})]),
    ("tv show", [("Severance", {"year": 2022}), ("The Bear", {"year": 2022})]),
    ("podcast", [("The Moth", {}), ("Hidden Brain", {})]),
    ("destination", [("Lisbon", {}), ("Japan", {}), ("Iceland", {})]),
]


async def main():
    rng = random.Random(2026102803)
    cases = [(query, kind, expected) for kind, pool in POOLS for query, expected in [rng.choice(pool)]]
    print(json.dumps({"sample_seed": 2026102803, "selected_queries": cases, "live_providers": True, "concurrency": 2}), flush=True)
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
