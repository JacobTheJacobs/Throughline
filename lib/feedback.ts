// Explicit feedback is a state: the latest choice wins over browsing history.
// `seq` orders events written in the same millisecond; on a full tie the later array entry wins.
export function latestFeedback<T extends {entityId:string;kind:string;createdAt:number;seq?:number}>(events:T[]):T[]{
 const order=(event:T)=>event.seq??event.createdAt*1000;
 const latest=new Map<string,T>();
 for(const event of events){
  if(!["love","unlove","reject"].includes(event.kind))continue;
  const previous=latest.get(event.entityId);
  if(!previous||order(event)>=order(previous))latest.set(event.entityId,event);
 }
 return [...latest.values()].filter(event=>event.kind!=="unlove");
}
