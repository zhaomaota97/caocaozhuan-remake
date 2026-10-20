"""Export readable native event observations into independent remake data."""
import argparse
import json
from pathlib import Path
from game_text import decode_game_text

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event',choices=('liu','victory'),default='liu')
    args=parser.parse_args()
    source=json.loads((ROOT/f'analysis/native-s00-{args.event}-movement-validation.json').read_text(encoding='utf-8'))
    if not source['passed']:raise ValueError('Native movement checks must pass')
    calls=source['eventExecution']['calls']
    for call in calls:
        if 'bytes' in call:
            call['text']=decode_game_text(bytes(call.pop('bytes')))
    result=dict(script='S_00.eex',segment=1,branch=1 if args.event=='liu' else 9,
                source_body_offsets=[7885,8353] if args.event=='liu' else [13169,14333],
                evidence_scope=source['scope'],observations=calls,path_checks=source['path_checks'],
                flag11_after=source['eventExecution']['flag11'],
                completion_flags=source['eventExecution'].get('completionFlags'),
                money_after=source['eventExecution'].get('money'),
                note='Observed fixture, not an executable replacement script or complete battle state')
    text=json.dumps(result,ensure_ascii=False,indent=2)
    (ROOT/f'analysis/s00-{args.event}-event-readable.json').write_text(text,encoding='utf-8')
    (ROOT.parent/f'caocaozhuan-remake/data/scenarios/S_00-{args.event}-event-trace.json').write_text(text,encoding='utf-8')
    print(f'Exported {sum(c["kind"]=="dialogue" for c in calls)} dialogue segments; '
          f'{len(source["path_checks"])} paths, {sum(p["steps"] for p in source["path_checks"])} steps')


if __name__=='__main__':main()
