export class EexCursor {
  readonly data:Uint8Array; pos:number; readonly end:number;
  constructor(data:Uint8Array,offset=0,end=data.length){
    if(offset<0||offset>end||end>data.length)throw new RangeError('invalid EEX cursor span');
    this.data=data;this.pos=offset;this.end=end;
  }
  integer(size:1|2|4):number{
    if(this.pos+size>this.end)throw new RangeError('truncated EEX integer');
    let value=0;for(let i=0;i<size;i++)value|=this.data[this.pos+i]<<(8*i);this.pos+=size;return value>>>0;
  }
  string():Uint8Array{
    let zero=this.pos;while(zero<this.end&&this.data[zero]!==0)zero++;
    if(zero>=this.end)throw new RangeError('unterminated EEX string');
    const value=this.data.slice(this.pos,zero);this.pos=zero+1;return value;
  }
  parameter(tag:1|2|4|5):number|Uint8Array{
    const actual=this.integer(2);
    if(tag===1)return actual;
    if(actual!==tag)return tag===4||tag===5?0x80000000:0x8000;
    if(tag===5)return this.string();
    return this.integer(tag===4?4:2);
  }
}
