// Offline counterexamples through extracted production helpers, not live provider results.
import {readFileSync} from 'node:fs';
import ts from 'typescript';
const api=readFileSync(new URL('../app/api/discover/route.ts',import.meta.url),'utf8');
const client=readFileSync(new URL('../app/page.tsx',import.meta.url),'utf8');
const line=(source:string,prefix:string)=>{const found=source.split('\n').find(s=>s.trimStart().startsWith(prefix));if(!found)throw new Error(`Missing production helper ${prefix}`);return found.trim()};
const canonicalStart=api.indexOf('function canonicalType('),canonicalEnd=api.indexOf('\nfunction entityTypeOf(',canonicalStart);
// Only prose/link adapters are stubbed; normalization, year extraction and exclusion are production code.
const adapters='const sourceLinks=()=>[],topTags=()=>[],profileReason=()=>null,reasonFor=()=>({}),anchoredReason=()=>({}),withPath=v=>v;';
const declarations=[
 adapters,line(api,'function cleanType('),api.slice(canonicalStart,canonicalEnd),
 line(api,'function entityTypeOf('),line(api,'function yearOf('),line(api,'function workIdentityKey('),
 line(api,'function normalize('),line(client,'function yearHint('),
 line(client,'function qlooImage(')+'\n'+client.slice(client.indexOf(' if(!src)return"";',client.indexOf('function qlooImage(')),client.indexOf('\nfunction qlooSrcSet(')),
 line(client,'function qlooSrcSet('),
 'function makeReject(excludeWorks){const body={excludeWorks};',
 line(api,'const rawWorks='),line(api,'const rejectedWork='),'return rejectedWork;}',
].join('\n');
const compiled=ts.transpileModule(declarations,{compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText;
const helpers=new Function(compiled+'\nreturn{normalize,yearHint,makeReject,qlooSrcSet};')();
const original={entity_id:'offline:1996',name:'Shared Title',type:'urn:entity:movie',properties:{release_year:1996,description:'A deliberately undated synopsis about one family.'}};
const normalized=helpers.normalize(original,'root','A Director','movie');
// Reproduce the actual dislike payload's yearHint(node), which falls back to zero here.
const rawWorks=[{name:normalized.name,type:normalized.type,year:helpers.yearHint(normalized)||undefined}];
const rejectedWork=helpers.makeReject(rawWorks);
const remake={entity_id:'offline:2004',name:'Shared Title',type:'urn:entity:movie',properties:{release_year:2004}};
const external='https://coverartarchive.org/release-group/bded1701-baf2-4066-b76a-49384de006b6/front-250';
const checks=[
 {label:'provider release_year must survive normalization for feedback identity',expected:1996,actual:normalized.year??null},
 {label:'rejecting the 1996 work must not exclude a known 2004 namesake',expected:false,actual:rejectedWork(remake,'movie')},
 {label:'fixed external cover must not advertise fabricated intrinsic widths',expected:true,actual:!/(?:160|240|420)w/.test(helpers.qlooSrcSet(external)??'')},
];
for(const check of checks)console.log(JSON.stringify({...check,pass:check.expected===check.actual,scope:'offline production-helper counterexample; namesake identities synthetic'}));
const failures=checks.filter(check=>check.expected!==check.actual).length;
console.log(JSON.stringify({summary:{checks:checks.length,failures},originalProviderYear:original.properties.release_year,serializedRejectionYear:rawWorks[0].year??null}));
process.exitCode=failures?1:0;
