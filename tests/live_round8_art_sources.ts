// Bounded provider/source diagnostics for three of the actual missing Katy Perry covers.
const cases=[{name:"Witness",qid:"Q29948806"},{name:"Teenage Dream",qid:"Q186188"},{name:"I Kissed a Girl",qid:"Q155512"}];
const key=process.env.QLOO_API_KEY;if(!key)throw new Error("Qloo is not configured");
const wiki=new URL("https://www.wikidata.org/w/api.php");for(const[k,v]of Object.entries({action:"wbgetentities",ids:cases.map(c=>c.qid).join("|"),props:"claims|labels|descriptions",languages:"en",format:"json"}))wiki.searchParams.set(k,v);
const wr=await fetch(wiki,{headers:{"user-agent":"SidewaysAudit/1.0"},signal:AbortSignal.timeout(10000)});if(!wr.ok)throw new Error(`Wikidata ${wr.status}`);const wd=await wr.json();
for(const item of cases){
 const u=new URL("/search",process.env.QLOO_BASE_URL||"https://hackathon.api.qloo.com");u.searchParams.set("query",item.name);u.searchParams.set("take","8");
 const r=await fetch(u,{headers:{"X-Api-Key":key},signal:AbortSignal.timeout(10000)});if(!r.ok)throw new Error(`Qloo ${r.status}`);const d=await r.json(),entities=Array.isArray(d.results)?d.results:d.results?.entities||[],w=wd.entities?.[item.qid];
 console.log(JSON.stringify({query:item.name,qid:item.qid,wikidata:{label:w?.labels?.en?.value,description:w?.descriptions?.en?.value,art:(w?.claims?.P18||[]).map((x:{mainsnak?:{datavalue?:{value:unknown}}})=>x.mainsnak?.datavalue?.value),releaseGroups:(w?.claims?.P436||[]).map((x:{mainsnak?:{datavalue?:{value:unknown}}})=>x.mainsnak?.datavalue?.value)},qloo:entities.map((e:{entity_id:string;name:string;type?:string;subtype?:string;types?:string[];external?:unknown;properties?:{image?:{url:string};description?:string;short_description?:string;external?:unknown}})=>({id:e.entity_id,name:e.name,type:e.subtype||e.types||e.type,image:e.properties?.image?.url,description:e.properties?.description||e.properties?.short_description,external:e.external||e.properties?.external}))}));
}
