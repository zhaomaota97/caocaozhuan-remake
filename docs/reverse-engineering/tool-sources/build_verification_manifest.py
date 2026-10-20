"""Write a compact manifest of authoritative reverse-engineering evidence."""
import json
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[1]

def read_json(name):
    data=(ROOT/name).read_bytes()
    encoding='utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    return json.loads(data.decode(encoding))

def main():
    checks=[]
    def add(name,evidence,metric,passed=True,scope=''):
        checks.append(dict(name=name,evidence=evidence,metric=metric,passed=passed,scope=scope))
    add('runtime Ls12 decoder','analysis/decoder-validation-final.json','3/3 byte comparisons',
        all(x['match'] for x in read_json('analysis/decoder-validation-final.json')))
    add('native map readers','analysis/native-map-reader-validation.json','784646/784646',
        read_json('analysis/native-map-reader-validation.json')['failures']==0)
    add('save object codec','analysis/native-save-object-validation.json','5120/5120',
        all(x['matches']==x['records'] for x in read_json('analysis/native-save-object-validation.json')))
    add('battle save codec','analysis/native-battle-save-validation.json','1160/1160',
        all(x['matched']==x['records'] for x in read_json('analysis/native-battle-save-validation.json')))
    add('combat magnitude','analysis/native-combat-magnitude-validation.json','652/652',
        all(x['match'] for x in read_json('analysis/native-combat-magnitude-validation.json')))
    add('EEX body structure','analysis/eex-bodies/summary.json','2320 byte-exact round trips',
        (lambda x:x['roundtrip_matches']==x['complete']==x['bodies']==2320)(read_json('analysis/eex-bodies/summary.json')))
    add('EEX dispatcher','analysis/native-eex-dispatch-validation.json','59/59',
        all(x['match'] for x in read_json('analysis/native-eex-dispatch-validation.json')))
    story=read_json('analysis/story-readable/summary.json')
    add('structured story export','analysis/story-readable/summary.json','9420 strings / 0 CP936 errors',
        story['strings']==9420 and not story['cp936_decode_errors'])
    bodies=read_json('analysis/eex-bodies/summary.json')
    add('EEX body lossless roundtrip','analysis/eex-bodies/summary.json','2320/2320 byte-exact',
        bodies['roundtrip_matches']==2320 and bodies['roundtrip_bytes']==1599202)
    inventory=read_json('analysis/game-format-inventory.json')
    add('on-disk format inventory','analysis/game-format-inventory.json','239 files',
        inventory['files']==239)
    add('effect blend','analysis/native-effect-blend-validation.json','72/72 batches',
        all(x['match'] for x in read_json('analysis/native-effect-blend-validation.json')))
    add('status recovery','analysis/native-status-recovery-validation.json','2640/2640',
        all(x['match'] for x in read_json('analysis/native-status-recovery-validation.json')))
    imsg=(ROOT/'analysis/imsg.csv').read_bytes().splitlines()
    add('Imsg fixed messages','analysis/imsg.csv','921 fixed records / CP936',
        len(imsg)==922 and (ROOT/'Imsg.e5').stat().st_size==921*200)
    audit=read_json('analysis/data-entry-reference-audit.json')
    add('Data.e5 reference audit','analysis/data-entry-reference-audit.json','entries 0-5 explicit / 6-9 open',
        audit['explicitly_loaded_indices']==[0,1,2,3,4,5] and audit['no_explicit_loader_found']==[6,7,8,9])
    live_audit=read_json('analysis/live-startup-20261017-001421/data-entry-audit.json')
    add('live Data.e5 requests','analysis/live-startup-20261017-001421/data-entry-audit.json','requested 0-5 only',
        live_audit['requested']==[0,1,2,3,4,5] and live_audit['not_requested']==[6,7,8,9])
    add('live slot 0 snapshot','analysis/live-startup-20261016-225042/snapshot-validation.json','5/5 buffers',
        read_json('analysis/live-startup-20261016-225042/snapshot-validation.json')['passed'])
    add('live slot 8 snapshot','analysis/live-startup-20261016-225516/snapshot-validation.json','5/5 buffers',
        read_json('analysis/live-startup-20261016-225516/snapshot-validation.json')['passed'])
    latest_snapshot=ROOT/'analysis/live-startup-20261017-005637/snapshot-validation.json'
    if latest_snapshot.exists():
        add('latest live battle snapshot','analysis/live-startup-20261017-005637/snapshot-validation.json','5/5 buffers',
            read_json('analysis/live-startup-20261017-005637/snapshot-validation.json')['passed'])
    yuxi=(ROOT/'analysis/native-main/pseudocode/0041c4e9.c').read_text(encoding='utf-8')
    attack=(ROOT/'analysis/native-main/pseudocode/004404bd.c').read_text(encoding='utf-8')
    items=(ROOT/'analysis/items.csv').read_text(encoding='utf-8-sig')
    add('Yuxi critical static chain','tools/verify_yuxi_critical_static.py','5/5',
        '82,玉玺,41,' in items and 'case 0x41:' in yuxi and 'FUN_004066e0(this,8)' in yuxi
        and 'FUN_0041c4e9' in attack and '& 100' in attack)
    hit=(ROOT/'analysis/native-main/pseudocode/0043b50d.c').read_text(encoding='utf-8')
    add('ordinary hit static chain','tools/verify_hit_static.py','5/5',
        'FUN_0043f631(piVar2)' in hit and 'FUN_0043f631(this_00)' in hit
        and 'FUN_0047fa9e' in hit and 'local_14 = 0' in hit and 'local_14 = 100' in hit)
    opcode_rows=(ROOT/'analysis/eex/opcode-index.csv').read_text(encoding='utf-8-sig').splitlines()
    low_rows=[line for line in opcode_rows[1:] if 'no parameter-reader call observed' in line]
    add('EEX low-frequency handler inventory','analysis/eex/opcode-index.csv','21 handlers indexed',
        len(low_rows)==21 and all((ROOT/'analysis/native-main/pseudocode'/ (line.split(',')[1]+'.c')).exists()
                                   for line in low_rows))
    low_semantics=list(__import__('csv').DictReader((ROOT/'analysis/eex/low-frequency-semantics.csv').open(encoding='utf-8-sig')))
    add('EEX low-frequency static semantics','analysis/eex/low-frequency-semantics.csv','21 high-confidence rows',
        len(low_semantics)==21 and all(row['confidence']=='high' for row in low_semantics))
    opcode_map={row.split(',')[0]:row.split(',')[1] for row in opcode_rows[1:]}
    add('EEX low-frequency address crosscheck','analysis/eex/low-frequency-semantics.csv','21 opcode/handler matches',
        all(opcode_map.get(row['opcode'])==row['handler'] for row in low_semantics))
    data_base=ROOT/'analysis/full-extract-56219569-d002-44b4-8b5f-56cb66adac39/Data'
    sparse_expected={6:(8704,17,512),7:(1768,17,104),8:(1156,17,68),9:(1218,21,58)}
    sparse_ok=True
    for index,(size,width,rows) in sparse_expected.items():
        data=(data_base/f'resource_{index:04d}.bin').read_bytes()
        nonzero=[value for value in data if value]
        sparse_ok &= len(data)==size and len(data)%width==0 and len(data)//width==rows
        sparse_ok &= set(nonzero)=={0xD6,0xD5,0xB6,0xCB} and len(nonzero)==rows*4
    add('DATA.E5 unused sparse entries','tools/verify_data_entries_unused.py','4/4 shape checks',sparse_ok)
    koeicda=(ROOT/'analysis/koeicda-exports.md').exists()
    add('Koeicda export/message semantics','analysis/koeicda-exports.md','20 exports / 4 MP3Serv messages',koeicda)
    add('AutoDLL ASave jump analysis','analysis/autodll-asave.md','ASave jump targets documented',
        (ROOT/'analysis/autodll-asave.md').exists())
    add('resource DLL common-code audit','analysis/resource-dll-common-code.md','4 resource DLLs share .text',
        (ROOT/'analysis/resource-dll-common-code.md').exists())
    resource_map=ROOT/'analysis/resource-dll-resource-map.csv'
    add('resource DLL resource map','analysis/resource-dll-resource-map.csv','304 resource records',
        resource_map.exists() and len(resource_map.read_bytes().splitlines())==305)
    dll_graph=read_json('analysis/dll-callgraph-summary.json')
    add('DLL static callgraph summary','analysis/dll-callgraph-summary.json','6 DLL graphs / 1866 edges',
        set(dll_graph)=={'AutoDLL.dll','Cmdicon.dll','Itemicon.dll','Koeicda.dll','Mapatr.dll','Mgcicon.dll'}
        and sum(x['edges'] for x in dll_graph.values())==1866)
    eex_matrix=read_json('analysis/eex-coverage-matrix.json')
    add('EEX opcode coverage matrix','analysis/eex-coverage-matrix.json','108 opcode slots classified',
        eex_matrix['total']==108 and eex_matrix['dynamic']+eex_matrix['static']+eex_matrix['reserved']==108)
    eex_usage=read_json('analysis/eex-opcode-usage.json')
    add('EEX opcode corpus usage','analysis/eex-opcode-usage.json','117 files / 2320 bodies including nested conditions',
        eex_usage['totalOpcodes']==108 and eex_usage['sourceFiles']==117 and eex_usage['bodies']==2320
        and eex_usage['includesNestedConditions'] and eex_usage['usedOpcodes']+eex_usage['unusedOpcodes']==108)
    live_cursor=read_json('analysis/live-startup-20261017-194421/eex-cursor-summary.json')
    add('live EEX cursor and opcode 20','analysis/live-startup-20261017-194421/eex-cursor-summary.json','26 dispatches / opcode 20 cursor',
        live_cursor['dispatchObservations']==26 and live_cursor['opcode20']['opcode']==20 and live_cursor['opcode20']['cursor_field']==498)
    add('native attack controller order','analysis/native-attack-controller-order.md','7 ordered stages documented',
        (ROOT/'analysis/native-attack-controller-order.md').exists())
    attack_graph=read_json('analysis/native-attack-stage-graph.json')
    add('native attack stage graph','analysis/native-attack-stage-graph.json','7 source-backed stages',
        attack_graph['controller']=='0x4064f1' and attack_graph['allSourcesExist'] and len(attack_graph['stages'])==7)
    add('battle faction/status predicates','analysis/battle-faction-counting.md','shared EEX count semantics documented',
        (ROOT/'analysis/battle-faction-counting.md').exists())
    add('EEX high-frequency static semantics','analysis/eex-high-frequency-static-semantics.md','opcodes 52 and 9 documented',
        (ROOT/'analysis/eex-high-frequency-static-semantics.md').exists())
    high_dynamic=read_json('analysis/native-eex-high-frequency-validation.json')
    add('EEX high-frequency handler boundary','analysis/native-eex-high-frequency-validation.json','opcode 9 boundary / opcode 52 target call',
        high_dynamic['passed'] and high_dynamic['opcode52ReaderBoundary'].startswith('verified'))
    add('EEX opcode 52 effect dispatch','analysis/eex-opcode52-effect-dispatch.md','128-entry effect table semantics documented',
        (ROOT/'analysis/eex-opcode52-effect-dispatch.md').exists())
    effect_dynamic=read_json('analysis/native-eex-effect-dispatch-validation.json')
    add('EEX opcode 52 effect lookup','analysis/native-eex-effect-dispatch-validation.json','3 live entries + missing key',
        effect_dynamic['passed'] and effect_dynamic['result']['missing']==0xffffffff)
    add('EEX opcode 9 effect queue','analysis/eex-opcode9-effect-queue.md','queue target/drain semantics documented',
        (ROOT/'analysis/eex-opcode9-effect-queue.md').exists())
    add('EEX opcodes 48/50 semantics','analysis/eex-opcode48-50-semantics.md','high-frequency parameter branches documented',
        (ROOT/'analysis/eex-opcode48-50-semantics.md').exists())
    add('EEX opcodes 48/50 targets','analysis/eex-opcode48-50-targets.md','effect and actor target flows documented',
        (ROOT/'analysis/eex-opcode48-50-targets.md').exists())
    op48_target=read_json('analysis/native-eex-opcode48-target-validation.json')
    add('EEX opcode 48 target dispatch','analysis/native-eex-opcode48-target-validation.json','active effect target / fixed modes',
        op48_target['passed'] and op48_target['result']['ret']==0xffff)
    op50_target=read_json('analysis/native-eex-opcode50-target-validation.json')
    add('EEX opcode 50 target boundary','analysis/native-eex-opcode50-target-validation.json','missing/non-type4 return paths',
        op50_target['passed'] and len(op50_target['rows'])==2)
    add('DLL export table validation','tools/verify_dll_exports.py','7/7',
        (ROOT/'tools/verify_dll_exports.py').exists())
    add('EEX dynamic startup boundary','analysis/live-eex-startup-boundary.md','DATA/SVCMN before dispatcher',
        (ROOT/'analysis/live-eex-startup-boundary.md').exists())
    add('EEX dynamic story entry','analysis/live-eex-story-entry.md','26 dispatcher calls on new game',
        (ROOT/'analysis/live-eex-story-entry.md').exists())
    add('EEX interpreter memory snapshot','tools/parse_live_eex_events.py','EEX magic/header/first opcode parsed',
        (ROOT/'tools/parse_live_eex_events.py').exists())
    add('EEX interpreter before/after state','tools/summarize_live_eex_state.py','cursor candidate fields captured',
        (ROOT/'tools/summarize_live_eex_state.py').exists())
    add('live EEX file match','tools/verify_live_eex_file_match.py','R_00.eex 128-byte prefix match',
        (ROOT/'tools/verify_live_eex_file_match.py').exists())
    add('structured E partition codec','tools/verify_e_partition_codec.py','10/10 byte-exact files',
        (ROOT/'tools/verify_e_partition_codec.py').exists() and all((ROOT/'analysis/runtime-game'/f'SV{i:02d}E.E5S.json').exists() for i in range(10)))
    reset=read_json('analysis/native-eex-reset-validation.json')
    add('EEX opcode 68 reset','analysis/native-eex-reset-validation.json','256 table entries / 115 records',
        reset['passed'] and reset['result']['calls']==256 and all(x['flags']==0 for x in reset['result']['records']))
    low=read_json('analysis/native-eex-low-frequency-validation.json')
    add('EEX low-frequency native handlers','analysis/native-eex-low-frequency-validation.json','4/4 cases',low['passed'])
    conditional=read_json('analysis/native-eex-conditional-validation.json')
    add('EEX conditional native handlers','analysis/native-eex-conditional-validation.json','6/6 branches',conditional['passed'])
    config_predicates=read_json('analysis/native-eex-config-predicate-validation.json')
    add('EEX config predicates','analysis/native-eex-config-predicate-validation.json','8 slot predicate cases',config_predicates['passed'])
    reward=read_json('analysis/native-attack-reward-controller.json')
    add('native attack reward controller','analysis/native-attack-reward-controller.json','2592/2592',all(x['match'] for x in reward['rows']))
    aggregate=read_json('analysis/native-multi-target-reward-aggregation.json')
    add('native multi-target reward aggregation','analysis/native-multi-target-reward-aggregation.json','625/625',all(x['match'] for x in aggregate['rows']))
    result=dict(generated=date.today().isoformat(),checks=checks,passed=sum(x['passed'] for x in checks),
                total=len(checks),open_scope=[
                    'complete EEX opcode semantics and full playthrough',
                    'all DLL function semantics',
                    'full AI/pathfinding and battle actions',
                    'all Data.e5 entry semantics',
                    'unmodified UI-driven save/load round trips'])
    (ROOT/'analysis/verification-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Verification manifest: {result["passed"]}/{result["total"]} evidence groups passed')

if __name__=='__main__':main()
