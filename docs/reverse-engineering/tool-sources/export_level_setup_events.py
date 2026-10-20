"""Export compact, raw setup/event records for one decoded S_NN script."""
import json
import sys
from pathlib import Path
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]
SETUP={35,39,42,54,55,61,68,69,70,71,72,73,74,75,76,77,78,79,80,81,83,85,88,89,90,92,93,95,97,98,99,100,101,102,103,104,105,106,107}


def main():
    name=(sys.argv[1] if len(sys.argv)>1 else 'S_00').upper().replace('.JSON','').replace('.EEX','')
    path=ROOT/'analysis/eex-bodies'/f'{name}.json'
    branches=json.loads(path.read_text(encoding='utf-8'));events=[]
    for branch in branches:
        for node,conditions in walk(branch['nodes']):
            if node['opcode'] in SETUP:
                events.append(dict(segment=branch['segment'],branch=branch['branch'],offset=node['offset'],opcode=node['opcode'],arguments=node.get('arguments',[]),nested_conditions=conditions))
    result=dict(script=name+'.eex',events=len(events),events_by_opcode={},scope='raw decoded arguments; no opcode meaning inferred',events_list=events)
    for event in events:result['events_by_opcode'][str(event['opcode'])]=result['events_by_opcode'].get(str(event['opcode']),0)+1
    target=ROOT/'analysis'/f'{name.lower()}-setup-events.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    md=ROOT/'analysis'/f'{name.lower()}-setup-events.md'
    with md.open('w',encoding='utf-8') as f:
        f.write(f'# {name} 战前/战斗事件原始表\n\n')
        f.write('这里只展示已解码的原始参数，未将 opcode 自行命名为单位生成或战斗行为。\n\n')
        f.write('| segment | branch | offset | opcode | 参数 | 嵌套条件数 |\n|---:|---:|---:|---:|---|---:|\n')
        for e in events:f.write(f'| {e["segment"]} | {e["branch"]} | {e["offset"]} | {e["opcode"]} | `{json.dumps(e["arguments"],ensure_ascii=False,separators=(",",":"))}` | {len(e["nested_conditions"])} |\n')
    print(f'{name}: exported {len(events)} raw setup/event nodes to {target}')


if __name__=='__main__':main()
