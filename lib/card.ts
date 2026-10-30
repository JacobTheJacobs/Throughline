// Card context shared by the JEV-scored routes.
export type CardContext={id:string;name:string;type:string;description?:string;tags?:string[];links?:Array<{label:string;url:string}>};
export function sanitizeCard(value:unknown):CardContext|null{
 if(!value||typeof value!=="object"||Array.isArray(value))return null;
 const raw=value as Record<string,unknown>,clean=(input:unknown,max:number)=>typeof input==="string"?input.replace(/[\u0000-\u001f\u007f]+/g," ").replace(/\s+/g," ").trim().slice(0,max):"",id=clean(raw.id,200),name=clean(raw.name,120),type=clean(raw.type,40);
 if(!id||!name||!type)return null;
 const description=clean(raw.description,600)||undefined,tags=Array.isArray(raw.tags)?raw.tags.map(tag=>clean(tag,50)).filter(Boolean).slice(0,8):undefined;
 return{id,name,type,description,tags};
}
export function describeCard(card:CardContext){return `${card.name} (${card.type})${card.description?`: ${card.description.slice(0,500)}`:""}${card.tags?.length?` Tags: ${card.tags.join(", ")}.`:""}`}
// "My Brother's Husband, All Volumes (Otouto no Otto, #1-4)" → "My Brother's Husband"
export function shortName(name:string){const cleaned=name.replace(/\s*[([].*?[)\]]/g,"").split(/\s*[,:|–—]\s+|\s+-\s+/)[0].trim();return cleaned.length>=3?cleaned:name.trim()}
