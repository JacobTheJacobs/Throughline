// Confirms a returned place lies in the geographic record the user selected.
// Region/country labels differ between Qloo records ("United States of America" vs "United States",
// "France (terres)" vs "France"), so names are normalised before comparison.
export type AreaIdentity={region?:string;country?:string};
export type Geocode=Partial<Record<"country"|"admin1_region"|"admin2_region"|"city"|"metro",string|null>>;
const ALIASES:Record<string,string>={"united states of america":"united states",usa:"united states",us:"united states",uk:"united kingdom"};
export function areaName(value:string){const plain=value.normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/\([^)]*\)/g,"").replace(/[^\p{L}\p{N}]+/gu," ").trim().toLowerCase();return ALIASES[plain]??plain}
// A selected region must match the candidate's own region, city or metro. The only exception is a label that
// merely restates the country ("France métropolitaine"), which is not a sub-national division.
const COUNTRY_SCOPE=new Set(["metropolitaine","metropolitan","mainland","proper","continental","terres"]);
// Country-wide only when the label is the country name plus a scope word ("France métropolitaine"); a real
// region that merely contains the country's name ("Île-de-France") is still enforced.
export function administrativeRegion(area:AreaIdentity){if(!area.region)return false;const region=areaName(area.region).split(" "),country=new Set(area.country?areaName(area.country).split(" "):[]);return !(country.size&&region.every(word=>country.has(word)||COUNTRY_SCOPE.has(word)))}
export function confirmsArea(area:AreaIdentity,geo:Geocode|undefined){
 if(!area.region&&!area.country)return false;
 if(!geo)return false;
 const names=new Set([geo.country,geo.admin1_region,geo.admin2_region,geo.city,geo.metro].filter((value):value is string=>!!value).map(areaName));
 if(area.country&&!names.has(areaName(area.country)))return false;
 if(administrativeRegion(area)&&!names.has(areaName(area.region!)))return false;
 return true;
}
