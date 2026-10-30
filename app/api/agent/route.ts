import {guard,readJson} from "@/lib/guard";
import {jevScore as scoreWithJev} from "@/lib/jev";
import {POST as discoverRoute} from "../discover/route";
// Explore-for-me agent. /api/discover applies the shared anchor-relevance gate; JEV here only ranks
// which branch to grow and orders the already-qualified candidates by taste;
// target categories follow a fixed cross-domain order, and log lines are templates.
type MapCard={parentId?:string;affinity?:number;id:string;name:string;type:string;depth:number;liked?:boolean;expanded?:boolean;tags?:string[];description?:string;image?:string;parentName?:string;available?:string[];unavailable?:string[]};
type AgentRequest={root:{id:string;name:string;type:string};purpose?:"creative"|"audience"|"personal";cards:MapCard[];likes:Array<{id:string;name?:string;type:string;tags:string[]}>;dislikes:Array<{id:string;name?:string;type:string;tags:string[]}>;excludeIds:string[];steps?:number;memory?:unknown;excludeWorks?:unknown};
type Candidate={id:string;name:string;type:string;description?:string;tags?:string[];affinity?:number;relevance?:number;reason?:string;reasonSource?:string;image?:string};
type Category="movie"|"tv_show"|"artist"|"book"|"podcast"|"video_game"|"place"|"destination"|"brand"|"person";
const CATEGORIES:Category[]=["movie","tv_show","artist","book","podcast","video_game","place","destination","brand","person"];
const LABEL:Record<Category,string>={movie:"films",tv_show:"TV shows",artist:"artists",book:"books",podcast:"podcasts",video_game:"games",place:"places",destination:"destinations",brand:"brands",person:"people"};
const SINGULAR:Record<Category,string>={movie:"film",tv_show:"TV show",artist:"artist",book:"book",podcast:"podcast",video_game:"game",place:"place",destination:"destination",brand:"brand",person:"person"};
const MAX_REVEALS=5;

function canonicalType(value=""){const type=value.replace("urn:entity:","").replaceAll("_"," ").trim().toLocaleLowerCase();if(type.includes("video game")||type==="videogame"||type==="game")return"video_game";if(type.includes("tv show")||type==="tv"||type==="show"||type==="series")return"tv_show";if(type.includes("movie")||type==="film")return"movie";if(type.includes("artist")||type.includes("musician"))return"artist";if(type.includes("book")||type.includes("publication"))return"book";if(type.includes("podcast"))return"podcast";if(type.includes("destination"))return"destination";if(type.includes("place"))return"place";if(type.includes("person")||type.includes("people"))return"person";if(type.includes("brand"))return"brand";return type.replaceAll(" ","_")}
function category(value?:string):Category|undefined{const type=canonicalType(value);return CATEGORIES.find(item=>item===type)}
function tasteSummary(body:AgentRequest){
 const count=(items:AgentRequest["likes"])=>Object.entries(items.reduce<Record<string,number>>((acc,item)=>{acc[item.type]=(acc[item.type]||0)+1;return acc},{})).map(([type,n])=>`${type}×${n}`).join(", ")||"none";
 const tags=(items:AgentRequest["likes"])=>[...new Set(items.flatMap(item=>item.tags))].slice(0,10).join(", ")||"none";
 const names=(items:AgentRequest["likes"])=>items.map(item=>item.name||body.cards.find(card=>card.id===item.id)?.name||item.id).join(", ");
 const goal=body.purpose==="audience"?"Map the audience's cultural affinities with useful, explainable evidence.":body.purpose==="personal"?"Follow personal curiosity while keeping the results relevant and surprising.":"Build a culturally coherent creative territory with useful references across multiple media categories.";
 return `Research goal: ${goal} Loved items: ${names(body.likes)||"none"}; categories: ${count(body.likes)}; themes: ${tags(body.likes)}. Rejected items: ${names(body.dislikes)||"none"}; categories: ${count(body.dislikes)}; themes: ${tags(body.dislikes)}. Treat feedback as preferences, not a ban on an entire category.`;
}

