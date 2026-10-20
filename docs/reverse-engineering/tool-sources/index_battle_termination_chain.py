"""Index native battle target, turn, and termination routines from pseudocode."""
import re, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
addresses=['00438a20','00438965','004391dc','004395ae','0043a529','0043ad1c','004337f4','00433bc8','0044c658','0044c74d','0044c8e6']
rows=[]
for address in addresses:
    path=ROOT/'analysis/native-main/pseudocode'/f'{address}.c'
    text=path.read_text(encoding='utf-8',errors='replace') if path.exists() else ''
    rows.append({'address':'0x'+address,'pseudocode':str(path.relative_to(ROOT)) if path.exists() else None,
                 'present':bool(text),'calledFunctions':sorted(set(re.findall(r'FUN_([0-9A-Fa-f]{8})',text))),
                 'globals':sorted(set(re.findall(r'DAT_([0-9A-Fa-f]{8})',text))),
                 'hasReturn':bool(re.search(r'\breturn\b',text))})
result={'chain':rows,'evidenceBoundary':'Static call/token index; victory/defeat integration remains dynamically unverified.'}
(ROOT/'analysis/battle-termination-chain.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('indexed',sum(row['present'] for row in rows),'of',len(rows),'termination-chain routines')
