"""Export boundary-decoded script strings with branch and condition provenance."""
import csv
import json
from pathlib import Path
from collections import Counter
from game_text import decode_game_text,visible_text

ROOT=Path(__file__).resolve().parents[1]
LABELS={2:'标记字符串',18:'选项',20:'对白',21:'战斗文本',22:'消息文本',44:'界面文本'}


def walk(nodes,conditions=()):
    for node in nodes:
        if node['opcode']==1:
            yield from walk(node['body']['nodes'],conditions+(node['condition'],))
        else:yield node,conditions


def compact(condition):
    return json.dumps({k:v for k,v in condition.items() if k not in ('offset','end','raw_hex')},ensure_ascii=False,separators=(',',':'))


def main():
    output=ROOT/'analysis/story-readable';output.mkdir(exist_ok=True)
    counts=Counter();errors=[];private=[];files=[];total=0
    with (output/'strings.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream)
        writer.writerow(['file','segment','branch','instruction_offset','opcode','argument',
                         'nested_conditions','text_cp936','raw_hex'])
        for path in sorted((ROOT/'analysis/eex-bodies').glob('*.json')):
            if path.name=='summary.json':continue
            branches=json.loads(path.read_text(encoding='utf-8'))
            predicates=json.loads((ROOT/'analysis/eex-predicates'/path.name).read_text(encoding='utf-8'))
            conditions={(r['segment'],r['branch']):r['instructions'] for r in predicates}
            lines=[f'# {path.stem} 脚本文本','',
                   '按文件顺序列出，不代表所有分支都会执行。满足条件的候选中最后一个优先；说话者和控制符按原文保留。','']
            strings=0
            for branch in branches:
                if not branch['complete']:raise ValueError('Incomplete body decode')
                emitted=[]
                for node,nested in walk(branch['nodes']):
                    for argument,arg in enumerate(node.get('arguments',[])):
                        if arg['tag']!=5:continue
                        raw=bytes.fromhex(arg['hex'])
                        try:text=decode_game_text(raw)
                        except UnicodeDecodeError:
                            text=raw.decode('gbk',errors='backslashreplace')
                            errors.append(dict(file=path.stem,offset=node['offset'],hex=arg['hex']))
                        if any(0xE000<=ord(c)<=0xF8FF for c in text):
                            private.append(dict(file=path.stem,offset=node['offset'],hex=arg['hex'],
                                codepoints=[f'U+{ord(c):04X}' for c in text if 0xE000<=ord(c)<=0xF8FF]))
                        total+=1;strings+=1;counts[node['opcode']]+=1
                        context=' AND '.join(compact(c) for c in nested)
                        writer.writerow([f'{path.stem}.eex',branch['segment'],branch['branch'],
                            hex(node['offset']),node['opcode'],argument,context,text,arg['hex']])
                        if not text:continue
                        emitted += [f'### {LABELS.get(node["opcode"],"文本字段")} · opcode {node["opcode"]} · {hex(node["offset"])}','']
                        if nested:emitted += ['嵌套条件：`'+context.replace('`','\\`')+'`','']
                        emitted += ['> '+part for part in visible_text(text).splitlines()]+['']
                if emitted:
                    outer=conditions[(branch['segment'],branch['branch'])]
                    lines += [f'## 段 {branch["segment"]} / 分支 {branch["branch"]}','',
                              '候选条件：`'+' AND '.join(compact(c) for c in outer).replace('`','\\`')+'`','',*emitted]
            (output/f'{path.stem}.md').write_text('\n'.join(lines),encoding='utf-8')
            files.append(dict(file=path.stem,strings=strings))
    summary=dict(files=len(files),strings=total,by_opcode=dict(counts),cp936_decode_errors=errors,
                 private_use_fields=private)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (output/'index.md').write_text('# 剧情与脚本文本索引\n\n'+
        '\n'.join(f'- [{r["file"]}]({r["file"]}.md)：{r["strings"]} 个字符串字段' for r in files),encoding='utf-8')
    print(f'Exported {total} structured string fields from {len(files)} scripts; CP936 errors: {len(errors)}; '
          f'private-use fields: {len(private)}')


if __name__=='__main__':main()
