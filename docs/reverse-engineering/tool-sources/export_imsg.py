"""Export fixed 200-byte Imsg.e5 message records from the native accessor."""
import csv
from pathlib import Path
from game_text import decode_game_text,visible_text

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=(ROOT/'Imsg.e5').read_bytes()
    if len(data)%200:raise ValueError('Imsg.e5 is not a 200-byte record table')
    rows=[];errors=[]
    for index in range(len(data)//200):
        raw=data[index*200:(index+1)*200].split(b'\0',1)[0]
        try:text=decode_game_text(raw)
        except UnicodeDecodeError as exc:
            errors.append(dict(index=index,error=str(exc),hex=raw.hex()));text=raw.decode('gbk',errors='replace')
        rows.append((index,visible_text(text),raw.hex()))
    with (ROOT/'analysis/imsg.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['id','text_cp936','raw_hex']);w.writerows(rows)
    print(f'Exported {len(rows)} Imsg records; CP936 errors: {len(errors)}')

if __name__=='__main__':main()
