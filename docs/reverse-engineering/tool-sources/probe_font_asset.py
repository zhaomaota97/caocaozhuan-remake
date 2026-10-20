"""Produce a clearly labeled exploratory view of raw Font.e5; no native format claim."""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=(ROOT/'Font.e5').read_bytes()
    # 1602 = 89 * 18; 18-byte glyph hypothesis is only a diagnostic view.
    glyphs=[]
    for index in range(len(data)//18):
        rows=data[index*18:(index+1)*18]
        image=Image.new('1',(16,9)); pixels=image.load()
        for y in range(9):
            word=rows[y*2] | rows[y*2+1]<<8
            for x in range(16):pixels[x,y]=1 if word&(1<<x) else 0
        glyphs.append(image)
    sheet=Image.new('1',(16*16,9*6))
    for i,glyph in enumerate(glyphs[:96]):sheet.paste(glyph,((i%16)*16,(i//16)*9))
    out=ROOT/'analysis/font-probe-16x9.png';sheet.resize((out.width if out.exists() else 256,144)).save(out)
    print(f'Wrote exploratory {out}; glyph hypothesis count={len(glyphs)}')

if __name__=='__main__':main()
