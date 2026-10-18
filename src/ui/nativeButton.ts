import Phaser from 'phaser';

/** Classic Win32 push-button chrome; geometry and labels come from dialog resources. */
export function nativeButton(scene:Phaser.Scene,parent:Phaser.GameObjects.Container,
  rect:number[],label:string,id:number,command:()=>void){
  const [x,y,w,h]=rect;
  const face=scene.add.rectangle(x,y,w,h,0xc0c0c0).setOrigin(0)
    .setInteractive(new Phaser.Geom.Rectangle(0,0,w,h),Phaser.Geom.Rectangle.Contains);
  const edge=scene.add.graphics();
  const text=scene.add.text(x+w/2,y+h/2,label,{fontFamily:'SimSun, "宋体", serif',fontSize:'15px',color:'#000000'}).setOrigin(0.5);
  text.setData('controlId',id);face.setData('controlId',id);
  function draw(pressed:boolean){
    edge.clear();
    const top=pressed?0x404040:0xffffff,bottom=pressed?0xffffff:0x404040;
    edge.lineStyle(1,top).beginPath().moveTo(x,y+h-1).lineTo(x,y).lineTo(x+w-1,y).strokePath();
    edge.lineStyle(1,bottom).beginPath().moveTo(x+w-1,y).lineTo(x+w-1,y+h-1).lineTo(x,y+h-1).strokePath();
    edge.lineStyle(1,pressed?0x808080:0xdfdfdf).beginPath().moveTo(x+1,y+h-2).lineTo(x+1,y+1).lineTo(x+w-2,y+1).strokePath();
    edge.lineStyle(1,pressed?0xdfdfdf:0x808080).beginPath().moveTo(x+w-2,y+1).lineTo(x+w-2,y+h-2).lineTo(x+1,y+h-2).strokePath();
    text.setPosition(x+w/2+(pressed?1:0),y+h/2+(pressed?1:0));
  }
  let down=false;
  face.on('pointerdown',(pointer:Phaser.Input.Pointer)=>{if(pointer.button===0){down=true;draw(true);}});
  face.on('pointerout',()=>{down=false;draw(false);});
  face.on('pointerup',(pointer:Phaser.Input.Pointer)=>{if(pointer.button!==0)return;const activate=down;down=false;draw(false);if(activate)command();});
  draw(false);parent.add([face,edge,text]);
  return {face,text};
}
