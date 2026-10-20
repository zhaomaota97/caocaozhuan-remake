"""Export the evidence-backed E-partition object schema."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = [
    ('record_table', '0x2044', '115 x 0x40', 'record base accessor', 'FUN_00418DD0', 'observed'),
    ('record.field0', '0x2044', 'u32', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field1', '0x2048', 'u8', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field2', '0x2049', 'u8', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field3', '0x204c', 'u32', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field4', '0x2050', 'u8', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field5', '0x2052', 'u16', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field6', '0x2054', 'u8', 'record scalar', 'FUN_00417A54', 'observed'),
    ('record.field7', '0x2055', 'u8', 'record scalar', 'FUN_00417A54', 'observed'),
    ('byte_state', '0x3d0e', 'u8', 'direct write/read', 'FUN_00418df0', 'observed'),
    ('predicate_pair_a', '0x3d04', 'u16,u16', 'bit0 + equality predicate', 'FUN_0044f7d0', 'observed'),
    ('predicate_pair_b', '0x3d08', 'u16,u16', 'bit0 + equality predicate', 'FUN_0044f860', 'observed'),
    ('tail_table', '0x38', '0x800 x u32', 'serialized sparse/event table', 'FUN_00417a54', 'observed'),
    ('tail_marker_a', '0x2038', 'u32', 'serialized marker', 'FUN_00417a54', 'observed'),
    ('tail_marker_b', '0x203c', 'u32', 'serialized marker', 'FUN_00417a54', 'observed'),
    ('final_header', 'temporary', '5 x i16', 'copied to object +04,+08,+10,+14,+24', 'FUN_00410506', 'observed'),
]
with (ROOT/'analysis/e-partition-schema.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['field','offset','type','operation','evidence','confidence']);w.writerows(rows)
print(f'exported E-partition schema: {len(rows)} fields')
