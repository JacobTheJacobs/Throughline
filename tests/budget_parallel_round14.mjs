// Real filesystem contention, no forced reads inside a lock and no provider calls.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
if(isMainThread){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'throughline-budget-parallel-'));
  const file=path.join(dir,'guard.json');
  fs.writeFileSync(file,JSON.stringify({start:Date.now(),counts:{agent:0}}));
  const run=()=>new Promise((resolve,reject)=>{
    const worker=new Worker(new URL(import.meta.url),{workerData:{file},execArgv:['--experimental-strip-types','--no-warnings']});
    worker.once('message',resolve);worker.once('error',reject);
  });
  const batches=await Promise.all(Array.from({length:12},run));
  const totals={allowed:0,capped:0,busy:0};
  for(const batch of batches)for(const key of Object.keys(totals))totals[key]+=batch[key];
  const finalCount=JSON.parse(fs.readFileSync(file,'utf8')).counts.agent;
  console.log(JSON.stringify({...totals,finalCount,cap:400,pass:totals.allowed<=400&&finalCount===totals.allowed}));
  if(totals.allowed>400||finalCount!==totals.allowed)process.exitCode=1;
}else{
  process.env.NODE_ENV='production';
  const {reserveGlobal}=await import('../lib/guard.ts');
  const results={allowed:0,capped:0,busy:0};
  for(let i=0;i<50;i++){
    const response=reserveGlobal('agent',Date.now(),workerData.file);
    if(!response)results.allowed++;else if(response.status===429)results.capped++;else results.busy++;
  }
  parentPort.postMessage(results);
}
