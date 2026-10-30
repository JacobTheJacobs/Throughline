// Execute inside the deployed app container. Print counts only, never key values.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const keys=[...new Set(['QLOO_API_KEY','JEV','TYPESAFE_API_KEY'].map(name=>process.env[name]).filter(value=>value&&value.length>=12))];
const roots=['/app/public','/app/dist/client','/app/dist/static','/app/.next/static'].filter(root=>fs.existsSync(root));
let scanned=0,matches=0,skipped=0;
function walk(dir){
  for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
    const file=path.join(dir,entry.name);
    if(entry.isDirectory())walk(file);
    else if(entry.isFile()){
      if(fs.statSync(file).size>20_000_000){skipped++;continue;}
      const bytes=fs.readFileSync(file);scanned++;
      if(keys.some(key=>bytes.includes(Buffer.from(key))))matches++;
    }
  }
}
for(const root of roots)walk(root);
const result={publicRoots:roots,filesScanned:scanned,filesSkipped:skipped,runtimeKeyValuesChecked:keys.length,filesContainingExactKey:matches};
const audit=spawnSync('npm',['audit','--omit=dev','--json'],{encoding:'utf8',timeout:60000,maxBuffer:10_000_000});
try{result.dependencyAudit=JSON.parse(audit.stdout).metadata?.vulnerabilities??'unavailable';}catch{result.dependencyAudit='unavailable';}
if(result.dependencyAudit==='unavailable'){
  // Standalone images may not include a lockfile. Query the registry with actual installed versions.
  try{
    const listed=spawnSync('npm',['ls','--omit=dev','--all','--json'],{encoding:'utf8',timeout:20000,maxBuffer:10_000_000});
    const inventory={};
    function collect(node){for(const [name,child] of Object.entries(node.dependencies??{})){if(child.version)(inventory[name]??=new Set()).add(child.version);collect(child);}}
    collect(JSON.parse(listed.stdout));
    const body=Object.fromEntries(Object.entries(inventory).map(([name,versions])=>[name,[...versions]]));
    if(!Object.keys(body).length)throw new Error('empty inventory');
    const response=await fetch('https://registry.npmjs.org/-/npm/v1/security/advisories/bulk',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
    if(!response.ok)throw new Error('registry unavailable');
    const advisories=Object.values(await response.json()).flat();
    result.dependencyAudit={installedPackageNames:Object.keys(body).length,advisoryCount:advisories.length,severities:advisories.map(item=>item.severity)};
    result.dependencyAuditSource='npm registry bulk advisory endpoint, installed dependency inventory';
  }catch{result.dependencyAudit='unavailable';}
}
console.log(JSON.stringify(result));
