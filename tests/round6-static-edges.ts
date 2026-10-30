// Offline counterexamples only: synthetic identities, no API calls or model mocks.
// Run: node --experimental-strip-types --no-warnings tests/round6-static-edges.ts
import {readFileSync} from "node:fs";
import ts from "typescript";
import {isEditionOf} from "../lib/search-choices.ts";

// These pure UI helpers are not exported. Compile their actual source, not a copied implementation.
const page=readFileSync(new URL("../app/page.tsx",import.meta.url),"utf8");
const helpers=["categoryOf","workKey","isAliasOf"].map(name=>{
 const line=page.split("\n").find(line=>line.startsWith(`function ${name}(`));
 if(!line)throw new Error(`Missing production helper ${name}`);
 return line;
}).join("\n");
const js=ts.transpileModule(helpers,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText;
const isAliasOf=new Function(js+"\nreturn isAliasOf;")() as (item:{id:string;name:string;type:string},existing:Array<{id:string;name:string;type:string}>)=>boolean;
const checks=[
 {label:"different works with year-qualified identical titles",expected:false,actual:isAliasOf({id:"qloo:fixture-2004",name:"Shared Title (2004)",type:"movie"},[{id:"wikidata:fixture-1996",name:"Shared Title (1996)",type:"movie"}])},
 {label:"artist and same-named album are not the same entity",expected:false,actual:isAliasOf({id:"qloo:fixture-album",name:"Shared Name",type:"album"},[{id:"wikidata:fixture-artist",name:"Shared Name",type:"artist"}])},
 {label:"different colon-subtitled sequel is not an edition",expected:false,actual:isEditionOf("Voyage: Part One","video_game","Voyage: Part Two Deluxe Edition","video_game")},
 {label:"earlier DOOM sequel counterexample repaired",expected:false,actual:isEditionOf("DOOM","video_game","DOOM Eternal Deluxe Edition","video_game")},
 {label:"intended Final Cut detection preserved",expected:true,actual:isEditionOf("Disco Elysium","video_game","Disco Elysium: The Final Cut","video_game")},
];
for(const item of checks)console.log(JSON.stringify({...item,pass:item.actual===item.expected,scope:"offline production-helper check; synthetic identity fixtures"}));
const failures=checks.filter(item=>item.actual!==item.expected).length;
console.log(JSON.stringify({summary:{checks:checks.length,failures}}));
process.exitCode=failures?1:0;
