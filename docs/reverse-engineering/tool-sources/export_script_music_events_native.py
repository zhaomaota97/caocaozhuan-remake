"""Verify every scripted opcode36 and link it to the native playlist mapping."""
import json
from pathlib import Path
import frida
from export_eex_bodies import encode_instruction
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]


def main():
    music=json.loads((ROOT/'analysis/native-music-mapping-validation.json').read_text(encoding='utf-8'))
    playlist={r['track']:r for r in music['rows'] if r['match']}
    events=[]
    for path in sorted((ROOT/'analysis/eex-bodies').glob('[RS]_*.json')):
        original=(ROOT/f'{path.stem}.eex').read_bytes()
        for branch in json.loads(path.read_text(encoding='utf-8')):
            for node,conditions in walk(branch['nodes']):
                if node['opcode']!=36:continue
                encoded=encode_instruction(node)
                if encoded!=original[node['offset']:node['end']]:raise ValueError('Music instruction differs from file')
                value=node['arguments'][0]['value'];track=None if value==255 else value+2
                entry=playlist.get(track)
                selected=entry['selected'] if entry else None
                events.append(dict(script=path.stem+'.eex',segment=branch['segment'],branch=branch['branch'],
                                   offset=node['offset'],value=value,operation='stop' if value==255 else 'play',
                                   nativeTrack=track,playlistPath=selected,
                                   webAsset='/assets/audio/bgm/'+selected.replace('\\','/').split('/')[-1] if selected else None,
                                   nested_conditions=conditions,bytes=list(encoded)))
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(events){
 const b=Process.mainModule.base,keep=[],obj=Memory.alloc(0x2040);let calls=[];
 const play=new NativeCallback((_o,track)=>calls.push({operation:'play',track}),'void',['pointer','uint'],'thiscall');
 const stop=new NativeCallback((_o)=>calls.push({operation:'stop'}),'void',['pointer'],'fastcall');
 keep.push(play,stop);Interceptor.replace(b.add(0x745FE),play);Interceptor.replace(b.add(0x74619),stop);Interceptor.flush();
 const dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall');
 return events.map(e=>{
  const input=Memory.alloc(e.bytes.length);input.writeByteArray(e.bytes);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
  b.add(0xB0770+4).writeU8(165);calls=[];
  const status=dispatch(obj)&255;
  return {status,consumed:obj.add(12).readPointer().sub(input).toInt32(),calls,commonMusic:b.add(0xB0770+4).readU8()};
 });
}};
''');script.load();actual=script.exports_sync.verify(events)
        for event,row in zip(events,actual):
            expected=[dict(operation='stop')] if event['operation']=='stop' else [dict(operation='play',track=event['nativeTrack'])]
            event['native_match']=(row['status']==1 and row['consumed']==len(event['bytes']) and row['calls']==expected
                                    and row['commonMusic']==(255 if event['operation']=='stop' else 165))
            event['native']=row;event.pop('bytes')
            if event['webAsset']:
                event['webAssetExists']=(ROOT.parent/'caocaozhuan-remake/public'/event['webAsset'].lstrip('/')).exists()
        report=dict(events=len(events),passed=sum(e['native_match'] for e in events),rows=events,
                    scope='all static opcode36 occurrences in117 R/S files; actual native dispatcher and handler, audio play/stop boundary intercepted; playlist links from separate native MP3Serv verification, no runtime audio/playthrough proof')
        target=ROOT/'analysis/script-music-events.json'
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT.parent/'caocaozhuan-remake/data/mappings/script-music-events.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'Script music events: {report["passed"]}/{len(events)}; S_00={[(e["offset"],e["value"],e["nativeTrack"],e["playlistPath"]) for e in events if e["script"]=="S_00.eex"]}')
        print('Missing Web assets:',sum(e.get('webAssetExists') is False for e in events))
        if report['passed']!=len(events):raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
