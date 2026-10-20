"""Recovered indexed-color effect blend primitives (four-bit palette channels)."""


def quantize(channels,lookup):
    return lookup[(channels[0]<<8)+(channels[1]<<4)+channels[2]]


def masked_pixel(source,mask,background,palette,current,lookup,strength):
    if source==0 or (mask==0 and strength==0):return background
    rgb=palette[source*3:source*3+3]
    if mask==255:return quantize(rgb,lookup)
    coefficient=((256-mask)*(256-(sum(rgb)//3)*strength))>>8
    return mix(rgb,current[background*3:background*3+3],coefficient,strength,lookup)


def mix(rgb,bg,coefficient,strength,lookup):
    weight=256-((coefficient*(16-strength))>>4)
    channels=[min(((b*coefficient+s*weight)>>8)&255,15) for b,s in zip(bg,rgb)]
    return quantize(channels,lookup)


def constant_pixel(source,background,palette,current,lookup,opacity,invert,strength):
    if source==0:return background
    rgb=palette[source*3:source*3+3]
    if opacity==0:return quantize(rgb,lookup)
    if strength==0 and opacity==16:return background
    brightness=(45-sum(rgb))//3+1 if invert else sum(rgb)//3
    coefficient=(opacity*(256-brightness*strength))>>4
    if coefficient==0:return quantize(rgb,lookup)
    return mix(rgb,current[background*3:background*3+3],coefficient,strength,lookup)
