// Offline checks of actual production helpers; identity fixtures are synthetic, no API/model mocks.
import {readFileSync} from "node:fs";
import ts from "typescript";
import {repeatsBookSource} from "../lib/search-choices.ts";
const source=readFileSync(new URL("../app/api/discover/route.ts",import.meta.url),"utf8");
const clean=source.split("\n").find(l=>l.startsWith("function cleanType("));
const identity=source.split("\n").find(l=>l.startsWith("function workIdentityKey("));
const start=source.indexOf('function canonicalType('),end=source.indexOf('\nfunction entityTypeOf(',start);
if(!clean||!identity||start<0||end<0)throw new Error('Production helper missing');
const js=ts.transpileModule([clean,source.slice(start,end),identity].join('\n'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText;
const workIdentityKey=new Function(js+'\nreturn workIdentityKey;')() as (name:string,type:string)=>string;
const one={id:'fixture:one',name:'Shared Title',type:'movie',year:1996},two={id:'fixture:two',name:'Shared Title',type:'movie',year:2004};
const checks=[
 {label:'different works with same unqualified title and category must not share a rejection identity',expected:false,actual:workIdentityKey(one.name,one.type)===workIdentityKey(two.name,two.type),scope:'offline synthetic namesakes; no live rejection sequence claimed'},
 {label:'confirmed Parable provider alias should still share a key',expected:true,actual:workIdentityKey('Parable of the Talents','book')===workIdentityKey('Parable of the Talents (Earthseed, #2)','book'),scope:'production normalization regression'},
 {label:'live Annihilation omnibus is not an entirely new work',expected:true,actual:repeatsBookSource('Annihilation (Southern Reach, #1)','book','Area X: The Southern Reach Trilogy (Southern Reach, #1-3)','book'),scope:'real returned source/bundle titles; contents verified separately with publisher'},
];
for(const c of checks)console.log(JSON.stringify({...c,pass:c.actual===c.expected}));
const failures=checks.filter(c=>c.actual!==c.expected).length;console.log(JSON.stringify({summary:{checks:checks.length,failures}}));process.exitCode=failures?1:0;
