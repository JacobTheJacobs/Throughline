import {aggregateEvidence,assignmentFor,blindedOutputs,STUDY_PROTOCOL,STUDY_SCHEMA,type AggregateEvidence,type ReviewerRecord,type StudyCondition,type StudyReference,type StudySessionV1,type StudyTask} from "./study.ts";

export const SYNTHETIC_SCHEMA="sideways.synthetic-evaluation.v1" as const;
export const SYNTHETIC_ENGINE="persona-simulator-2026-10-25.v1" as const;
export const DEFAULT_SYNTHETIC_SEED=104729;

export type SyntheticPersona={
 id:string;
 name:string;
 role:string;
 bio:string;
 patience:number;
 curiosity:number;
 crossDomain:number;
 toolFluency:number;
 skepticism:number;
};

export const SYNTHETIC_PERSONAS:SyntheticPersona[]=[
 {id:"p01",name:"Maya",role:"Brand strategist",bio:"Fast, evidence-led, and impatient with generic references.",patience:.35,curiosity:.72,crossDomain:.82,toolFluency:.88,skepticism:.78},
 {id:"p02",name:"Jonah",role:"Independent filmmaker",bio:"Follows emotional tone across films, music, and locations.",patience:.72,curiosity:.92,crossDomain:.9,toolFluency:.62,skepticism:.42},
 {id:"p03",name:"Priya",role:"UX researcher",bio:"Methodical and cautious; values explanations over novelty.",patience:.9,curiosity:.62,crossDomain:.58,toolFluency:.8,skepticism:.9},
 {id:"p04",name:"Theo",role:"Junior designer",bio:"Visual-first, playful, and easily distracted by weak matches.",patience:.44,curiosity:.88,crossDomain:.76,toolFluency:.7,skepticism:.3},
 {id:"p05",name:"Amara",role:"Creative director",bio:"Looks for coherent territories she can defend to a client.",patience:.55,curiosity:.75,crossDomain:.9,toolFluency:.9,skepticism:.84},
 {id:"p06",name:"Luis",role:"Music supervisor",bio:"Expert in sound, exploratory elsewhere, allergic to obvious picks.",patience:.63,curiosity:.94,crossDomain:.79,toolFluency:.82,skepticism:.68},
 {id:"p07",name:"Noor",role:"Travel writer",bio:"Place-led storyteller who prefers specificity and lived texture.",patience:.8,curiosity:.86,crossDomain:.74,toolFluency:.58,skepticism:.61},
 {id:"p08",name:"Eli",role:"Agency producer",bio:"Deadline-driven and pragmatic; wants usable answers quickly.",patience:.25,curiosity:.48,crossDomain:.55,toolFluency:.92,skepticism:.7},
 {id:"p09",name:"Sasha",role:"Culture journalist",bio:"Wide-ranging, critical, and interested in unexpected connections.",patience:.76,curiosity:.96,crossDomain:.94,toolFluency:.77,skepticism:.88},
 {id:"p10",name:"Kenji",role:"Illustrator",bio:"Quiet browser who builds worlds from images, books, and objects.",patience:.86,curiosity:.83,crossDomain:.87,toolFluency:.5,skepticism:.47},
 {id:"p11",name:"Rina",role:"Social strategist",bio:"Trend-aware and fast, with a bias toward recognizable references.",patience:.3,curiosity:.68,crossDomain:.64,toolFluency:.95,skepticism:.38},
 {id:"p12",name:"Owen",role:"Copywriter",bio:"Narrative-minded contrarian who tests whether a connection can be explained.",patience:.67,curiosity:.8,crossDomain:.72,toolFluency:.73,skepticism:.93},
];

const CATALOG:Record<StudyTask,StudyReference[]>={
 "nostalgic-wonder":[
  {name:"Maquia",category:"film",rationale:"Hand-crafted fantasy frames memory and separation with emotional restraint."},
  {name:"Snoopy Museum Tokyo",category:"place",rationale:"A tactile character archive turns familiar illustration into a physical world."},
  {name:"The Little Prince",category:"book",rationale:"Childlike wonder carries adult ideas about care, loss, and imagination."},
  {name:"Ichiko Aoba",category:"artist",rationale:"Intimate acoustic worlds evoke nature, stillness, and dreamlike movement."},
  {name:"Monument Valley",category:"game",rationale:"Impossible architecture becomes a calm, touchable storybook journey."},
  {name:"Tove Jansson",category:"artist",rationale:"Moomin stories balance sanctuary, melancholy, and playful independence."},
  {name:"Naoshima",category:"place",rationale:"Art, landscape, and slow travel meet in a quietly surreal island setting."},
 ],
 "rebellious-precision":[
  {name:"Air Jordan",category:"brand",rationale:"Performance engineering became a symbol of individual style and defiance."},
  {name:"Moneyball",category:"film",rationale:"A disciplined system challenges institutional instinct and accepted wisdom."},
  {name:"Virgil Abloh",category:"artist",rationale:"Rules of luxury and street culture are remixed through precise visual systems."},
  {name:"Bauhaus Dessau",category:"place",rationale:"Radical reduction joins function, geometry, and a new social proposition."},
  {name:"The Creative Act",category:"book",rationale:"Creative confidence is framed as deliberate practice rather than mythology."},
  {name:"Tony Hawk's Pro Skater",category:"game",rationale:"Technical mastery and subculture energy share the same expressive surface."},
  {name:"Run-DMC",category:"artist",rationale:"Minimal beats, sharp identity, and street credibility changed popular culture."},
 ],
};

