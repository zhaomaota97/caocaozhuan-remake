import Phaser from 'phaser';
import type { BattleMap, Unit } from '../model/battle';
import slot08 from '../../data/saves/slot-08.json';
import savedConsumableStock from '../../data/saves/consumable-stock.json';
import {nativeConsumableCount} from '../rules/consumableInventory';
import { loadUnits, saveUnits,loadRngState,setRngState } from '../save/localSave';
import { idleFrame } from '../rules/idleFrame';
import toolbar from '../../data/mappings/battle-toolbar.json';
import minimapUnits from '../../data/mappings/minimap-31-units.json';
import { movementCosts } from '../rules/movementCosts';
import { terrainCost } from '../rules/terrainCost';
import itemCategories from '../../data/rules/item-categories.json';
import terrainMovement from '../../data/rules/terrain-movement.json';
import classMovement from '../../data/rules/class-movement.json';
import {movementBudget} from '../rules/movementBudget';
import {movementPath,movementFrames,directions} from '../rules/movementPath';
import movementSounds from '../../data/mappings/movement-sounds.json';
import attackClasses from '../../data/rules/class-attack-ranges.json';
import targetShapes from '../../data/rules/target-shapes.json';
import {attackRange,inAttackRange} from '../rules/attackRange';
import combatAttributes from '../../data/mappings/slot08-combat-attributes.json';
import {ordinaryDamage} from '../rules/ordinaryDamage';
import combatRuntime from '../../data/mappings/slot08-combat-runtime.json';
import combatSheets from '../../data/mappings/combat-sheets-map31.json';
import actedMovementArt from '../../data/mappings/acted-movement-art.json';
import {nativeActorIsDarkened} from '../rules/actedDarkening';
import scenarioCombat from '../../data/mappings/scenario-combat-runtime.json';
import nativeEquipmentAttributes from '../../data/rules/native-equipment-attributes.json';
import {nativeBattleAttributes} from '../rules/battleAttributes';
import {ordinaryExchange,type ExchangeStrike} from '../rules/ordinaryExchange';
import {GameRng} from '../rules/gameRng';
import nativeUi from '../../data/mappings/native-ui-templates.json';
import effectLearning from '../../data/mappings/effect-learning-runtime.json';
import {allRuntimeEffects,effectById} from '../rules/effectCatalog';
import {nativeButton} from '../ui/nativeButton';
import {nearestNativeCandidate} from '../rules/aiCandidateFilter';
import {nativeAiOrdinaryAttackScore,nativeAiClassFiltered} from '../rules/aiAttackScore';
import {nativeManualItemEligible} from '../rules/manualItemEligibility';
import {collectNativeAdjacentCandidates,selectNativeAiCandidate} from '../rules/aiCandidateSelection';
import treasureCatalog from '../../data/mappings/treasure-catalog.json';
import rosterColumns from '../../data/mappings/roster-columns.json';
import rosterFields from '../../data/mappings/slot08-roster-fields.json';
import effectGeometry from '../../data/rules/effect-target-shapes.json';
import soundValidation from '../../data/mappings/native-sound-mapping-validation.json';
import battleResources from '../../data/mappings/battle-resource-links.json';
import s00Units from '../../data/scenarios/S_00-units-native.json';
import s00Terrain from '../../data/scenarios/S_00-terrain.json';
import s00LiuTrace from '../../data/scenarios/S_00-liu-event-trace.json';
import s01Units from '../../data/scenarios/S_01-units-native.json';
import {scenarioUnits} from '../data/scenarioUnits';
import nativeTerrainIndex from '../../data/scenarios/native-terrain-index.json';
import portraitBank from '../../public/assets/portraits/bank.json';
import { portraitIndex, portraitRgba } from '../rules/portraitIndex';
import { nativeCameraSteps, clampNativeCamera } from '../rules/nativeCamera';
import {applyEexOpcode32,applyEexOpcode58,applyEexOpcode103,type NativeCommonState} from '../rules/nativeCommonState';
import scenarioMusic from '../../data/mappings/scenario-music.json';