function targetOrder(parentType:string):Category[]{
 const type=canonicalType(parentType);
 if(type==="artist")return["movie","book","place","artist","podcast"];
 if(type==="book")return["movie","tv_show","place","book","artist"];
 if(type==="movie")return["artist","book","tv_show","place","movie"];
 if(type==="tv_show")return["movie","artist","book","podcast","tv_show"];
 if(type==="podcast")return["book","artist","tv_show","person","podcast"];
 if(type==="video_game")return["movie","artist","book","video_game"];
 if(type==="destination")return["place","destination","book","movie","brand"];
 if(type==="place")return["place","destination","artist","movie","brand"];
 if(type==="person")return["movie","tv_show","book","artist","person"];
 if(type==="brand")return["place","artist","movie","brand","person"];
 return["movie","artist","book","place"];
}
export async function POST(request:Request){
 const operation=new AbortController(),operationSignal=operation.signal;
 let jevCalls=0,qlooCalls=0,budgetExhausted=false;const startedAt=Date.now(),overBudget=()=>Date.now()-startedAt>50_000;
 const jevScore=(state:string,items:Record<string,string>)=>jevCalls++<10&&!operationSignal.aborted?scoreWithJev(state,items,6000,operationSignal):Promise.resolve(null);
 const blocked=guard(request,"agent",4,300_000);if(blocked)return blocked;
 let body:AgentRequest;
 try{body=await readJson(request)}catch{return Response.json({message:"Invalid agent request."},{status:400})}
 if(!body?.root?.id||!Array.isArray(body.cards))return Response.json({message:"Start a map first."},{status:400});
 body.cards=body.cards.filter(card=>card&&typeof card.id==="string"&&typeof card.name==="string"&&typeof card.type==="string").filter((card,index,all)=>all.findIndex(other=>other.id===card.id)===index).slice().reverse().sort((a,b)=>Number(!!b.liked)-Number(!!a.liked)).slice(0,80).map(card=>({...card,id:card.id.slice(0,80),name:card.name.slice(0,120),depth:Number.isFinite(card.depth)?card.depth:1,tags:Array.isArray(card.tags)?card.tags.filter((tag):tag is string=>typeof tag==="string").slice(0,8).map(tag=>tag.slice(0,40)):[],description:typeof card.description==="string"?card.description.slice(0,1600):undefined,affinity:typeof card.affinity==="number"&&Number.isFinite(card.affinity)?Math.max(0,Math.min(1,card.affinity)):undefined}));
 body.root={id:String(body.root.id).slice(0,80),name:String(body.root.name||"").slice(0,120),type:String(body.root.type||"").slice(0,40)};
 const cookiePurpose=request.headers.get("cookie")?.match(/(?:^|;\s*)sideways_purpose=(creative|audience|personal)(?:;|$)/)?.[1];
 body.purpose=body.purpose==="audience"||body.purpose==="personal"?body.purpose:cookiePurpose==="audience"||cookiePurpose==="personal"?cookiePurpose:"creative";
 body.likes=Array.isArray(body.likes)?body.likes.filter(item=>item&&typeof item.id==="string"&&typeof item.type==="string").map(item=>({...item,type:canonicalType(item.type)||item.type,tags:Array.isArray(item.tags)?item.tags.filter((tag):tag is string=>typeof tag==="string").slice(0,8):[]})).slice(-40):[];body.dislikes=Array.isArray(body.dislikes)?body.dislikes.filter(item=>item&&typeof item.id==="string"&&typeof item.type==="string").map(item=>({...item,type:canonicalType(item.type)||item.type,tags:Array.isArray(item.tags)?item.tags.filter((tag):tag is string=>typeof tag==="string").slice(0,8):[]})).slice(-60):[];body.excludeIds=(Array.isArray(body.excludeIds)?body.excludeIds:body.cards.map(card=>card.id)).filter((id):id is string=>typeof id==="string").slice(0,400).map(id=>id.slice(0,80));
 const steps=Math.max(1,Math.min(MAX_REVEALS,Number.isFinite(Number(body.steps))?Math.round(Number(body.steps)):MAX_REVEALS)),encoder=new TextEncoder(),origin=new URL(request.url).origin;
 // Forward the caller's identity headers so guard() rate-limits these internal discover calls per user, not in one shared bucket.
 const clientHeaders:Record<string,string>={"content-type":"application/json"};for(const name of ["cf-ray","cf-connecting-ip","x-real-ip","x-forwarded-for"]){const value=request.headers.get(name);if(value)clientHeaders[name]=value}
 const stream=new ReadableStream({async start(controller){
  // Vinext may mark the inbound request signal complete once the streaming
  // Response is handed off. Do not confuse that lifecycle event with a client
  // disconnect; enqueue itself is the reliable closed-stream check.
  let closed=false,delivered=0;const completion=(reason:string)=>delivered?`${delivered} new ${delivered===1?"recommendation":"recommendations"} added. ${reason}`:`No recommendations added. ${reason}`;const send=(event:Record<string,unknown>)=>{if(closed)return false;try{controller.enqueue(encoder.encode(JSON.stringify(event)+"\n"));if(event.kind==="add"&&Array.isArray(event.discoveries))delivered+=event.discoveries.length;return true}catch{closed=true;return false}};
  const hardStop=setTimeout(()=>{if(closed)return;send({kind:"done",total:steps,text:completion("Search deadline reached; try again to continue.")});operation.abort();closed=true;try{controller.close()}catch{}},58_000);
  try{
 const usedParents=new Set<string>(),usedTargets=new Set<Category>(),exclude=new Set([...body.excludeIds,...body.dislikes.map(item=>item.id)]),added:Candidate[]=[];
  const lovedIds=new Set(body.likes.map(item=>item.id));
  const savedTypes=new Set(body.likes.map(item=>category(item.type)).filter((item):item is Category=>!!item));
  const rejectedIds=new Set(body.dislikes.map(item=>item.id));
  // Wikidata-only cards are expandable too: /api/discover crosswalks them to their Qloo record.
  const pool=body.cards.filter(card=>!rejectedIds.has(card.id));
  send({kind:"start",text:`Scoring ${pool.length} discoveries with ${body.likes.length} saved ${body.likes.length===1?"signal":"signals"}.`,total:steps});
  const fit:Record<string,number>={};
  for(let offset=0;offset<pool.length;offset+=24){const batch=pool.slice(offset,offset+24),scores=await jevScore(`Seed: ${body.root.name} (${body.root.type}). ${tasteSummary(body)}`,Object.fromEntries(batch.map(card=>[card.id,`Would exploring beyond ${card.name} (${card.type}) suit this person's likes and dislikes? Context: ${card.description?.slice(0,500)||""}. Tags: ${(card.tags??[]).slice(0,6).join(", ")}. Connected from: ${card.parentName||body.root.name}.`])));for(const card of batch)fit[card.id]=scores?.[card.id]??card.affinity??.5}
  const childCount=new Map<string,number>();for(const card of body.cards)if(card.parentId)childCount.set(card.parentId,(childCount.get(card.parentId)||0)+1);const rankScore=(card:MapCard)=>fit[card.id]+(lovedIds.has(card.id)?.12:0)-Math.min(.1,Math.max(0,card.depth-1)*.015)-Math.min(.12,(childCount.get(card.id)||0)*.025),ranked=pool.sort((a,b)=>rankScore(b)-rankScore(a)||(a.id<b.id?-1:1));
  let upstreamFailed=false;
  const fetchCandidates=async(parent:MapCard,targets:Category[])=>{
   if(qlooCalls>=9||overBudget()){budgetExhausted=true;return[]}qlooCalls++;
   try{
    const typeCounts=(items:AgentRequest["likes"])=>items.reduce<Record<string,number>>((counts,item)=>{counts[item.type]=(counts[item.type]||0)+1;return counts},{});
    // Bounded so one rate-limited branch cannot monopolise the run, but long enough for
    // discover's Qloo retrieval (~4.5s) plus its relevance check (6s) and one pending-category retry.
    const branchSignal=AbortSignal.any([operationSignal,AbortSignal.timeout(16_000)]);
    const response=await discoverRoute(new Request(`${origin}/api/discover`,{signal:branchSignal,method:"POST",headers:clientHeaders,body:JSON.stringify({entityId:parent.id,name:parent.name,entityType:parent.type,image:parent.image,excludeIds:[...exclude],types:targets,probeTypes:true,strictType:true,agent:true,limit:7,fallbackAnchors:[body.cards.find(card=>card.id===parent.parentId),body.root].filter(anchor=>!!anchor&&!anchor.id.startsWith("wikidata:")&&anchor.id!==parent.id).map(anchor=>({id:anchor!.id,name:anchor!.name,type:anchor!.type})),rootName:body.root.name,depth:parent.depth+1,parentDescription:parent.description,parentTags:parent.tags??[],memory:body.memory&&typeof body.memory==="object"?body.memory:undefined,excludeWorks:Array.isArray(body.excludeWorks)?body.excludeWorks.slice(0,80):undefined,taste:{dislikedIds:body.dislikes.map(item=>item.id),likedTypes:typeCounts(body.likes),dislikedTypes:typeCounts(body.dislikes),likedTags:[...new Set(body.likes.flatMap(item=>item.tags))].slice(0,20),dislikedTags:[...new Set(body.dislikes.flatMap(item=>item.tags))].slice(0,20)}})}));
    if(!response.ok&&response.status!==422)upstreamFailed=true;
    const data=await response.json() as {discoveries?:Candidate[]};
    return(Array.isArray(data.discoveries)?data.discoveries:[]).filter(item=>{const type=category(item.type);return!!type&&targets.includes(type)});
   }catch{if(!operationSignal.aborted)upstreamFailed=true;return[]}
  };

  for(let step=1,attempt=0;step<=steps&&added.length<MAX_REVEALS&&attempt<Math.min(ranked.length,steps*2);attempt++){
   if(overBudget()){budgetExhausted=true;break}
   if(operationSignal.aborted)break;
   const open=ranked.filter(card=>!usedParents.has(card.id));
   if(!open.length)break;
   const fresh=step===steps&&steps>=3?added.filter(item=>!usedParents.has(item.id)).sort((a,b)=>(b.affinity??0)-(a.affinity??0))[0]:undefined,grown=fresh?body.cards.find(card=>card.id===fresh.id):undefined;
   const parent=grown??open[0];
   if(!parent)break;
   usedParents.add(parent.id);upstreamFailed=false;
   if(operationSignal.aborted)break;
   const targets=targetOrder(parent.type),targetScores=await jevScore(`Exploring beyond ${parent.name}. ${tasteSummary(body)}`,Object.fromEntries(targets.map(type=>[type,`Would new ${LABEL[type]} connected to ${parent.name} be useful for this person's preferences?`])));
   const diversityBoost=(type:Category)=>body.purpose==="creative"&&!savedTypes.has(type)?.18:0;
   const orderedTargets=targetScores?[...targets].sort((a,b)=>(targetScores[b]??0)+diversityBoost(b)-(targetScores[a]??0)-diversityBoost(a)+Number(usedTargets.has(a))*.1-Number(usedTargets.has(b))*.1):[...targets].sort((a,b)=>diversityBoost(b)-diversityBoost(a));
   // Categories the inspector already confirmed (e.g. a verified film adaptation) go first; confirmed-empty ones are skipped.
   const known=(list?:string[])=>new Set((Array.isArray(list)?list:[]).map(item=>category(String(item))).filter((item):item is Category=>!!item)),available=known(parent.available),unavailable=known(parent.unavailable);
   orderedTargets.splice(0,orderedTargets.length,...orderedTargets.filter(type=>available.has(type)),...orderedTargets.filter(type=>!available.has(type)&&!unavailable.has(type)));
   if(!orderedTargets.length)continue;
   let target=orderedTargets[0],candidates:Candidate[]=[],kept:Candidate[]=[];
   let scores:Record<string,number>|null=null;
   let selected:number[]=[];
   // One probe covers the five most promising categories for this card, so the budget is spent on cards rather
   // than on one empty category at a time. Verified/strict matches rank above labelled looser ones.
   const probe=[...new Set(orderedTargets)].slice(0,5);
   send({kind:"plan",step,total:steps,parentId:parent.id,text:`Checking ${probe.map(type=>LABEL[type]).join(", ")} connected to ${parent.name}.`,target:probe[0]});
   const all=(await fetchCandidates(parent,probe)).filter(item=>!exclude.has(item.id)&&!rejectedIds.has(item.id));probe.forEach(type=>usedTargets.add(type));
   const tierRank=(item:Candidate)=>(item as {tier?:string}).tier==="audience"?2:(item as {tier?:string}).tier==="related"?1:0;
   candidates=all;
   if(candidates.length){
    scores=await jevScore(`Seed: ${body.root.name}. Reached from: ${parent.name} (${parent.type}). ${tasteSummary(body)}`,Object.fromEntries(candidates.map((item,index)=>[`c${index}`,`Is "${item.name}" (${item.type}; ${(item.tags??[]).slice(0,5).join(", ")}; ${item.description?.slice(0,500)||""}) an on-taste pick for this person?`])));
    const combined=(index:number)=>{const item=candidates[index],unit=(value:unknown)=>typeof value==="number"&&Number.isFinite(value)?Math.max(0,Math.min(1,value)):.5;return unit(item.relevance)*.45+unit(scores?.[`c${index}`])*.35+unit(item.affinity)*.2-tierRank(item)*.25};
    selected=candidates.map((_,index)=>index).sort((a,b)=>combined(b)-combined(a)).slice(0,Math.min(4,MAX_REVEALS-added.length));
    kept=selected.map(index=>candidates[index]);target=category(kept[0]?.type)??probe[0];
   }
   if(!kept.length){send({kind:"skip",step,total:steps,parentId:parent.id,text:budgetExhausted?"Exploration reached its search budget. Added matches are kept; run it again to continue.":upstreamFailed?"Qloo did not respond for this branch. Try Explore again in a moment.":"No new matches passed the available category checks."});continue}
   kept.forEach(item=>exclude.add(item.id));
   const withheld=Math.max(0,candidates.length-kept.length);
   if(withheld)send({kind:"critique",step,total:steps,parentId:parent.id,text:`Kept ${kept.length} of ${candidates.length}; ${withheld} strong ${withheld===1?"match was":"matches were"} saved for the next run${scores&&selected.length?` (top fit ${(scores[`c${selected[0]}`]??0).toFixed(2)})`:""}.`});
   added.push(...kept);
   send({kind:"add",step,total:steps,parentId:parent.id,parentDepth:parent.depth,discoveries:kept,text:`${lovedIds.has(parent.id)?`Loved ${parent.name}`:`From ${parent.name}`} → ${candidates.length} relevant ${LABEL[target]} → kept ${kept.length}${scores?" by taste fit":""}.`,target});
   body.cards.push(...kept.map(item=>({id:item.id,name:item.name,type:item.type,depth:parent.depth+1,tags:item.tags,description:item.description,image:item.image,parentName:parent.name})))
   step++;
  }
  const tagCount=new Map<string,number>();for(const item of added)for(const tag of (item.tags??[]).slice(0,4).filter(tag=>tag.length>3&&!CATEGORIES.some(type=>tag.toLocaleLowerCase().replace(" ","_")===type||tag.toLocaleLowerCase()===LABEL[type]||tag.toLocaleLowerCase()===SINGULAR[type])&&!/^(place|location|venue|attraction)$/i.test(tag)))tagCount.set(tag,(tagCount.get(tag)??0)+1);
  const topTag=[...tagCount.entries()].sort((a,b)=>b[1]-a[1])[0]?.[0],standouts=[...added].sort((a,b)=>(b.affinity??0)-(a.affinity??0)).slice(0,3);
  send({kind:"done",total:steps,highlights:standouts.map(item=>item.id),text:added.length?`Added ${added.length} new ${added.length===1?"recommendation":"recommendations"}.${topTag?` Strongest direction: ${topTag}.`:""}${budgetExhausted?" Run again to continue.":""}`:budgetExhausted?"Search limit reached. Run again to continue.":upstreamFailed?"Qloo was unavailable. Try again shortly.":"No strong new matches this time."});
  }catch{send({kind:"done",total:steps,text:completion("Exploration stopped unexpectedly; try again to continue.")})}finally{clearTimeout(hardStop);if(!closed)try{controller.close()}catch{}}
 },cancel(){operation.abort()}});
 return new Response(stream,{headers:{"content-type":"application/x-ndjson","cache-control":"no-store"}});
}
