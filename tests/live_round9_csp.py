"""Isolated browser compatibility test of the configured policy, not a deployment claim."""
import asyncio,html,json,re
from pathlib import Path
from playwright.async_api import async_playwright
from live_queries import BASE

async def main():
 source=Path('next.config.ts').read_text()
 policy=re.search(r'"(default-src[^"\n]+)"',source).group(1)
 images={
  'new-identity-bound-cover':'https://coverartarchive.org/release-group/bded1701-baf2-4066-b76a-49384de006b6/front-250',
  'existing-qloo-control':'https://images.qloo.com/i/702E1246-C2FD-4638-BA18-E05299F03A89-160x-auto.webp',
 }
 async with async_playwright() as p:
  browser=await p.chromium.launch();page=await browser.new_page();failures=[];errors=[]
  response=await page.goto(BASE)
  actual_policy=response.headers.get('content-security-policy')
  # A blank isolated page avoids React replacing the diagnostic markup.
  await page.close();page=await browser.new_page()
  page.on('requestfailed',lambda r:failures.append({'url':r.url,'failure':r.failure}) if r.resource_type=='image' else None)
  page.on('console',lambda m:errors.append(m.text[:800]) if m.type=='error' else None)
  markup='<html><head><meta http-equiv="Content-Security-Policy" content="'+html.escape(policy,quote=True)+'"></head><body>'
  markup+=''.join('<img id="'+name+'" src="'+html.escape(url,quote=True)+'">' for name,url in images.items())+'</body></html>'
  await page.set_content(markup)
  try:await page.wait_for_function('[...document.images].every(i=>i.complete)',timeout=15000)
  except Exception as error:
   if type(error).__name__!='TimeoutError':raise
  result=await page.locator('img').evaluate_all('els=>els.map(i=>({id:i.id,src:i.currentSrc,complete:i.complete,width:i.naturalWidth}))')
  print(json.dumps({'kind':'controlled-configured-policy-check','live_response_policy':actual_policy,'configured_policy':policy,'images':result,'failures':failures,'console':errors}),flush=True)
  await browser.close()

asyncio.run(main())
