import {guard,readJson} from "@/lib/guard";
// Card links: template searches per platform, ranked by JEV. Returns the top pick plus alternatives.
import {describeCard,sanitizeCard,shortName,type CardContext} from "@/lib/card";
import {jevScore} from "@/lib/jev";
type Platform="youtube"|"tiktok"|"reddit"|"google";
type Ranked=Partial<Record<Platform,string>>&{options?:Partial<Record<Platform,string[]>>};
const cache=new Map<string,Ranked>();
function creatorOf(card:CardContext){const match=card.description?.match(/\b(?:by|directed by|written by|from)\s+([A-Z][\p{L}.'-]+(?:\s+[A-Z][\p{L}.'-]+){0,2})/u);return match?.[1]}
function yearOf(card:CardContext){return card.description?.match(/\b(19|20)\d{2}\b/)?.[0]}
function templates(card:CardContext):Record<Platform,string[]>{
 const n=shortName(card.name),t=card.type.toLocaleLowerCase(),who=creatorOf(card),year=yearOf(card),tag=card.tags?.find(item=>item.length<24);
 const video=t.includes("movie")||t.includes("film")||t.includes("tv")?["official trailer","review","explained","behind the scenes"]:t.includes("artist")||t.includes("music")?["official music video","live","full album","interview"]:t.includes("book")?["book review","author interview","summary","booktube"]:t.includes("game")?["official trailer","gameplay","review","lore explained"]:t.includes("place")?["walking tour","visit guide","vlog","review"]:["review","story","documentary","ad"];
 return{
  youtube:[...video.map(word=>`${n} ${word}`),...(who?[`${n} ${who} interview`]:[]),...(year?[`${n} ${year} ${video[0]}`]:[])],
  tiktok:[`${n} ${t}`,`${n} review`,`${n} edit`,...(tag?[`${n} ${tag}`]:[])],
  reddit:[`${n} discussion`,`${n} recommendations`,`${n} ${t} worth it`,...(who?[`${n} ${who}`]:[])],
  google:[`${n} ${t}`,...(who?[`${n} ${who}`]:[]),...(year?[`${n} ${year} ${t}`]:[])],
 };
}
export async function POST(request:Request){
 const blocked=guard(request,"card",40);if(blocked)return blocked;
 let body:{card?:CardContext};
 try{body=await readJson(request)}catch{return Response.json({},{status:400})}
 const card=body&&typeof body==="object"?sanitizeCard(body.card):null;if(!card)return Response.json({},{status:400});
 // Keyed by all sanitized evidence (creator, year, tags…), so richer identity is never served an older answer.
 const cacheKey=JSON.stringify(card),hit=cache.get(cacheKey);if(hit)return Response.json({...hit,source:"jev"});
 const all=templates(card),items:Record<string,string>={};
 for(const [platform,list] of Object.entries(all))list.forEach((query,index)=>{items[`${platform}_${index}`]=`On ${platform}, will searching "${query}" surface content about exactly ${card.name} (the ${card.type}), not something else with a similar name?`});
 const scores=await jevScore(describeCard(card),items);
 const result:Ranked={options:{}};
 for(const [platform,list] of Object.entries(all) as Array<[Platform,string[]]>){
  const ranked=list.map((query,index)=>({query,score:scores?.[`${platform}_${index}`]??(1-index/10)})).sort((a,b)=>b.score-a.score).map(item=>item.query);
  result[platform]=ranked[0];result.options![platform]=ranked.slice(1,3);
 }
 if(scores){if(cache.size>500)cache.delete(cache.keys().next().value!);cache.set(cacheKey,result)}
 return Response.json({...result,source:scores?"jev":"template"});
}
