"""Bounded real endpoint regressions and identity-control checks; no quota bypass."""
import asyncio
import json
from playwright.async_api import async_playwright
from live_queries import BASE


def compact(data):
    out = {k: data[k] for k in ["mode", "reason", "message", "availability", "coverage", "question", "seed", "defaultIntent"] if k in data}
    if "choices" in data:
        out["choices"] = [{k: c.get(k) for k in ["id", "name", "type", "year", "externalId"]} for c in data["choices"]]
    if "discoveries" in data:
        out["discoveries"] = [{k: c.get(k) for k in ["id", "name", "type", "relation", "reason", "reasonSource", "links"]} for c in data["discoveries"]]
    return out


async def main():
    async with async_playwright() as p:
        api = await p.request.new_context(base_url=BASE, timeout=45000)
        cases = [(q,{"text":q}) for q in ["The Jungle Book","The Artist","Up movie","U2 band","Iceland country"]]
        cases += [
            ("Aphex direct identity repair",{"entityId":"4278382F-4991-4D63-B207-942D86A26ACB","name":"Aphex Twin","entityType":"artist","intent":"direct","externalSource":"wikidata","externalId":"Q97228784"}),
            ("Ishiguro source-role repair",{"entityId":"C4461C94-721C-4A32-8CB2-4DCCB9370FA4","name":"Kazuo Ishiguro","entityType":"person","intent":"direct","externalSource":"imdb","externalId":"nm0410958"}),
            ("Disco edition exclusion",{"entityId":"BF4E74F3-8495-4962-B988-1F0E5BF28453","name":"Disco Elysium","entityType":"video_game"}),
            ("Her explicit type",{"text":"Her","preferType":"movie"}),
        ]
        road={"entityId":"B248BC9F-15C3-424F-AC89-DDBC1D94915A","name":"The Road","entityType":"book","types":["movie"],"probeTypes":True,"strictType":True,"depth":2,"limit":5}
        cases += [("Road raw edition identity",road),("Road corrected identity existing cache key",{**road,"externalSource":"wikidata","externalId":"Q1140295"}),("Road corrected identity other category key",{**road,"externalSource":"wikidata","externalId":"Q1140295","types":["movie","tv_show"]})]
        for label, body in cases:
            response = await api.post('/api/discover',data=body)
            print(json.dumps({"label":label,"request":body,"http":response.status,"data":compact(await response.json())},ensure_ascii=False),flush=True)
        response = await api.post('/api/card',data='null',headers={'content-type':'application/json'})
        print(json.dumps({"label":"null card","http":response.status,"text":await response.text()}),flush=True)
        await api.dispose()


if __name__=='__main__':
    asyncio.run(main())
