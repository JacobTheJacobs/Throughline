// Unit tests for the pure server logic. Run: npm run test:unit
import { test } from "node:test";
import assert from "node:assert/strict";
import { jevScore } from "../lib/jev.ts";
import {allowedArtworkUrl,artworkStatus} from "../lib/artwork.ts";
import { sanitizeCard } from "../lib/card.ts";
import { dailyLimitFor, guard, readJson } from "../lib/guard.ts";
import {aggregateEvidence,assignmentFor,blindedOutputs,categoryDiversity,categoryEntropy,checksumSession,sealSession,trialDuration,validateSession,STUDY_PROTOCOL,STUDY_SCHEMA,type ReviewerRecord,type StudySessionV1} from "../lib/study.ts";
import {DEFAULT_SYNTHETIC_SEED,runSyntheticStudy,SYNTHETIC_PERSONAS} from "../lib/synthetic-study.ts";
import {diversifyRecommendations,qualifiesAnchorMatch,qualifiesCategoryMatch} from "../lib/recommendation-ranker.ts";
import {evidence,hasEvidence,judgeRelevance,judgementKey,qualifies} from "../lib/relevance.ts";
import {graphPaths,isRetrievableEvent,mergeEntity,obsoleteEdgeIds,type MemoryEdge,type MemoryEvent} from "../lib/taste-memory.ts";
import {directConnectionType,directConnectionReason,repairDirectConnection,wikidataWorkType} from "../lib/direct-connections.ts";
import {canonicalDiscoveryType,choiceEvidence,choiceQuality,matchesSearchName,repeatsBookSource,uniqueChoices,isEditionOf} from "../lib/search-choices.ts";
import {requestScopedLimiter} from "../lib/request-limiter.ts";
import {musicalWork,matchesPerformer,verifiedMusicWorks,type MusicEntity} from "../lib/music-discovery.ts";
import {invalidInterestAnchor} from "../lib/discovery-errors.ts";

test("an invalid interest anchor is not confused with empty results or other provider errors",()=>{
 assert.equal(invalidInterestAnchor({errors:[{path:"signal.interests.entities",message:"All of the provided signal.interests.entities were invalid. At least one valid signal or filter is required."}]}),true);
 assert.equal(invalidInterestAnchor({errors:[{path:"filter.type",message:"All filter types were invalid."}]}),false);
 assert.equal(invalidInterestAnchor({error:{message:"Rate limit exceeded"}}),false);
 assert.equal(invalidInterestAnchor({results:[]}),false);
});

test("artwork redirects are allowlisted and a redirect alone does not verify an image",async()=>{
 assert.equal(allowedArtworkUrl("https://ia8001.us.archive.org/cover.jpg"),true);
 for(const url of ["http://archive.org/x","https://archive.org.evil.test/x","https://127.0.0.1/x","https://archive.org:8080/x","https://user@archive.org/x"])assert.equal(allowedArtworkUrl(url),false);
 const original=globalThis.fetch;let calls=0;
 try{
  globalThis.fetch=async()=>{calls++;return new Response(null,{status:302,headers:{location:"http://169.254.169.254/latest/meta-data/"}})};
  assert.equal(await artworkStatus("https://coverartarchive.org/x"),"missing");assert.equal(calls,1);
  globalThis.fetch=async()=>new Response(null,{status:500});
  assert.equal(await artworkStatus("https://coverartarchive.org/x"),"retry");
  globalThis.fetch=async()=>new Response(null,{status:200,headers:{"content-type":"text/html"}});
  assert.equal(await artworkStatus("https://coverartarchive.org/x"),"retry");
 }finally{globalThis.fetch=original}
});

test("music recovery requires an exact work and a verified performer edge",()=>{
 const statement=(id:string)=>({mainsnak:{datavalue:{value:{id}}}});
 const work:MusicEntity={id:"Q100",labels:{en:{value:"A Shared Song"}},descriptions:{en:{value:"2003 single"}},claims:{P31:[statement("Q134556")],P175:[statement("Q101")]}};
 const people={Q101:{labels:{en:{value:"Original Artist"}}}};
 assert.equal(musicalWork(work,"A Shared Song",people)?.performers[0].id,"Q101");
 assert.equal(musicalWork(work,"A Shared Song (Remix)",people),null,"do not silently strip remix identity");
 assert.equal(musicalWork({...work,claims:{P31:[statement("Q134556")]}},"A Shared Song",people),null,"description alone is not a performer link");
 assert.equal(musicalWork({...work,claims:{P31:[statement("Q134556")],P175:[{...statement("Q101"),rank:"deprecated"}]}},"A Shared Song",people),null);
 assert.equal(musicalWork(work,"A Shared Song",{}),null,"never invent an unavailable performer label");
});

