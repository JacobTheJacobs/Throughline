// Shared anchor-relevance gate for every discovery entry point (map, category probe, Discover feed,
// "more like this", agent). One prompt, one evidence shape, one decision rule, cached per anchor.
import {jevScore} from "./jev.ts";
import {qualifiesAnchorMatch} from "./recommendation-ranker.ts";
export type RelevanceItem={id:string;name:string;type:string;description?:string;tags?:string[];affinity?:number;themes?:string};
export type Judgement={subject:number;loose:number};
const judgements=new Map<string,{judgement:Judgement;expires:number}>(),TTL=6*3_600_000;
// Keys hash the evidence itself, so an edited description or tag set is judged again.
function hash(text:string){let h=2166136261;for(let i=0;i<text.length;i++)h=Math.imul(h^text.charCodeAt(i),16777619);return(h>>>0).toString(36)}
export function judgementKey(anchor:RelevanceItem,item:RelevanceItem){return`v2:${anchor.id}:${hash(evidence(anchor,1600))}|${item.id}:${hash(evidence(item,1600))}`}
export type RelevanceResult={scores:Map<string,Judgement>;unjudged:Set<string>};
export function evidence(item:RelevanceItem,max=1600){const description=(item.description??"").replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim().slice(0,max),tags=[...new Set(item.tags??[])].slice(0,8).join(", ");return`${item.name} (${item.type.replaceAll("_"," ")}). Description: ${description||"none"}. Themes: ${(item.themes??"").slice(0,600)||"none"}. Tags: ${tags||"none"}.`}
export function hasEvidence(item:RelevanceItem){return (item.description?.trim().length??0)>=40||(item.themes?.trim().length??0)>=40||(item.tags?.length??0)>=2}
// Judgements are memoised per (anchor evidence, candidate evidence) so repeating a search yields
// the same decisions. `unjudged` lists candidates with evidence that received no score (retryable).
export async function judgeRelevance(anchor:RelevanceItem,candidates:RelevanceItem[],timeoutMs=6000,signal?:AbortSignal):Promise<RelevanceResult|null>{
 const now=Date.now(),out=new Map<string,Judgement>(),withEvidence=[...new Map(candidates.filter(item=>hasEvidence(item)).map(item=>[item.id,item])).values()],missing=withEvidence.filter(item=>{const cached=judgements.get(judgementKey(anchor,item));if(cached&&cached.expires>now){out.set(item.id,cached.judgement);return false}return true}).sort((a,b)=>a.id<b.id?-1:1),asked=missing.slice(0,108),unjudged=()=>new Set(withEvidence.filter(item=>!out.has(item.id)).map(item=>item.id));
 if(!asked.length)return{scores:out,unjudged:unjudged()};
 // Large probes are judged in parallel chunks of 36 so every candidate gets a decision.
 const chunks=Array.from({length:Math.ceil(asked.length/36)},(_,index)=>asked.slice(index*36,index*36+36)),results=await Promise.all(chunks.map(chunk=>judgeChunk(anchor,chunk,timeoutMs,signal)));
 if(results.every(result=>!result))return out.size?{scores:out,unjudged:unjudged()}:null;
 for(const result of results)for(const[id,judgement]of result??[]){out.set(id,judgement);const item=asked.find(candidate=>candidate.id===id)!;if(judgements.size>5000)judgements.delete(judgements.keys().next().value!);judgements.set(judgementKey(anchor,item),{judgement,expires:now+TTL})}
 return{scores:out,unjudged:unjudged()};
}
async function judgeChunk(anchor:RelevanceItem,asked:RelevanceItem[],timeoutMs:number,signal?:AbortSignal){
 const scores=await jevScore(`Reference: ${evidence(anchor)} Judge only the supported connections to THIS reference. Read the full descriptions, including their endings. Saved preferences, popularity and audience overlap are irrelevant. Concrete gameplay systems (procedural runs, death/retry progression, combat systems), destructive mentorship/performance pressure, and cross-cultural political or anthropological ideas can be distinctive connections; they are not merely format labels. "Both games", "both dramas", "both documentaries", mood or a genre name alone are not sufficient. Do not infer factual credits or adaptations.`,Object.fromEntries(asked.flatMap((item,index)=>[[`s${index}`,`Candidate: "${evidence(item)}" Does the supplied evidence establish a concrete, nameable shared subject, setting, central idea, distinctive craft, or gameplay system? Consider the actual content rather than requiring the identical plot. Score low if only a general genre, mood or audience is shared.`],[`l${index}`,`Candidate: "${evidence(item)}" Is the connection ONLY a broad genre/format/mood/audience label, with NO supported distinctive shared subject, idea, craft or gameplay system? If the descriptions support a specific connection, this answer must be low even if they also share a genre. If they share nothing meaningful, answer high.`]])),timeoutMs,signal);
 if(!scores)return null;
 const out=new Map<string,Judgement>();asked.forEach((item,index)=>{const subject=scores[`s${index}`],loose=scores[`l${index}`];if(subject!==undefined&&loose!==undefined)out.set(item.id,{subject,loose})});
 return out;
}
export function qualifies(item:RelevanceItem,judgement:Judgement|undefined){return hasEvidence(item)&&qualifiesAnchorMatch(item.affinity,judgement?.subject,judgement?.loose)}
