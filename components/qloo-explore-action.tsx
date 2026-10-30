"use client";

import {useId} from "react";
import {ArrowUpRight,Sparkles} from "lucide-react";

export function QlooExploreAction({onExplore,busy=false,disabled=false,sourceName}:{onExplore:()=>void;busy?:boolean;disabled?:boolean;sourceName?:string}){
 const sourceId=useId();
 return <section className="qloo-quick-action" aria-label="Qloo exploration">
  <button type="button" onClick={onExplore} disabled={disabled||busy} aria-busy={busy} aria-describedby={sourceName?sourceId:undefined}>
   <Sparkles aria-hidden="true"/><span>{busy?"Finding matches…":"Explore with Qloo"}</span><ArrowUpRight aria-hidden="true"/>
  </button>
  {sourceName&&<small id={sourceId}>From {sourceName}</small>}
 </section>;
}
