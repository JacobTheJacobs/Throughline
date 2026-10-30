// Synthetic counterexamples/control against current exported production helpers.
import {administrativeRegion,confirmsArea} from '../lib/geography.ts';
for(const [selected,candidate] of [
  [{region:'Ontario',country:'Canada'},{country:'Canada',admin1_region:'British Columbia',city:'Vancouver'}],
  [{region:'Île-de-France',country:'France'},{country:'France',admin1_region:'Nouvelle-Aquitaine',city:'Bordeaux'}],
])console.log(JSON.stringify({syntheticEvidence:true,selected,candidate,consideredAdministrative:administrativeRegion(selected),accepted:confirmsArea(selected,candidate),expected:false}));
