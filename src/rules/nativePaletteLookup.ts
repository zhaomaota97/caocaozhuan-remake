/** Native 0x42FB10: constrained color search, later equal candidates win. */
export function nativePaletteColorIndex(color:readonly number[],palette:readonly number[]):number{
  let dominant=0,maximum=0;
  for(let channel=0;channel<3;channel++)if(color[channel]>maximum){maximum=color[channel];dominant=channel;}
  let result=0,bestMaximum=65535,bestTotal=65535;
  for(let index=10;index<246;index++){
    let differenceMaximum=0,total=0,candidateDominant=0,candidateMaximum=0;
    for(let channel=0;channel<3;channel++){
      const value=palette[index*3+channel],difference=Math.abs(color[channel]-value);
      differenceMaximum=Math.max(differenceMaximum,difference);total+=difference;
      if(value>candidateMaximum){candidateMaximum=value;candidateDominant=channel;}
    }
    if(differenceMaximum<=bestMaximum&&total<=bestTotal&&dominant===candidateDominant){
      result=index;bestMaximum=differenceMaximum;bestTotal=total;
    }
  }
  return result;
}

/** Native 0x42FCC6 uses four-bit channel order, not display RGB order. */
export function buildNativePaletteLookup(palette:readonly number[]):Uint8Array{
  if(palette.length!==768)throw new RangeError('Native palette must contain 768 bytes');
  const lookup=new Uint8Array(4096);
  for(let a=0;a<16;a++)for(let b=0;b<16;b++)for(let c=0;c<16;c++)lookup[a*256+b*16+c]=nativePaletteColorIndex([a,b,c],palette);
  return lookup;
}
