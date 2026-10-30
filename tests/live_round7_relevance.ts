// Live full-evidence rerun. No mocked scores; negatives are explicitly crossed controls.
import {readFileSync} from "node:fs";
import ts from "typescript";
import {judgeRelevance,qualifies,type RelevanceItem} from "../lib/relevance.ts";
type Fixture={query:string;seed:{id:string;name:string;type:string};positive:RelevanceItem;negative:RelevanceItem};
const fixtures=JSON.parse(readFileSync(process.env.ROUND7_FIXTURES||"/tmp/sideways-round7-relevance-fixtures.json","utf8")) as Fixture[];
const route=readFileSync(new URL("../app/api/discover/route.ts",import.meta.url),"utf8");
const helperSource=["const WEAK_TAG=","function topTags("].map(prefix=>{const line=route.split("\n").find(line=>line.startsWith(prefix));if(!line)throw new Error(`Missing production helper ${prefix}`);return line}).join("\n");
const topTags=new Function(ts.transpileModule(helperSource,{compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText+"\nreturn topTags;")() as (entity:Record<string,unknown>)=>string[];
const key=process.env.QLOO_API_KEY;if(!key||!(process.env.JEV||process.env.TYPESAFE_API_KEY))throw new Error("Provider credentials missing");
const stamp=Date.now();let missing=0,mismatches=0;
for(const [index,fixture] of fixtures.entries()){
 const records=[fixture.seed,fixture.positive,fixture.negative];
 const url=new URL("/entities",process.env.QLOO_BASE_URL||"https://hackathon.api.qloo.com");url.searchParams.set("entity_ids",records.map(r=>r.id).join(","));
 const response=await fetch(url,{headers:{"X-Api-Key":key},signal:AbortSignal.timeout(10000)});
 if(!response.ok)throw new Error(`Qloo entity hydration ${response.status}`);
 const payload=await response.json() as {results?:any};/* eslint-disable-line @typescript-eslint/no-explicit-any */const entities=Array.isArray(payload.results)?payload.results:payload.results?.entities||[];
 const evidence=records.map(record=>{
  const entity=entities.find((item:{entity_id:string})=>item.entity_id===record.id);if(!entity)throw new Error(`Missing ${record.id}`);
  return {...record,tags:topTags(entity).slice(0,8),description:entity.properties?.description||entity.properties?.short_description||entity.properties?.short_descriptions?.[0]?.value,themes:entity.properties?.plot_themes_description} as RelevanceItem;
 });
 const [anchor,...candidates]=evidence;for(const item of candidates)item.affinity=.95;
 for(let run=0;run<2;run++){
  const scores=await judgeRelevance({...anchor,id:`${anchor.id}#round7-${stamp}-${index}-${run}`},candidates);
  for(const [i,item] of candidates.entries()){
   const judgement=scores?.scores.get(item.id),accepted=qualifies(item,judgement),expected=i===0;
   if(!judgement)missing++;else if(accepted!==expected)mismatches++;
   console.log(JSON.stringify({query:fixture.query,anchor,candidate:item,run,judgement,accepted,expected}));
  }
 }
}
console.log(JSON.stringify({summary:{fixtures:fixtures.length,decisions:fixtures.length*4,missing,mismatches},scope:"Real Qloo full metadata plus production topTags; actual JEV; affinity fixed .95; crossed negative controls, not a measured population accuracy"}));
process.exitCode=missing||mismatches?1:0;
