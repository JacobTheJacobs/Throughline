// Small, live JEV semantic regression using actual round-five returned candidates.
// Negative pairs cross two returned records; they are not claimed to be Qloo suggestions.
// Usage: node --env-file=.env.local --experimental-strip-types --no-warnings tests/live_round5_relevance.ts
import {readFileSync} from "node:fs";
import {judgeRelevance,qualifies,type RelevanceItem} from "../lib/relevance.ts";
type Fixture={query:string;seed:{id:string;name:string;type:string};positive:RelevanceItem;negative:RelevanceItem};
const fixtures=JSON.parse(readFileSync(process.env.ROUND5_FIXTURES||"/tmp/sideways-round5-relevance-fixtures.json","utf8")) as Fixture[];
if(!process.env.QLOO_API_KEY||!(process.env.JEV||process.env.TYPESAFE_API_KEY))throw new Error("Live provider credentials are not configured");
const stamp=Date.now();let failed=0,mismatches=0;
for(const [i,fixture] of fixtures.entries()){
 const url=new URL("/entities",process.env.QLOO_BASE_URL||"https://hackathon.api.qloo.com");url.searchParams.set("entity_ids",fixture.seed.id);
 const response=await fetch(url,{headers:{"X-Api-Key":process.env.QLOO_API_KEY!},signal:AbortSignal.timeout(10000)});
 if(!response.ok){console.log(JSON.stringify({kind:"anchor-unavailable",query:fixture.query,http:response.status}));failed++;continue}
 const data=await response.json() as {results?:any}; // eslint-disable-line @typescript-eslint/no-explicit-any
 const entities=Array.isArray(data.results)?data.results:data.results?.entities||[];
 const entity=entities.find((item:{entity_id:string})=>item.entity_id===fixture.seed.id);
 if(!entity){console.log(JSON.stringify({kind:"anchor-missing",query:fixture.query}));failed++;continue}
 const anchor:RelevanceItem={...fixture.seed,description:entity.properties?.description||entity.properties?.short_description||entity.properties?.short_descriptions?.[0]?.value,themes:entity.properties?.plot_themes_description,tags:(entity.tags||[]).map((t:{name:string})=>t.name).slice(0,8)};
 const candidates=[fixture.positive,fixture.negative].map(item=>({...item,affinity:.95}));
 for(let run=0;run<2;run++){
  const result=await judgeRelevance({...anchor,id:`${anchor.id}#round5-${stamp}-${i}-${run}`},candidates);
  for(let j=0;j<candidates.length;j++){
   const item=candidates[j],judgement=result?.scores.get(item.id),expected=j===0,accepted=qualifies(item,judgement);
   if(!judgement)failed++;else if(accepted!==expected)mismatches++;
   console.log(JSON.stringify({query:fixture.query,anchor,candidate:{id:item.id,name:item.name,type:item.type},run,expected,judgement,accepted,scored:!!judgement}));
  }
 }
}
console.log(JSON.stringify({summary:{fixtures:fixtures.length,pairs:fixtures.length*2,runsPerPair:2,failed,mismatches},scope:"semantic gate only; affinity fixed at .95; cross-paired negatives"}));
process.exitCode=failed||mismatches?1:0;
