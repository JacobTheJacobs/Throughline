"""Fourth live sample: ten new names, sampled before provider calls."""
import asyncio
import json
import random
from playwright.async_api import async_playwright
from live_queries import audit

POOLS = [
    ("person", [("Sofia Coppola", {"detail_pattern": "director|filmmaker|screenwriter"}), ("David Lynch", {"detail_pattern": "director|filmmaker"}), ("Ridley Scott", {"detail_pattern": "director|filmmaker"})]),
    ("person", [("James Baldwin", {"detail_pattern": "writer|author|novelist"}), ("Kazuo Ishiguro", {"detail_pattern": "writer|author|novelist"}), ("Salman Rushdie", {"detail_pattern": "writer|author|novelist"})]),
    ("artist", [("Radiohead", {"detail_pattern": "band"}), ("Aphex Twin", {"detail_pattern": "musician|producer|electronic"}), ("Massive Attack", {"detail_pattern": "band|group|collective"})]),
    ("brand", [("LEGO", {}), ("Adidas", {}), ("Porsche", {})]),
    ("movie", [("Moonlight", {"year": 2016}), ("Her", {"year": 2013}), ("The Grand Budapest Hotel", {"year": 2014})]),
    ("book", [("Dune", {"year": 1965}), ("Sapiens", {"year": 2011}), ("Solaris", {"year": 1961})]),
    ("video game", [("Disco Elysium", {"year": 2019}), ("Celeste", {"year": 2018}), ("Control", {"year": 2019})]),
    ("tv show", [("Severance", {"year": 2022}), ("Dark", {"year": 2017}), ("Atlanta", {"year": 2016})]),
    ("podcast", [("Hidden Brain", {}), ("Serial", {}), ("No Such Thing As A Fish", {})]),
    ("destination", [("Lisbon", {}), ("Tokyo", {}), ("Berlin", {})]),
]


async def main():
    rng=random.Random(2026102804)
    cases=[(name,kind,expected) for kind,pool in POOLS for name,expected in [rng.choice(pool)]]
    print(json.dumps({"sample_seed":2026102804,"selected_queries":cases,"live_providers":True,"concurrency":2}),flush=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        sem=asyncio.Semaphore(2)

        async def run(i,case):
            async with sem:
                return await audit(browser,i,*case)

        results=await asyncio.gather(*(run(i,c) for i,c in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary":{s:sum(r['status']==s for r in results) for s in ['FLOW_PASS','FALLBACK','FAIL']}}),flush=True)


if __name__=='__main__':
    asyncio.run(main())
