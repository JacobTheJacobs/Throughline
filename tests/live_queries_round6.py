"""Sixth reproducible live sample: new query names, real providers, isolated browsers."""
import asyncio
import json
import random
import sys
from playwright.async_api import async_playwright
from live_queries import audit, BASE

SEED = 2026102806
POOLS = [
    ("person", [("Céline Sciamma", {"detail_pattern":"director|filmmaker"}), ("Park Chan-wook", {"detail_pattern":"director|filmmaker"}), ("David Cronenberg", {"detail_pattern":"director|filmmaker"})]),
    ("person", [("Chinua Achebe", {"detail_pattern":"writer|author|novelist"}), ("Neil Gaiman", {"detail_pattern":"writer|author|novelist"}), ("Isabel Allende", {"detail_pattern":"writer|author|novelist"})]),
    ("artist", [("Portishead", {"detail_pattern":"band"}), ("Sufjan Stevens", {"detail_pattern":"musician|singer|songwriter"}), ("FKA twigs", {"detail_pattern":"musician|singer|songwriter"})]),
    ("brand", [("Muji",{}), ("Dyson",{}), ("ASICS",{})]),
    ("movie", [("Children of Men",{"year":2006}), ("Amélie",{"year":2001}), ("Ex Machina",{"year":2014})]),
    ("book", [("Piranesi",{"year":2020}), ("The Three-Body Problem",{"year":2006}), ("The Overstory",{"year":2018})]),
    ("video game", [("Outer Wilds",{"year":2019}), ("Undertale",{"year":2015}), ("Journey",{"year":2012})]),
    ("tv show", [("Better Call Saul",{"year":2015}), ("Station Eleven",{"year":2021}), ("The Good Place",{"year":2016})]),
    ("podcast", [("Heavyweight",{}), ("Hardcore History",{}), ("Reply All",{})]),
    ("destination", [("Marrakesh",{}), ("Helsinki",{}), ("Melbourne",{})]),
]


async def main():
    rng=random.Random(SEED)
    cases=[(name,kind,expected) for kind,pool in POOLS for name,expected in [rng.choice(pool)]]
    print(json.dumps({"sample_seed":SEED,"selected_queries":cases,"live_providers":True,"concurrency":2},ensure_ascii=False),flush=True)
    async with async_playwright() as p:
        if "--api-only" in sys.argv:
            api=await p.request.new_context(base_url=BASE,timeout=15000)
            for name,kind,expected in cases:
                response=await api.post('/api/discover',data={"text":name})
                data=await response.json()
                print(json.dumps({"query":name,"intended_type":kind,"expected_identity":expected,"http":response.status,"retry_after":response.headers.get('retry-after'),"data":data,"status":"BLOCKED" if response.status==429 else "API_RESPONSE_ONLY"},ensure_ascii=False),flush=True)
            await api.dispose()
            return
        browser=await p.chromium.launch()
        sem=asyncio.Semaphore(2)

        async def run(index,case):
            async with sem:
                return await audit(browser,index,*case)

        results=await asyncio.gather(*(run(i,c) for i,c in enumerate(cases)))
        await browser.close()
    print(json.dumps({"summary":{s:sum(r["status"]==s for r in results) for s in ["FLOW_PASS","FALLBACK","FAIL"]}}),flush=True)


if __name__=="__main__":
    asyncio.run(main())
