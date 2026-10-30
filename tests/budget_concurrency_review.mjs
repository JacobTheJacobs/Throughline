// Offline controlled interleaving: two processes can read the same remaining slot.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Worker, isMainThread, parentPort, workerData} from 'node:worker_threads';
import {syncBuiltinESMExports} from 'node:module';

if (isMainThread) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'throughline-budget-race-'));
  const file=path.join(dir,'guard.json');
  fs.writeFileSync(file,JSON.stringify({start:Date.now(),counts:{agent:399}}));
  const barrier=new SharedArrayBuffer(8);
  const run=()=>new Promise((resolve,reject)=>{
    const worker=new Worker(new URL(import.meta.url),{workerData:{file,barrier},execArgv:['--experimental-strip-types','--no-warnings']});
    worker.once('message',resolve);worker.once('error',reject);
  });
  const results=await Promise.all([run(),run()]);
  console.log(JSON.stringify({initialCount:399,cap:400,results,finalCount:JSON.parse(fs.readFileSync(file,'utf8')).counts.agent}));
} else {
  // Pause both readers after reading the same file, then serialize their writes.
  const original=fs.readFileSync,barrier=new Int32Array(workerData.barrier);
  let ticket;
  fs.readFileSync=function(file,...args){
    const value=original.call(this,file,...args);
    if(file===workerData.file){
      ticket=Atomics.add(barrier,0,1);Atomics.notify(barrier,0);
      while(Atomics.load(barrier,0)<2)Atomics.wait(barrier,0,1,5000);
      if(ticket===1)while(Atomics.load(barrier,1)<1)Atomics.wait(barrier,1,0,5000);
    }
    return value;
  };
  syncBuiltinESMExports();
  const {reserveGlobal}=await import('../lib/guard.ts');
  const response=reserveGlobal('agent',Date.now(),workerData.file);
  if(ticket===0){Atomics.store(barrier,1,1);Atomics.notify(barrier,1);}
  parentPort.postMessage({allowed:response===null,status:response?.status??200});
}
