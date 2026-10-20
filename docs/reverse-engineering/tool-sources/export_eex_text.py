"""Export indexed EEX segments and conservative GBK text candidates."""
import csv
from pathlib import Path
from eex_segments import inspect


def main():
    out = Path('analysis/eex')
    out.mkdir(parents=True, exist_ok=True)
    texts = []
    tagged = []
    for path in sorted(Path('.').glob('*.eex')):
        data = path.read_bytes()
        for number, segment in enumerate(inspect(path)['segments']):
            start = segment['offset']
            end = start + segment['size']
            (out / f'{path.stem}-{number:03d}.bin').write_bytes(data[start:end])
            cursor = start
            while cursor < end:
                tag = data.find(b'\x05\x00', cursor, end)
                if tag < 0:
                    break
                zero = data.find(b'\0', tag + 2, end)
                if zero >= 0:
                    raw = data[tag + 2:zero]
                    try:
                        text = raw.decode('gbk')
                    except UnicodeDecodeError:
                        pass
                    else:
                        if len(raw) >= 2 and all(c in '\r\n\t' or ord(c) >= 32 for c in text):
                            tagged.append([path.name, number, hex(tag), text])
                cursor = tag + 2
            pos = start
            while pos < end:
                if data[pos] < 0x80:
                    pos += 1
                    continue
                first = pos
                while pos + 1 < end and 0x81 <= data[pos] <= 0xFE and 0x40 <= data[pos+1] <= 0xFE and data[pos+1] != 0x7F:
                    pos += 2
                raw = data[first:pos]
                if len(raw) >= 8:
                    try:
                        text = raw.decode('gbk')
                    except UnicodeDecodeError:
                        pass
                    else:
                        texts.append([path.name, number, hex(first), text])
                pos = max(pos, first + 1)
    with (out / 'text-candidates.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['file', 'segment', 'offset', 'text_candidate'])
        writer.writerows(texts)
    preview = ['# R_00 Script Text Candidates', '',
               'GBK text spans in file order; speaker and branch semantics are not yet decoded.', '']
    for filename, segment, offset, text in texts:
        if filename == 'R_00.eex':
            preview.extend([f'`segment {segment}, {offset}`', '', text, ''])
    (out / 'R_00-readable.md').write_text('\n'.join(preview), encoding='utf-8')
    with (out / 'tag5-string-candidates.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['file', 'segment', 'tag_offset', 'gbk_text'])
        writer.writerows(tagged)
    print('tag-5 string candidates:', len(tagged))
    print('text candidates:', len(texts))


if __name__ == '__main__':
    main()
