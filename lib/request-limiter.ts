// Queue only work belonging to the same request. Workers can cancel unfinished
// work when a response ends; a global queue would strand every later request.
export function requestScopedLimiter(limit=4){
 type Waiter={resolve:()=>void;reject:(error:Error)=>void;cleanup:()=>void};
 type State={active:number;queue:Waiter[]};
 const requests=new WeakMap<AbortSignal,State>();
 return async function runLimited<T>(run:()=>Promise<T>,signal?:AbortSignal):Promise<T>{
  if(signal?.aborted)throw new Error("ABORTED");
  let state=signal?requests.get(signal):undefined;
  if(!state){state={active:0,queue:[]};if(signal)requests.set(signal,state)}
  const current=state;
  if(current.active<limit)current.active++;
  else await new Promise<void>((resolve,reject)=>{
   const waiter:Waiter={resolve,reject,cleanup:()=>signal?.removeEventListener("abort",abort)};
   const abort=()=>{const index=current.queue.indexOf(waiter);if(index>=0)current.queue.splice(index,1);waiter.cleanup();reject(new Error("ABORTED"))};
   current.queue.push(waiter);signal?.addEventListener("abort",abort,{once:true});
   if(signal?.aborted)abort();
  });
  try{if(signal?.aborted)throw new Error("ABORTED");return await run()}
  finally{const next=current.queue.shift();if(next){next.cleanup();next.resolve()}else current.active--}
 };
}