test("performer crosswalks do not equate similarly named artists",()=>{
 assert.equal(matchesPerformer({id:"Q101"},{wikidata:"q101"}),true);
 assert.equal(matchesPerformer({id:"Q101"},{wikidata:"Q102"}),false);
 assert.equal(matchesPerformer({id:"Q101"},{}),false);
 assert.equal(matchesPerformer({id:"Q101",musicbrainz:"verified-mbid"},{musicbrainz:"verified-mbid"}),true);
 assert.equal(matchesPerformer({id:"Q101",musicbrainz:"verified-mbid"},{wikidata:"Q102",musicbrainz:"verified-mbid"}),false,"conflicting identities cannot be silently accepted");
 assert.equal(matchesPerformer({id:"Q101",musicbrainz:"verified-mbid"},{wikidata:"Q101",musicbrainz:"provider-secondary-error"}),true,"an exact primary identity is not overridden by unrelated secondary metadata");
});

test("an invalid music identity does not widen into a title search",async()=>{
 assert.deepEqual(await verifiedMusicWorks("A Shared Song",async()=>{throw new Error("must not fetch")},undefined,"not-an-id"),[]);
});

test("search uses identity evidence, preserves company aliases and removes contradictory duplicates",()=>{
 const weak={id:"weak",name:"Some Writer",type:"person",detail:"Peerage person ID=123",popularity:1};
 const verified={id:"verified",name:"Some Writer",type:"person",detail:"A novelist and poet with a documented bibliography",image:"image",externalSource:"wikidata",externalId:"Q123"};
 assert.ok(choiceQuality(verified)>choiceQuality(weak)+2,"even a maximum model score cannot hide stronger identity evidence");
 assert.ok(choiceEvidence(verified).includes("novelist"));assert.ok(choiceEvidence(verified).includes("Q123"));
 assert.equal(matchesSearchName("Apple","Apple Inc","brand"),true);
 assert.equal(matchesSearchName("Adidas","Adidas AG","brand"),true);
 assert.equal(matchesSearchName("Dune","Dune (Dune, #1)","book"),true);
 assert.equal(matchesSearchName("Dune","Dune Messiah","book"),false);
 assert.equal(matchesSearchName("Apple","Apple Valley","place"),false);
 assert.equal(matchesSearchName("Apple","Apple Records","brand"),false);
 assert.equal(matchesSearchName("Bjork","Björk","artist"),true);
 assert.deepEqual(uniqueChoices([weak,{...weak,type:"author"},verified,{id:"wrong",name:"Portugal",type:"artist",detail:"Portugal is a country, not a music artist or group."}]).map(x=>x.id),["verified","weak"]);
 assert.equal(canonicalDiscoveryType("urn:entity:locality"),"destination");assert.equal(canonicalDiscoveryType("videogame"),"video_game");
});

test("a musical credit never guesses album versus song, and adaptations do not repeat the anchor",()=>{
 assert.equal(directConnectionType("Performed by","artist"),"work");
 assert.equal(directConnectionType("Performed by","artist","album"),"album");
 assert.equal(wikidataWorkType(["Q482994"]),"album");
 assert.equal(wikidataWorkType([],"1993 studio album by an artist"),"album");
 assert.equal(wikidataWorkType([],"Nintendo home video game console"),"product");
 assert.equal(wikidataWorkType([],"handheld game console"),"product");
 assert.equal(wikidataWorkType(["Q7366"]),"song");
 assert.equal(wikidataWorkType([],"Unclassified creative work"),undefined);
 assert.equal(directConnectionReason("Adapted from Fleabag","Fleabag","Mouche"),"Based on Fleabag.");
 assert.equal(directConnectionReason("Located in","Example City","Example Museum"),"Example Museum is located in Example City.");
});

test("relevance sees distinctive evidence after cast/credit prefixes, and caches its full meaning",()=>{
 const anchor={id:"anchor",name:"A reference",type:"movie",description:"An artist under extreme performance pressure."};
 const prefix="Cast names and production credits. ".repeat(14);
 const candidate={id:"candidate",name:"Another work",type:"movie",description:prefix+"Artistic obsession and destructive performance pressure."};
 assert.ok(evidence(candidate).includes("destructive performance pressure"));
 assert.notEqual(judgementKey(anchor,candidate),judgementKey(anchor,{...candidate,description:prefix+"An unrelated bird migration documentary."}));
 assert.equal(hasEvidence({id:"theme",name:"A work",type:"book",themes:"A human envoy faces cultural barriers and political systems on an alien world."}),true);
});

