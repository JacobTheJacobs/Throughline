// Ontario selection must reject a British Columbia candidate even though both are in Canada.
import {confirmsArea} from '../lib/geography.ts';
const area={region:'Ontario',country:'Canada'},bc={country:'Canada',admin1_region:'British Columbia',city:'Vancouver'};
const accepted=confirmsArea(area,bc);
console.log(JSON.stringify({selectedRegion:'Ontario, Canada',candidateRegion:'British Columbia, Canada',accepted,expected:false}));process.exit(accepted?1:0);
