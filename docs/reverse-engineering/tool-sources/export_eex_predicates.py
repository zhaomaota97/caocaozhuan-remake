"""Decode known candidate predicates, stopping strictly at unknown instructions."""
import json
from collections import Counter
from pathlib import Path
from eex_cursor import Cursor

ROOT=Path(__file__).resolve().parents[1]


def parameter(cursor,tag):
    actual=cursor.integer(2)
    if actual!=tag:raise ValueError(f'Expected tag {tag}, got {actual}')
    return cursor.string() if tag==5 else cursor.integer(4 if tag==4 else 2)


def predicate(raw,start,end):
    cursor=Cursor(raw,start,end);instructions=[]
    while cursor.pos<end:
        offset=cursor.pos;opcode=cursor.integer(2)
        row=dict(offset=offset,opcode=opcode)
        if opcode==0:
            body_length=cursor.integer(2);body_start=cursor.pos
            if body_start+body_length!=end:raise ValueError('Predicate/body boundary mismatch')
            return dict(complete=True,instructions=instructions,body_offset=body_start,body_size=body_length)
        if opcode==2:
            text=parameter(cursor,5)
            row.update(name='string_marker',text=text.decode('gbk',errors='replace'),raw_hex=text.hex())
        elif opcode==4:
            row.update(name='ui_input_result_comparison',value=parameter(cursor,0x26))
        elif opcode==5:
            count=parameter(cursor,0x35)
            required=[cursor.integer(2) for _ in range(count)]
            count=parameter(cursor,0x35)
            forbidden=[cursor.integer(2) for _ in range(count)]
            row.update(name='flag_groups',required=required,forbidden=forbidden)
        elif opcode==7:row['name']='consume_event_latch'
        elif opcode==19:row.update(name='choice_comparison',value=parameter(cursor,4))
        elif opcode in (37,38,45,46,54,55,63,64,65,66,67):
            name,tags={
                37:('unit_at_coordinate',[2,4,4]),
                38:('unit_in_rectangle',[2,4,4,4,4]),
                45:('event_register_unit_comparison',[2]),
                46:('unit_relation_candidate',[2,2,0x26]),
                54:('unit_attribute_comparison',[2,0x23,4,0x24]),
                55:('common_state_comparison',[0x28,4,0x24]),
                63:('turn_comparison',[4,0x24]),
                64:('battle_phase_comparison',[0x48]),
                65:('unit_count_comparison',[3,4,0x24,0x3f,4,4,4,4]),
                66:('event_register_5_equals_one',[]),
                67:('event_register_6_equals_one',[]),
            }[opcode]
            row.update(name=name,arguments=[parameter(cursor,tag) for tag in tags])
        else:
            return dict(complete=False,instructions=instructions,unknown_opcode=opcode,unknown_offset=offset)
        instructions.append(row)
    raise ValueError('Predicate has no terminator')


def main():
    sources=json.loads((ROOT/'analysis/eex-branches.json').read_text(encoding='utf-8'))
    output=ROOT/'analysis/eex-predicates';output.mkdir(exist_ok=True)
    complete=total=0;unknown=Counter();errors=[]
    for source in sources:
        raw=(ROOT/source['file']).read_bytes();rows=[]
        for segment in source['segments']:
            for branch in segment['branches']:
                total+=1;start=branch['payload_offset'];end=start+branch['size']
                try:decoded=predicate(raw,start,end)
                except ValueError as exc:
                    decoded=dict(complete=False,error=str(exc));errors.append([source['file'],segment['index'],branch['index'],str(exc)])
                complete+=int(decoded['complete'])
                if 'unknown_opcode' in decoded:unknown[decoded['unknown_opcode']]+=1
                rows.append(dict(segment=segment['index'],branch=branch['index'],**decoded))
        (output/f'{Path(source["file"]).stem}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=dict(branches=total,complete_predicates=complete,stopped_at_unknown=dict(unknown.most_common()),errors=errors)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(f'Known predicate prefixes: {complete}/{total} complete; {len(errors)} structural errors; unknowns {unknown.most_common(8)}')
    if total!=2320 or errors:raise SystemExit(1)


if __name__=='__main__':main()