test("book collections containing the source are not treated as new works",()=>{
 assert.equal(repeatsBookSource("1984","book","Animal Farm / 1984","book"),true);
 assert.equal(repeatsBookSource("Dune","book","Dune & Dune Messiah","book"),true);
 assert.equal(repeatsBookSource("1984","book","1984 (Play)","book"),false);
 assert.equal(repeatsBookSource("1984","book","Brave New World","book"),false);
 assert.equal(repeatsBookSource("A & B","artist","A & B","album"),false);
});

test("abandoned provider work cannot block another request",async()=>{
 const slot=requestScopedLimiter(1),first=new AbortController(),second=new AbortController();
 let release!:()=>void;
 const active=slot(()=>new Promise<void>(resolve=>{release=resolve}),first.signal);
 const waiting=slot(async()=>"must not run",first.signal);
 const rejected=assert.rejects(waiting,/ABORTED/);
 assert.equal(await slot(async()=>"independent",second.signal),"independent");
 first.abort();await rejected;release();await active;
 assert.equal(await slot(async()=>"still works",second.signal),"still works");
});

test("provider concurrency stays bounded and failed work releases its slot",async()=>{
 const slot=requestScopedLimiter(1),signal=new AbortController().signal;let release!:()=>void,started=false;
 const first=slot(()=>new Promise<void>(resolve=>{release=resolve}),signal);
 const second=slot(async()=>{started=true;throw new Error("upstream failed")},signal);
 const rejected=assert.rejects(second,/upstream failed/);
 assert.equal(started,false);release();await first;await rejected;
 assert.equal(await slot(async()=>"recovered",signal),"recovered");
});

test("direct relationships preserve direction and entity kind for every brand",()=>{
 for(const brand of ["Sprite","Northstar"]){
  assert.equal(directConnectionType("Manufacturer","brand"),"company");
  assert.equal(directConnectionType("Manufacturer","brand","brand"),"company");
  assert.equal(directConnectionReason("Manufacturer",brand,"Example Company"),`Example Company manufactures ${brand}.`);
 }
 assert.equal(directConnectionReason("Founded by","Example Brand","Example Founder"),"Example Brand was founded by Example Founder.");
 assert.equal(directConnectionReason("Directed by","Example Director","Example Film"),"Directed by Example Director.");
 assert.equal(directConnectionType("Screenplay by","person"),"movie");
 assert.equal(directConnectionType("Product of","brand"),"product");
 assert.equal(directConnectionType("Written by","person","tv show"),"tv show");
});

test("older manufacturer cards are repaired without changing identity or inventing relationships",()=>{
 const legacy={id:"wikidata:Q123",name:"Example Company",type:"product",queryType:"product",relation:"Manufactured by",seedName:"Example Brand",reason:"Manufactured by Example Brand."};
 const repaired=repairDirectConnection(legacy);
 assert.equal(repaired.id,legacy.id);assert.equal(repaired.type,"company");assert.equal(repaired.queryType,"company");
 assert.equal(repaired.relation,"Manufacturer");assert.equal(repaired.reason,"Example Company manufactures Example Brand.");
 const ordinary={name:"An unrelated book",type:"book",reason:"Qloo audience affinity"};
 assert.deepEqual(repairDirectConnection(ordinary),ordinary);
});

test("category matches require affinity and subject relevance, including when scoring fails",()=>{
 assert.equal(qualifiesCategoryMatch(.98,.1),false);
 assert.equal(qualifiesCategoryMatch(.98,undefined),false);
 assert.equal(qualifiesCategoryMatch(undefined,.95),false);
 assert.equal(qualifiesCategoryMatch(.4,.95),false);
 assert.equal(qualifiesCategoryMatch(.9,.8),true);
 assert.equal(qualifiesCategoryMatch(.9,NaN),false);
});
import {latestFeedback} from "../lib/feedback.ts";

test("latest explicit feedback overrides repeated saves and browsing",()=>{
 const event=(kind:string,createdAt:number)=>({entityId:"a",kind,createdAt});
 assert.deepEqual(latestFeedback([event("love",1),event("love",2),event("unlove",3),event("open",4)]),[]);
 assert.equal(latestFeedback([event("reject",3),event("love",5)])[0]?.kind,"love");
 assert.deepEqual(latestFeedback([event("open",1),event("explore",2)]),[]);
});

const post = (body: BodyInit, headers: Record<string, string> = {}) =>
  new Request("http://localhost/api/x", { method: "POST", headers: { host: "localhost", ...headers }, body });

test("jevScore clamps scores to 0..1 and drops non-numbers", async () => {
  process.env.JEV = "test";
  const original = globalThis.fetch;
  globalThis.fetch = (async () =>
    new Response(JSON.stringify({ answers: { a: { noul: 7 }, b: { noul: -2 }, c: { noul: "x" }, d: { noul: 0.4 } } }))) as typeof fetch;
  try {
    const scores = await jevScore("state", { a: "a", b: "b", c: "c", d: "d" });
    assert.deepEqual(scores, { a: 1, b: 0, d: 0.4 });
  } finally {
    globalThis.fetch = original;
  }
});

