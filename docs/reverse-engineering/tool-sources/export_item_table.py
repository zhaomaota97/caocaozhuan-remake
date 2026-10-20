"""Export DATA.E5 item records and the native loader's byte permutation."""
import csv
import struct
from pathlib import Path
from extract_e5 import decode
import pefile


def main():
    data = Path('Data.e5').read_bytes()
    packed, size, offset = struct.unpack_from('>III', data, 0x11c)
    records = decode(data, offset, packed, size)
    assert len(records) == 104 * 25
    pe = pefile.PE('Ekd5.exe')
    base = pe.OPTIONAL_HEADER.ImageBase
    pointers = struct.unpack('<11I', pe.get_data(0x48bc20-base,44))
    labels = [pe.get_data(p-base,80).split(b'\0',1)[0].decode('gbk') for p in pointers]
    pe.close()
    with Path('analysis/items.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'name', 'category_byte', 'category_group', 'category_label',
                         'value_at_level_0', 'base_effect_byte', 'growth_byte', 'disk_hex', 'runtime_hex'])
        for index in range(104):
            raw = records[index*25:(index+1)*25]
            runtime = bytearray(raw)
            runtime[16] = 0
            runtime[20], runtime[18], runtime[19] = raw[18], raw[19], raw[20]
            value = raw[17]
            group = 0 if value < 14 else 1 if value < 18 else 2 if value < 63 else 3
            label = labels[value//2 if value < 18 else 9 if value < 63 else 10]
            price = 65535 if runtime[18] == 255 else runtime[18] * 75
            if price != 65535 and group < 2:
                price //= 2
            writer.writerow([index, raw[:16].split(b'\0',1)[0].decode('gbk', errors='replace'),
                             value, group, label, price, runtime[21], runtime[23],
                             raw.hex(' '), runtime.hex(' ')])
    print('exported 104 item records')


if __name__ == '__main__':
    main()
