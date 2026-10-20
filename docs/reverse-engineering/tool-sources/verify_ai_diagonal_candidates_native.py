"""Extend the original suspended-process candidate probe to eight neighbors."""
import ast
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/verify_ai_candidate_selection_native.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
old='for(let i=0;i<4;i++){\n   const slot='
assert source.count(old)==1
source=source.replace(old,'for(let i=0;i<8;i++){\n   const slot=')
source=source.replace('const x=c.xy[0]+cardinal[i][0],y=c.xy[1]+cardinal[i][1];','const offsets=cardinal.concat(diagonal);const x=c.xy[0]+offsets[i][0],y=c.xy[1]+offsets[i][1];')
cases=[dict(side_mask=side,hp_mask=hp,scores=scores,shape=1,xy=list(xy))
       for side,hp,scores,xy in itertools.product([0,15,240,85,170,255],[0,15,240,85,170,255],[[10]*8,[10,20,20,1,255,256,511,512]],[(4,5),(0,0),(7,7)])]
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script(source);script.load()
    native=script.exports_sync.verify(cases)
    offsets=native['cardinal']+native['diagonal'];rows=[]
    for c,actual in zip(cases,native['rows']):
        candidates=[i+1 for i,(dx,dy) in enumerate(offsets) if 0<=c['xy'][0]+dx<8 and 0<=c['xy'][1]+dy<8 and c['side_mask']&(1<<i) and c['hp_mask']&(1<<i)]
        score=0;target=255
        for slot in candidates:
            value=c['scores'][slot-1]&255
            if value>score:score,target=value,slot
        expected=dict(score=score,target=target,candidates=candidates,visits=[dict(target=s,position=c['xy'][0]+c['xy'][1]*256) for s in candidates])
        rows.append(dict(input=c,actual=actual,expected=expected,match=actual==expected))
    result=dict(total=len(rows),passed=sum(r['match'] for r in rows),cardinal=native['cardinal'],diagonal=native['diagonal'],rows=rows,scope='native shape1 eight-neighbor filtering and selector; controlled score leaf and buffers; process never resumed')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-ai-diagonal-candidates.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-ai-diagonal-candidates.json').write_text(text,encoding='utf-8')
    print(f'Native eight-neighbor candidate chain: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
