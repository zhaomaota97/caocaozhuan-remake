"""Export GBK strings from fixed save header text windows."""
import csv
from pathlib import Path


def main():
    rows = []
    for path in sorted(Path('.').glob('Sv??[sd].e5s')):
        data = path.read_bytes()
        raw = data[5:0x23].split(b'\0', 1)[0] if path.stem.endswith('s') else data[5:0x35].split(b'\0', 1)[0]
        rows.append([path.name, data[:5].hex(' '), raw.decode('gbk', errors='replace'), raw.hex(' ')])
    with Path('analysis/save-header-text.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['file', 'header_hex', 'text_candidate', 'raw_hex'])
        writer.writerows(rows)
    print('headers', len(rows))


if __name__ == '__main__':
    main()
