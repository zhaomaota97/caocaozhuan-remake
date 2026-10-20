/** Native 0x40C7A9; priceByte comes from loaded item +0x12. */
export function nativeItemResale(item:{categoryByte:number;priceByte:number},level:number):number{
  if(item.priceByte===255)return 65535;
  const value=item.priceByte*75;
  return item.categoryByte<18?Math.floor(value*((level&255)+1)/2):value;
}
