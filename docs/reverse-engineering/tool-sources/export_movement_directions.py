"""Export the native coordinate-neighbor table used by EEX/map propagation."""
import json,struct
from pathlib import Path
import pefile

ROOT=Path(__file__).resolve().parents[1]

def main():
    pe=pefile.PE(str(ROOT/'Ekd5.exe'));data=pe.get_data(0x8df68,8*8)
    directions=[dict(index=i,dx=struct.unpack_from('<i',data,i*8)[0],dy=struct.unpack_from('<i',data,i*8+4)[0]) for i in range(8)]
    (ROOT/'analysis/movement-directions.json').write_text(json.dumps(directions,indent=2),encoding='utf-8')
    print(directions)
if __name__=='__main__':main()
