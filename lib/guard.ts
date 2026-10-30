import {closeSync,openSync,readFileSync,renameSync,statSync,unlinkSync,writeFileSync} from "node:fs";
// Per-IP rate limit, same-origin check and body size cap for API routes.
// In-memory per server instance: approximate on Lambda, paired with reserved concurrency.
const limits=new WeakMap<Request,number>();
const hits=new Map<string,number[]>();
const WINDOW=60_000,DAY=86_400_000,MAX_BODY=64_000;
// Daily per-IP caps for the routes that spend JEV calls.
const DAILY:Record<string,number>={agent:30,card:300,suggestions:200,discover:800};
// Local audits share one IP bucket and make many background/category requests.
// Give development 10x headroom, while retaining bounded budgets and production defaults.
export function dailyLimitFor(route:string,environment:string|undefined=process.env.NODE_ENV){
 const base=Object.hasOwn(DAILY,route)?DAILY[route]:undefined;
 return base===undefined?undefined:base*(environment==="development"?10:1);
}
const daily=new Map<string,{start:number;count:number}>();
// Service-wide daily ceilings across all clients, so distributed callers cannot exceed the provider budget.
// With GUARD_STATE_FILE set (a mounted volume), counts are re-read and written atomically on every
// counted request, so restarts and overlapping old/new containers share one ledger. Any storage
// failure fails closed: paid routes are refused rather than granted a fresh allowance.
const GLOBAL_DAILY:Record<string,number>={agent:400,card:4000,suggestions:3000,discover:12000};
type Ledger={start:number;counts:Record<string,number>};
let memoryLedger:Ledger={start:Date.now(),counts:{}};
function readLedger(file:string):Ledger{
 let raw:string;
 try{raw=readFileSync(file,"utf8")}catch(error){if((error as NodeJS.ErrnoException).code==="ENOENT")return{start:Date.now(),counts:{}};throw error}
 const saved=JSON.parse(raw) as Ledger;
 if(typeof saved?.start!=="number"||!saved.counts||typeof saved.counts!=="object")throw new Error("corrupt budget ledger");
 return saved;
}
function writeLedger(file:string,ledger:Ledger){const temp=`${file}.${process.pid}.tmp`;writeFileSync(temp,JSON.stringify(ledger));renameSync(temp,file)}
// Returns null when the request may spend, or a refusal response.
export function reserveGlobal(route:string,now=Date.now(),file=process.env.GUARD_STATE_FILE):Response|null{
 if(!Object.hasOwn(GLOBAL_DAILY,route))return null;
 const cap=GLOBAL_DAILY[route]*(process.env.NODE_ENV==="development"?10:1);
 let lock="";
 try{
  // An exclusive lock file serialises read-increment-write across processes and containers.
  if(file){lock=`${file}.lock`;for(let tries=0;;tries++){try{closeSync(openSync(lock,"wx"));break}catch(error){if((error as NodeJS.ErrnoException).code!=="EEXIST")throw error;try{if(Date.now()-statSync(lock).mtimeMs>5_000)unlinkSync(lock)}catch{}if(tries>=100){lock="";throw new Error("budget ledger busy")}Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,10)}}}
  const ledger=file?readLedger(file):memoryLedger,current=now-ledger.start>=DAY?{start:now,counts:{}}:ledger;
  if((current.counts[route]??0)>=cap)return Response.json({error:"Throughline has reached today's usage limit for this feature — come back tomorrow."},{status:429,headers:{"Retry-After":"3600"}});
  current.counts[route]=(current.counts[route]??0)+1;
  if(file)writeLedger(file,current);else memoryLedger=current;
  return null;
 }catch{return Response.json({error:"Usage budget is unavailable, so this feature is paused. Try again shortly."},{status:503,headers:{"Retry-After":"60"}})}
 finally{if(lock)try{unlinkSync(lock)}catch{}}
}
// Reads a JSON body with a hard byte limit, regardless of Content-Length.
export async function readJson<T>(request:Request):Promise<T>{
 const max=limits.get(request)??MAX_BODY,reader=request.body?.getReader();
 if(!reader)throw new Error("empty");
 const chunks:Uint8Array[]=[];let total=0;
 for(;;){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>max){await reader.cancel();throw new Error("too large")}chunks.push(value)}
 const bytes=new Uint8Array(total);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 return JSON.parse(new TextDecoder().decode(bytes)) as T;
}
export function guard(request:Request,route:string,perMinute:number,maxBody=MAX_BODY):Response|null{
 const origin=request.headers.get("origin"),host=request.headers.get("host");
 if(origin){let originHost="";try{originHost=new URL(origin).host}catch{}if(!host||originHost!==host)return Response.json({error:"Forbidden"},{status:403})}
 if(Number(request.headers.get("content-length")||0)>maxBody)return Response.json({error:"Too large"},{status:413});
 limits.set(request,maxBody);
 // Trust provider IP headers only when a deployment proxy is explicitly enabled
 // or Cloudflare has attached its own request marker. Direct clients cannot
 // rotate arbitrary forwarding headers to evade the API budget.
 const forwarded=(request.headers.get("x-forwarded-for")||"").split(",").map(value=>value.trim()).filter(Boolean);
 const trustedProxy=process.env.TRUST_PROXY_HEADERS==="1";
 // A cf-ray header is client-controlled outside Cloudflare and proves nothing.
 // The private app port accepts traffic only from our proxy; use the last
 // appended X-Forwarded-For entry, never a client-supplied x-real-ip value.
 const ip=trustedProxy?forwarded.at(-1)||"proxy":"local";
 const key=route+"|"+ip,now=Date.now(),recent=(hits.get(key)||[]).filter(t=>now-t<WINDOW);
 if(recent.length>=perMinute)return Response.json({error:"Slow down — try again in a minute."},{status:429,headers:{"Retry-After":"60"}});
 const cap=dailyLimitFor(route);
 if(cap){const d=daily.get(key);const cur=d&&now-d.start<DAY?d:{start:now,count:0};
  if(cur.count>=cap)return Response.json({error:"Daily limit reached for this feature — come back tomorrow."},{status:429,headers:{"Retry-After":"3600"}});
  daily.set(key,cur);}
 const budget=reserveGlobal(route,now);if(budget)return budget;
 const used=daily.get(key);if(cap&&used)used.count++;
 recent.push(now);hits.set(key,recent);
 if(daily.size>5000)for(const [k,v] of daily)if(now-v.start>=DAY)daily.delete(k);
 if(hits.size>5000)for(const [k,v] of hits)if(!v.some(t=>now-t<WINDOW))hits.delete(k);
 return null;
}
