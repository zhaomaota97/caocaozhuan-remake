import {readFileSync,writeFileSync} from 'node:fs';

const result={};
for(let id=0;id<58;id++){
  const name=`S_${String(id).padStart(2,'0')}`;
  const source=JSON.parse(readFileSync(`data/scenarios/native-units/${name}.json`,'utf8'));
  if(!source.passed)throw new Error(`${name}: native placement validation failed`);
  result[id]=source.units.map(unit=>{
    for(const field of ['attack','defense','agility','luck']){
      if(!Number.isInteger(unit.combat?.[field]))throw new Error(`${name}/${unit.slot}: missing ${field}`);
    }
    return {slot:unit.slot,unitId:unit.unitId,level:unit.level,...unit.combat};
  });
}
writeFileSync('data/mappings/scenario-combat-runtime.json',JSON.stringify(result,null,2)+'\n');
console.log(`Exported native combat getter snapshots for ${Object.keys(result).length} scenarios.`);
