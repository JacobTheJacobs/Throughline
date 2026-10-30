"""Fifth live sample: ten unseen query names chosen before provider requests.
Flow checks use isolated browser contexts and actual configured providers.
"""
import asyncio
import json
import random
from playwright.async_api import async_playwright
from live_queries import audit

SEED = 2026102805
POOLS = [
    ("person", [("Wong Kar-wai", {"detail_pattern": "director|filmmaker"}), ("Céline Sciamma", {"detail_pattern": "director|filmmaker"}), ("Park Chan-wook", {"detail_pattern": "director|filmmaker"})]),
    ("person", [("Zadie Smith", {"detail_pattern": "writer|author|novelist"}), ("Neil Gaiman", {"detail_pattern": "writer|author|novelist"}), ("Chinua Achebe", {"detail_pattern": "writer|author|novelist"})]),
    ("artist", [("Portishead", {"detail_pattern": "band"}), ("Sufjan Stevens", {"detail_pattern": "musician|singer|songwriter"}), ("MF DOOM", {"detail_pattern": "rapper|producer|hip.hop"})]),
    ("brand", [("Muji", {}), ("Converse", {}), ("Dyson", {})]),
    ("movie", [("In the Mood for Love", {"year": 2000}), ("Children of Men", {"year": 2006}), ("Amélie", {"year": 2001})]),
    ("book", [("The Road", {"year": 2006}), ("Piranesi", {"year": 2020}), ("The Three-Body Problem", {"year": 2006})]),
    ("video game", [("Outer Wilds", {"year": 2019}), ("Return of the Obra Dinn", {"year": 2018}), ("Undertale", {"year": 2015})]),
    ("tv show", [("Better Call Saul", {"year": 2015}), ("Station Eleven", {"year": 2021}), ("Mr. Robot", {"year": 2015})]),
    ("podcast", [("Freakonomics Radio", {}), ("Heavyweight", {}), ("Hardcore History", {})]),
    ("destination", [("São Paulo", {}), ("Marrakesh", {}), ("Helsinki", {})]),
]


async def main():
    rng = random.Random(SEED)
    cases = [(name, kind, expected) for kind, pool in POOLS for name, expected in [rng.choice(pool)]]
    print(json.dumps({"sample_seed": SEED, "selected_queries": cases, "live_providers": True, "concurrency": 2}, ensure_ascii=False), flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        sem = asyncio.Semaphore(2)

        async def run(index, case):
            async with sem:
                return await audit(browser, index, *case)

        results = await asyncio.gather(*(run(i, c) for i, c in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary": {s: sum(r["status"] == s for r in results) for s in ["FLOW_PASS", "FALLBACK", "FAIL"]}}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
