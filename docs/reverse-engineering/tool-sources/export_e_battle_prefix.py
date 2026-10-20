"""Decode the battle-state prefix consumed by native 0x44F384/0x44F6E6."""
import hashlib,json,struct,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: export_e_battle_prefix.py <Sv??E.e5s>')
path=Path(sys.argv[1]);raw=path.read_bytes();base=0x23;state=raw[base:base+1266]
if len(state)!=1266: raise ValueError('missing E battle state')
pos=0
def take(n):
 global pos
 v=state[pos:pos+n];pos+=n;return v
header={'bytes0_3':take(4).hex(),'byte4':take(1)[0],'byte5':take(1)[0],
 'byte6':take(1)[0],'byte7':take(1)[0],'byte8':take(1)[0],'byte9':take(1)[0],
 'byte10':take(1)[0],'byte11':take(1)[0],
 'byte_to_object_0x500':take(1)[0],'byte_to_object_0x504':take(1)[0],
 'uint16_0x4fc':struct.unpack('<H',take(2))[0]}
entries=[list(take(5)) for _ in range(250)]
actors=raw[base+1266:base+1266+115*26]
occupancy=raw[base+1266+115*26:base+1266+115*26+640]
result={'file':path.name,'stateOffset':'0x23','stateBytes':1266,'stateHeader':header,
 'stateEntries250':entries,'actorsOffset':hex(base+1266),'actorsBytes':len(actors),
 'actorsSha256':hashlib.sha256(actors).hexdigest(),
 'occupancyOffset':hex(base+1266+115*26),'occupancyBytes':len(occupancy),
 'occupancySha256':hashlib.sha256(occupancy).hexdigest(),
 'stateReader':'0x44F384','battleBridge':'0x44F6E6'}
out=path.with_suffix(path.suffix+'.battle-prefix.json')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(f'{path.name}: state 1266, actors {len(actors)}, occupancy {len(occupancy)} -> {out}')
