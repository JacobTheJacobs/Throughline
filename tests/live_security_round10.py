"""Bounded public-route checks. No credential values or real user state collected."""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.environ.get('SIDEWAYS_BASE', 'https://throughline.51-21-210-47.sslip.io')

async def main():
    results = []
    async with async_playwright() as p:
        api = await p.request.new_context(base_url=BASE)
        for path in ['/.env', '/.env.local', '/.git/config', '/server.js', '/package.json', '/app.env', '/api/discover', '/api/agent']:
            r = await api.get(path)
            results.append({'probe': path, 'status': r.status, 'blocked': r.status in [400, 404, 405]})
        for route in ['discover', 'agent', 'card', 'suggestions']:
            r = await api.post('/api/'+route, data='null', headers={'content-type':'application/json'})
            results.append({'probe':route+' null body', 'status':r.status, 'blocked':r.status==400})
        r = await api.post('/api/discover', data='{}', headers={'content-type':'application/json','origin':'https://evil.example'})
        results.append({'probe':'foreign origin','status':r.status,'blocked':r.status==403})
        r = await api.post('/api/discover', data=json.dumps({'text':'x','padding':'a'*66000}), headers={'content-type':'application/json'},timeout=10000)
        results.append({'probe':'oversized discover body','status':r.status,'blocked':r.status in [400,413]})
        await api.dispose()
    Path('/tmp/throughline-security-round10.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))
    assert all(r['blocked'] for r in results), 'A security probe failed'

asyncio.run(main())
