// Identity-bound cover URLs only; validate every redirect before contacting it.
export function allowedArtworkUrl(value:string){
 try{const u=new URL(value);return u.protocol==="https:"&&!u.username&&!u.password&&(!u.port||u.port==="443")&&(["coverartarchive.org","covers.openlibrary.org","archive.org"].includes(u.hostname)||u.hostname.endsWith(".archive.org"))}catch{return false}
}
export async function artworkStatus(value:string,signal?:AbortSignal):Promise<"available"|"missing"|"retry">{
 const bounded=AbortSignal.any([AbortSignal.timeout(6000),...(signal?[signal]:[])]);
 let current=value;
 try{for(let count=0;count<5;count++){
  if(!allowedArtworkUrl(current))return "missing";
  const response=await fetch(current,{method:"HEAD",redirect:"manual",signal:bounded});
  if(response.status===404||response.status===410)return "missing";
  if(response.status>=300&&response.status<400){const location=response.headers.get("location");if(!location)return "retry";current=new URL(location,current).href;continue}
  return response.ok&&(response.headers.get("content-type")??"").startsWith("image/")?"available":"retry";
 }}catch{/* Transient network failures must not become a cached absence. */}
 return "retry";
}
