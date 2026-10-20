"""Compare captured original-engine buffers to the offline decoder."""
import hashlib
import json
import struct
import sys
from pathlib import Path
from extract_e5 import decode


def main(log):
    results = []
    for line in Path(log).read_text(encoding='utf-8').splitlines():
        item = json.loads(line).get('payload', {})
        if item.get('event') != 'decoded-resource':
            continue
        source = Path(item['container'])
        data = source.read_bytes()
        packed, size, offset = struct.unpack_from('>III', data, 0x110 + item['index'] * 12)
        result = decode(data, offset, packed, size)
        observed = Path(item['dump_path']).read_bytes()
        match = result == observed
        results.append({'container': str(source), 'index': item['index'],
                        'size': size, 'match': match,
                        'sha256': hashlib.sha256(result).hexdigest()})
    print(json.dumps(results, indent=2))
    if not results or not all(r['match'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