test("jevScore returns null without a key or on failure", async () => {
  delete process.env.JEV;
  delete process.env.TYPESAFE_API_KEY;
  assert.equal(await jevScore("s", { a: "a" }), null);
});

test("recommendation reranker preserves relevance while diversifying the selected set",()=>{
 const candidates=[
  {id:"a",type:"book",tags:["comedy","satire"],affinity:.96,quality:96,taste:.8},
  {id:"b",type:"book",tags:["comedy","satire"],affinity:.95,quality:95,taste:.8},
  {id:"c",type:"movie",tags:["comedy","absurdism"],affinity:.91,quality:91,taste:.7},
  {id:"d",type:"artist",tags:["rock","dark humor"],affinity:.89,quality:89,taste:.7},
 ];
 const ranked=diversifyRecommendations(candidates,{limit:3});
 assert.equal(ranked[0].id,"a");
 assert.deepEqual(new Set(ranked.map(item=>item.type)),new Set(["book","movie","artist"]));
});

test("recommendation reranker suppresses seen, rejected and rejected-theme candidates",()=>{
 const candidates=[
  {id:"seen",type:"movie",tags:["comedy"],affinity:.99},
  {id:"rejected",type:"book",tags:["comedy"],affinity:.99},
  {id:"bad-theme",type:"artist",tags:["gore"],affinity:.98},
  {id:"fresh",type:"place",tags:["architecture"],affinity:.82},
 ];
 const ranked=diversifyRecommendations(candidates,{limit:1,seenIds:["seen"],rejectedIds:["rejected"],rejectedTags:["gore"]});
 assert.equal(ranked[0].id,"fresh");
});

test("card API context is normalized and strictly bounded", () => {
  const card = sanitizeCard({ id: ` id\u0000${"x".repeat(300)} `, name: `  A\n${"b".repeat(200)}  `, type: ` movie ${"z".repeat(80)}`, description: "d".repeat(900), tags: [...Array.from({ length: 12 }, (_, index) => ` tag ${index} `), 42] });
  assert.ok(card);
  assert.equal(card.id.length, 200);
  assert.equal(card.name.length, 120);
  assert.equal(card.type.length, 40);
  assert.equal(card.description?.length, 600);
  assert.equal(card.tags?.length, 8);
  assert.equal(sanitizeCard({ id: "", name: "Missing id", type: "movie" }), null);
  assert.equal(sanitizeCard("not an object"), null);
});

test("daily budgets increase only in development, retaining production and test defaults",()=>{
 for(const[route,base]of Object.entries({agent:30,card:300,suggestions:200,discover:800})){
  assert.equal(dailyLimitFor(route,"development"),base*10);
  assert.equal(dailyLimitFor(route,"production"),base);
  assert.equal(dailyLimitFor(route,"test"),base);
  assert.equal(dailyLimitFor(route,"unknown"),base);
 }
 assert.equal(dailyLimitFor("unknown-route","development"),undefined);
 assert.equal(dailyLimitFor("toString","development"),undefined);
});

test("the daily budget remains enforced even with a higher minute allowance",async()=>{
 const cap=dailyLimitFor("agent");assert.ok(cap);
 for(let i=0;i<cap;i++)assert.equal(guard(post("{}"),"agent",cap+1),null);
 const blocked=guard(post("{}"),"agent",cap+1);
 assert.equal(blocked?.status,429);
 assert.deepEqual(await blocked?.json(),{error:"Daily limit reached for this feature — come back tomorrow."});
});

test("guard rejects foreign and malformed origins", () => {
  assert.equal(guard(post("{}", { origin: "https://evil.example" }), "t1", 5)?.status, 403);
  assert.equal(guard(post("{}", { origin: "not a url" }), "t2", 5)?.status, 403);
  assert.equal(guard(post("{}", { origin: "http://localhost" }), "t3", 5), null);
});

test("guard rate-limits per route and IP", () => {
  process.env.TRUST_PROXY_HEADERS = "1";
  const ip = { "x-forwarded-for": "9.9.9.9" };
  for (let i = 0; i < 3; i++) assert.equal(guard(post("{}", ip), "t4", 3), null);
  assert.equal(guard(post("{}", ip), "t4", 3)?.status, 429);
  assert.equal(guard(post("{}", { "x-forwarded-for": "8.8.8.8" }), "t4", 3), null);
  delete process.env.TRUST_PROXY_HEADERS;
});

