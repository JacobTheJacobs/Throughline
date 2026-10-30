export type SearchChoice={id:string;name:string;type:string;detail?:string;year?:number;image?:string;externalSource?:string;externalId?:string;popularity?:number};
export function canonicalDiscoveryType(value="discovery"){
 const type=value.replace("urn:entity:","").replaceAll("_"," ").trim().toLowerCase();
 if(["video game","videogame","game"].includes(type))return "video_game";
 if(["locality","destination","country","city","region"].includes(type))return "destination";
 if(["tv show","tv","television","show","series"].includes(type))return "tv_show";
 return type.replaceAll(" ","_");
}
export function searchNameKey(value:string){return value.normalize("NFD").replace(/\p{M}/gu,"").toLowerCase().replace(/[^\p{L}\p{N}]/gu,"")}
export function matchesSearchName(query:string,name:string,type:string){
 if(searchNameKey(query)===searchNameKey(name))return true;
 if(["book","movie","tv_show","video_game","album"].includes(canonicalDiscoveryType(type))&&searchNameKey(query)===searchNameKey(name.replace(/\s*[([][^)\]]*[)\]]\s*/g," ")))return true;
 // "The Dispossessed: An Ambiguous Utopia" is the work the query names; a subtitle must not hide it behind namesakes.
 if(["book","movie","tv_show","video_game","album"].includes(canonicalDiscoveryType(type))&&/:\s/.test(name)&&searchNameKey(query)===searchNameKey(name.split(/:\s/)[0]))return true;
 if(canonicalDiscoveryType(type)!=="brand")return false;
 // Legal suffixes are aliases, not a reason to hide a company among exact-title songs.
 const stem=(value:string)=>value.replace(/(?:,?\s+)(?:incorporated|inc\.?|limited|ltd\.?|llc|plc|ag|gmbh|corp(?:oration)?\.?|company|co\.?)$/i,"");
 return searchNameKey(stem(query))===searchNameKey(stem(name));
}
export function contradictsChoiceType(choice:SearchChoice){
 const detail=choice.detail??"",type=canonicalDiscoveryType(choice.type);
 if(type==="artist"&&/\bnot (?:a|an) (?:music(?:al)?\s+)?artist\b/i.test(detail))return true;
 return type==="brand"&&/\b(?:video game|videogame)\b/i.test(detail)&&!/\b(?:brand|company|studio|publisher|developer|merchandise)\b/i.test(detail);
}
export function choiceQuality(choice:SearchChoice){
 const descriptive=!!choice.detail&&choice.detail.length>=25&&!/^peerage person id=/i.test(choice.detail);
 return (choice.externalSource&&choice.externalId?6:0)+(descriptive?3:0)+(choice.image?1:0)+(choice.year?1:0)+(canonicalDiscoveryType(choice.type)==="destination"?4:0)+Math.max(0,Math.min(1,choice.popularity??0));
}
export function uniqueChoices<T extends SearchChoice>(choices:T[]){
 const byId=new Map<string,T>();
 for(const choice of choices){if(contradictsChoiceType(choice))continue;const previous=byId.get(choice.id);if(!previous||choiceQuality(choice)>choiceQuality(previous))byId.set(choice.id,choice)}
 return [...byId.values()].sort((a,b)=>choiceQuality(b)-choiceQuality(a));
}
export function choiceEvidence(choice:SearchChoice){return JSON.stringify({name:choice.name,type:choice.type,description:choice.detail??"none",year:choice.year??null,identity:choice.externalSource&&choice.externalId?`${choice.externalSource}:${choice.externalId}`:"not linked",hasImage:!!choice.image,popularity:choice.popularity??null})}

// A collection that contains the original book is not an entirely new reference.
// Do not confuse distinct adaptations ("1984 (Play)") with edition/bundle aliases.
// "Disco Elysium: The Final Cut" is an edition of Disco Elysium, not a new discovery from it.
const EDITION=/\b(?:final cut|definitive|remaster(?:ed)?|director'?s cut|complete|deluxe|game of the year|goty|anniversary|enhanced|special|expanded|ultimate|edition|remake)\b/i;
export function isEditionOf(source:string,sourceType:string,target:string,targetType:string){
 if(canonicalDiscoveryType(sourceType)!==canonicalDiscoveryType(targetType)||!source.trim())return false;
 const base=searchNameKey(source.replace(/\s*[([][^)\]]*[)\]]\s*/g," ")),rest=target.replace(/\s*[([]([^)\]]*)[)\]]\s*/g," $1 ");
 // The title in front of the edition words must be exactly the source title: "DOOM Eternal Deluxe Edition" and
 // "Resident Evil 2 Remake" are different works.
 // A subtitle is part of the title ("Voyage: Part One" vs "Voyage: Part Two Deluxe Edition"); only a trailing
 // ": The"/"the" joiner before the edition words is dropped.
 const qualifier=rest.match(EDITION),head=qualifier?rest.slice(0,qualifier.index):rest;
 // "Hollow Knight: Voidheart Edition": a single word between the title's colon and the edition word names the edition.
 const named=qualifier?rest.slice(0,qualifier.index).match(/^(.*?):\s*([\p{L}'’-]+)\s*$/u):null;if(named&&searchNameKey(named[1])===base&&!/^(?:part|chapter|episode|book|volume)$/i.test(named[2]))return true;
 return !!base&&!!qualifier&&searchNameKey(head.replace(/[:\s]*\b(?:the|a)\s*$/i,""))===base&&searchNameKey(target)!==base;
}
export function repeatsBookSource(source:string,sourceType:string,target:string,targetType:string){
 if(canonicalDiscoveryType(sourceType)!=="book"||canonicalDiscoveryType(targetType)!=="book")return false;
 // "(Southern Reach, #1-3)" contains "(Southern Reach, #1)": a series range covering the source's number.
 const own=source.match(/\(([^,#)]+?),?\s*#(\d+)\)/),range=target.match(/\(([^,#)]+?),?\s*#(\d+)\s*[-–]\s*(\d+)\)/);
 if(own&&range&&searchNameKey(own[1])===searchNameKey(range[1])&&Number(own[2])>=Number(range[2])&&Number(own[2])<=Number(range[3]))return true;
 const parts=target.split(/\s*[\/|]\s*|\s+(?:&|and)\s+/i);
 return parts.length>1&&parts.some(part=>searchNameKey(part)===searchNameKey(source));
}
