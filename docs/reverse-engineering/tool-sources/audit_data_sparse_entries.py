"""Describe Data.e5 entries 6-9 without inventing a runtime semantic."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for index,raw in entries(ROOT/'Data.e5'):
    if index<6: continue
    counts={str(value):raw.count(value) for value in sorted(set(raw))}
    nonzero=[(pos,value) for pos,value in enumerate(raw) if value]
    runs=[]
    if nonzero:
        start=last=nonzero[0][0]; value=nonzero[0][1]
        for pos,current in nonzero[1:]:
            if pos!=last+1 or current!=value:
                runs.append({'start':start,'end':last,'value':value})
                start=pos;value=current
            last=pos
        runs.append({'start':start,'end':last,'value':value})
    record_size=17
    record_count,record_remainder=divmod(len(raw),record_size)
    record_signatures=[]
    if record_remainder==0:
        record_signatures=sorted({raw[j:j+record_size].hex() for j in range(0,len(raw),record_size)})
    rows.append({'index':index,'decodedBytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                 'distinctByteValues':sorted(set(raw)),'counts':counts,
                 'nonzeroBytes':len(nonzero),'nonzeroRuns':runs[:100],
                 'nonzeroRunsTruncated':len(runs)>100,
                 'record17':{'count':record_count,'remainder':record_remainder,
                              'distinctRecordSignatures':len(record_signatures),
                              'signatures':record_signatures[:16]},
                 'periodicRecordHypotheses':[{'recordBytes':width,'records':len(raw)//width,'remainder':len(raw)%width,
                   'allRecordsEqual':len(raw)%width==0 and len({raw[j:j+width] for j in range(0,len(raw),width)})==1}
                  for width in (17,21) if len(raw)%width==0]})
result={'file':'Data.e5','entries':rows,
        'interpretation':'decoded sparse binary payloads; no runtime semantic assigned',
        'staticLoaderEvidence':'no literal loader index 6-9 found in recovered Ekd5 pseudocode'}
(ROOT/'analysis/data-sparse-entry-summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Sparse Data.e5 entries:',', '.join(f"{r['index']}={r['nonzeroBytes']} nonzero/{r['decodedBytes']}" for r in rows))
