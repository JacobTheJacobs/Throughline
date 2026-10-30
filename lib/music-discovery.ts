import {wikidataWorkType} from "./direct-connections.ts";

type Claim={rank?:string;mainsnak?:{datavalue?:{value?:unknown}}};
export type MusicEntity={id?:string;labels?:Record<string,{value:string}>;aliases?:Record<string,Array<{value:string}>>;descriptions?:Record<string,{value:string}>;claims?:Record<string,Claim[]>};
export type MusicWork={id:string;name:string;type:"song"|"album";detail:string;year?:number;performers:Array<{id:string;name:string;musicbrainz?:string}>};
type ReadJson=(url:URL,signal?:AbortSignal)=>Promise<unknown>;
const cache=new Map<string,{expires:number;works:MusicWork[]}>();
const key=(text:string)=>text.normalize("NFD").replace(/\p{M}/gu,"").toLowerCase().replace(/[^\p{L}\p{N}]/gu,"");
const values=(entity:MusicEntity,property:string)=>(entity.claims?.[property]??[]).filter(c=>c.rank!=="deprecated").map(c=>c.mainsnak?.datavalue?.value);
const ids=(entity:MusicEntity,property:string)=>values(entity,property).flatMap(v=>v&&typeof v==="object"&&"id" in v&&/^Q\d+$/.test(String(v.id))?[String(v.id)]:[]);
const api=(params:Record<string,string>)=>{const url=new URL("https://www.wikidata.org/w/api.php");for(const[k,v]of Object.entries({format:"json",...params}))url.searchParams.set(k,v);return url};

// Only exact labels/aliases plus a musical classification and explicit P175 qualify.
// A same-title remix, video, or another performer's recording is never silently substituted.
export function musicalWork(entity:MusicEntity,name:string,performers:Record<string,MusicEntity>):MusicWork|null{
 const names=[...Object.values(entity.labels??{}).map(v=>v.value),...Object.values(entity.aliases??{}).flat().map(v=>v.value)];
 if(!entity.id||!names.some(n=>key(n)===key(name)))return null;
 const description=entity.descriptions?.en?.value??"",type=wikidataWorkType(ids(entity,"P31"),description);
 if(type!=="song"&&type!=="album")return null;
 const people=ids(entity,"P175").slice(0,4).flatMap(id=>{const p=performers[id],label=p?.labels?.en?.value;if(!label)return[];const mb=values(p,"P434").find(v=>typeof v==="string");return[{id,name:label,musicbrainz:typeof mb==="string"?mb:undefined}]});
 if(!people.length)return null;
 const dates=values(entity,"P577").flatMap(v=>v&&typeof v==="object"&&"time" in v?[Number(String(v.time).match(/^\+(\d{4})/)?.[1])]:[]).filter(n=>Number.isFinite(n)&&n>1000);
 return{id:entity.id,name:entity.labels?.en?.value??name,type,detail:`${description}${description?" · ":""}Performed by ${people.map(p=>p.name).join(", ")}`,year:dates.length?Math.min(...dates):undefined,performers:people};
}

export async function verifiedMusicWorks(name:string,read:ReadJson,signal?:AbortSignal,qid?:string):Promise<MusicWork[]>{
 if(qid&&!/^Q\d+$/.test(qid))return[];
 const cacheKey=`${qid??"search"}:${key(name)}`,cached=cache.get(cacheKey);if(cached&&cached.expires>Date.now())return cached.works;
 let wanted=qid&&/^Q\d+$/.test(qid)?[qid]:[];
 if(!wanted.length){const found=await read(api({action:"wbsearchentities",search:name,language:"en",limit:"8"}),signal) as {search?:Array<{id?:string;label?:string}>};wanted=(found.search??[]).filter(v=>v.id&&/^Q\d+$/.test(v.id)&&key(v.label??"")===key(name)).map(v=>v.id!).slice(0,5)}
 if(!wanted.length)return[];
 const data=await read(api({action:"wbgetentities",ids:wanted.join("|"),props:"labels|aliases|descriptions|claims",languages:"en"}),signal) as {entities?:Record<string,MusicEntity>};
 const entities=data.entities??{},people=[...new Set(Object.values(entities).flatMap(e=>ids(e,"P175")))].slice(0,12);
 const performers=people.length?(await read(api({action:"wbgetentities",ids:people.join("|"),props:"labels|claims",languages:"en"}),signal) as {entities?:Record<string,MusicEntity>}).entities??{}:{};
 const works=Object.values(entities).flatMap(e=>{const w=musicalWork(e,name,performers);return w?[w]:[]});
 if(cache.size>300)cache.delete(cache.keys().next().value!);cache.set(cacheKey,{expires:Date.now()+3_600_000,works});return works;
}

export function matchesPerformer(performer:{id:string;musicbrainz?:string},linked:{wikidata?:string;musicbrainz?:string}){
 // The linked Wikidata item is the primary identity used by P175. Qloo can
 // carry an incorrect secondary MusicBrainz ID even when that item is exact.
 // A conflicting primary item never falls through to a weaker MBID match.
 if(linked.wikidata)return linked.wikidata.toUpperCase()===performer.id;
 return!!performer.musicbrainz&&linked.musicbrainz===performer.musicbrainz;
}
