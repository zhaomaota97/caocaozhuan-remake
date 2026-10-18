export interface NativeDialogueSegment { speakerId?:number; speakerToken?:string; text:string; }

/**
 * Parse the native opcode-20 line layout after the EEX string reader has
 * decoded it. A leading '&' introduces a speaker selector; the body ends at
 * the next newline followed by '&'. Plain narration has no selector.
 */
export function parseNativeDialogueSegments(input:string):NativeDialogueSegment[]{
  const segments:NativeDialogueSegment[]=[];
  const chunks=input.split(/\n(?=&)/g);
  for(const chunk of chunks){
    if(chunk.startsWith('&')){
      const match=/^&([^\n\r]*)(?:\r?\n)?([\s\S]*)$/.exec(chunk);
      if(!match)continue;
      const token=match[1].trim(),numeric=/^\d+$/.test(token)?Number(token):undefined;
      segments.push(numeric===undefined?{speakerToken:token,text:match[2]}:{speakerId:numeric,text:match[2]});
    }else if(chunk.length){segments.push({text:chunk});}
  }
  return segments;
}
