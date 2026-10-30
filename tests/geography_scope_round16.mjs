// Synthetic evidence through the exported production geography helper: a wrong province is rejected
// even when every returned place is in that province.
import {confirmsArea} from '../lib/geography.ts';
const selected={region:'Ontario',country:'Canada'};
const returned=[{country:'Canada',admin1_region:'British Columbia',city:'Vancouver'}];
const accepted=confirmsArea(selected,returned[0]);
console.log(JSON.stringify({syntheticEvidence:true,selected,returned,accepted,expected:false}));process.exit(accepted?1:0);
