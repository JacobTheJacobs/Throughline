"""Bounded public-asset scan for exact locally configured provider key values.
Never prints values; does not establish whether production uses the same keys.
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

base='https://throughline.51-21-210-47.sslip.io/'
keys=[]
for line in Path('.env.local').read_text().splitlines():
    match=re.match(r'\s*(?:export\s+)?(QLOO_API_KEY|JEV|TYPESAFE_API_KEY)\s*=\s*(.*)',line)
    if match:
        value=match[2].strip().strip('\"\'')
        if len(value)>=12:keys.append(value.encode())
pending=[base];seen=set();matches=0;errors=0
while pending and len(seen)<60:
    url=pending.pop(0)
    if url in seen:continue
    seen.add(url)
    try:
        with urlopen(url,timeout=15) as response:data=response.read(8_000_000)
    except Exception:
        errors+=1;continue
    matches+=sum(key in data for key in keys)
    text=data.decode('utf8',errors='ignore')
    refs=re.findall(r'''(?:src|href)=["']([^"']+)["']''',text)
    refs+=re.findall(r'''["']([^"']+\.m?js(?:\?[^"']*)?)["']''',text)
    for ref in refs:
        target=urljoin(url,ref)
        if urlsplit(target).netloc==urlsplit(base).netloc and re.search(r'\.(?:m?js|css)(?:\?|$)',target) and target not in seen:
            pending.append(target)
print(json.dumps({'assetsFetched':len(seen)-errors,'fetchErrors':errors,'configuredKeyValuesChecked':len(keys),'exactKeyMatches':matches,'remainingQueue':len(pending),'scope':'local key values against bounded public assets; not production-key rotation verification'}))
