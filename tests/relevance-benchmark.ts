// Labeled benchmark for the shared anchor-relevance gate (lib/relevance.ts). Needs JEV in the env.
// Runs every judgement RUNS times under fresh cache keys to measure accuracy and run-to-run stability.
// Usage: node --experimental-strip-types --no-warnings tests/relevance-benchmark.ts
//
// Product rule the labels encode: KEEP when the candidate shares a concrete subject, real-world topic,
// setting, central idea or distinctive craft with the reference. REJECT when the only link is a broad
// genre label (e.g. "space opera", "documentary"), format, mood or audience overlap.
// Cases marked "live" were retrieved by the running app from Qloo, not written by hand.
import {judgeRelevance,qualifies,type RelevanceItem} from "../lib/relevance.ts";
const RUNS=Number(process.env.RUNS||3);
const anchors:Record<string,RelevanceItem>={
 record:{id:"permanent-record",name:"Permanent Record",type:"book",description:"Edward Snowden, the man who risked everything to expose the US government's system of mass surveillance, reveals the story of his life and how he helped build that system.",tags:["memoir","surveillance","privacy","politics"]},
 ghibli:{id:"studio-ghibli",name:"Studio Ghibli",type:"brand",description:"Japanese animation studio behind hand-drawn films such as Spirited Away and My Neighbor Totoro, known for nature, flight and childhood wonder.",tags:["anime","animation","fantasy","japan"]},
 dune:{id:"dune",name:"Dune",type:"book",description:"Frank Herbert's science-fiction epic of a desert planet, a noble family's betrayal, ecology, religion and the spice that controls the galaxy.",tags:["science fiction","space opera","ecology","politics"]},
 whiplash:{id:"whiplash",name:"Whiplash",type:"movie",description:"A talented drummer at a music conservatory pursues artistic greatness under an abusive instructor. Obsession and ambition threaten his relationships and wellbeing through tense musical performances and jazz-driven editing.",tags:["music","performance","psychological drama"]},
 hades:{id:"hades",name:"Hades",type:"video_game",description:"A Greek-mythology action roguelike dungeon crawler. Zagreus attempts to escape the Underworld in procedurally varied combat runs, dying and retrying with persistent progression, changing weapons and character interactions.",tags:["action","roguelike","dungeon crawler"]},
 darkness:{id:"darkness",name:"The Left Hand of Darkness",type:"book",description:"A human envoy tries to bring an alien world into an interstellar civilization. Inhabitants live mostly without a fixed gender. He must confront his cultural prejudices and negotiate radically different social and political systems.",tags:["anthropological science fiction","culture","politics"]},
};
const cases:Array<[keyof typeof anchors,RelevanceItem,boolean]>=[
 ["whiplash",{id:"birdman",name:"Birdman",type:"movie",description:"A former movie star writes, directs and stars in a Broadway play. His pursuit of artistic validation threatens his relationships and mental stability. Jazz-driven rhythm and a backstage setting explore performance, ego and artistic integrity.",tags:["performance","artistic integrity","psychological drama"]},true],
 ["whiplash",{id:"imitation",name:"The Imitation Game",type:"movie",description:"A mathematician leads a secret team breaking the Nazi Enigma code during World War II.",tags:["biography","war","cryptography"]},false],
 ["hades",{id:"dead-cells",name:"Dead Cells",type:"video_game",description:"A rogue-lite action platformer through a procedurally changing castle. Fight enemies with varied weapons, die, learn and retry; there are no checkpoints. Permanent unlocks and new paths support repeated combat runs.",tags:["roguelite","action","procedural combat"]},true],
 ["hades",{id:"football",name:"A football game",type:"video_game",description:"A realistic football simulation in which players manage teams and play football matches in licensed stadiums.",tags:["sports","simulation"]},false],
 ["darkness",{id:"dispossessed",name:"The Dispossessed",type:"book",description:"A physicist crosses from an isolated anarchist society to its capitalist sister planet. Cultural misunderstandings and contrasting social and political systems challenge his assumptions about freedom and human solidarity across alien civilizations.",tags:["anthropological science fiction","political systems","culture"]},true],
 ["darkness",{id:"juicy-gossip",name:"Juicy Gossip",type:"book",description:"A seventh-grade school newspaper editor is embarrassed by her parents' new juice bar and the gossip around it.",tags:["middle grade","school","fiction"]},false],
 ["record",{id:"great-hack",name:"The Great Hack",type:"movie",description:"Documentary on how Cambridge Analytica harvested personal data from Facebook to target voters.",tags:["documentary","data privacy","politics"]},true],
 ["record",{id:"citizenfour",name:"Citizenfour",type:"movie",description:"Laura Poitras documents her meetings with Edward Snowden in Hong Kong as he leaks NSA surveillance documents.",tags:["documentary","surveillance","whistleblower"]},true],
 ["record",{id:"1984",name:"Nineteen Eighty-Four",type:"book",description:"Orwell's novel of a totalitarian state that watches its citizens through telescreens.",tags:["dystopia","surveillance","classic"]},true],
 ["record",{id:"virunga",name:"Virunga",type:"movie",description:"Rangers in Congo's Virunga National Park fight to protect the last mountain gorillas from poachers and oil exploration.",tags:["documentary","wildlife","conservation"]},false],
 ["record",{id:"free-solo",name:"Free Solo",type:"movie",description:"Alex Honnold attempts to climb El Capitan without ropes.",tags:["documentary","climbing","adventure"]},false],
 ["record",{id:"educated",name:"Educated",type:"book",description:"Tara Westover's memoir of growing up in a survivalist family in Idaho and finding education.",tags:["memoir","family","education"]},false],
 // live: Permanent Record -> Books / Movies / agent, retrieved by the app on 2026-10-28.
 ["record",{id:"mindfck",name:"Mindf*ck: Cambridge Analytica and the Plot to Break America",type:"book",description:"Christopher Wylie, the whistleblower behind the Cambridge Analytica scandal, reveals how personal data was harvested to manipulate voters.",tags:["nonfiction","politics","technology"]},true],
 ["record",{id:"surveillance-capitalism",name:"The Age of Surveillance Capitalism",type:"book",description:"Shoshana Zuboff examines how technology companies harvest personal data to predict and shape human behaviour.",tags:["nonfiction","technology","privacy"]},true],
 ["ghibli",{id:"princess-kaguya",name:"The Tale of the Princess Kaguya",type:"movie",description:"Hand-drawn animated film adapting a Japanese folktale about a girl found in a bamboo stalk.",tags:["anime","animation","folklore"]},true],
 ["ghibli",{id:"wolfwalkers",name:"Wolfwalkers",type:"movie",description:"Hand-animated fantasy about a girl in Ireland who befriends a wolfwalker in the forest.",tags:["animation","fantasy","nature"]},true],
 ["ghibli",{id:"joe-hisaishi",name:"Joe Hisaishi",type:"artist",description:"Japanese composer known for orchestral film scores for Spirited Away, Totoro and Princess Mononoke.",tags:["soundtrack","composer","orchestral"]},true],
 ["ghibli",{id:"fast-furious",name:"Fast & Furious",type:"movie",description:"Street racers and heist crews in high-speed car action.",tags:["action","cars"]},false],
 ["ghibli",{id:"nike",name:"Nike",type:"brand",description:"American sportswear and athletic footwear company.",tags:["sportswear","fashion"]},false],
 // Genre sibling only (space opera); no shared desert, ecology or messiah subject under the rule above.
 ["dune",{id:"foundation",name:"Foundation",type:"book",description:"Asimov's saga of a mathematician predicting the fall of a galactic empire.",tags:["science fiction","space opera","politics"]},false],
 ["dune",{id:"nausicaa",name:"Nausicaä of the Valley of the Wind",type:"movie",description:"A princess tries to bring peace between humans and a toxic jungle ecosystem after a planetary collapse.",tags:["science fiction","ecology","anime"]},true],
 ["dune",{id:"lawrence",name:"Lawrence of Arabia",type:"movie",description:"T. E. Lawrence unites Arab tribes in the desert against the Ottoman Empire.",tags:["epic","desert","war"]},true],
 ["dune",{id:"notebook",name:"The Notebook",type:"movie",description:"A romance between a poor young man and a rich young woman in 1940s South Carolina.",tags:["romance","drama"]},false],
 ["dune",{id:"bake-off",name:"The Great British Bake Off",type:"tv_show",description:"Amateur bakers compete in a tent in the English countryside.",tags:["reality","cooking"]},false],
];
let tp=0,fp=0,fn=0,tn=0,unstable=0,failed=0;
for(const[key,candidate,label]of cases){
 const votes:boolean[]=[],seen:string[]=[];
 for(let run=0;run<RUNS;run++){const anchor={...anchors[key],id:`${anchors[key].id}#${Date.now()}-${run}`},item={...candidate,affinity:.95},result=await judgeRelevance(anchor,[item]);if(!result||!result.scores.has(item.id)){failed++;continue}const judgement=result.scores.get(item.id);if(judgement)seen.push(`${judgement.subject.toFixed(2)}/${judgement.loose.toFixed(2)}`);votes.push(qualifies(item,judgement))}
 if(!votes.length)continue;
 const majority=votes.filter(Boolean).length*2>votes.length;if(new Set(votes).size>1)unstable++;
 if(majority&&label)tp++;else if(majority)fp++;else if(label)fn++;else tn++;
 console.log(`${majority===label?"ok  ":"MISS"} ${anchors[key].name} -> ${candidate.name}: expected ${label?"keep":"reject"}, votes ${votes.map(Number).join("")} subject/loose ${seen.join(" ")}`);
}
const precision=tp/Math.max(1,tp+fp),recall=tp/Math.max(1,tp+fn);
console.log(`\nprecision ${precision.toFixed(2)} recall ${recall.toFixed(2)} accuracy ${((tp+tn)/Math.max(1,tp+tn+fp+fn)).toFixed(2)} unstable ${unstable}/${cases.length} failed calls ${failed}`);
const problems=[failed?`${failed} failed or partial JEV calls`:"",unstable>1?`${unstable} unstable cases (max 1)`:"",fp?`${fp} false positives`:"",precision<.9?"precision below 0.90":"",recall<.7?"recall below 0.70":""].filter(Boolean);
if(problems.length){console.error(`FAIL: ${problems.join("; ")}`);process.exit(1)}
