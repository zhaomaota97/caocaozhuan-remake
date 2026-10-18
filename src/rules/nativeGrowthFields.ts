export interface NativeGrowthField {category:number;unitOffset:number;actorIndex:number;}
const fields:NativeGrowthField[]=[
  {category:0x46,unitOffset:0x15,actorIndex:0},
  {category:0x47,unitOffset:0x17,actorIndex:2},
  {category:0x48,unitOffset:0x16,actorIndex:1},
  {category:0x49,unitOffset:0x18,actorIndex:3},
  {category:0x4a,unitOffset:0x19,actorIndex:4}
];
export function nativeGrowthField(category:number):NativeGrowthField|undefined{return fields.find(field=>field.category===category);}
export function nativeGrowthFields():NativeGrowthField[]{return fields.slice();}
