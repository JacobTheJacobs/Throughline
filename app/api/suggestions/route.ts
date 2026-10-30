import {guard,readJson} from "@/lib/guard";
// Suggest plain-language "more like this" paths. Tags still guide retrieval,
// but the interface describes the outcome instead of exposing search mechanics.
import {describeCard,sanitizeCard,type CardContext} from "@/lib/card";
import {jevScore} from "@/lib/jev";
type Direction={label:string;type:string;theme?:string};
type DirectionRequest={card?:CardContext;root?:{name:string};path?:string[];liked?:string[];disliked?:string[]};
const CATS=["movie","tv_show","artist","book","podcast","place","destination","video_game","brand","person"] as const;
const cache=new Map<string,{expires:number;directions:Direction[]}>();
const NOUN:Record<string,string>={movie:"movies",tv_show:"TV shows",artist:"artists",book:"books",podcast:"podcasts",place:"places",destination:"destinations",video_game:"games",brand:"brands",person:"people"};
function candidates():Direction[]{return CATS.map(type=>({label:`More ${NOUN[type]} like this`,type}))}
function preferredTypes(type:string){
 const own=type.toLocaleLowerCase();
 if(own.includes("tv")||own.includes("show")||own.includes("series"))return["tv_show","movie","book","artist"];
 if(own.includes("movie")||own.includes("film"))return["movie","tv_show","book","artist"];
 if(own.includes("book")||own.includes("author"))return["book","movie","artist","place"];
 if(own.includes("artist")||own.includes("music")||own.includes("album")||own.includes("song"))return["artist","movie","place","book"];
 if(own.includes("podcast"))return["podcast","book","artist","tv_show"];
 if(own.includes("destination"))return["destination","place","book","movie"];
 if(own.includes("place"))return["place","destination","book","movie"];
 if(own.includes("game"))return["video_game","movie","book","artist"];
 if(own.includes("brand")||own.includes("product"))return["brand","place","artist","movie"];
 if(own.includes("person")||own.includes("actor")||own.includes("director"))return["person","movie","tv_show","book"];
 return["movie","book","artist","place"];
}
export async function POST(request:Request){
 const blocked=guard(request,"suggestions",30);if(blocked)return blocked;
 let body:DirectionRequest;
 try{body=await readJson(request)}catch{return Response.json({directions:[]},{status:400})}
 const card=body&&typeof body==="object"?sanitizeCard(body.card):null;if(!card)return Response.json({directions:[]},{status:400});
	 const liked=(Array.isArray(body.liked)?body.liked:[]).filter((item):item is string=>typeof item==="string").slice(-8),disliked=(Array.isArray(body.disliked)?body.disliked:[]).filter((item):item is string=>typeof item==="string").slice(-8),path=(Array.isArray(body.path)?body.path:[]).filter((item):item is string=>typeof item==="string").slice(-12),cacheKey=["v5",card.id,body.root?.name,path.join(">"),liked.join(","),disliked.join(",")].join("|").slice(0,900),cached=cache.get(cacheKey);if(cached&&cached.expires>Date.now())return Response.json({directions:cached.directions,source:"cache"});
 const pool=candidates();
	 const scores=await jevScore(`${describeCard(card)} Path: ${path.join(" → ")||card.name}. Loved: ${liked.join(", ")||"nothing yet"}. Rejected: ${disliked.join(", ")||"nothing yet"}.`,Object.fromEntries(pool.map((item,index)=>[`d${index}`,`Would ${item.label} using the card's overall Qloo affinity be an exciting, believable next direction from ${card.name}?`])));
	 const order=pool.map((item,index)=>({item,score:scores?.[`d${index}`]??.6-index/1000})).sort((a,b)=>b.score-a.score);
	 const picked:Direction[]=scores?order.slice(0,4).map(candidate=>candidate.item):preferredTypes(card.type).flatMap(type=>{const best=order.find(candidate=>candidate.item.type===type);return best?[best.item]:[]}).slice(0,4);
	 // A short fallback cache prevents repeated model calls during an outage,
	 // without pinning the template order for the full successful-result TTL.
	 if(cache.size>300)cache.delete(cache.keys().next().value!);cache.set(cacheKey,{expires:Date.now()+(scores?1_800_000:60_000),directions:picked});
 return Response.json({directions:picked,source:scores?"jev":"template"});
}