test("guard ignores spoofed forwarding headers without a trusted proxy", () => {
  for (let i = 0; i < 2; i++) assert.equal(guard(post("{}", { "x-real-ip": `1.1.1.${i}`, "x-forwarded-for": `2.2.2.${i}` }), "t-spoof", 2), null);
  assert.equal(guard(post("{}", { "x-real-ip": "9.9.9.9", "x-forwarded-for": "8.8.8.8" }), "t-spoof", 2)?.status, 429);
});

test("forged Cloudflare headers cannot rotate the rate-limit bucket",()=>{
 delete process.env.TRUST_PROXY_HEADERS;
 assert.equal(guard(post("{}",{"cf-ray":"fake","cf-connecting-ip":"1.1.1.1"}),"cf-spoof",1),null);
 assert.equal(guard(post("{}",{"cf-ray":"also-fake","cf-connecting-ip":"2.2.2.2"}),"cf-spoof",1)?.status,429);
});

test("trusted proxy uses the appended peer and ignores forged real-ip",()=>{
 process.env.TRUST_PROXY_HEADERS="1";
 try{
  assert.equal(guard(post("{}",{"x-forwarded-for":"fake, 1.1.1.1","x-real-ip":"2.2.2.2"}),"proxy-spoof",1),null);
  assert.equal(guard(post("{}",{"x-forwarded-for":"different, 1.1.1.1","x-real-ip":"3.3.3.3"}),"proxy-spoof",1)?.status,429);
 }finally{delete process.env.TRUST_PROXY_HEADERS}
});

test("concert film description takes priority over an ambiguous album class",()=>{
 assert.equal(wikidataWorkType(["Q482994"],"documentary film directed by Dick Carruthers (1998)"),"movie");
 assert.equal(wikidataWorkType(["Q482994"],"1994 studio album by Portishead"),"album");
});

test("readJson enforces a real byte limit even without Content-Length", async () => {
  const big = new Request("http://localhost/api/x", {
    method: "POST",
    headers: { host: "localhost", "x-forwarded-for": "7.7.7.7" },
    body: JSON.stringify({ x: "a".repeat(5000) }),
  });
  assert.equal(guard(big, "t5", 5, 1000), null);
  await assert.rejects(() => readJson(big));
  const small = post(JSON.stringify({ ok: true }), { "x-forwarded-for": "6.6.6.6" });
  assert.equal(guard(small, "t6", 5, 1000), null);
  assert.deepEqual(await readJson(small), { ok: true });
});

test("study assignment is deterministic and covers all counterbalanced variants", () => {
  assert.deepEqual(assignmentFor("S-ABCDEFGH"), assignmentFor("S-ABCDEFGH"));
  const variants = new Set(Array.from({ length: 200 }, (_, index) => JSON.stringify(assignmentFor(`S-${index.toString().padStart(8, "0")}`))));
  assert.equal(variants.size, 4);
});

test("study timing and category metrics are auditable", () => {
  assert.equal(trialDuration({ condition: "sideways", task: "nostalgic-wonder", startedAt: 1000, completedAt: 4500, references: [], savedEvents: 0, rejectedEvents: 0 }), 3500);
  const references = [{ name: "a", category: "Film", rationale: "x" }, { name: "b", category: "film", rationale: "x" }, { name: "c", category: "Place", rationale: "x" }, { name: "d", category: "Artist", rationale: "x" }];
  assert.equal(categoryDiversity(references), 3);
  assert.ok(categoryEntropy(references) > 1.4 && categoryEntropy(references) < 1.6);
});

test("study exports reject malformed records and checksum tampering", async () => {
  const session: StudySessionV1 = { schema: STUDY_SCHEMA, protocol: STUDY_PROTOCOL, participantId: "S-ABCDEFGH", assignment: assignmentFor("S-ABCDEFGH"), createdAt: 1, appVersion: "test", trials: [] };
  const sealed = await sealSession(session);
  assert.equal((await validateSession(sealed)).ok, true);
  assert.equal((await validateSession({ ...sealed, participantId: "person@example.com" })).ok, false);
  assert.notEqual(await checksumSession({ ...sealed, createdAt: 2 }), sealed.checksum);
});

