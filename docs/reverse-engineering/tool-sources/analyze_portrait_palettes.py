"""Measure FACE color-index stability across actual scene palettes."""
import json
from pathlib import Path

from PIL import Image
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    faces = list(entries(ROOT / 'Face.e5'))
    used = sorted(set(b''.join(raw for _, raw in faces)))
    palettes = [(name, index, raw) for name in ('Pmpalet.e5', 'Spalet.e5')
                for index, raw in entries(ROOT / name)]
    baseline = palettes[0][2]
    rows = []
    profiles = {}
    for name, index, raw in palettes:
        changed = [c for c in used if c != 0 and
                   bytes(v & 0xF0 for v in raw[c*3:c*3+3]) !=
                   bytes(v & 0xF0 for v in baseline[c*3:c*3+3])]
        rows.append(dict(file=name, entry=index, size=len(raw),
                         changed_visible_indices=changed))
        key = bytes(v & 0xF0 for c in used if c != 0 for v in raw[c*3:c*3+3])
        if key not in profiles:
            profiles[key] = dict(id=len(profiles), representative=dict(file=name, entry=index),
                                 members=[], changed_indices=changed,
                                 affected_faces=[dict(index=i, pixels=sum(p in changed for p in pixels))
                                                 for i, pixels in faces if any(p in changed for p in pixels)])
        profiles[key]['members'].append(dict(file=name, entry=index))
        rows[-1]['profile'] = profiles[key]['id']
    target = ROOT / 'analysis/portraits'
    target.mkdir(exist_ok=True)
    # These are labeled baseline previews, not a claim of scene-independent colors.
    rgb = bytes(v & 0xF0 for c in range(256)
                for v in (baseline[c*3+1], baseline[c*3+2], baseline[c*3]))
    for index, raw in faces:
        image = Image.frombytes('P', (64, 80), raw)
        image.putpalette(rgb)
        image.save(target / f'{index:04d}.png', transparency=0)
    for profile in profiles.values():
        rep = profile['representative']
        palette = next(raw for name, index, raw in palettes
                       if name == rep['file'] and index == rep['entry'])
        palette = palette.ljust(768, b'\0')
        colors = bytes(v & 0xF0 for c in range(256)
                       for v in (palette[c*3+1], palette[c*3+2], palette[c*3]))
        image = Image.frombytes('P', (64, 80), faces[0][1])
        image.putpalette(colors)
        image.save(target / f'profile-{profile["id"]}-face0000.png', transparency=0)
    result = dict(baseline=dict(file=palettes[0][0], entry=palettes[0][1]),
                  used_indices=used, nonzero_visible_indices=len([c for c in used if c]),
                  palettes=rows, palette_count=len(rows),
                  equal_visible_colors=sum(not r['changed_visible_indices'] for r in rows),
                  visible_color_profiles=list(profiles.values()),
                  actual_zero_index_pixels=sum(raw.count(0) for _, raw in faces),
                  preview='64x80 PNG, baseline palette, index 0 transparent; not final Web assets',
                  channel_evidence='native stored channel order converted as channel1,channel2,channel0; high nibble retained')
    (ROOT / 'analysis/portrait-palette-analysis.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    print(f'{len(faces)} previews; {len(used)} used indices; '
          f'{result["equal_visible_colors"]}/{len(rows)} palettes preserve all visible FACE colors')
    print('Changed palette examples:', [(r['file'], r['entry'], len(r['changed_visible_indices']))
                                         for r in rows if r['changed_visible_indices']][:8])
    print(f'{len(profiles)} visible-color profiles; {result["actual_zero_index_pixels"]} zero-index pixels')


if __name__ == '__main__':
    main()