function mulberry32(seed:number){let state=seed>>>0;return()=>{state+=0x6D2B79F5;let value=state;value=Math.imul(value^value>>>15,value|1);value^=value+Math.imul(value^value>>>7,value|61);return((value^value>>>14)>>>0)/4294967296}}
const clamp=(value:number,min=1,max=5)=>Math.max(min,Math.min(max,value));
const score=(value:number)=>Math.round(clamp(value));
function shuffle<T>(items:T[],random:()=>number){for(let index=items.length-1;index>0;index--){const target=Math.floor(random()*(index+1));[items[index],items[target]]=[items[target],items[index]]}return items}
function conditionTrial(persona:SyntheticPersona,condition:StudyCondition,task:StudyTask,random:()=>number,index:number){
 const sideways=condition==="sideways",breadth=sideways?.92:.48+persona.crossDomain*.34,catalog=shuffle([...CATALOG[task]],random),categories=new Set<string>(),references:StudyReference[]=[];
 for(const candidate of catalog){if(references.length===5)break;if(random()<breadth||categories.size<3){references.push({...candidate,path:sideways?[task,candidate.name]:undefined});categories.add(candidate.category)}}
 while(references.length<5)references.push({...catalog[references.length%catalog.length]});
 const speedBase=sideways?205000:270000;
 const duration=Math.round(speedBase-(persona.toolFluency*(sideways?28000:52000))-(persona.curiosity*9000)+(persona.patience*18000)+(random()-.5)*70000);
 const usefulness=3+(sideways?.65:.05)+persona.crossDomain*.45-persona.skepticism*.22+(random()-.5)*1.4;
 const surprise=2.8+(sideways?.75:.1)+persona.curiosity*.5+(random()-.5)*1.5;
 const confidence=3.15+(sideways?.55:.15)+persona.toolFluency*.3-persona.skepticism*.15+(random()-.5)*1.2;
 const willingness=2.8+(sideways?.75:0)+persona.crossDomain*.45-persona.skepticism*.2+(random()-.5)*1.5;
 const startedAt=1761360000000+index*7200000;
 return{condition,task,startedAt,completedAt:startedAt+Math.max(105000,duration),references,savedEvents:sideways?5:0,rejectedEvents:Math.round(persona.skepticism*3+random()*2),generatedBrief:sideways?`${task.replaceAll("-"," ")}: ${references.map(item=>item.name).join(", ")}.`:undefined,rating:{usefulness:score(usefulness),surprise:score(surprise),confidence:score(confidence),willingness:score(willingness)},events:sideways?references.map((reference,eventIndex)=>({kind:"save",nodeId:reference.name,at:startedAt+30000+eventIndex*24000})):[]};
}

export type SyntheticRun={schema:typeof SYNTHETIC_SCHEMA;engine:typeof SYNTHETIC_ENGINE;kind:"synthetic";seed:number;generatedAt:string;disclosure:string;personas:SyntheticPersona[];sessions:StudySessionV1[];reviews:ReviewerRecord[];aggregate:AggregateEvidence};

export function runSyntheticStudy(seed=DEFAULT_SYNTHETIC_SEED):SyntheticRun{
 const random=mulberry32(seed),sessions=SYNTHETIC_PERSONAS.map((persona,index)=>{const participantId=`S-${String(70000000+index)}`,assignment=assignmentFor(participantId),createdAt=1761360000000+index*7200000;return{schema:STUDY_SCHEMA,protocol:STUDY_PROTOCOL,participantId,assignment,createdAt,appVersion:`synthetic:${SYNTHETIC_ENGINE}`,trials:[conditionTrial(persona,assignment.firstCondition,assignment.firstTask,random,index),conditionTrial(persona,assignment.secondCondition,assignment.secondTask,random,index)]} satisfies StudySessionV1});
 const outputs=blindedOutputs(sessions),conditionByOutput=new Map<string,StudyCondition>();
 for(const session of sessions){const sessionOutputs=blindedOutputs([session]);for(const trial of session.trials){const match=sessionOutputs.find(output=>output.task===trial.task);if(match)conditionByOutput.set(match.blindId,trial.condition)}}
 const reviewers=[{id:"reviewer-methodical",leniency:-.15},{id:"reviewer-exploratory",leniency:.15}].map((reviewer,reviewIndex)=>({reviewerId:reviewer.id,completedAt:1761500000000+reviewIndex,scores:Object.fromEntries(outputs.map(output=>{const condition=conditionByOutput.get(output.blindId)??"normal",boost=condition==="sideways"?.35:0,noise=(random()-.5)*1.1;return[output.blindId,{relevance:score(3.7+boost+reviewer.leniency+noise),coherence:score(3.5+boost+.15+reviewer.leniency+noise),usefulness:score(3.4+boost+reviewer.leniency+noise),surprise:score(3.1+(condition==="sideways"?.65:.1)+reviewer.leniency+noise),explanation:score(3.25+(condition==="sideways"?.8:0)+reviewer.leniency+noise)}]}))}));
 return{schema:SYNTHETIC_SCHEMA,engine:SYNTHETIC_ENGINE,kind:"synthetic",seed,generatedAt:"2026-10-25",disclosure:"Synthetic agent rehearsal only. These personas are simulations, not human participants, and these results are not evidence of real-world impact.",personas:SYNTHETIC_PERSONAS,sessions,reviews:reviewers,aggregate:aggregateEvidence(sessions,reviewers)};
}
