/** Original 0x47FAE7 / 0x47FB13 / 0x47FB32. State must be saved with a battle. */
export class GameRng {
  state:number;
  constructor(seed:number){this.state=seed>>>0;}
  draw():number{
    this.state=(Math.imul(this.state,0x41c64e6d)+0x3039)>>>0;
    return (this.state>>>16)&0x7fff;
  }
  bounded(bound:number):number{return bound>1?this.draw()%bound:0;}
  chance(percent:number):boolean{return this.bounded(100)<percent;}
}
