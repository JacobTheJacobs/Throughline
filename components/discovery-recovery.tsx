import {ArrowUpRight,RefreshCw,Search,Shuffle} from "lucide-react";

export function DiscoveryRecovery({name,message,onAudience,onRetry,onMeaning,onSearch,onDismiss,onMap=false,artists=[]}:{name:string;message:string;onAudience?:()=>void;onRetry?:()=>void;onMeaning?:()=>void;onSearch:()=>void;onDismiss:()=>void;onMap?:boolean;artists?:Array<{id:string;name:string;onExplore:()=>void}>}){
 return <section className={`discovery-recovery ${onMap?"is-on-map":""}`} role="status" aria-label={`Discovery options for ${name}`}>
  <div><h2>{artists.length?`Explore ${name} through its artist`:`No confirmed matches from ${name} yet`}</h2><button type="button" onClick={onDismiss} aria-label="Dismiss discovery options">×</button></div>
  <p>{message}</p><nav aria-label="Continue exploring">
   {artists.map(artist=><button type="button" key={artist.id} onClick={artist.onExplore}>Find matches from {artist.name}<ArrowUpRight aria-hidden="true"/></button>)}
   {onAudience&&<button type="button" onClick={onAudience}><Shuffle aria-hidden="true"/>Try audience matches<ArrowUpRight aria-hidden="true"/></button>}
   {onRetry&&<button type="button" onClick={onRetry}><RefreshCw aria-hidden="true"/>Try again</button>}
   {onMeaning&&<button type="button" onClick={onMeaning}>Choose another meaning</button>}
   <button type="button" onClick={onSearch}><Search aria-hidden="true"/>Change search</button>
  </nav>{artists.length>0&&<small>Verified performer. Recommendations start from the artist, not directly from this recording.</small>}{onAudience&&<small>Audience overlap, not a factual or subject connection.</small>}
 </section>;
}
