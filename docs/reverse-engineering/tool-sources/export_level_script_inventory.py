"""Summarize each S_NN EEX script without guessing unresolved opcode semantics."""
import json
from collections import Counter
from pathlib import Path
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]


def main():
    rows=[]
    for path in sorted((ROOT/'analysis/eex-bodies').glob('S_*.json')):
        branches=json.loads(path.read_text(encoding='utf-8'));nodes=[]
        for branch in branches:
            for node,conditions in walk(branch['nodes']):
                nodes.append(dict(segment=branch['segment'],branch=branch['branch'],offset=node['offset'],opcode=node['opcode'],arguments=node.get('arguments',[]),nested=bool(conditions)))
        scenes=[n for n in nodes if n['opcode']==39 and n['arguments'] and n['arguments'][0].get('value')==3]
        rows.append(dict(script=path.stem+'.eex',segments=len(branches),nodes=len(nodes),opcode_counts=dict(sorted(Counter(n['opcode'] for n in nodes).items())),
                         map_entries=[dict(offset=n['offset'],arguments=n['arguments'],nested=n['nested']) for n in scenes],
                         dialogue=sum(n['opcode'] in (20,21,22,23,96) for n in nodes),
                         battle_setup=sum(n['opcode'] in (39,42,54,55,61,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,83,84,85,88,89,90,91,92,93,95,97,98,99,100,101,102,103,104,105,106,107) for n in nodes)))
    result=dict(scripts=len(rows),rows=rows,scope='decoded S_*.eex nodes and static opcode families; opcode meanings are not inferred where unresolved')
    (ROOT/'analysis/level-script-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'analysis/level-script-inventory.md').open('w',encoding='utf-8') as f:
        f.write('# S_NN 剧本入口清单\n\n')
        f.write('该清单来自完整解码的 S_00–S_57 EEX；只统计实际节点，不把资源文件数量当成关卡完成。\n\n')
        f.write('| 脚本 | segment数 | 节点数 | 对话节点 | 战斗/状态候选节点 | 地图入口数 |\n|---|---:|---:|---:|---:|---:|\n')
        for r in rows:f.write(f'| {r["script"]} | {r["segments"]} | {r["nodes"]} | {r["dialogue"]} | {r["battle_setup"]} | {len(r["map_entries"])} |\n')
        f.write('\n地图入口的原始参数、segment、branch、offset 在 `level-script-inventory.json`；需结合 `scenario-resource-links.csv` 使用。\n')
    print(f'Indexed {len(rows)} level scripts; {sum(len(r["map_entries"]) for r in rows)} map-entry nodes')


if __name__=='__main__':main()
