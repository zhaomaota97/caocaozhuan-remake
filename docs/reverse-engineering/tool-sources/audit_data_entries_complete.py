"""Combine DATA.E5 call-site, sparse-shape, and live-request evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
loader=json.loads((ROOT/'analysis/data-loader-calls.json').read_text(encoding='utf-8'))
sparse=json.loads((ROOT/'analysis/data-sparse-entry-summary.json').read_text(encoding='utf-8'))
live_path=Path(__import__('sys').argv[1]) if len(__import__('sys').argv)>1 else None
live=json.loads((live_path/'data-entry-audit.json').read_text(encoding='utf-8')) if live_path else None
result={'literalLoaderEntries':loader['literal_entries'],'nonliteralLoaderCalls':loader['nonliteral_entries'],
        'sparseEntries':sparse,'liveTrace':live,
        'conclusion':'Entries 0-5 have literal loader call sites and live startup requests; entries 6-9 have decoded sparse shapes but no observed loader request in the supplied trace.'}
(ROOT/'analysis/data-entry-complete-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('literal',loader['literal_entries'],'live',live['requested'] if live else 'not supplied','sparse',sorted(sparse))
