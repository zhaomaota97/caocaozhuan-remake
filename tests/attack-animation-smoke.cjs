const {chromium}=require('@playwright/test');
(async()=>{
  const browser=await chromium.launch();
  try{
    const page=await browser.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto('http://127.0.0.1:5173');
    await page.waitForFunction(()=>window.battleGame?.scene.getScenes(true)[0]?.units?.length>0);
    const rows=await page.evaluate(async()=>{
      const scene=window.battleGame.scene.getScenes(true)[0],attacker=scene.units[0],defender=scene.units[1],rows=[];
      defender.acted=true;
      for(const critical of [false,true])for(const damaged of [true,false])for(const [dx,dy] of [[0,-1],[1,0],[0,1],[-1,0]]){
        defender.direction=dy<0?0:dx>0?1:dy>0?2:3;
        defender.x=attacker.x+dx;defender.y=attacker.y+dy;scene.refreshUnitSprite(defender);
        const frames=[],hurtFrames=[],hurtSamples=[],timer=setInterval(()=>{
          for(const sprite of scene.children.list.filter(o=>o.texture?.key.startsWith('atk-')))
            frames.push(Number(sprite.frame.name));
          for(const sprite of scene.children.list.filter(o=>o.texture?.key.startsWith('spc-')&&o.visible)){
            hurtFrames.push(Number(sprite.frame.name));
            hurtSamples.push({flip:sprite.flipX,x:sprite.x-(defender.x*48+24),y:sprite.y-(defender.y*48+80)});
          }
        },20);
        await scene.playAttackStrike(attacker,defender,{critical,hpDamage:damaged?1:0,mpDamage:0});
        clearInterval(timer);
        const restored=scene.unitSprites.filter(v=>v.unit===attacker||v.unit===defender).every(v=>v.sprite.visible);
        rows.push({critical,damaged,dx,dy,defenderDirection:defender.direction,frames:[...new Set(frames)],hurtFrames:[...new Set(hurtFrames)],hurtSamples,acted:defender.acted,restored,locks:scene.presentationUnits.size});
      }
      return rows;
    });
    console.log(JSON.stringify({rows:rows.map(({hurtSamples,...row})=>({...row,hurt:hurtSamples[0]})),errors}));
    if(errors.length||rows.some(row=>!row.frames.length||row.frames.some(frame=>frame<0||frame>=12)))throw new Error('Attack frame regression');
    if(rows.some(row=>!row.acted||!row.hurtFrames.length||row.hurtFrames.some(frame=>frame<0||frame>=5)))throw new Error('Acted defender hit animation regression');
    for(const row of rows){
      const direction=row.defenderDirection,expectedFrame=row.damaged?3:[1,2,0,2][direction];
      const distance=row.damaged&&!row.critical?4:8;
      const [x,y]=[[0,distance],[-distance,0],[0,-distance],[distance,0]][direction];
      if(row.hurtFrames.some(frame=>frame!==expectedFrame)||row.hurtSamples.some(sample=>sample.flip!==(!row.damaged&&direction===1)||sample.x!==x||sample.y!==y))throw new Error('Native SPC facing/offset mismatch');
      if(!row.restored||row.locks!==0)throw new Error('Presentation state leaked after strike');
    }
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
