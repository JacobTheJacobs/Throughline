// A verified relationship still needs the right direction and entity type in the UI.
export function directConnectionType(relation:string,seedKind:string,actualType?:string){
 if(relation==="Manufacturer"||relation==="Manufactured by")return "company";
 if(actualType)return actualType;
 if(relation==="Founded by")return "person";
 if(relation==="Written by")return "book";
 if(["Directed by","Screenplay by","Appeared in"].includes(relation))return "movie";
 // A performer/composer relation does not identify the kind of musical work.
 if(["Performed by","Music by"].includes(relation))return "work";
 return seedKind==="brand"?"product":"work";
}

// Older saves used stronger adaptation wording than a Wikidata P144 edge supports.
function legacyBasedOn(relation:string){return relation.replace(/^Adapted from the same source as /,"Shares a source with ").replace(/^Source work of (.+)$/,"$1 is based on this").replace(/^Adapted from /,"Based on ")}
export function directConnectionReason(relation:string,source:string,target:string){
 if(relation==="Manufacturer"||relation==="Manufactured by")return `${target} manufactures ${source}.`;
 if(relation==="Founded by")return `${source} was founded by ${target}.`;
 // Imported credit statements are reported as what the source says, not as independently confirmed screen credits.
 {const role=relation.match(/^Also (?:(written|directed|developed|created) )?by (.+)$/);if(role)return role[1]?`${role[2]} is credited as ${({written:"author",directed:"director",developed:"developer",created:"creator"} as Record<string,string>)[role[1]]} of both ${source} and ${target}.`:`${target} is also by ${role[2]}, the creator of ${source}.`}
 if(relation==="Based on a work by")return `Wikidata records ${target} as based on a work by ${source}.`;
 if(relation==="Screenplay by")return `Wikidata lists ${source} among the screenwriters of ${target}.`;
 if(relation==="Located in")return `${target} is located in ${source}.`;
 // P144 "based on" relations carry their own subject; never append the source title again.
 if(/^(?:Adapted from|Adaptation of|Based on|Source for|Source work of|Shares source with|Shares a source with|Adapted from the same source as)\b|is based on this$/i.test(relation))return `${legacyBasedOn(relation).replace(/[.]+$/,"")}.`;
 return `${relation} ${source}.`;
}

// Use the source record's classification, not its credit relation, for unresolved works.
export function wikidataWorkType(instanceIds:string[],description=""){
 if(/\b(?:(?:video game|game|handheld|home) consoles?|gaming (?:device|hardware))\b/i.test(description))return "product";
 // Concert films can share an item with an album. Prefer the concrete film
 // description over a coexisting album class in that ambiguous source record.
 if(/\b(?:documentary film|concert film|film directed by)\b/i.test(description))return "movie";
 // The record's own description decides first, so a restored card (description only) gets the same type
 // as the live result (description + instance classes): "song by Arlo Parks" stays a song after reload.
 if(/\b(?:song|single)\b/i.test(description))return "song";
 if(/\b(?:album|EP|extended play)\b/i.test(description))return "album";
 if(instanceIds.includes("Q482994"))return "album";
 if(instanceIds.some(id=>["Q7366","Q134556"].includes(id)))return "song";
 if(/\b(?:television series|TV series|miniseries)\b/i.test(description))return "tv_show";
 if(/\bfilm\b/i.test(description))return "movie";
 if(/\b(?:novel|book|memoir)\b/i.test(description))return "book";
 if(/\bvideo game\b/i.test(description))return "video_game";
 return undefined;
}

// Repair older locally saved maps as well as new API responses. Never infer a new
// relationship: only correct records that already carry one of these verified labels.
export function repairDirectConnection<T extends {id?:string;name:string;type:string;description?:string;relation?:string;seedName?:string;reason?:string;queryType?:string}>(item:T):T{
 if(!item.seedName||!item.relation)return item;
 const musicalFallback=item.id?.startsWith("wikidata:")&&["Performed by","Music by"].includes(item.relation);
 const repairedMusic=musicalFallback?wikidataWorkType([],item.description??"")??(item.type==="song"?"work":item.type):undefined;
 const type=repairedMusic??directConnectionType(item.relation,"",item.type);
 const relation=item.relation==="Manufactured by"?"Manufacturer":item.relation;// older saves used a label that read backwards on the card
 return {...item,relation,type,queryType:type,reason:directConnectionReason(relation,item.seedName,item.name)};
}
