"""Summarize s/e/d save-partition structure for one slot."""
from pathlib import Path
import sys

stable_mode = len(sys.argv) > 1 and sys.argv[1] == '--stable'
slot = sys.argv[1] if len(sys.argv) > 1 and not stable_mode else '00'
for suffix in 'sed':
    p = Path(f'Sv{slot}{suffix}.e5s')
    b = p.read_bytes()
    runs=[]; start=0; last=b[0]
    for i,x in enumerate(b[1:],1):
        if x != last:
            if i-start >= 8: runs.append((start,i,last))
            start,last=i,x
    if len(b)-start >= 8: runs.append((start,len(b),last))
    print(f'{p.name} size={len(b)} nonzero={sum(x != 0 for x in b)} nonff={sum(x not in (0,255) for x in b)}')
    print('  long constant runs:', ' '.join(f'0x{s:X}-0x{e:X}:{v:02X}' for s,e,v in runs[:30]))

if stable_mode:
    for suffix in 'sed':
        blobs = [Path(f'Sv{i:02d}{suffix}.e5s').read_bytes() for i in range(10)]
        stable = [off for off in range(len(blobs[0])) if len({b[off] for b in blobs}) == 1]
        print(f'{suffix}: stable_offsets={len(stable)} first=' + ' '.join(f'0x{x:X}' for x in stable[:80]))
        changed = [off for off in range(len(blobs[0])) if len({b[off] for b in blobs}) > 1]
        ranges=[]
        if changed:
            start=prev=changed[0]
            for off in changed[1:]:
                if off != prev + 1:
                    ranges.append((start, prev)); start=off
                prev=off
            ranges.append((start, prev))
        print('  changed_ranges=' + ' '.join(f'0x{s:X}-0x{e:X}' for s,e in ranges[:120]))