test("blinding hides conditions and aggregation stays locked below preregistered gates", () => {
  const references = Array.from({ length: 5 }, (_, index) => ({ name: `Reference ${index}`, category: ["film", "place", "artist"][index % 3], rationale: "Relevant cultural connection" }));
  const makeSession = (index: number): StudySessionV1 => ({ schema: STUDY_SCHEMA, protocol: STUDY_PROTOCOL, participantId: `S-${index.toString().padStart(8, "0")}`, assignment: assignmentFor(`S-${index.toString().padStart(8, "0")}`), createdAt: index, appVersion: "test", trials: [{ condition: "sideways", task: "nostalgic-wonder", startedAt: 0, completedAt: 200000, references, savedEvents: 5, rejectedEvents: 1, rating: { usefulness: 5, surprise: 4, confidence: 5, willingness: 5 } }, { condition: "normal", task: "rebellious-precision", startedAt: 0, completedAt: 300000, references, savedEvents: 0, rejectedEvents: 0, rating: { usefulness: 3, surprise: 3, confidence: 4, willingness: 3 } }] });
  const sessions = Array.from({ length: 10 }, (_, index) => makeSession(index));
  const outputs = blindedOutputs(sessions);
  assert.equal(outputs.length, 20);
  assert.equal(JSON.stringify(outputs).includes('"condition"'), false);
  assert.equal(aggregateEvidence(sessions, []).status, "in-progress");
  const scores = Object.fromEntries(outputs.map(output => [output.blindId, { relevance: 4, coherence: 5, usefulness: 5, surprise: 4, explanation: 5 }]));
  const reviews: ReviewerRecord[] = [{ reviewerId: "a", scores, completedAt: 1 }, { reviewerId: "b", scores, completedAt: 2 }];
  const aggregate = aggregateEvidence(sessions, reviews);
  assert.equal(aggregate.status, "complete");
  assert.equal(aggregate.metrics?.medianPairedTimeDifference, 100000);
  assert.equal(aggregate.metrics?.usableOutputs, 1);
});

test("synthetic rehearsal is deterministic, diverse, and explicitly not human evidence", () => {
  const first = runSyntheticStudy(DEFAULT_SYNTHETIC_SEED);
  const repeat = runSyntheticStudy(DEFAULT_SYNTHETIC_SEED);
  const alternate = runSyntheticStudy(DEFAULT_SYNTHETIC_SEED + 1);
  assert.deepEqual(first, repeat);
  assert.notDeepEqual(first.aggregate.metrics?.pairedTimes, alternate.aggregate.metrics?.pairedTimes);
  assert.equal(first.kind, "synthetic");
  assert.match(first.disclosure, /not human participants/i);
  assert.equal(first.sessions.length, 12);
  assert.equal(first.aggregate.status, "complete");
  assert.equal(SYNTHETIC_PERSONAS.length, 12);
  assert.ok(new Set(SYNTHETIC_PERSONAS.map(persona => persona.role)).size >= 10);
  assert.ok(first.sessions.every(session => session.appVersion.startsWith("synthetic:")));
});

test("anchor matches need a specific shared subject, not just a broad genre or audience link",()=>{
 assert.equal(qualifiesAnchorMatch(.95,.85,.2),true);
 assert.equal(qualifiesAnchorMatch(.95,.7,.6),false);
 assert.equal(qualifiesAnchorMatch(.95,.62,.45),false);
 assert.equal(qualifiesAnchorMatch(.95,.9,undefined),false);
 assert.equal(qualifiesAnchorMatch(.7,.95,.05),false);
 assert.equal(qualifiesAnchorMatch(undefined,.95,.05),false);
});

test("title-only candidates never qualify, whatever the score",()=>{
 const bare={id:"x",name:"Virunga",type:"movie",affinity:.95};
 assert.equal(hasEvidence(bare),false);
 assert.equal(qualifies(bare,{subject:.95,loose:.05}),false);
 assert.equal(qualifies({...bare,tags:["documentary","conservation"]},{subject:.95,loose:.05}),true);
});

test("relevance cache re-judges when candidate evidence changes, and reports partial failures",async()=>{
 const original=globalThis.fetch,previous=process.env.JEV;let calls=0,omit=false;process.env.JEV="test";
 globalThis.fetch=(async(_url:unknown,init?:{body?:string})=>{calls++;const questions=Object.keys(JSON.parse(init?.body??"{}").questions??{}),climbing=(init?.body??"").includes("climb");return new Response(JSON.stringify({answers:Object.fromEntries(questions.filter(id=>!(omit&&id.endsWith("1"))).map(id=>[id,{noul:id.startsWith("s")?(climbing?.05:.9):(climbing?.8:.1)}]))}),{status:200})}) as typeof fetch;
 try{
  const anchor={id:"a-"+Math.random(),name:"Permanent Record",type:"book",description:"Edward Snowden's memoir about mass surveillance and the NSA whistleblowing leaks.",tags:["surveillance"]};
  const doc={id:"c1",name:"Doc",type:"movie",description:"A documentary about digital privacy and government data collection.",tags:["privacy","documentary"],affinity:.95};
  const first=await judgeRelevance(anchor,[doc]);assert.equal(qualifies(doc,first?.scores.get("c1")),true);assert.equal(calls,1);
  await judgeRelevance(anchor,[doc]);assert.equal(calls,1,"unchanged evidence is served from cache");
  const edited={...doc,description:"A documentary about mountain climbing on El Capitan.",tags:["climbing","documentary"]};
  const second=await judgeRelevance(anchor,[edited]);assert.equal(calls,2,"edited evidence triggers a new judgement");assert.equal(qualifies(edited,second?.scores.get("c1")),false);
  omit=true;const other={...doc,id:"c2",description:"A second documentary about privacy and surveillance capitalism."};
  const partial=await judgeRelevance({...anchor,id:"b-"+Math.random()},[doc,other]);assert.equal(partial?.unjudged.size,1,"candidates without a score are reported as unjudged");
 }finally{globalThis.fetch=original;if(previous===undefined)delete process.env.JEV;else process.env.JEV=previous}
});

