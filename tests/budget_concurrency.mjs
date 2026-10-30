// Real contention: 4 workers race 150 reservations each against cap 400 on one ledger file.
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
if(isMainThread){
  const file=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'budget-')),'guard.json');
  const run=()=>new Promise((ok,bad)=>{const w=new Worker(new URL(import.meta.url),{workerData:{file},execArgv:['--experimental-strip-types','--no-warnings']});w.once('message',ok);w.once('error',bad)});
  const allowed=(await Promise.all([run(),run(),run(),run()])).reduce((a,b)=>a+b,0),final=JSON.parse(fs.readFileSync(file,'utf8')).counts.agent;
  console.log(JSON.stringify({allowed,final}));process.exit(allowed===400&&final===400?0:1);
}else{
  const {reserveGlobal}=await import('../lib/guard.ts');let n=0;
  for(let i=0;i<150;i++)if(reserveGlobal('agent',Date.now(),workerData.file)===null)n++;
  parentPort.postMessage(n);
}
