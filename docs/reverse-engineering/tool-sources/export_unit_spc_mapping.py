"""Export the native unit-type -> Unit_spc resource mapping table."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    # Literal local_40 table from 0x406947, indexed by character record +0x2B.
    table=[5,5,5,0,1,2,6,7,8,3,4,5,9,10,11,18,19,20,12,13,14,15,16,17,
           21,22,23,24,25,26,27,28,29,23,23,23,14,14,14,33,34,32,31,30,23,23,
           39,35,36,37,38,68,69]
    rows=[]
    for character_class,base in enumerate(table):
        rows.append(dict(character_class=character_class,base_index=base,
                         direction_variants=(min(2,0),min(2,1),min(2,2)),
                         resource_indices=[base*3+d for d in (0,1,2)] if base<34 else [base+68]))
    result=dict(function='0x43FC48',class_lookup='0x406947',table=table,
                formula='if base<0x22: resource=base*3+min(slot+5,2); else resource=base+0x44',
                entries=rows,unit_spc_entries=151,
                note='slot+5 is the native byte used by 0x43FC48; its product-level direction/name is not assumed')
    target=ROOT/'analysis/unit-spc-mapping.json';target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Exported {len(table)} class mappings and {len(set(r["resource_indices"][0] for r in rows))} base resources')


if __name__=='__main__':main()
