"""Inventory every shipped E5/E5S/EEX file by proven container/layout class."""
import hashlib,json,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def e5(path):
    data=path.read_bytes()
    if data[:4]==b'Ls12':return 'Ls12-container'
    if path.stem.lower().startswith('hm'):return 'raw-Hm-artwork'
    known={'Mark':'raw-Mark-mask','Mcall':'raw-Mcall-clip','Imsg':'raw-Imsg','Font':'raw-Font'}
    for key,value in known.items():
        if path.stem.lower().startswith(key.lower()):return value
    return 'raw-unclassified'

def main():
    rows=[]
    for path in sorted(ROOT.glob('*.e5')):
        data=path.read_bytes();rows.append(dict(file=path.name,kind=e5(path),size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),head=data[:8].hex()))
    for path in sorted(ROOT.glob('*.e5s')):
        data=path.read_bytes();rows.append(dict(file=path.name,kind='save-s-partition' if path.stem.lower().endswith('s') else 'save-partition',
            size=len(data),version=data[0],sha256=hashlib.sha256(data).hexdigest()))
    for path in sorted(ROOT.glob('*.eex')):
        data=path.read_bytes();rows.append(dict(file=path.name,kind='EEX-script',size=len(data),sha256=hashlib.sha256(data).hexdigest()))
    result=dict(files=len(rows),by_kind={},fileset=rows)
    for row in rows:result['by_kind'][row['kind']]=result['by_kind'].get(row['kind'],0)+1
    (ROOT/'analysis/game-format-inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Game format inventory: {len(rows)} files; {result["by_kind"]}')

if __name__=='__main__':main()
