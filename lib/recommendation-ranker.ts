export type RankingCandidate={
 id:string;
 type:string;
 tags:string[];
 affinity?:number;
 quality?:number;
 taste?:number;
 explainability?:number;
 memoryFit?:number;
};

type RankingOptions={
 limit?:number;
 seenIds?:Iterable<string>;
 rejectedIds?:Iterable<string>;
 rejectedTags?:Iterable<string>;
 preferredTypes?:Iterable<string>;
};

const clamp=(value:number,min=0,max=1)=>Math.max(min,Math.min(max,value));
const key=(value:string)=>value.trim().toLocaleLowerCase().replaceAll("_"," ");

// Category clicks promise a useful connection to the selected reference.
// Neither audience affinity nor model confidence is sufficient on its own.
export function qualifiesCategoryMatch(affinity:unknown,relevance:unknown){
 return typeof affinity==="number"&&Number.isFinite(affinity)&&affinity>=.8&&affinity<=1
  &&typeof relevance==="number"&&Number.isFinite(relevance)&&relevance>=.55&&relevance<=1;
}

// Anchor relevance is a two-sided check: a specific shared subject must score high
// and "only a broad genre/format/audience link" must score low. Either alone admits weak themes.
export function qualifiesAnchorMatch(affinity:unknown,subject:unknown,loose:unknown){
 const score=(value:unknown):value is number=>typeof value==="number"&&Number.isFinite(value)&&value>=0&&value<=1;
 // Scores are compared in whole thousandths so equal margins (.6-.4 vs .61-.41) get the same decision.
 const milli=(value:number)=>Math.round(value*1000);
 return score(affinity)&&milli(affinity)>=800&&score(subject)&&milli(subject)>=600&&score(loose)&&milli(loose)<=650&&milli(subject)-milli(loose)>=200;
}

// A compact set-level reranker: Qloo supplies relevance; this pass makes the
// returned set personal, novel, explainable and less repetitive.
export function diversifyRecommendations<T extends RankingCandidate>(items:T[],options:RankingOptions={}):T[]{
 const limit=Math.max(0,Math.min(items.length,options.limit??items.length));
 if(limit===0)return[];
 const seen=new Set(options.seenIds??[]),rejected=new Set(options.rejectedIds??[]),negativeTags=new Set([...options.rejectedTags??[]].map(key)),preferredTypes=new Set([...options.preferredTypes??[]].map(key));
 const remaining=[...items],selected:T[]=[],selectedTypes=new Map<string,number>(),selectedTags=new Map<string,number>();
 while(remaining.length&&selected.length<limit){
  let bestIndex=0,bestScore=-Infinity;
  for(let index=0;index<remaining.length;index++){
   const item=remaining[index],type=key(item.type),tags=[...new Set((item.tags??[]).map(key).filter(Boolean))],affinity=Number.isFinite(item.affinity)?clamp(item.affinity!):clamp((item.quality??50)/100),taste=clamp(((item.taste??0)+1)/2),explainability=clamp(item.explainability??Math.min(1,tags.length/3)),memoryFit=clamp(item.memoryFit??.5);
   const categoryNovelty=selectedTypes.has(type)?0:1,tagRepetition=tags.length?tags.reduce((sum,tag)=>sum+(selectedTags.get(tag)??0),0)/tags.length:0,negativeHits=tags.filter(tag=>negativeTags.has(tag)).length;
   const score=affinity*.45+taste*.18+memoryFit*.07+categoryNovelty*.15+explainability*.05+.1
    +(preferredTypes.has(type)?.04:0)-Math.min(.2,tagRepetition*.08)-Math.min(.3,negativeHits*.12)
    -(seen.has(item.id)?.65:0)-(rejected.has(item.id)?1:0)+(item.quality??0)*.0001-index*.000001;
   if(score>bestScore){bestScore=score;bestIndex=index}
  }
  const [winner]=remaining.splice(bestIndex,1);selected.push(winner);const type=key(winner.type);selectedTypes.set(type,(selectedTypes.get(type)??0)+1);for(const tag of new Set((winner.tags??[]).map(key).filter(Boolean)))selectedTags.set(tag,(selectedTags.get(tag)??0)+1);
 }
 return selected;
}