export class BattleScene extends Phaser.Scene {
  private mapId=0;
  private map: BattleMap = {id:slot08.mapId,width:slot08.width,height:slot08.height,terrain:slot08.terrain};
  private units: Unit[] = loadUnits(slot08.actors.map((unit) => ({...unit, side: unit.side as Unit['side'], acted:false})));
  private selected?: Unit; private cells = new Map<string, Phaser.GameObjects.Rectangle>();
  private selectedStart?: {x:number;y:number;direction?:number;mirror?:boolean;actorFlags?:number};
  private animating=false;
  private moving=false;
  private presentationUnits=new Set<Unit>();
  private bgmStarted=false;
  private consumableStock?:number[];
  private unitSprites: Array<{unit: Unit; sprite: Phaser.GameObjects.Sprite; hpBack: Phaser.GameObjects.Rectangle; hpFill: Phaser.GameObjects.Rectangle}> = [];
  private phase = slot08.animationPhase;
  private phaseElapsed = 0;
  private minimap?: Phaser.GameObjects.Container;
  private minimapActors?: Phaser.GameObjects.Graphics;
  private minimapViewport?: Phaser.GameObjects.Rectangle;
  private statusText?: Phaser.GameObjects.Text;
  private conditionText?: Phaser.GameObjects.Text;
  private terrainText?: Phaser.GameObjects.Text;
  private inventoryText?: Phaser.GameObjects.Text;
  private rosterText?: Phaser.GameObjects.Text;
  private contextMenu?: Phaser.GameObjects.Container;
  private utilityMenu?: Phaser.GameObjects.Container;
  private selectedEffectId?:number;
  private selectedItemId?:number;
  private actionMode?: 'attack'|'strategy'|'item';
  private actionNotice?: Phaser.GameObjects.Text;
  private turnText?: Phaser.GameObjects.Text;
  private turnTransitioning=false;
  private openingEventActive=false;
  private battleEnded=false;
  private gold=0;
  private currentTurn=slot08.turn;
  private commonState:NativeCommonState={portraitFlags:0,portraitPhase:0};
  private modal?: Phaser.GameObjects.Container;
  private battleRng=new GameRng(loadRngState());
  private lastExchange:ExchangeStrike[]=[];
  private readonly size=48; private readonly ox=0; private readonly oy=56;
  init(data?:{mapId?:number}){
    if(data?.mapId!==undefined)this.mapId=data.mapId;
    for(let index=0;index<58;index++)this.sound.get(`scenario-bgm-${index}`)?.destroy();
    this.sound.get('saved-bgm')?.destroy();
    this.input.mouse?.disableContextMenu();
    this.bgmStarted=false;
    this.consumableStock=undefined;
    this.animating=false;this.moving=false;
    this.selected=undefined;
    this.cells.clear();
    this.unitSprites=[];
    this.statusText=undefined;
    this.conditionText=undefined;
    this.terrainText=undefined;
    this.inventoryText=undefined;
    this.rosterText=undefined;
    this.contextMenu=undefined;this.actionMode=undefined;
    this.utilityMenu=undefined;this.selectedEffectId=undefined;this.selectedItemId=undefined;
    this.minimapActors=undefined;this.minimapViewport=undefined;
    this.actionNotice=undefined;this.turnText=undefined;this.turnTransitioning=false;this.currentTurn=slot08.turn;
    this.openingEventActive=false;
    this.battleEnded=false;this.gold=0;
    this.modal=undefined;
    setRngState(this.battleRng.state);
    this.phase=slot08.animationPhase;
    this.commonState={portraitFlags:0,portraitPhase:0};
    this.phaseElapsed=0;
    this.events.once(Phaser.Scenes.Events.SHUTDOWN,()=>{
      for(let index=0;index<58;index++)this.sound.get(`scenario-bgm-${index}`)?.destroy();
      this.sound.get('saved-bgm')?.destroy();
    });
  }
  preload(){
    const profile=(actedMovementArt.scenes as Record<string,number>)[String(this.mapId)];
    const bank=actedMovementArt.banks.find(row=>row.profile===profile);
    for(const sheet of bank?.assets??[]){
      const key=`mov-acted-${profile}-${sheet.art}`;
      if(!this.textures.exists(key))this.load.spritesheet(key,sheet.url,{frameWidth:48,frameHeight:48});
    }
    for(const item of treasureCatalog.entries)this.load.image(`treasure-${item.itemId}`,item.iconUrl);
    // The native selector was verified for 212 sound IDs. Keep the complete
    // bank available so effect, menu, movement and combat paths do not fall
    // back to invented or missing audio.
    for(const asset of soundValidation as Array<{id?:number;expected?:string}>){
      if(!Number.isFinite(Number(asset.id))||!asset.expected)continue;
      const id=Number(asset.id);
      const file=asset.expected.toLowerCase();
      this.load.audio(`native-se-${id}`,`/assets/audio/native/${file}`);
    }
    for(const id of [7,30,31,32,33,34,35,36,37])this.load.audio(`combat-${id}`,`/assets/audio/native/se${String(id).padStart(2,'0')}.wav`);
    for(const effect of allRuntimeEffects()){
      const match=effect.sound?.match(/(\d+)/);
      if(match)this.load.audio(`effect-${effect.effectId}`,`/assets/audio/Se_m_${String(Number(match[1])).padStart(2,'0')}.wav`);
    }
    for(let i=0;i<9;i++)this.load.image(`effect-mcall-${i}`,`/assets/effects/Mcall${String(i).padStart(2,'0')}.gif`);
    for(const sheet of combatSheets){
      this.load.spritesheet(`${sheet.family}-${sheet.index}`,sheet.url,{frameWidth:sheet.tileSize,frameHeight:sheet.tileSize});
    }
    for(let id=23;id<=29;id++)this.load.audio(`step-${id}`,`/assets/audio/native/se${id}.wav`);
    this.load.image('minimap-31','/assets/maps/minimap-31.png');
    for(const button of toolbar.buttons){
      if(button.url)this.load.image(`toolbar-${button.commandId}`,button.url);
    }
    for(let index=0;index<58;index++){
      const id=String(index).padStart(2,'0');
      this.load.image(`battle-${id}`,`/assets/maps/battle-${id}.png`);
      const music=(scenarioMusic as Record<string,{asset:string}>)[`S_${id}.eex`];
      if(music)this.load.audio(`scenario-bgm-${index}`,music.asset);
    }
    for(let index=0;index<4;index++){
      this.load.image(`cmd-${index}`,`/assets/ui/${String(index).padStart(4,'0')}.png`);
    }
    for(let index=0;index<151;index++){
      const key=`mov-${String(index).padStart(3,'0')}`;
      this.load.spritesheet(key,`/assets/animations/movement-map31/${key}.png`,{frameWidth:48,frameHeight:48});
    }
  }
  create(_data?: {mapId?:number}){if(_data?.mapId!==undefined)this.mapId=_data.mapId; const resource=(battleResources as Array<{map_id:number;width_tiles:number;height_tiles:number}>).find(item=>item.map_id===this.mapId)??battleResources[0] as {width_tiles:number;height_tiles:number}; this.map={id:this.mapId,width:resource.width_tiles,height:resource.height_tiles,terrain:[]}; this.units=this.mapId===31?loadUnits(slot08.actors.map((unit) => ({...unit, side: unit.side as Unit['side'], acted:false}))):this.mapId===0?this.createS00Units():[]; this.add.image(0,this.oy,`battle-${String(this.mapId).padStart(2,'0')}`).setOrigin(0,0); this.add.rectangle(0,0,960,56,0x18202a).setOrigin(0); this.add.text(38,17,this.mapId===31?'马超迎击战':this.mapId===0?'颍川黄巾战':`关卡 ${String(this.mapId).padStart(2,'0')}`,{fontSize:'20px',color:'#f0f3f5',fontStyle:'bold'}); this.add.text(690,18,this.mapId===31?`回合数   ${slot08.turn} / ${slot08.turnLimit}`:this.mapId===0?'S_00 原生单位已接入':'地图资源已还原，单位/剧本待接入',{fontSize:'16px',color:'#d9e6f2'}); for(let i=0;i<4;i++)this.add.image(250+i*28,20,`cmd-${i}`).setDisplaySize(20,20); this.drawGrid(); this.drawUnits(); if(this.mapId===0)this.time.delayedCall(350,()=>void this.playS00OpeningEvent());
    this.input.on('gameobjectdown',(_p: Phaser.Input.Pointer,obj: Phaser.GameObjects.GameObject)=>{if(_p.button!==0||this.animating)return;const unit=obj.getData('unit') as Unit; if(!unit||unit.hp<=0)return; if(this.actionMode){if(this.actionMode==='attack'&&this.selected&&unit.side!==this.selected.side)void this.executeAttack(unit);else if(this.actionMode==='strategy'&&this.selected)this.previewVerifiedEffect(unit);else if(this.actionMode==='item'&&this.selected)this.previewVerifiedItem(unit);return;} this.select(unit);});
    this.input.once('pointerdown',()=>{void (this.sound as Phaser.Sound.WebAudioSoundManager).context?.resume();});
    this.input.on('pointerdown',(pointer:Phaser.Input.Pointer)=>{
      if(pointer.leftButtonDown()&&this.modal){
        const regions=this.modal.getData('nativeHitRegions') as Array<{x:number;y:number;width:number;height:number;command:()=>void}>|undefined;
        const region=regions?.find(item=>pointer.x>=this.modal!.x+item.x&&pointer.x<this.modal!.x+item.x+item.width&&pointer.y>=this.modal!.y+item.y&&pointer.y<this.modal!.y+item.y+item.height);
        if(region){region.command();return;}
      }
      if(this.modal)return;
      if(this.battleEnded)return;
      // Fixed UI containers must be hit in screen coordinates. Phaser's
      // normal child hit test can apply the battlefield camera offset after
      // scrolling, so use the dialog's native pixel regions as a fallback.
      if(pointer.leftButtonDown()&&this.contextMenu){
        const panel=this.contextMenu,regions=panel.getData('nativeHitRegions') as Array<{id:number;x:number;y:number;width:number;height:number;command:()=>void}>|undefined;
        const region=regions?.find(item=>pointer.x>=panel.x+item.x&&pointer.x<panel.x+item.x+item.width&&pointer.y>=panel.y+item.y&&pointer.y<panel.y+item.y+item.height);
        if(region){region.command();return;}
      }
      if(!pointer.rightButtonDown())return;
      if(this.actionMode&&this.selected){this.actionMode=undefined;this.actionNotice?.setVisible(false);this.clearReach();this.openContextMenu(this.selected,pointer.x,pointer.y);return;}
      const world=this.cameras.main.getWorldPoint(pointer.x,pointer.y);
      const x=Math.floor((world.x-this.ox)/this.size),y=Math.floor((world.y-this.oy)/this.size);
      const unit=this.moving?this.selected:this.units.find(candidate=>candidate.x===x&&candidate.y===y);
      // Native behavior: a right click on any actor opens its information
      // dialog; only a living player actor with an available action gets the
      // command menu. Empty battlefield space opens end-turn confirmation.
      if(unit){
        if(unit.side==='player' && !unit.acted)this.openContextMenu(unit,pointer.x,pointer.y);
        else this.openUnitInfoModal(unit);
      }else this.openEndTurnConfirm();
    });
    this.fixInterfaceToViewport();
    this.statusText=this.add.text(834,270,'选择单位查看原版存档信息',{fontSize:'12px',color:'#e6edf3',backgroundColor:'#18202a',padding:{x:8,y:8},wordWrap:{width:108}}).setScrollFactor(0).setDepth(120);
    this.conditionText=this.add.text(834,430,'',{fontSize:'14px',color:'#f4e3a1',backgroundColor:'#18202a',padding:{x:8,y:8},wordWrap:{width:190}}).setScrollFactor(0).setDepth(120).setVisible(false);
    this.terrainText=this.add.text(0,0,'',{fontSize:'13px',color:'#eef5f8',backgroundColor:'#18202a',padding:{x:6,y:5}}).setScrollFactor(0).setDepth(200).setVisible(false);
    this.inventoryText=this.add.text(620,270,'',{fontSize:'13px',color:'#eef5f8',backgroundColor:'#18202a',padding:{x:8,y:8},wordWrap:{width:195}}).setScrollFactor(0).setDepth(120).setVisible(false);
    this.rosterText=this.add.text(400,270,'',{fontSize:'13px',color:'#eef5f8',backgroundColor:'#18202a',padding:{x:8,y:8},wordWrap:{width:200},maxLines:14}).setScrollFactor(0).setDepth(120).setVisible(false);
    this.cameras.main.setBounds(0,0,960,1592);
    this.input.on('wheel',(_pointer: Phaser.Input.Pointer,_objects: Phaser.GameObjects.GameObject[],_dx:number,dy:number)=>{
      if(this.modal)return;
      const maxScroll=Math.max(0,this.map.height*this.size+this.oy-this.cameras.main.height);
      this.cameras.main.scrollY=Phaser.Math.Clamp(this.cameras.main.scrollY+dy,0,maxScroll);
    });
    for(const [key,cell] of this.cells){
      cell.setInteractive();
      cell.on('pointerdown',(pointer:Phaser.Input.Pointer)=>{if(pointer.button===0)this.moveSelectedTo(key);});
    }
  }
  private ensureNativeTerrain(mapId:number){const terrain=(nativeTerrainIndex as any)[String(mapId)];if(terrain){this.map.width=terrain.width;this.map.height=terrain.height;this.map.terrain=Array.isArray(terrain.terrain)?terrain.terrain:terrain.terrain.value;}}
  private createS01Units():Unit[]{
    this.ensureNativeTerrain(1);
    return (s01Units.units as Array<any>).map(record=>({id:`s01-slot-${record.slot}`,name:`角色 ${record.unitId}`,art:record.art,side:record.slot<35?'player':'enemy',x:record.position[0],y:record.position[1],hp:record.hp,maxHp:record.maxHp,mp:record.mp,move:6,acted:false,direction:record.facing,actorFlags:record.actorFlags,statusFlags:0,nativeClassId:record.classId,nativeEquipment:(record.equipment??[]).map((row:number[],slot:number)=>({slot,itemId:row[0],byte1:row[1]??255,byte2:row[2]??255}))}));
  }
  private createNativeScenarioUnits(mapId:number):Unit[]{
    this.ensureNativeTerrain(mapId);
    const source=scenarioUnits[mapId] as {units?:Array<any>}|undefined;
    return (source?.units??[]).map(record=>({id:`s${String(mapId).padStart(2,'0')}-slot-${record.slot}`,name:`角色 ${record.unitId}`,art:record.art,side:record.slot<35?'player':'enemy',x:record.position[0],y:record.position[1],hp:record.hp,maxHp:record.maxHp,mp:record.mp,move:6,acted:false,direction:record.facing,actorFlags:record.actorFlags,statusFlags:0,nativeClassId:record.classId,nativeEquipment:(record.equipment??[]).map((row:number[],slot:number)=>({slot,itemId:row[0],byte1:row[1]??255,byte2:row[2]??255}))}));
  }
  private createS00Units():Unit[]{
    this.map.terrain=s00Terrain.terrain as number[];
    return (s00Units.units as Array<any>).map((record:any)=>{
      const native=record.controlledNativeExpansion ?? {};
      const placement=record.nativePlacement ?? {};
      const group=record.nativeSlotGroup as string;
      const unitHex=String(native.unitHex??'');
      const readLe32=(hex:string)=>parseInt(hex.match(/../g)!.reverse().join(''),16)>>>0;
      const nativeWord0=unitHex.length>=8?readLe32(unitHex.slice(0,8)):record.unitId16;
      const portraitCharacterId=nativeWord0&0xfff;
      const portraitStoredIndex=unitHex.length>=16?readLe32(unitHex.slice(8,16))|0:record.unitId16;
      // S_00 opcode75 places Cao Cao in the primary slot at (7,0); auxiliary
      // type-1 records remain deferred until their verified appearance event.
      const eventPosition:Record<number,[number,number]>={32:[14,1],3:[13,2],33:[13,1]};
      const isInitialAlly=record.unitId16 in eventPosition;
      const hidden=placement.type===1 && group!=='primary-slot-group' && !isInitialAlly;
      const initialPosition=eventPosition[record.unitId16];
      return {id:`s00-slot-${record.nativeBattleSlot}`,name:record.characterName??`角色 ${record.unitId16}`,
        art:native.art??record.animationLink?.index??0,side:group==='enemy-slot-group'?'enemy':'player',
        x:hidden?0:(initialPosition?.[0]??(placement.position?.[0]===255?record.coordinateBytes[0]:(placement.position?.[0]??record.coordinateBytes[0]))),y:hidden?0:(initialPosition?.[1]??(placement.position?.[1]===255?record.coordinateBytes[1]:(placement.position?.[1]??record.coordinateBytes[1]))),
        hp:native.hp??1,maxHp:native.maxHp??1,mp:native.mp??0,move:6,acted:false,
        direction:native.facing??2,actorFlags:native.actorFlags??0,statusFlags:0,injuredPose:false,
        nativeMovementCosts:[],nativeEquipment:(native.equipment??[]).map((row:number[],index:number)=>({slot:index,itemId:row[0],byte1:row[1]??255,byte2:row[2]??255})),nativePortraitCharacterId:portraitCharacterId,nativePortraitStoredIndex:portraitStoredIndex,nativeHidden:hidden,nativeClassId:native.classId};
    });
  }
  private async playS00OpeningEvent(){
    if(this.openingEventActive)return;
    this.openingEventActive=true;this.animating=true;
    const tracedPaths=(s00LiuTrace.observations as Array<{kind:string;actor?:number;steps?:Array<{from:number[];direction:number}>}>).filter(row=>row.kind==='native-path'&&row.steps);
    try{
      await this.playS00Dialogue();
      const actorSlotMap:Record<number,number>={32:15,3:16,33:17};
      for(const pathRow of tracedPaths){
        const id=pathRow.actor;
        if(id===undefined)continue;
        const unit=this.units.find(row=>Number(row.id.replace('s00-slot-',''))===actorSlotMap[id]);
        if(!unit)continue;
        const path=pathRow.steps??[];
        for(const step of path){
          const direction=step.direction;
          if(step.from?.length===2&&(unit.x!==step.from[0]||unit.y!==step.from[1]))continue;
          const [dx,dy]=directions[direction],startX=unit.x,startY=unit.y;
          unit.direction=2;unit.mirror=direction===1;
          const visual=this.unitSprites.find(entry=>entry.unit===unit);
          for(const sample of movementFrames(unit.nativeClassId??0,direction)){
            visual?.sprite.setPosition(this.ox+startX*48+24+dx*sample.progress,this.oy+startY*48+24+dy*sample.progress).setFrame(sample.frame);
            await new Promise<void>(resolve=>this.time.delayedCall(35,resolve));
          }
          unit.x+=dx;unit.y+=dy;this.refreshUnitSprite(unit);this.refreshMinimap();
        }
      }
    }finally{this.animating=false;this.openingEventActive=false;this.showActionNotice('S_00 登场事件完成');this.time.delayedCall(900,()=>this.actionNotice?.setVisible(false));}
  }
  private async playS00Dialogue(){
    const lines=(s00LiuTrace.observations as Array<{kind:string;speaker?:number;text?:string}>).filter(row=>row.kind==='dialogue'&&row.text);
    for(const line of lines){
      await new Promise<void>(resolve=>{
        const width=520,height=132;
        const group=this.add.container((this.scale.width-width)/2,this.scale.height-height-18).setScrollFactor(0).setDepth(700);
        group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
        const unit=this.units.find(row=>Number(row.id.replace('s00-slot-',''))===({32:15,3:16,33:17} as Record<number,number>)[Number(line.speaker)]);
        group.add(this.add.text(12,8,unit?.name??`角色 ${line.speaker}`,{fontFamily:'SimSun',fontSize:'15px',color:'#000000'}));
        if(unit){const portrait=this.createNativePortrait(unit,unit.portraitFlags??this.commonState.portraitFlags,unit.portraitPhase??this.commonState.portraitPhase);if(portrait)group.add(this.add.image(12,28,portrait).setOrigin(0).setDisplaySize(96,120));}
        group.add(this.add.text(120,38,String(line.text),{fontFamily:'SimSun',fontSize:'14px',color:'#000000',wordWrap:{width:width-134},lineSpacing:4}));
        const close=()=>{group.destroy();this.modal=undefined;resolve();};
        nativeButton(this,group,[width-104,height-32,86,24],'确定',1,close);
        group.setData('nativeHitRegions',[{x:width-104,y:height-32,width:86,height:24,command:close}]);this.modal=group;
      });
    }
  }
  private createNativePortrait(unit:Unit,flags:number,phase:number):string|undefined{
    const characterId=unit.nativePortraitCharacterId,storedIndex=unit.nativePortraitStoredIndex;
    if(characterId===undefined||storedIndex===undefined)return undefined;
    const index=portraitIndex(characterId,storedIndex,flags,phase);
    const face=(portraitBank.faces as Array<{index:number;pixelsBase64:string}>).find(row=>row.index===index);
    const palette=(portraitBank.palettes as Array<{nativeBgrBase64:string}>)[0];
    if(!face||!palette)return undefined;
    const bytes=(input:string)=>Uint8Array.from(atob(input),char=>char.charCodeAt(0));
    const rgba=portraitRgba(bytes(face.pixelsBase64),bytes(palette.nativeBgrBase64));
    const key=`native-portrait-${index}`;
    if(!this.textures.exists(key)){
      const canvas=this.textures.createCanvas(key,portraitBank.width,portraitBank.height);
      if(!canvas)return undefined;
      canvas.context.putImageData(new ImageData(rgba as unknown as Uint8ClampedArray<ArrayBuffer>,portraitBank.width,portraitBank.height),0,0);canvas.refresh();
    }
    return key;
  }
  /** Event-runner entry points mirroring native EEX common-state writes. */
  applyNativeEexPortraitFlags(tag:number,value:number):number{
    const result=applyEexOpcode32(this.commonState,tag,value);this.commonState=result.state;return result.status;
  }
  applyNativeEexChapterPhase(tag:number,value:number):number{
    const result=applyEexOpcode103(this.commonState,tag,value);this.commonState=result.state;return result.status;
  }
  applyNativeEexDirectPhase(modeTag:number,mode:number,valueTag:number,value:number):number{
    const result=applyEexOpcode58(this.commonState,modeTag,mode,valueTag,value);this.commonState=result.state;return result.status;
  }
  private fixInterfaceToViewport(){
    for(const object of [...this.children.list]){
      if(object instanceof Phaser.GameObjects.Image && object.texture.key.startsWith('cmd-')){
        object.destroy();
        continue;
      }
      if(object instanceof Phaser.GameObjects.Image || object instanceof Phaser.GameObjects.Text || object instanceof Phaser.GameObjects.Rectangle){
        if(object.y<this.oy){
          object.setScrollFactor(0).setDepth(100);
        if(object instanceof Phaser.GameObjects.Text && object.x===690)this.turnText=object;
          if(object instanceof Phaser.GameObjects.Text)object.setY(34).setFontSize(14);
          if(object instanceof Phaser.GameObjects.Text && object.x===38 && this.mapId===slot08.mapId)object.setText(slot08.title);
        }
      }
    }
    let x=2;
    const tooltip=this.add.text(0,31,'',{
      fontSize:'14px',color:'#111111',backgroundColor:'#ffffdc',padding:{x:5,y:3}
    }).setScrollFactor(0).setDepth(200).setVisible(false);
    for(const button of toolbar.buttons){
      if(button.separator){x+=8;continue;}
      this.add.rectangle(x,0,24,24,0xc0c0c0).setOrigin(0).setScrollFactor(0).setDepth(101);
      const icon=this.add.image(x,0,`toolbar-${button.commandId}`).setOrigin(0).setDisplaySize(24,24).setScrollFactor(0).setDepth(102).setInteractive();
      const tooltipX=x;
      icon.on('pointerover',()=>tooltip.setPosition(tooltipX,31).setText(button.label ?? '').setVisible(Boolean(button.label)));
      icon.on('pointerout',()=>tooltip.setVisible(false));
      if(button.commandId===101)icon.on('pointerdown',()=>saveUnits(this.units));
      if(button.commandId===102)icon.on('pointerdown',()=>this.restoreNativeSave());
      if(button.commandId===106)icon.on('pointerdown',()=>this.showConditions());
      if(button.commandId===40150)icon.on('pointerdown',()=>this.terrainText?.setVisible(!this.terrainText.visible));
      if(button.commandId===40147)icon.on('pointerdown',()=>this.showInventory());
      if(button.commandId===105)icon.on('pointerdown',()=>this.showRoster());
      if(button.commandId===108)icon.on('pointerdown',()=>this.minimap?.setVisible(!this.minimap.visible));
      if(button.commandId===104)icon.on('pointerdown',()=>this.openModal('结束游戏','确认返回主菜单？',['返回','取消']));
      if(button.commandId===107)icon.on('pointerdown',()=>this.openModal('环境设定','音乐\n音效\n战斗动画\n文字速度',['确定']));
      if(button.commandId===109)icon.on('pointerdown',()=>this.openEndTurnConfirm());
      if(button.commandId===40151)icon.on('pointerdown',()=>this.showItemEncyclopedia());
      x+=24;
    }
    if(this.mapId===31||this.mapId===0){
      const frame=this.add.rectangle(-2,-2,124,196,0xc0c0c0).setOrigin(0);
      const terrain=this.textures.exists('minimap-31')&&this.mapId===31?this.add.image(0,0,'minimap-31').setOrigin(0):this.add.rectangle(0,0,124,196,0x294b3c).setOrigin(0);
      const actors=this.add.graphics();
      for(const rectangle of this.mapId===31?minimapUnits.rectangles:[]){
        const [red,green,blue]=rectangle.rgb;
        actors.fillStyle((red<<16)|(green<<8)|blue);
        actors.fillRect(rectangle.left,rectangle.top,rectangle.right-rectangle.left+1,rectangle.bottom-rectangle.top+1);
      }
      // The original small map is a sibling panel outside the main battle
      // viewport, not an overlay inside the 960px battlefield.
      const dynamicActors=this.add.graphics();
      const viewport=this.add.rectangle(0,0,124,72).setOrigin(0).setStrokeStyle(1,0xffff80,0.9).setFillStyle(0xffff80,0.08);
      this.minimapActors=dynamicActors;this.minimapViewport=viewport;
      this.minimap=this.add.container(980,64,[frame,terrain,actors,dynamicActors,viewport]).setScrollFactor(0).setDepth(90);
      this.minimap.setSize(124,196).setInteractive();
      this.minimap.on('pointerdown',(pointer:Phaser.Input.Pointer)=>{
        const localY=Phaser.Math.Clamp(pointer.y-this.minimap!.y,0,196);
        const worldY=(localY/196)*this.map.height*this.size;
        const maxScroll=Math.max(0,this.map.height*this.size+this.oy-this.cameras.main.height);
        this.cameras.main.scrollY=Phaser.Math.Clamp(worldY-this.cameras.main.height/2,0,maxScroll);
      });
      this.refreshMinimap();
    }
  }
  private refreshMinimap(){
    if(!this.minimapActors||!this.minimapViewport)return;
    const scaleX=124/this.map.width,scaleY=196/this.map.height;
    this.minimapActors.clear();
    for(const unit of this.units){
      if(unit.hp<=0||unit.nativeHidden)continue;
      const color=unit.side==='player'?(unit.acted?0x6b3030:0xc00000):(unit.acted?0x203060:0x001070);
      this.minimapActors.fillStyle(color,1);
      this.minimapActors.fillRect(unit.x*scaleX,unit.y*scaleY,Math.max(3,scaleX*.7),Math.max(3,scaleY*.7));
    }
    const visibleHeight=this.cameras.main.height/(this.map.height*this.size)*196;
    this.minimapViewport.setSize(124,visibleHeight).setY(this.cameras.main.scrollY/(this.map.height*this.size)*196);
  }
  private drawGrid(){const lines=this.add.graphics().setDepth(2); lines.lineStyle(1,0x9bb6c4,0.22); for(let x=0;x<=this.map.width;x++){lines.moveTo(this.ox+x*this.size,this.oy);lines.lineTo(this.ox+x*this.size,this.oy+this.map.height*this.size);} for(let y=0;y<=this.map.height;y++){lines.moveTo(this.ox,this.oy+y*this.size);lines.lineTo(this.ox+this.map.width*this.size,this.oy+y*this.size);} lines.strokePath(); for(let y=0;y<this.map.height;y++)for(let x=0;x<this.map.width;x++){const terrain=this.map.terrain[y*this.map.width+x];const r=this.add.rectangle(this.ox+x*this.size,this.oy+y*this.size,this.size-2,this.size-2,0x36566b,0).setOrigin(0).setDepth(3).setInteractive();r.on('pointerover',()=>this.showTerrain(x,y,terrain));r.on('pointerout',()=>this.terrainText?.setVisible(false));this.cells.set(`${x},${y}`,r);}}
  private showTerrain(x:number,y:number,terrain:number){if(!this.terrainText?.visible)return;const source=this.selected&&this.movementActors().find(actor=>actor.id===this.selected?.id);const cost=source?terrainCost(source.classId,source.equipmentSlots,terrain,itemCategories,terrainMovement):undefined;this.terrainText.setPosition(this.ox+x*this.size+this.size+4,this.oy+y*this.size).setText(`地形 ${terrain}\n坐标 ${x},${y}\n移动代价 ${cost===undefined?'未选单位':cost===255?'不可通行':cost}`).setVisible(true);}
  update(_time: number, delta: number){
    this.refreshMinimap();
    if(this.actionMode==='item'&&this.selected)this.showStrategyReach(0xc29b4b);
    if(!this.bgmStarted){
      this.bgmStarted=true;
      const key=`scenario-bgm-${this.mapId}`;
      if(this.cache.audio.exists(key))this.sound.add(key,{loop:true}).play();
    }
    this.phaseElapsed += delta;
    if(this.phaseElapsed < slot08.animationStepMs) return;
    this.phaseElapsed %= slot08.animationStepMs;
    this.phase = (this.phase + 1) & 7;
    for(const {unit,sprite} of this.unitSprites){
      if(this.presentationUnits.has(unit)||(this.animating&&unit===this.selected))continue;
      const frame=this.unitIdleFrame(unit);
      sprite.setFrame(frame).setFlipX(Boolean(unit.mirror) && [4,5,8].includes(frame));
    }
  }
  private drawUnits(){
    if(this.mapId>0&&this.mapId!==31&&this.units.length===0){
      this.units=this.mapId===1?this.createS01Units():this.createNativeScenarioUnits(this.mapId);
      const records=(scenarioUnits[this.mapId] as {units:Array<{slot:number;type:number}>}).units;
      for(const unit of this.units){
        const slot=Number(unit.id.match(/-slot-(\d+)$/)?.[1]);
        unit.nativeHidden=records.find(row=>row.slot===slot)?.type===1;
      }
    }
    for(const {sprite,hpBack,hpFill} of this.unitSprites){sprite.destroy();hpBack.destroy();hpFill.destroy();}
    this.unitSprites=[];
    this.units.forEach(unit=>{
      const key=`mov-${String(unit.art ?? 0).padStart(3,'0')}`;
      const frame=this.unitIdleFrame(unit);
      // Native mirror modifies only tiles 4/5 and 8, not the whole sheet.
      const sx=this.ox+unit.x*48+24,sy=this.oy+unit.y*48+24;
      const visible=unit.hp>0&&!unit.nativeHidden;
      const sprite=this.add.sprite(sx,sy,key,frame).setDepth(4).setVisible(visible);
      const hpBack=this.add.rectangle(sx,sy-25,34,4,0x35151a).setDepth(6).setVisible(visible);
      const hpFill=this.add.rectangle(sx-17,sy-25,34,4,0x35c96b).setOrigin(0,.5).setDepth(7).setVisible(visible);
      this.applyUnitAppearance(unit,sprite);
      sprite.setFlipX(Boolean(unit.mirror) && [4,5,8].includes(frame));
      sprite.setData('unit',unit).setInteractive();
      this.unitSprites.push({unit,sprite,hpBack,hpFill});
    });
  }
  /**
   * Native actor rendering uses actor flags 0x06 for the completed-action
   * standing bank. `acted` is the serialized UI turn state, so apply the
   * native flag at the rendering boundary as well. This keeps restored saves
   * and actions taken in the browser visually identical.
   */
  private unitIdleFrame(unit: Unit): number {
    const actorFlags=(unit.actorFlags ?? 0) | (unit.acted ? 0x06 : 0);
    return idleFrame(unit.direction ?? 2,actorFlags,unit.statusFlags ?? 0,this.phase,unit.injuredPose === true);
  }
  private refreshUnitSprite(unit: Unit){
    const visual=this.unitSprites.find(entry=>entry.unit===unit);
    if(!visual)return;
    const x=this.ox+unit.x*this.size+24,y=this.oy+unit.y*this.size+24;
    visual.sprite.setPosition(x,y);
    visual.hpBack.setPosition(x,y-25);
    visual.hpFill.setPosition(x-17,y-25);
    const frame=this.unitIdleFrame(unit);
    visual.sprite.setFrame(frame).setFlipX(Boolean(unit.mirror)&&[4,5,8].includes(frame));
    const ratio=unit.maxHp>0?Phaser.Math.Clamp(unit.hp/unit.maxHp,0,1):0;
    visual.hpFill.setScale(ratio,1).setFillStyle(ratio>.5?0x35c96b:ratio>.25?0xe5bb45:0xd64545).setVisible(unit.hp>0);
    visual.hpBack.setVisible(unit.hp>0);
    this.applyUnitAppearance(unit,visual.sprite);
  }
  private applyUnitAppearance(unit: Unit,sprite: Phaser.GameObjects.Sprite){
    const flags=(unit.actorFlags??0)|(unit.acted?6:0);
    const profile=(actedMovementArt.scenes as Record<string,number>)[String(this.mapId)];
    const key=nativeActorIsDarkened(flags,unit.hp)?`mov-acted-${profile}-${unit.art??0}`:`mov-${String(unit.art??0).padStart(3,'0')}`;
    if(sprite.texture.key!==key&&this.textures.exists(key))sprite.setTexture(key,sprite.frame.name);
    sprite.clearTint();
  }
  private select(unit: Unit){
    if(this.modal||this.battleEnded)return;
    if(this.animating||this.moving)return;
    this.clearReach();
    this.selected=unit;
    this.playNativeSound(2);
    this.selectedStart={x:unit.x,y:unit.y,direction:unit.direction,mirror:unit.mirror,actorFlags:unit.actorFlags};
    this.moving=false;
    this.updateStatus(unit);
    this.cells.get(`${unit.x},${unit.y}`)?.setStrokeStyle(2,0xffffff,0.9);
    const actors=this.movementActors(),source=actors.find(actor=>actor.id===unit.id);
    if(source && unit.side==='player'&&!unit.acted){
      movementCosts(this.map.width,this.map.height,this.map.terrain,actors,source,itemCategories,terrainMovement,classMovement).forEach((cost,index)=>{
        if(cost!==255)this.cells.get(`${index%this.map.width},${Math.floor(index/this.map.width)}`)?.setFillStyle(0x3c8d76,0.35);
      });
    }
  }
  private updateStatus(unit?:Unit){
    if(!this.statusText)return;
    if(!unit){this.statusText.setText('选择单位查看原版存档信息');return;}
    const source=slot08.actors.find(actor=>actor.id===unit.id) as (typeof slot08.actors)[number] | undefined;
    if(!source){this.statusText.setText(`${unit.name}\n坐标 ${unit.x},${unit.y}`);return;}
    const equipment=(source.equipmentSlots ?? []).map(item=>item.name ?? `道具 ${item.itemId}`).join('\n');
    const attributes=combatAttributes.actors.find(actor=>actor.id===unit.id);
    this.statusText.setText([
      source.name,
      `坐标 ${unit.x},${unit.y}`,
      `HP ${unit.hp}/${unit.maxHp}`,
      `MP ${unit.mp??source.mp}/${source.maxMp}`,
      `攻击力 ${attributes?.attack ?? '-'}  防御力 ${attributes?.defense ?? '-'}`,
      `兵种 ${source.classId}  移动力 ${source.move}`,
      `装备:\n${equipment || '无'}`,
      unit.acted?'已行动':'可行动'
    ].join('\n'));
  }
  private restoreNativeSave(){
    if(this.animating)return;
    if(this.mapId===0){
      this.units=this.createS00Units();this.battleEnded=false;this.currentTurn=1;this.selected=undefined;this.selectedStart=undefined;this.moving=false;this.clearReach();this.closeContextMenu();this.actionMode=undefined;this.drawUnits();this.updateStatus();this.time.delayedCall(350,()=>void this.playS00OpeningEvent());return;
    }
    this.units=loadUnits(slot08.actors.map((unit)=>({...unit,side:unit.side as Unit['side'],acted:false})));
    this.battleRng=new GameRng(loadRngState());setRngState(this.battleRng.state);this.closeContextMenu();this.actionMode=undefined;
    this.selected=undefined;this.selectedStart=undefined;this.moving=false;this.clearReach();this.drawUnits();this.updateStatus();
  }
  private showConditions(){
    if(!this.conditionText)return;
    const visible=!this.conditionText.visible;
    this.conditionText.setVisible(visible);
    if(visible)this.conditionText.setText(`胜利条件\n${this.mapId===0?'颍川黄巾战':slot08.title}\n当前回合 ${this.currentTurn} / ${slot08.turnLimit}\n金钱 ${this.gold}`);
  }
  private showInventory(){
    if(!this.inventoryText)return;
    const visible=!this.inventoryText.visible;this.inventoryText.setVisible(visible);
    if(!visible)return;
    const rows=this.units.filter(unit=>unit.nativeEquipment?.some(item=>item.itemId!==255)).map(unit=>{
      const items=(unit.nativeEquipment??[]).filter(item=>item.itemId!==255).map(item=>{const catalog=(itemCategories as Array<{id:number;name?:string}>).find(row=>row.id===item.itemId);return catalog?.name??`道具 ${item.itemId}`;}).join('、');
      return `${unit.name}: ${items}`;
    });
    this.inventoryText.setText(['持有道具一览',...rows].join('\n'));
  }
  private showRoster(){
    this.modal?.destroy();this.closeContextMenu();
    const width=792,height=379,group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(500);
    group.setData('dialogResource',186);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(10,7,'部队情报一览',{fontFamily:'SimSun',fontSize:'15px',color:'#000000'}));
    const table=this.add.container(11,28);group.add(table);
    let side:Unit['side']='player',first=0,sortColumn=0,descending=false;
    const widths=[92,94,40,44,52,52,74,74,74,74,68];
    const value=(unit:Unit,column:number):string|number=>{
      const source=slot08.actors.find(row=>row.id===unit.id) ?? {nativeLevel:1,maxMp:unit.mp??0,mp:unit.mp??0};
      const stats=combatRuntime.actors.find(row=>`unit-${row.slot}`===unit.id);
      const native=rosterFields.find(row=>`unit-${row.slot}`===unit.id);
      return [unit.name,native?.className??'',source.nativeLevel,native?.experience===255?'MAX':native?.experience??'',`${unit.hp}/${unit.maxHp}`,`${unit.mp??source.mp}/${source.maxMp}`,stats?.attack??'',native?.spirit??'',stats?.defense??'',stats?.agility??'',stats?.luck??''][column];
    };
    const render=()=>{
      table.removeAll(true);let x=0;
      for(const column of rosterColumns.columns){
        const cx=x,w=widths[column.id];
        nativeButton(this,table,[cx,0,w,24],column.label,column.id,()=>{descending=sortColumn===column.id?!descending:column.id!==0;sortColumn=column.id;first=0;render();});x+=w;
      }
      const rows=this.units.filter(unit=>unit.side===side).sort((a,b)=>{
        if(sortColumn===0)return (Number(a.id.replace('s00-slot-',''))-Number(b.id.replace('s00-slot-','')))*(descending?-1:1);
        const av=value(a,sortColumn),bv=value(b,sortColumn);
        return (typeof av==='number'&&typeof bv==='number'?av-bv:String(av).localeCompare(String(bv)))*(descending?-1:1);
      });
      rows.slice(first,first+12).forEach((unit,index)=>{let cx=0;for(let column=0;column<11;column++){
        table.add(this.add.rectangle(cx,24+index*21,widths[column],21,index%2?0xf0f0f0:0xffffff).setOrigin(0));
        table.add(this.add.text(cx+4,27+index*21,String(value(unit,column)),{fontFamily:'SimSun',fontSize:'12px',color:'#000000'}));cx+=widths[column];
      }});
    };
    render();
    const wheel=(_p:Phaser.Input.Pointer,_o:unknown,_dx:number,dy:number)=>{if(this.modal!==group)return;first=Phaser.Math.Clamp(first+Math.sign(dy),0,Math.max(0,this.units.filter(unit=>unit.side===side).length-12));render();};
    this.input.on('wheel',wheel);group.once('destroy',()=>this.input.off('wheel',wheel));
    const switchSide=(next:Unit['side'])=>{side=next;first=0;render();};
    nativeButton(this,group,[35,336,70,24],'我军',1033,()=>switchSide('player'));
    nativeButton(this,group,[115,336,60,24],'敌军',1043,()=>switchSide('enemy'));
    const close=()=>{group.destroy();this.modal=undefined;};
    nativeButton(this,group,[685,328,90,24],'确定',2,close);
    group.setData('nativeHitRegions',[{x:685,y:328,width:90,height:24,command:close},{x:35,y:336,width:70,height:24,command:()=>switchSide('player')},{x:115,y:336,width:60,height:24,command:()=>switchSide('enemy')}]);
    this.modal=group;return;
  }
  private openContextMenu(unit:Unit,x:number,y:number){
    if(this.battleEnded)return;
    if(this.animating||unit.side!=='player'){
      if(unit && !this.animating)this.openUnitInfoModal(unit);
      return;
    }
    if(unit.acted){this.openUnitInfoModal(unit);return;}
    if(this.selected!==unit)this.select(unit);
    if(this.selected!==unit)return;
    this.contextMenu?.destroy();
    const template=nativeUi.dialogs.find(dialog=>dialog.resourceId===279)!;
    const [width,height]=template.nativeWindowPixels!,[clientWidth,clientHeight]=template.nativeClientPixels!;
    const borderX=(width-clientWidth)/2,borderY=(height-clientHeight)/2;
    const panel=this.add.container(Phaser.Math.Clamp(x,0,this.scale.width-width),Phaser.Math.Clamp(y,0,this.scale.height-height)).setScrollFactor(0).setDepth(300);
    panel.setSize(width,height).setData('dialogResource',279);
    panel.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    const entries:Record<number,()=>void>={1287:()=>this.beginAttackSelection(),1288:()=>this.beginUtilitySelection('strategy'),1289:()=>this.beginUtilitySelection('item'),1291:()=>this.finishAction(),2:()=>{this.actionMode=undefined;this.cancelMovement();this.closeContextMenu();}};
    const nativeHitRegions:Array<{id:number;x:number;y:number;width:number;height:number;command:()=>void}>=[];
    for(const control of [...template.controls].sort((a,b)=>a.rectDlu[1]-b.rectDlu[1])){
      const rect=(control as {nativeRectPixels?:number[]}).nativeRectPixels;
      const handler=entries[control.id];
      if(!rect||!handler)continue;
      const [cx,cy,w,h]=rect;
      nativeHitRegions.push({id:control.id,x:cx+borderX,y:cy+borderY,width:w,height:h,command:handler});
      nativeButton(this,panel,[cx+borderX,cy+borderY,w,h],String(control.text),control.id,handler);
      const iconIndex={1287:0,1288:1,1289:2,1291:3}[control.id as 1287|1288|1289|1291];
      if(iconIndex!==undefined)panel.add(this.add.image(cx+borderX+8,cy+borderY+h/2,`cmd-${iconIndex}`).setDisplaySize(16,16));
    }
    panel.setData('nativeHitRegions',nativeHitRegions);
    this.contextMenu=panel;
  }
  private openUnitInfoModal(unit:Unit){
    this.openNativeUnitInfo(unit);return;
    const source=slot08.actors.find(actor=>actor.id===unit.id);
    this.openModal('单位信息',`${source?.name??unit.name}\nHP ${unit.hp}/${unit.maxHp}\n${unit.acted?'已行动':'可行动'}`,['确定']);
  }
  private openEndTurnConfirm(){
    if(this.turnTransitioning||this.animating)return;
    this.modal?.destroy();
    const w=300,h=120,group=this.add.container((this.scale.width-w)/2,(this.scale.height-h)/2).setScrollFactor(0).setDepth(500);
    group.add(this.add.rectangle(0,0,w,h,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(10,8,'结束回合',{fontSize:'16px',color:'#000000'}));
    group.add(this.add.text(14,38,'是否结束当前回合？',{fontSize:'14px',color:'#000000'}));
    nativeButton(this,group,[120,82,70,26],'是',1,()=>{group.destroy();this.modal=undefined;this.finishTurn();});
    nativeButton(this,group,[205,82,70,26],'否',2,()=>{group.destroy();this.modal=undefined;});
    group.setData('nativeHitRegions',[
      {x:120,y:82,width:70,height:26,command:()=>{group.destroy();this.modal=undefined;this.finishTurn();}},
      {x:205,y:82,width:70,height:26,command:()=>{group.destroy();this.modal=undefined;}}
    ]);
    this.modal=group;return;
    this.openModal('END TURN','Confirm end current turn?',['OK','Cancel']);return;
    this.openModal('纭','缁撴潫鍥炲悎锛?',['纭畾','鍙栨秷']);
  }
  private openNativeUnitInfo(unit:Unit){
    this.modal?.destroy();this.closeContextMenu();
    const source=slot08.actors.find(row=>row.id===unit.id) ?? {
      id:unit.id,name:unit.name,classId:unit.nativeClassId??0,nativeLevel:1,
      hp:unit.hp,maxHp:unit.maxHp,mp:unit.mp??0,maxMp:unit.mp??0,
      equipmentSlots:[],move:unit.move,unitId:Number(unit.id.replace('s00-slot-',''))
    };
    const extra=rosterFields.find(row=>`unit-${row.slot}`===unit.id);
    const stats=this.combatActor(unit);
    const template=nativeUi.dialogs.find(row=>row.resourceId===166)!;
    const [width,height]=template.nativeWindowPixels!;
    const group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(500).setData('dialogResource',166);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    const text=(x:number,y:number,value:string,size=13)=>group.add(this.add.text(x,y,value,{fontFamily:'SimSun',fontSize:`${size}px`,color:'#000000'}));
    text(8,6,'武将情报',15);
    for(const [id,value] of [[1002,unit.name],[1016,extra?.className??''],[1017,String(source.nativeLevel)],[1381,extra?.experience===255?'MAX':String(extra?.experience??'')],[1376,`${unit.hp}/${unit.maxHp}`],[1380,`${unit.mp??source.mp}/${source.maxMp}`]] as const){
      const control=template.controls.find(row=>row.id===id)! as {nativeRectPixels:number[]};
      text(control.nativeRectPixels[0]+3,control.nativeRectPixels[1]+24,value);
    }
    text(19,191,'Lv');text(65,191,'Exp');text(15,245,'HP');text(15,270,'MP');
    const attributes=[['攻击力',stats?.attack],['精神力',extra?.spirit],['防御力',stats?.defense],['爆发力',stats?.agility],['士气',stats?.luck],['移动力',unit.move]] as const;
    text(180,32,'能力');attributes.forEach(([label,value],index)=>{const y=58+index*45;text(185,y,label);text(215,y+18,String(value??''));});
    const close=()=>{group.destroy();this.modal=undefined;};
    const cycle=(step:number)=>{const index=this.units.indexOf(unit);this.openNativeUnitInfo(this.units[(index+step+this.units.length)%this.units.length]);};
    const regions:Array<{x:number;y:number;width:number;height:number;command:()=>void}>=[];
    for(const [id,command] of [[2,close],[1027,()=>cycle(-1)],[1028,()=>cycle(1)]] as const){
      const control=template.controls.find(row=>row.id===id)! as {nativeRectPixels:number[];text:string};
      const [x,y,w,h]=control.nativeRectPixels;
      nativeButton(this,group,[x+3,y+24,w,h],control.text,id,command);regions.push({x:x+3,y:y+24,width:w,height:h,command});
    }
    group.setData('nativeHitRegions',regions);this.modal=group;
  }
  private closeContextMenu(){this.contextMenu?.destroy();this.contextMenu=undefined;}
  private closeUtilityMenu(){this.utilityMenu?.destroy();this.utilityMenu=undefined;}
  private openModal(title:string,body:string,buttons:string[]){
    this.modal?.destroy();
    const template=title==='环境设定'?nativeUi.dialogs.find(dialog=>dialog.resourceName==='KANKYOU'):title==='确认'?nativeUi.dialogs.find(dialog=>dialog.resourceId===346):undefined;
    const width=template?.nativeWindowPixels?.[0]??260,height=template?.nativeWindowPixels?.[1]??100;
    const group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(500);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(8,5,title,{fontFamily:'SimSun, "宋体", serif',fontSize:'15px',color:'#000000'}));
    group.add(this.add.text(12,32,body,{fontFamily:'SimSun, "宋体", serif',fontSize:'13px',color:'#000000',wordWrap:{width:width-24},lineSpacing:3}));
    const rects=template?.controls.filter(control=>control.text==='确定'||control.text==='取消'||control.text==='是'||control.text==='否').map(control=>(control as {nativeRectPixels?:number[]}).nativeRectPixels).filter(Boolean)??[];
    buttons.forEach((label,index)=>{const rect=rects[index]??[width-116+index*57,height-36,50,26];nativeButton(this,group,rect,label,index+1,()=>{if((title==='确认'||title==='纭')&&index===0){group.destroy();this.modal=undefined;this.finishTurn();}else if(label==='返回'||label==='是')this.scene.restart({mapId:this.mapId});else{group.destroy();this.modal=undefined;}});});
    this.modal=group;
  }
  private finishTurn(){
    if(this.animating||this.turnTransitioning)return;
    this.turnTransitioning=true;this.showActionNotice('enemy turn');
    this.time.delayedCall(900,()=>{ this.runEnemyTurn().then(()=>{
      if(this.units.filter(unit=>unit.side==='player'&&unit.hp>0).length===0){this.openS00Defeat();this.turnTransitioning=false;this.input.enabled=true;return;}
      for(const unit of this.units){if(unit.hp<=0)continue;unit.acted=false;unit.actorFlags=(unit.actorFlags??0)&~0x06;this.refreshUnitSprite(unit);}
      this.currentTurn=Math.min(this.currentTurn+1,slot08.turnLimit);
      this.turnText?.setText(`回合数   ${this.currentTurn} / ${slot08.turnLimit}`);
      this.turnTransitioning=false;this.showActionNotice('player turn');this.updateStatus(this.selected);
    });});
    this.clearReach();this.closeContextMenu();this.updateStatus(this.selected);this.showActionNotice('回合结束');
  }
  private async runEnemyTurn(){
    for(const enemy of this.units.filter(unit=>unit.side==='enemy'&&unit.hp>0&&!unit.nativeHidden)){
      const chooseTarget=(afterMovement=false)=>{
        const candidates=this.units.filter(unit=>unit.side==='player'&&unit.hp>0&&!unit.nativeHidden&&unit.x>=0&&unit.y>=0&&unit.x<this.map.width&&unit.y<this.map.height);
        const attacker=this.combatActor(enemy);
        const slot=Number(enemy.id.match(/(?:unit-|slot-)(\d+)$/)?.[1]);
        const attackMode=(scenarioCombat as Record<string,Array<{slot:number;attackMode:number}>>)[String(this.mapId)]?.find(row=>row.slot===slot)?.attackMode;
          const score=(target:Unit)=>{
            const defender=this.combatActor(target);
            const targetSlot=Number(target.id.match(/(?:unit-|slot-)(\d+)$/)?.[1]);
            const identity=target.id.startsWith('unit-')
              ?slot08.actors.find(row=>row.id===target.id)?.unitId
              :(scenarioCombat as Record<string,Array<{slot:number;unitId:number}>>)[String(this.mapId)]?.find(row=>row.slot===targetSlot)?.unitId;
            return nativeAiOrdinaryAttackScore({
              currentHp:target.hp,maxHp:target.maxHp,predictedDamage:ordinaryDamage(attacker,defender,itemCategories),
              attackerMode:attackMode??0,targetFlags:target.statusFlags??0,targetIdentity:identity??174,targetSlot,leaderMatch:false,
              covered:nativeAiClassFiltered(attacker.classId),sameSide:false,
              candidateRisk:inAttackRange(defender,attacker,attackRange(defender,itemCategories,attackClasses),targetShapes.shapes)});
          };
        const range=attackRange(attacker,itemCategories,attackClasses);
        if(afterMovement&&range!==255&&((range&127)===0||(range&127)===1)){
          const nativeSlot=(unit:Unit)=>Number(unit.id.match(/(?:unit-|slot-)(\d+)$/)?.[1]);
          const occupants=this.units.filter(unit=>unit.hp>0&&!unit.nativeHidden).map(unit=>({slot:nativeSlot(unit),groupSlot:nativeSlot(unit),hp:unit.hp,x:unit.x,y:unit.y}));
          const ordered=collectNativeAdjacentCandidates(enemy,range,this.map.width,this.map.height,slot,occupants);
          const bySlot=new Map(candidates.map(unit=>[nativeSlot(unit),unit]));
          const result=selectNativeAiCandidate(ordered,targetSlot=>{
            const unit=bySlot.get(targetSlot);return unit?score(unit):0;
          });
          return bySlot.get(result.target);
        }
        return candidates.sort((a,b)=>{
          return score(b)-score(a)||(Math.abs(a.x-enemy.x)+Math.abs(a.y-enemy.y))-(Math.abs(b.x-enemy.x)+Math.abs(b.y-enemy.y))||a.id.localeCompare(b.id);
        })[0] ?? nearestNativeCandidate(enemy,this.units,this.map.width,this.map.height);
      };
      let target=chooseTarget();
      if(!target)continue;
      const source=this.combatActor(enemy);
      const costs=movementCosts(this.map.width,this.map.height,this.map.terrain,this.movementActors(),source,itemCategories,terrainMovement,classMovement);
      if(!inAttackRange(source,this.combatActor(target),attackRange(source,itemCategories,attackClasses),targetShapes.shapes)){
        let best:{x:number;y:number;distance:number;path:number[]}|undefined;
        const occupied=new Set(this.units.filter(u=>u.hp>0&&u!==enemy).map(u=>`${u.x},${u.y}`));
        for(const candidate of Array.from({length:this.map.width*this.map.height},(_,index)=>({x:index%this.map.width,y:Math.floor(index/this.map.width)})).filter(cell=>!occupied.has(`${cell.x},${cell.y}`))){
          const path=movementPath(this.map.width,this.map.height,costs,this.movementActors(),source,candidate.x,candidate.y,itemCategories);
          const distance=Math.abs(candidate.x-target.x)+Math.abs(candidate.y-target.y);
          if(path.length&&distance<Math.abs(enemy.x-target.x)+Math.abs(enemy.y-target.y)&&(!best||distance<best.distance))best={x:candidate.x,y:candidate.y,distance,path};
        }
        if(best){
          const visual=this.unitSprites.find(entry=>entry.unit===enemy);
          this.presentationUnits.add(enemy);
          try{for(const direction of best.path){
            const [dx,dy]=directions[direction],startX=enemy.x,startY=enemy.y;
            if(occupied.has(`${startX+dx},${startY+dy}`))break;
            enemy.direction=direction;if(direction===1)enemy.mirror=true;if(direction===3)enemy.mirror=false;
            for(const sample of movementFrames(source.classId,direction)){
              visual?.sprite.setPosition(this.ox+startX*48+24+dx*sample.progress,this.oy+startY*48+24+dy*sample.progress).setFrame(sample.frame).setFlipX(Boolean(enemy.mirror)&&[4,5].includes(sample.frame));
              await new Promise<void>(resolve=>this.time.delayedCall(50,resolve));
            }
            enemy.x+=dx;enemy.y+=dy;this.refreshUnitSprite(enemy);this.refreshMinimap();
          }}finally{this.presentationUnits.delete(enemy);this.refreshUnitSprite(enemy);}
        }
      }
      // Native turn flow resolves the target again after movement. Do not
      // attack the pre-movement target when it is no longer in range.
      target=chooseTarget(true);
      if(!target||!inAttackRange(this.combatActor(enemy),this.combatActor(target),attackRange(this.combatActor(enemy),itemCategories,attackClasses),targetShapes.shapes)){
        enemy.acted=true;enemy.actorFlags=(enemy.actorFlags??0)|6;this.refreshUnitSprite(enemy);continue;
      }
      const outcome=ordinaryExchange(this.combatActor(enemy),this.combatActor(target),this.battleRng,{items:itemCategories,classes:attackClasses,shapes:targetShapes.shapes});
      if(!outcome.supported)continue;
      for(const strike of outcome.strikes){const attacker=this.units.find(unit=>unit.id===strike.attacker),defender=this.units.find(unit=>unit.id===strike.defender);if(!attacker||!defender)continue;await this.playAttackStrike(attacker,defender,strike);Object.assign(defender,strike.after);this.refreshUnitSprite(defender);if(defender.hp<=0)break;}
      enemy.acted=true;enemy.actorFlags=(enemy.actorFlags??0)|6;this.refreshUnitSprite(enemy);
    }
    setRngState(this.battleRng.state);
  }
  private showItemEncyclopedia(){
    this.modal?.destroy();this.closeContextMenu();
    // 0x47072D: three columns, six visible rows; resource 334 is 109x40 DLU.
    const columns=3,visibleRows=6,tileWidth=218,tileHeight=75,width=columns*tileWidth+24,height=visibleRows*tileHeight+74;
    const group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(500);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(10,6,'宝物图鉴',{fontFamily:'SimSun',fontSize:'15px',color:'#000000'}));
    const list=this.add.container(8,28);group.add(list);let firstRow=0;
    const render=()=>{
      list.removeAll(true);
      treasureCatalog.entries.slice(firstRow*columns,(firstRow+visibleRows)*columns).forEach((item,index)=>{
        const x=index%columns*tileWidth,y=Math.floor(index/columns)*tileHeight;
        list.add(this.add.rectangle(x,y,tileWidth,tileHeight,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0xa0a0a0));
        const hit=this.add.rectangle(x,y,tileWidth,tileHeight,0,0).setOrigin(0).setInteractive();
        hit.on('pointerup',()=>{if(item.discovered)this.openTreasureDetail(item,group);});
        list.add(hit);
        if(item.discovered)list.add(this.add.image(x+30,y+30,`treasure-${item.itemId}`));
        list.add(this.add.text(x+64,y+13,`No.${String(item.number).padStart(2,' ')}: ${item.discovered?item.name:'？？？'}`,{fontFamily:'SimSun',fontSize:'13px',color:item.discovered?'#000000':'#808080'}));
        if(item.discovered)list.add(this.add.text(x+64,y+40,item.description,{fontFamily:'SimSun',fontSize:'12px',color:'#000000',wordWrap:{width:142},maxLines:2}));
      });
    };
    render();
    const onWheel=(_p:Phaser.Input.Pointer,_o:unknown,_dx:number,dy:number)=>{if(this.modal!==group)return;firstRow=Phaser.Math.Clamp(firstRow+Math.sign(dy),0,Math.max(0,Math.ceil(treasureCatalog.entries.length/columns)-visibleRows));render();};
    this.input.on('wheel',onWheel);group.once('destroy',()=>this.input.off('wheel',onWheel));
    group.add(this.add.text(10,height-30,`Find: ${treasureCatalog.entries.filter(item=>item.discovered).length} / ${treasureCatalog.entries.length}`,{fontSize:'13px',color:'#000000'}));
    const close=()=>{group.destroy();this.modal=undefined;};
    nativeButton(this,group,[width-110,height-36,100,26],'确定',2,close);
    group.setData('nativeHitRegions',[{x:width-110,y:height-36,width:100,height:26,command:close}]);
    this.modal=group;return;
    const rows=slot08.actors.flatMap(actor=>actor.equipmentSlots.filter(item=>item.itemId!==255).map(item=>item.name??`道具 ${item.itemId}`));
    this.openModal('宝物图鉴',Array.from(new Set(rows)).slice(0,18).join('\n'),['确定']);
  }
  private showActionNotice(message:string){
    this.actionNotice??=this.add.text(620,92,'',{fontSize:'14px',color:'#ffd35a',backgroundColor:'#18202a',padding:{x:6,y:4},wordWrap:{width:310}}).setScrollFactor(0).setDepth(220);
    this.actionNotice.setText(message).setVisible(true);
  }
  private openTreasureDetail(item:(typeof treasureCatalog.entries)[number],parent:Phaser.GameObjects.Container){
    if(this.modal!==parent)return;
    const template=nativeUi.dialogs.find(row=>row.resourceId===167)!;
    const [width,height]=template.nativeWindowPixels!;
    const panel=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(550);
    panel.setData('dialogResource',167);
    panel.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    panel.add(this.add.image(40,28,`treasure-${item.itemId}`));
    for(const [id,value] of [[1016,item.name],[1070,item.description],[1023,item.categoryLabel],[1018,item.price===null?'---':String(item.price)],[1025,item.effectText],[1455,item.additionalEffectText]] as const){
      const control=template.controls.find(row=>row.id===id)!;
      const [x,y,w]=(control as {nativeRectPixels:number[]}).nativeRectPixels;
      panel.add(this.add.text(x,y,value,{fontFamily:'SimSun',fontSize:'13px',color:'#000000',wordWrap:{width:w},lineSpacing:3}));
    }
    panel.add(this.add.text(22,71,'属性：',{fontFamily:'SimSun',fontSize:'13px',color:'#000000'}));
    panel.add(this.add.text(22,94,'价格：',{fontFamily:'SimSun',fontSize:'13px',color:'#000000'}));
    for(const control of template.controls.filter(row=>row.id>=1472&&row.id<=1484)){
      const [x,y]=(control as {nativeRectPixels:number[]}).nativeRectPixels;
      panel.add(this.add.text(x,y,String(control.text),{fontFamily:'SimSun',fontSize:'13px',color:item.equipGroups[control.id-1472]?'#000000':'#808080'}));
    }
    const close=()=>{panel.destroy();this.modal=parent;};
    const rect=(template.controls.find(row=>row.id===2)! as {nativeRectPixels:number[]}).nativeRectPixels;
    nativeButton(this,panel,rect,'确认',2,close);
    const [x,y,w,h]=rect;
    panel.setData('nativeHitRegions',[{x,y,width:w,height:h,command:close}]);
    this.modal=panel;
  }
  private beginAttackSelection(){
    if(this.battleEnded||!this.selected||this.selected.acted)return;
    const actor=this.movementActors().find(actor=>actor.id===this.selected!.id)!;
    const range=attackRange(actor,itemCategories,attackClasses);
    this.actionMode='attack';this.closeContextMenu();this.clearReach();this.actionNotice?.setVisible(false);
    for(const [key,cell] of this.cells){
      const [x,y]=key.split(',').map(Number);
      if(inAttackRange(actor,{x,y},range,targetShapes.shapes))cell.setFillStyle(0xc45442,0.4);
    }
  }
  private beginUtilitySelection(mode:'strategy'|'item'){
    if(!this.selected||this.selected.acted)return;
    this.actionMode=mode;this.closeContextMenu();this.closeUtilityMenu();this.clearReach();
    const menu=this.add.container(420,92).setScrollFactor(0).setDepth(340);this.utilityMenu=menu;
    if(mode==='item')this.showStrategyReach(0xc29b4b);
    menu.add(this.add.rectangle(0,0,300,24,0x202a35).setOrigin(0));
    menu.add(this.add.text(8,4,mode==='strategy'?'策略':'道具',{fontSize:'14px',color:'#ffffff'}));
    if(mode==='strategy'){
      const actor=this.combatActor(this.selected);
      const learned=(effectLearning as Array<{effect_id:string;name_gbk:string;class_id:string;required_level:string;learnable:string}>)
        .filter(row=>Number(row.class_id)===actor?.classId&&Number(row.required_level)<=Number(actor?.nativeLevel)&&row.learnable==='True')
        .map(row=>({id:Number(row.effect_id),name:row.name_gbk || `效果 ${row.effect_id}`}));
      if(!learned.length){this.showActionNotice('无已验证可用策略');this.closeUtilityMenu();return;}
      learned.slice(0,8).forEach((effect,index)=>nativeButton(this,menu,[8,30+index*28,284,24],effect.name,effect.id,()=>{
        this.selectedEffectId=effect.id;this.closeUtilityMenu();this.showStrategyReach();this.showActionNotice(`选择${effect.name}的目标`);
      }));
    }else{
      if(!this.consumableStock&&this.mapId===31)this.consumableStock=savedConsumableStock.rows.find(row=>row.slot===8)?.stock.slice();
      if(!this.consumableStock){this.closeUtilityMenu();this.clearReach();this.showActionNotice('该关卡的原生库存尚未接入');return;}
      const items=(itemCategories as Array<{id:number;name?:string;categoryByte:number}>).filter(item=>item.id>=87&&item.id<=103&&item.categoryByte>=63&&item.categoryByte<=76&&nativeConsumableCount(this.consumableStock!,item.id)>0).map(item=>({itemId:item.id,name:item.name}));
      if(!items.length){this.showActionNotice('没有已验证消耗品定义');this.closeUtilityMenu();return;}
      items.forEach((item,index)=>nativeButton(this,menu,[8,30+index*28,284,24],item.name??`道具 ${item.itemId}`,item.itemId,()=>{
        this.selectedItemId=item.itemId;this.closeUtilityMenu();this.clearReach();
        this.showStrategyReach(0xc29b4b);
        this.showActionNotice(`选择${item.name??`道具 ${item.itemId}`}的目标`);
      }));
    }
  }
  private previewVerifiedEffect(target:Unit){
    const geometry=effectGeometry.effects.find(row=>row.effectId===this.selectedEffectId);
    const origin=this.movementActors().find(row=>row.id===this.selected?.id);
    if(!geometry||!origin||!inAttackRange(origin,target,geometry.targetShape,targetShapes.shapes))return;
    const actor=this.combatActor(this.selected!);
    const learned=(effectLearning as Array<{effect_id:string;class_id:string;required_level:string;learnable:string}>)
      .filter(row=>Number(row.class_id)===actor?.classId&&Number(row.required_level)<=Number(actor?.nativeLevel)&&row.learnable==='True');
    const effect=effectById(this.selectedEffectId ?? Number(learned[0]?.effect_id));
    if(!effect){this.showActionNotice(`No verified native effect mapping for ${target.name}`);return;}
    if(this.cache.audio.exists(`effect-${effect.effectId}`))this.sound.play(`effect-${effect.effectId}`);
    if(effect.resource.startsWith('Mcall')){
      const match=effect.resource.match(/Mcall(\d+)/);const index=match?Number(match[1]):-1;
      if(index>=0&&index<9){
        const visual=this.add.image(this.ox+target.x*this.size+24,this.oy+target.y*this.size+24,`effect-mcall-${index}`).setDepth(15).setAlpha(0.9);
        visual.setDisplaySize(96,96);this.tweens.add({targets:visual,alpha:0,duration:700,onComplete:()=>visual.destroy()});
      }
    }
    this.showActionNotice(`${effect.name} -> ${target.name}\nresource ${effect.resource} entry ${effect.entry}\nsound ${effect.sound} timeline ${effect.timelineFrames} frame(s)`);
    // Native strategy dispatch consumes the acting unit's command after a
    // valid target is accepted, even when the effect result is visual/status
    // work handled by a separate native dispatcher.
    if(this.selected){
      this.selected.acted=true;this.selected.actorFlags=(this.selected.actorFlags??0)|6;
      this.refreshUnitSprite(this.selected);this.actionMode=undefined;this.selectedEffectId=undefined;this.clearReach();this.closeUtilityMenu();this.maybeOpenEndTurnConfirm();
    }
  }
  private showStrategyReach(color=0x7567c7){
    this.clearReach();
    if(!this.selected)return;
    if(this.actionMode==='item'){
      const actor=this.combatActor(this.selected);
      for(const [key,cell] of this.cells){
        const [x,y]=key.split(',').map(Number);
        if(inAttackRange(actor,{x,y},1,targetShapes.shapes,1))cell.setFillStyle(color,0.35);
      }
      return;
    }
    if(this.actionMode!=='strategy')return;
    const geometry=effectGeometry.effects.find(row=>row.effectId===this.selectedEffectId);
    if(!geometry||geometry.targetShape===255)return;
    const shape=targetShapes.shapes.find(row=>row.id===(geometry.targetShape&127));
    for(const [key,cell] of this.cells){
      const [x,y]=key.split(',').map(Number);
      if(shape&&(shape.fullMap||shape.offsets.some(([dx,dy])=>this.selected!.x+dx===x&&this.selected!.y+dy===y)))cell.setFillStyle(color,0.35);
    }
  }
  private previewVerifiedItem(target:Unit){
    if(!this.selected||target.hp<=0||target.nativeHidden||target.side!==this.selected.side)return;
    if(!this.consumableStock||this.selectedItemId===undefined||nativeConsumableCount(this.consumableStock,this.selectedItemId)===0)return;
    if(!inAttackRange(this.combatActor(this.selected),target,1,targetShapes.shapes,1))return;
    const rule=(itemCategories as Array<{id:number;name?:string;categoryByte?:number;baseValue?:number;secondaryValue?:number}>).find(row=>row.id===this.selectedItemId);
    if(!rule){this.showActionNotice(`No verified item mapping for ${target.name}`);return;}
    if(!nativeManualItemEligible(rule.categoryByte??255,this.combatActor(target),false))return;
    this.showActionNotice(`${rule.name??`Item ${rule.id}`} -> ${target.name}\nid ${rule.id} category ${rule.categoryByte??'-'} base ${rule.baseValue??'-'} secondary ${rule.secondaryValue??'-'}\nNative item result controller is not reconstructed.`);
  }
  private showAttackPreview(target:Unit){
    if(!this.selected)return;
    const actor=this.movementActors().find(actor=>actor.id===this.selected?.id);
    if(!actor)return;
    const range=attackRange(actor,itemCategories,attackClasses);
    if(!inAttackRange(actor,target,range,targetShapes.shapes))return;
    const combat=(unit:Unit)=>{
      const source=this.movementActors().find(actor=>actor.id===unit.id)!;
      const values=combatAttributes.actors.find(actor=>actor.id===unit.id)!;
      const type=source.classId<39?Math.floor(source.classId/3):source.classId-26;
      const adaptation=terrainMovement.find(row=>row.movementType===type)?.adaptation[this.map.terrain[unit.y*this.map.width+unit.x]]??0;
      return {...source,attack:values.attack,defense:values.defense,adaptation:adaptation===255?0:adaptation};
    };
    const damage=ordinaryDamage(combat(this.selected),combat(target),itemCategories);
    this.showActionNotice(`攻击目标：${target.name}\n伤害预览 ${damage}`);
  }
  private movementActors(){return this.units.filter(unit=>unit.hp>0&&!unit.nativeHidden).map(unit=>{
    const native=slot08.actors.find(actor=>actor.id===unit.id);
    if(native)return {...native,...unit};
    const classId=unit.nativeClassId??0;
    const slot=Number(unit.id.match(/-slot-(\d+)$/)?.[1]);
    const movementState=(scenarioCombat as Record<string,Array<{slot:number;movementTier:number}>>)[String(this.mapId)]?.find(row=>row.slot===slot);
    const record=this.mapId===0
      ?s00Units.units.find(row=>row.nativeBattleSlot===slot)?.controlledNativeExpansion
      :(scenarioUnits[this.mapId] as {units?:Array<{slot:number;level:number}>}|undefined)?.units?.find(row=>row.slot===slot);
    const actor={...unit,classId,equipmentSlots:unit.nativeEquipment??[],terrainCosts:unit.nativeMovementCosts??[],move:unit.move,attack:20,defense:10,movementTier:movementState?.movementTier??1,nativeLevel:record?.level??1,mp:unit.mp??0,actorFlags:unit.actorFlags??0,statusFlags:unit.statusFlags??0};
    actor.move=movementBudget(actor,itemCategories,classMovement);
    return actor;
  });}
  private combatActor(unit:Unit){
    const source=this.movementActors().find(actor=>actor.id===unit.id);
    if(!source){
      return {id:unit.id,x:unit.x,y:unit.y,hp:unit.hp,mp:unit.mp??0,classId:unit.nativeClassId??0,
        equipmentSlots:[],attack:20,defense:10,agility:10,luck:0,hit:80,critical:0,
        actorFlags:unit.actorFlags??0,statusFlags:unit.statusFlags??0,adaptation:0,nativeLevel:1,
        movementTier:1,move:unit.move};
    }
    const nativeSlot=Number(unit.id.match(/-slot-(\d+)$/)?.[1]);
    const scenarioValues=(scenarioCombat as Record<string,Array<{slot:number;baseStats:number[];states:number[];attack:number;defense:number;agility:number;luck:number}>>)[String(this.mapId)]?.find(actor=>actor.slot===nativeSlot);
    const values=combatRuntime.actors.find(actor=>`unit-${actor.slot}`===unit.id)
      ?? (scenarioValues?nativeBattleAttributes(scenarioValues.baseStats,scenarioValues.states,unit.nativeEquipment??[],nativeEquipmentAttributes):undefined)
      ?? {attack:20,defense:10,hit:80,critical:0,agility:10,luck:0};
    const type=source.classId<39?Math.floor(source.classId/3):source.classId-26;
    const adaptation=terrainMovement.find(row=>row.movementType===type)?.adaptation[this.map.terrain[unit.y*this.map.width+unit.x]]??0;
    return {...source,...values,id:unit.id,x:unit.x,y:unit.y,hp:unit.hp,mp:unit.mp??source.mp??0,
      actorFlags:unit.actorFlags??0,statusFlags:unit.statusFlags??0,adaptation:adaptation===255?0:adaptation};
  }
  private async executeAttack(target:Unit){
    if(this.battleEnded||this.animating||!this.selected||this.selected.acted||this.selected.side!=='player'||target.hp<=0)return;
    const outcome=ordinaryExchange(this.combatActor(this.selected),this.combatActor(target),this.battleRng,{items:itemCategories,classes:attackClasses,shapes:targetShapes.shapes});
    if(!outcome.supported){this.showActionNotice(outcome.reason);return;}
    this.lastExchange=outcome.strikes;this.actionMode=undefined;this.closeContextMenu();this.clearReach();this.animating=true;
    try{
      for(const strike of outcome.strikes){
        const a=this.units.find(unit=>unit.id===strike.attacker)!,d=this.units.find(unit=>unit.id===strike.defender)!;
        this.showActionNotice(`${a.name} → ${d.name}\n${strike.critical?'会心一击  ':''}${strike.hpDamage||strike.mpDamage?`HP -${strike.hpDamage}  MP -${strike.mpDamage}`:'未命中'}`);
        await this.playAttackStrike(a,d,strike);
        Object.assign(d,strike.after);
        this.unitSprites.find(entry=>entry.unit===d)?.sprite.setVisible(d.hp>0);this.refreshUnitSprite(d);
      }
      }finally{setRngState(this.battleRng.state);this.animating=false;this.finishAction();if(this.mapId===0&&this.units.filter(unit=>unit.side==='enemy'&&unit.hp>0).length===0)this.openS00Victory();}
  }
  private async moveNativeCameraToActor(unit:Unit){
    const viewport={width:Math.max(1,Math.floor(this.cameras.main.width/this.size)),height:Math.max(1,Math.floor(this.cameras.main.height/this.size))};
    const target=clampNativeCamera({x:unit.x,y:unit.y},{width:this.map.width,height:this.map.height},viewport);
    const from={x:Math.round(this.cameras.main.scrollX/this.size),y:Math.round(Math.max(0,this.cameras.main.scrollY-this.oy)/this.size)};
    for(const step of nativeCameraSteps(from,target)){
      this.cameras.main.scrollX=step.x*this.size;
      const maxScroll=Math.max(0,this.map.height*this.size+this.oy-this.cameras.main.height);
      this.cameras.main.scrollY=Phaser.Math.Clamp(step.y*this.size+this.oy,0,maxScroll);
      this.refreshMinimap();
      await new Promise<void>(resolve=>this.time.delayedCall(16,resolve));
    }
  }
  private async playAttackStrike(attacker:Unit,defender:Unit,strike:ExchangeStrike){
    await this.moveNativeCameraToActor(defender);
    this.presentationUnits.add(attacker);this.presentationUnits.add(defender);
    const av=this.unitSprites.find(entry=>entry.unit===attacker)!.sprite,dv=this.unitSprites.find(entry=>entry.unit===defender)!.sprite;
    const dx=defender.x-attacker.x,dy=defender.y-attacker.y;
    const direction=Math.abs(dx)>=Math.abs(dy)?(dx>0?1:3):(dy>0?2:0),bank=[1,2,0,2][direction];
    attacker.direction=direction;if(direction===1)attacker.mirror=true;if(direction===3)attacker.mirror=false;
    const source=this.movementActors().find(actor=>actor.id===attacker.id)!;
    const type=source.classId<39?Math.floor(source.classId/3):source.classId-26;
    const attack=this.add.sprite(av.x,av.y,`atk-${attacker.art}`,bank*4).setDepth(8).setFlipX(direction===1);
    // 0x403D85: damaging hits use SPC frame 3 without mirroring. Dodge
    // frames use the defender's own facing, with only east mirrored.
    const damaged=strike.hpDamage!==0||strike.mpDamage!==0;
    const defenderDirection=defender.direction??2;
    const hurtFrame=damaged?3:[1,2,0,2][defenderDirection];
    const hurt=this.add.sprite(dv.x,dv.y,`spc-${defender.art}`,hurtFrame).setDepth(7).setFlipX(!damaged&&defenderDirection===1).setVisible(false);
    const displacement=damaged?(strike.critical?8:4):8;
    const hitOffset=[[0,displacement],[-displacement,0],[0,-displacement],[displacement,0]][defenderDirection];
    av.setVisible(false);
    try{
      for(let tick=0;tick<27;tick++){
        if(tick===2)this.sound.play(`combat-${[0,1,7,9,10,14,15,18].includes(type)?34:[2,4].includes(type)?37:32}`);
        if(tick===8){attack.setFrame(bank*4+([2,4].includes(type)?1:0));if(strike.critical)this.sound.play('combat-33');}
        if(tick===12)attack.setFrame(bank*4+1);
        if(tick===13){attack.setFrame(bank*4+2);dv.setVisible(false);hurt.setPosition(dv.x+hitOffset[0],dv.y+hitOffset[1]).setVisible(true);this.sound.play(`combat-${damaged?(strike.critical?36:35):(strike.critical?31:30)}`);}
        if(tick===14)attack.setFrame(bank*4+3);
        await new Promise<void>(resolve=>this.time.delayedCall(50,resolve));
      }
    }finally{attack.destroy();hurt.destroy();this.presentationUnits.delete(attacker);this.presentationUnits.delete(defender);av.setVisible(attacker.hp>0);dv.setVisible(defender.hp>0);this.refreshUnitSprite(attacker);this.refreshUnitSprite(defender);}
  }
  private async moveSelectedTo(key:string){
    if(this.modal)return;
    if(!this.selected || this.actionMode || this.moving || this.selected.acted||this.selected.side!=='player')return;
    const [x,y]=key.split(',').map(Number);
    if(x===this.selected.x && y===this.selected.y)return;
    const actors=this.movementActors(),source=actors.find(actor=>actor.id===this.selected?.id);
    if(!source)return;
      const costs=movementCosts(this.map.width,this.map.height,this.map.terrain,actors,source,itemCategories,terrainMovement,classMovement);
    if(costs[y*this.map.width+x]===255)return;
    const occupied=this.units.find(unit=>unit.hp>0&&unit!==this.selected && unit.x===x && unit.y===y);
    if(occupied)return;
    const path=movementPath(this.map.width,this.map.height,costs,actors,source,x,y,itemCategories);
    if(!path.length)return;
    const unit=this.selected,visual=this.unitSprites.find(entry=>entry.unit===unit);
    if(!visual)return;
    this.moving=true;
    this.animating=true;this.clearReach();
    for(const direction of path){
      const [dx,dy]=directions[direction],startX=unit.x,startY=unit.y;
      unit.direction=direction;
      if(direction===1)unit.mirror=true;
      if(direction===3)unit.mirror=false;
      for(const sample of movementFrames(source.classId,direction)){
        visual.sprite.setPosition(this.ox+startX*48+24+dx*sample.progress,this.oy+startY*48+24+dy*sample.progress)
          .setFrame(sample.frame).setFlipX(Boolean(unit.mirror)&&[4,5].includes(sample.frame));
        await new Promise<void>(resolve=>this.time.delayedCall(50,resolve));
      }
      unit.x+=dx;unit.y+=dy;
      const type=source.classId<39?Math.floor(source.classId/3):source.classId-26;
      const sound=movementSounds.rows.find(row=>row.movementType===type&&row.terrain===this.map.terrain[unit.y*this.map.width+unit.x]);
      for(const id of sound?.soundIds??[])this.sound.play(`step-${id}`);
    }
    unit.actorFlags=(unit.actorFlags??0)|4;
    this.animating=false;this.updateStatus(unit);
    this.clearReach();
    this.cells.get(key)?.setStrokeStyle(2,0x9fe3b1,0.9);
    // Original 0x43DDE3 opens the action selector after 0x43D538 completes movement.
    // Sprite coordinates are already cell-center coordinates. The native
    // action dialog opens at the destination cursor; adding another half
    // tile here shifted the dialog and its hit targets after movement.
    this.openContextMenu(unit,visual.sprite.x-this.cameras.main.scrollX,visual.sprite.y-this.cameras.main.scrollY);
  }
  private cancelMovement(){
    this.playNativeSound(1);
    this.actionMode=undefined;this.actionNotice?.setVisible(false);this.closeUtilityMenu();this.selectedEffectId=undefined;
    if(this.animating||!this.selected || !this.selectedStart || !this.moving)return;
    Object.assign(this.selected,this.selectedStart);
    this.closeContextMenu();
    const visual=this.unitSprites.find(entry=>entry.unit===this.selected);
    visual?.sprite.setPosition(this.ox+this.selected.x*this.size+24,this.oy+this.selected.y*this.size+24);
    this.moving=false;this.select(this.selected);
  }
  private playNativeSound(id:number){
    const key=`native-se-${id}`;
    if(this.cache.audio.exists(key))this.sound.play(key);
  }
  private finishAction(){
    if(this.battleEnded||this.animating||!this.selected || this.selected.acted||this.selected.side!=='player')return;
    this.selected.actorFlags=(this.selected.actorFlags??0)|6;
    this.actionMode=undefined;this.actionNotice?.setVisible(false);this.closeUtilityMenu();this.selectedEffectId=undefined;
    this.selected.acted=true;this.moving=false;this.clearReach();
    this.refreshUnitSprite(this.selected);
    this.closeContextMenu();
    this.updateStatus(this.selected);
    this.maybeOpenEndTurnConfirm();
  }
  private openS00Victory(){
    if(this.battleEnded||this.modal)return;
    this.battleEnded=true;this.gold+=800;this.actionMode=undefined;this.closeContextMenu();this.clearReach();
    const width=320,height=150,group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(600);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(12,10,'颍川黄巾战',{fontFamily:'SimSun',fontSize:'17px',color:'#000000'}));
    group.add(this.add.text(16,45,'战斗胜利\n获得金钱 800',{fontFamily:'SimSun',fontSize:'14px',color:'#000000',lineSpacing:5}));
    const close=()=>{group.destroy();this.modal=undefined;};
    nativeButton(this,group,[230,112,70,26],'确定',1,close);
    group.setData('nativeHitRegions',[{x:230,y:112,width:70,height:26,command:close}]);this.modal=group;
  }
  private openS00Defeat(){
    if(this.battleEnded||this.modal)return;
    this.battleEnded=true;this.actionMode=undefined;this.closeContextMenu();this.clearReach();
    const width=320,height=150,group=this.add.container((this.scale.width-width)/2,(this.scale.height-height)/2).setScrollFactor(0).setDepth(600);
    group.add(this.add.rectangle(0,0,width,height,0xc0c0c0).setOrigin(0).setStrokeStyle(1,0x808080));
    group.add(this.add.text(12,10,'颍川黄巾战',{fontFamily:'SimSun',fontSize:'17px',color:'#000000'}));
    group.add(this.add.text(16,45,'战斗失败',{fontFamily:'SimSun',fontSize:'14px',color:'#000000'}));
    const close=()=>{group.destroy();this.modal=undefined;};
    nativeButton(this,group,[230,112,70,26],'确定',1,close);
    group.setData('nativeHitRegions',[{x:230,y:112,width:70,height:26,command:close}]);this.modal=group;
  }
  /** Keep the native automatic prompt reachable from every action completion path. */
  private maybeOpenEndTurnConfirm(){
    const living=this.units.filter(unit=>unit.side==='player'&&unit.hp>0&&!unit.nativeHidden);
    if(living.length>0 && living.every(unit=>unit.acted) && !this.modal && !this.contextMenu)
      this.openEndTurnConfirm();
  }
  private clearReach(){for(const r of this.cells.values()){r.setFillStyle(0x253341,0);r.setStrokeStyle();}}
}