test("taste-memory retrieval keeps only feedback for the requested map, so browsing elsewhere cannot evict it",()=>{
 const event=(kind:MemoryEvent["kind"],sessionId:string):MemoryEvent=>({id:Math.random().toString(),entityId:"x",kind,weight:1,sessionId,createdAt:1});
 const browsing=Array.from({length:1201},()=>event("open","map-b"));
 const kept=[event("love","map-a"),...browsing].filter(item=>isRetrievableEvent(item,"map-a"));
 assert.equal(kept.length,1);assert.equal(kept[0].kind,"love");
 assert.equal(isRetrievableEvent(event("open","map-a"),"map-a"),false);
});

test("graph paths drop edges that touch a currently rejected reference",()=>{
 const edge=(from:string,to:string):MemoryEdge=>({id:`${from}:${to}`,from,to,relation:"discovered_from",score:.9,sessionId:"s",createdAt:1});
 const names=new Map([["a",{name:"Anchor"}],["b",{name:"Kept"}],["r",{name:"Rejected"}]]);
 assert.deepEqual(graphPaths([edge("a","b"),edge("a","r")],names,new Set(["a"]),new Set(["r"]),"s"),["Anchor → Kept"]);
});

test("memory reconciliation: all rejections filter paths, removed edges are pruned, sparse updates keep evidence, same-ms feedback is ordered",()=>{
 const edge=(from:string,to:string):MemoryEdge=>({id:`s:${from}:${to}`,from,to,relation:"discovered_from",score:.9,sessionId:"s",createdAt:1});
 const rejected=Array.from({length:10},(_,i)=>`r${i}`),names=new Map<string,{name:string}>([["a",{name:"A"}],...rejected.map(id=>[id,{name:id}] as [string,{name:string}])]);
 assert.deepEqual(graphPaths(rejected.map(id=>edge("a",id)),names,new Set(["a"]),new Set(rejected),"s"),[]);
 assert.deepEqual(obsoleteEdgeIds([edge("a","b"),edge("a","c")],new Set(["s:a:b"])),["s:a:c"]);
 const stored=mergeEntity(undefined,{id:"x",name:"X",type:"movie",description:"A film about surveillance and privacy.",tags:["privacy","documentary"]},1);
 const sparse=mergeEntity(stored,{id:"x",name:"X",type:"movie"},2);
 assert.deepEqual(sparse.tags,["privacy","documentary"]);assert.equal(sparse.description,stored.description);
 const love={entityId:"x",kind:"love",createdAt:5,seq:5000},unlove={entityId:"x",kind:"unlove",createdAt:5,seq:5001};
 assert.deepEqual(latestFeedback([unlove,love]),[],"higher seq wins regardless of array order");
 assert.deepEqual(latestFeedback([{entityId:"y",kind:"love",createdAt:5},{entityId:"y",kind:"unlove",createdAt:5}]),[],"legacy tie: later chronological entry wins");
});

test("relevance margin boundaries are decided consistently",()=>{
 assert.equal(qualifiesAnchorMatch(.9,.6,.4),true);assert.equal(qualifiesAnchorMatch(.9,.7,.5),true);assert.equal(qualifiesAnchorMatch(.9,.61,.41),true);assert.equal(qualifiesAnchorMatch(.9,.6,.41),false);
});

test("editions are not new discoveries",()=>{
 assert.equal(isEditionOf("Disco Elysium","video_game","Disco Elysium: The Final Cut","video_game"),true);
 assert.equal(isEditionOf("Dune","book","Dune Messiah","book"),false);
 assert.equal(isEditionOf("Portal","video_game","Portal 2","video_game"),false);
 assert.equal(isEditionOf("DOOM","video_game","DOOM Eternal Deluxe Edition","video_game"),false);
 assert.equal(isEditionOf("Resident Evil","video_game","Resident Evil 2 Remake","video_game"),false);
 assert.equal(isEditionOf("Doom","video_game","Doom (Deluxe Edition)","video_game"),true);
 assert.equal(isEditionOf("Voyage: Part One","video_game","Voyage: Part Two Deluxe Edition","video_game"),false);
 assert.equal(isEditionOf("Hollow Knight","video_game","Hollow Knight: Voidheart Edition","video_game"),true);
 assert.equal(isEditionOf("Voyage: Part One","video_game","Voyage: Part One Deluxe Edition","video_game"),true);
});

