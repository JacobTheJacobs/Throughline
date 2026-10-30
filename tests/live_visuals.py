"""Rendered artwork and graph evidence; no mocked requests or replacement images."""
from browser_wait import wait_until


async def capture_visuals(page, settle_ms=0):
    # Keep immediate snapshots available, but allow audits to distinguish a
    # pending download from failed/missing art using a bounded real load wait.
    if settle_ms:
        try:
            await wait_until(page,
                "[...document.querySelectorAll('.town-image img')].every(i=>i.complete)",
                timeout=settle_ms,
            )
        except Exception as error:
            if type(error).__name__ != "TimeoutError":
                raise
    return await page.evaluate("""()=>{
      const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth&&r.bottom>0&&r.top<innerHeight};
      const cards=[...document.querySelectorAll('.town-card')].map(el=>({id:el.dataset.nodeId,type:el.dataset.type,name:el.querySelector('.hover-caption strong')?.textContent||el.innerText,visible:visible(el),images:[...el.querySelectorAll('.town-image img')].map(i=>({src:i.currentSrc||i.getAttribute('src'),complete:i.complete,width:i.naturalWidth,visible:visible(i),state:!i.complete?'pending':i.naturalWidth>0?'loaded':'failed'}))}));
      const edges=[...document.querySelectorAll('.world-lines g.branch')].map(el=>{const path=el.querySelector('path'),s=path?getComputedStyle(path):null;return{parent:el.dataset.parentId,child:el.dataset.childId,visible:!!path&&visible(path)&&s.display!=='none'&&Number(s.opacity)>0,stroke:s?.stroke,opacity:s?.opacity}});
      return{cards,edges,cardCount:cards.length,cardsWithArtwork:cards.filter(c=>c.images.some(i=>i.state==='loaded')).length,cardsWithoutImageElement:cards.filter(c=>!c.images.length).length,pendingImages:cards.flatMap(c=>c.images).filter(i=>i.state==='pending').length,failedImages:cards.flatMap(c=>c.images).filter(i=>i.state==='failed').length,visibleEdgeCount:edges.filter(e=>e.visible).length,edgeCount:edges.length,seedHidden:[...document.querySelectorAll('.seed-card')].every(el=>!visible(el)),overflow:document.documentElement.scrollWidth>innerWidth};
    }""")
