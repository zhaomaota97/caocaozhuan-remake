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
    const unitBytes=Buffer.from(unit.unitHex,'hex'),actorBytes=Buffer.from(unit.actorHex,'hex');
    return {slot:unit.slot,unitId:unit.unitId,level:unit.level,attackMode:actorBytes[0x0e],movementTier:actorBytes[0x1d],baseStats:[...unitBytes.subarray(0x15,0x1a)],states:[...actorBytes.subarray(0x18,0x1d)],...unit.combat};
  });
}
writeFileSync('data/mappings/scenario-combat-runtime.json',JSON.stringify(result,null,2)+'\n');
const equipment=JSON.parse(readFileSync('docs/reverse-engineering/native-equipment-accumulator.json','utf8'));
writeFileSync('data/rules/native-equipment-attributes.json',JSON.stringify(equipment.definitions,null,2)+'\n');
console.log(`Exported native combat getter snapshots for ${Object.keys(result).length} scenarios.`);
