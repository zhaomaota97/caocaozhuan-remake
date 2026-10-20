import {nativeItemRestoreWriteback} from './itemRestoreAmount';
import {decrementNativeConsumable} from './consumableInventory';

/** State path of native 0x41DC43 for restoration categories after eligibility. */
export function nativeManualRestoreDispatch(input:{category:63|64;itemId:number;value:number;targetSelected:boolean;presentationCompleted:boolean;freeUse:boolean;stock:readonly number[];target:{hp:number;maxHp:number;mp:number;maxMp:number}}){
  const resources=input.targetSelected?nativeItemRestoreWriteback(input.category,input.value,input.target):{hp:input.target.hp,mp:input.target.mp};
  const completed=input.targetSelected&&input.presentationCompleted;
  const stock=completed&&!input.freeUse?decrementNativeConsumable(input.stock,input.itemId):input.stock.slice();
  return {...resources,completed,stock};
}
