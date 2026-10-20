"""Decode explicitly recovered EEX body formats, without resynchronization guesses."""
import json
import struct
from pathlib import Path
from collections import Counter
from eex_cursor import Cursor
from export_eex_predicates import parameter

ROOT=Path(__file__).resolve().parents[1]
FORMATS={2:[5],3:[],4:[38],7:[],8:[46],9:[4],10:[],11:[4,39],12:[],13:[],
         14:[],15:[18],16:[],17:[55],18:[5,2],19:[4],20:[5],21:[2,2,5],
         22:[5],23:[5],24:[5],25:[5],26:[5],27:[2,39],28:[],29:[],30:[],
         31:[4,4],32:[74],35:[30,4],36:[9],37:[2,4,4],38:[2,4,4,4,4],40:[54],
         45:[2],46:[2,2,38],54:[2,35,4,36],55:[40,4,36],63:[4,36],64:[72],
         65:[3,4,36,63,4,4,4,4],66:[],67:[]}
FORMATS.update({39:[45,12,26,28,21],61:[23,73,38,2],79:[2,2,43,38,38,38],
                81:[],83:[44,2,4,4,4,4,3,38],85:[64,2,4,4,4,43]})
FORMATS.update({47:[],48:[2,4,4,43,13],49:[44,2,4,4,4,4,3],76:[64,2,4],
                78:[44,2,4,4,4,4,3,7,2,4,4],80:[2,70,38,38]})
FORMATS.update({6:[46,4]+[56]*5+[57]*5,41:[2,4,4],52:[2,13],68:[],73:[],
                89:[4,23,73,23,73,23,73,38]})
FORMATS.update({44:[5,38,38,38],50:[64,2,4,4,4,43],51:[2,13,43],
                69:[38,38,4,62,50,2,50,2,71,34],88:[66,67,68,4,4,38,38],104:[2,2]})
FORMATS.update({42:[2,4,4],70:[2,38,4,4,43,62,69,7,2,4,4]*20,
                77:[65,2,4,4,4,4,4,3,47,24,48,4,4],91:[4,4,4,4,38],
                96:[38,5,76],105:[5]})
FORMATS.update({43:[2],58:[40,52,4],59:[2,14,62],
                71:[2,38,38,4,4,43,62,69,7,2,4,4]*80,97:[],100:[38,76]})
FORMATS.update({53:[2,19],62:[2,59,73,60,73,61],75:[4,4,4,43,38],
                99:[38,5,38],101:[38,77,38],102:[38,78,38]})
FORMATS.update({72:[2,59,73,60,73,61],90:[],92:[2],95:[],98:[38],103:[4,5]})
FORMATS.update({33:[4,4,16,38,38],34:[27],57:[2,4],74:[4]+[56]*5+[57]*5,
                84:[],93:[52,4],106:[],107:[4,4,75,38]})


def instruction(cursor):
    start=cursor.pos;opcode=cursor.integer(2);row=dict(offset=start,opcode=opcode)
    if opcode==0:return dict(**row,end=cursor.pos)
    if opcode==5:
        required=[cursor.integer(2) for _ in range(parameter(cursor,53))]
        forbidden=[cursor.integer(2) for _ in range(parameter(cursor,53))]
        return dict(**row,required=required,forbidden=forbidden,end=cursor.pos)
    if opcode not in FORMATS:return dict(**row,unknown=True)
    args=[]
    for tag in FORMATS[opcode]:
        value=parameter(cursor,tag)
        args.append(dict(tag=tag,text=value.decode('gbk',errors='replace'),hex=value.hex())
                    if isinstance(value,bytes) else dict(tag=tag,value=value))
    return dict(**row,arguments=args,end=cursor.pos)


def block(raw,start,end,depth=0):
    if depth>128:raise ValueError('Unreasonable block nesting')
    cursor=Cursor(raw,start,end);nodes=[]
    while cursor.pos<end:
        offset=cursor.pos
        opcode=int.from_bytes(raw[offset:offset+2],'little')
        if opcode==1:
            cursor.integer(2);condition=instruction(cursor)
            if condition.get('unknown'):return dict(complete=False,nodes=nodes,unknown=condition)
            size=cursor.integer(2);child_start=cursor.pos;child_end=child_start+size
            if child_end>end:raise ValueError('Conditional block exceeds parent')
            child=block(raw,child_start,child_end,depth+1)
            nodes.append(dict(offset=offset,opcode=1,condition=condition,body=child))
            if not child['complete']:return dict(complete=False,nodes=nodes,unknown=child['unknown'])
            cursor.pos=child_end
        else:
            node=instruction(cursor);nodes.append(node)
            if node.get('unknown'):return dict(complete=False,nodes=nodes,unknown=node)
            if node['opcode']==0:
                if cursor.pos!=end:raise ValueError('Bytes after block terminator')
                return dict(complete=True,nodes=nodes)
    raise ValueError('Missing body terminator')


def encode_instruction(node):
    out=struct.pack('<H',node['opcode'])
    if node['opcode']==0:return out
    if node['opcode']==5:
        for key in ('required','forbidden'):
            out+=struct.pack('<HH',53,len(node[key]))
            out+=b''.join(struct.pack('<H',v) for v in node[key])
        return out
    for arg in node['arguments']:
        tag=arg['tag'];out+=struct.pack('<H',tag)
        out+=bytes.fromhex(arg['hex'])+b'\0' if tag==5 else struct.pack('<I' if tag==4 else '<H',arg['value'])
    return out


def encode_block(decoded):
    out=b''
    for node in decoded['nodes']:
        if node['opcode']==1:
            child=encode_block(node['body'])
            out+=struct.pack('<H',1)+encode_instruction(node['condition'])+struct.pack('<H',len(child))+child
        else:out+=encode_instruction(node)
    return out


def main():
    output=ROOT/'analysis/eex-bodies';output.mkdir(exist_ok=True)
    unknown=Counter();errors=[];total=complete=roundtrips=byte_count=0
    for path in sorted((ROOT/'analysis/eex-predicates').glob('*.json')):
        if path.name=='summary.json':continue
        source=ROOT/f'{path.stem}.eex';raw=source.read_bytes();rows=[]
        for branch in json.loads(path.read_text(encoding='utf-8')):
            if not branch['complete']:raise ValueError('Run the full predicate exporter first')
            total+=1
            try:
                result=block(raw,branch['body_offset'],branch['body_offset']+branch['body_size'])
                if result['complete']:
                    encoded=encode_block(result)
                    original=raw[branch['body_offset']:branch['body_offset']+branch['body_size']]
                    if encoded!=original:raise ValueError('Body re-encoding differs from source')
                    roundtrips+=1;byte_count+=len(encoded)
            except ValueError as exc:
                errors.append([source.name,branch['segment'],branch['branch'],str(exc)])
                result=dict(complete=False,error=str(exc))
            complete+=int(result['complete'])
            if 'unknown' in result:unknown[result['unknown']['opcode']]+=1
            rows.append(dict(segment=branch['segment'],branch=branch['branch'],**result))
        (output/path.name).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=dict(bodies=total,complete=complete,roundtrip_matches=roundtrips,
                 roundtrip_bytes=byte_count,unknown=dict(unknown.most_common()),errors=errors)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(f'EEX bodies: {complete}/{total} complete; {roundtrips} byte-exact round trips '
          f'({byte_count} bytes); {len(errors)} structure errors; first stops {unknown.most_common(6)}')
    if total!=2320 or errors:raise SystemExit(1)


if __name__=='__main__':main()
