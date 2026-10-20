"""Build a per-level event inventory from decoded S_NN scripts."""
import csv,json
from collections import Counter
from pathlib import Path
from export_story_readable import walk
ROOT=Path(__file__).resolve().parents[1]


def main():
 rows=[]
 for path in sorted((ROOT/'analysis/eex-bodies').glob('S_*.json')):
  branches=json.loads(path.read_text(encoding='utf-8'));counts=Counter();map_id=None
  for branch in branches:
   for node,_ in walk(branch['nodes']):
    counts[node['opcode']]+=1
    if node['opcode']==39 and node['arguments'][0]['value']==3:map_id=node['arguments'][4]['value']
  rows.append(dict(script=path.stem+'.eex',map_id=map_id,appearance=counts[76],setup=counts[50],attribute=counts[54],relation=counts[79],dialogue=counts[20],music=counts[36],nodes=sum(counts.values())))
 with (ROOT/'analysis/level-event-inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result=dict(levels=len(rows),rows=rows,totals={key:sum(r[key] for r in rows) for key in ('appearance','setup','attribute','relation','dialogue','music','nodes')},scope='decoded S_NN nodes; opcode columns are neutral families, not completed behavior')
 (ROOT/'analysis/level-event-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'analysis/level-event-inventory.md').write_text('# 58关事件族清单\n\n'+
  '这是从已解码S_NN脚本生成的事件族计数。计数证明原始节点存在，不证明Web已执行。\n\n'+
  '|脚本|地图|出场opcode76|单位/状态opcode50|关系opcode79|对白opcode20|BGM opcode36|节点总数|\n|---|---:|---:|---:|---:|---:|---:|---:|\n'+
  ''.join(f'|{r["script"]}|{r["map_id"]}|{r["appearance"]}|{r["setup"]}|{r["relation"]}|{r["dialogue"]}|{r["music"]}|{r["nodes"]}|\n' for r in rows)+
  f'\n总计：{result["totals"]}\n',encoding='utf-8')
 print(f'Exported {len(rows)} level event inventories')

if __name__=='__main__':main()