test("based-on wording never repeats the source title",()=>{
 assert.equal(directConnectionReason("Source work of Children of Men","Children of Men","The Children of Men"),"Children of Men is based on this.");
 assert.equal(directConnectionReason("Based on Undertale","Undertale","Deltarune"),"Based on Undertale.");
});

test("global budget fails closed and persists across fresh state", async () => {
  const {reserveGlobal}=await import("../lib/guard.ts");
  const {mkdtempSync,writeFileSync,readFileSync}=await import("node:fs");
  const dir=mkdtempSync("/tmp/guard-test-"),file=`${dir}/guard.json`;
  assert.equal(reserveGlobal("agent",Date.now(),file),null);
  assert.equal(JSON.parse(readFileSync(file,"utf8")).counts.agent,1);
  writeFileSync(file,JSON.stringify({start:Date.now(),counts:{agent:400}}));
  assert.equal(reserveGlobal("agent",Date.now(),file)?.status,429);
  assert.equal(reserveGlobal("agent",Date.now(),"/nonexistent-dir/guard.json")?.status,503);
  writeFileSync(file,"{broken");
  assert.equal(reserveGlobal("agent",Date.now(),file)?.status,503);
});

test("P144 'based on a work by' never invents a movie type or adaptation claim", async () => {
  const {directConnectionType,directConnectionReason,wikidataWorkType}=await import("../lib/direct-connections.ts");
  assert.equal(wikidataWorkType([],"policy plan by the Heritage Foundation"),undefined);
  assert.notEqual(directConnectionType("Based on a work by","author",undefined),"movie");
  assert.doesNotMatch(directConnectionReason("Based on a work by","George Orwell","Project 2025"),/adapted/);
});

test("same-creator links name the shared role", async () => {
  const {directConnectionReason}=await import("../lib/direct-connections.ts");
  assert.equal(directConnectionReason("Also directed by Helen Shaver","Station Eleven","The Penguin"),"Helen Shaver is credited as director of both Station Eleven and The Penguin.");
});

test("geographic results must confirm the selected region, not just the country", async () => {
  const {confirmsArea}=await import("../lib/geography.ts");
  const ontario={region:"Ontario",country:"Canada"},bc={country:"Canada",admin1_region:"British Columbia",city:"Vancouver"},toronto={country:"Canada",admin1_region:"Ontario",city:"Toronto"};
  assert.equal(confirmsArea(ontario,bc),false);
  assert.equal(confirmsArea(ontario,toronto),true);
  assert.equal(confirmsArea({region:"Indiana",country:"United States of America"},{country:"United States",admin1_region:"Indiana"}),true);
  assert.equal(confirmsArea({country:"Scotland"},{country:"United States",admin1_region:"Indiana",city:"Edinburgh"}),false);
  assert.equal(confirmsArea({country:"Scotland"},{country:"United Kingdom",admin1_region:"Scotland"}),true);
  assert.equal(confirmsArea({region:"France métropolitaine",country:"France (terres)"},{country:"France",admin1_region:"Ile-de-France",city:"Paris"}),true);
  assert.equal(confirmsArea({},{country:"France"}),false);
});

test("a region containing the country's name is still enforced", async () => {
  const {confirmsArea}=await import("../lib/geography.ts");
  assert.equal(confirmsArea({region:"Île-de-France",country:"France"},{country:"France",admin1_region:"Nouvelle-Aquitaine",city:"Bordeaux"}),false);
  assert.equal(confirmsArea({region:"Île-de-France",country:"France"},{country:"France",admin1_region:"Ile-de-France",city:"Paris"}),true);
  assert.equal(confirmsArea({region:"France métropolitaine",country:"France (terres)"},{country:"France",admin1_region:"Nouvelle-Aquitaine"}),true);
});

test("music type is identical before and after reload", async () => {
  const {wikidataWorkType,repairDirectConnection}=await import("../lib/direct-connections.ts");
  const live=wikidataWorkType(["Q482994"],"song by Arlo Parks");
  const restored=repairDirectConnection({id:"wikidata:Q96072224",name:"Black Dog",type:live!,description:"song by Arlo Parks",relation:"Performed by",seedName:"Arlo Parks"}).type;
  assert.equal(live,"song");assert.equal(restored,live);
});
