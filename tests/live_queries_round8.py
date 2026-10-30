"""Ten fresh seeded live queries, including missing art/graph regression observations."""
import asyncio
import json
import random
import sys
from playwright.async_api import async_playwright
from live_queries import audit

SEED = 2026102808
POOLS = [
    ("artist", [("Janelle Monáe",{}),("Sade",{}),("Kraftwerk",{})]),
    ("artist", [("Adele",{}),("Lorde",{}),("Rosalía",{})]),
    ("person", [("Pedro Almodóvar",{"detail_pattern":"director|filmmaker"}),("Akira Kurosawa",{"detail_pattern":"director|filmmaker"}),("Agnès Varda",{"detail_pattern":"director|filmmaker"})]),
    ("person", [("N. K. Jemisin",{"detail_pattern":"writer|author|novelist"}),("Hilary Mantel",{"detail_pattern":"writer|author|novelist"}),("Italo Calvino",{"detail_pattern":"writer|author|novelist"})]),
    ("brand", [("Fjällräven",{}),("Oatly",{}),("Lush",{})]),
    ("movie", [("Perfect Days",{"year":2023}),("Portrait of a Lady on Fire",{"year":2019}),("Brazil",{"year":1985})]),
    ("book", [("Braiding Sweetgrass",{"year":2013}),("Annihilation",{"year":2014}),("The Master and Margarita",{"year":1967})]),
    ("video game", [("Return of the Obra Dinn",{"year":2018}),("Celeste",{"year":2018}),("Slay the Spire",{"year":2019})]),
    ("podcast", [("Song Exploder",{}),("The Allusionist",{}),("Ologies",{})]),
    ("destination", [("Valparaíso",{}),("Bergen",{"detail_pattern":"Norway|Norwegian"}),("Ljubljana",{})]),
]


async def main():
    rng=random.Random(SEED)
    cases=[(name,kind,expected) for kind,pool in POOLS for name,expected in [rng.choice(pool)]]
    print(json.dumps({"sample_seed":SEED,"selected_queries":cases,"real_providers":True,"visual_checks":True,"concurrency":2},ensure_ascii=False),flush=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        sem=asyncio.Semaphore(2)
        async def run(i,case):
            async with sem:
                return await audit(browser,i,*case,visuals=True)
        if "--artists-via-form" in sys.argv:
            async def form_run(i,case):
                async with sem:
                    return await audit(browser,i,*case,visuals=True,entry="form")
            results=await asyncio.gather(*(form_run(i,c) for i,c in enumerate(cases) if c[1]=="artist"))
        else:
            results=await asyncio.gather(*(run(i,c) for i,c in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary":{s:sum(r['status']==s for r in results) for s in ['FLOW_PASS','FALLBACK','FAIL']},"visual_summary":{"checked":sum('visuals' in r for r in results),"with_issues":sum(bool(r.get('visual_issues')) for r in results)}},ensure_ascii=False),flush=True)
    # A functional save/reload flow must not mask a visually empty graph or missing covers.
    if any(r['status']=='FAIL' or r.get('visual_issues') for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    asyncio.run(main())
