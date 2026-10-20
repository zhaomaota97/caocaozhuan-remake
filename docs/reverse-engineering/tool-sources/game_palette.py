"""Reproduce the game's four-bit color lookup, including its ordered tie rule."""


def dominant(rgb):
    return max(range(3),key=lambda i:rgb[i])


def color_lookup(palette):
    if len(palette)!=768 or any(v>15 for v in palette):
        raise ValueError('Expected 256 four-bit triples in native channel order')
    groups=[[],[],[]]
    for index in range(10,246):
        rgb=palette[index*3:index*3+3]
        groups[dominant(rgb)].append((index,*rgb))
    out=bytearray(4096)
    for a in range(16):
        for b in range(16):
            for c in range(16):
                best_max=best_sum=65535;chosen=0
                for index,x,y,z in groups[dominant((a,b,c))]:
                    d0,d1,d2=abs(a-x),abs(b-y),abs(c-z)
                    maximum=max(d0,d1,d2);total=d0+d1+d2
                    if maximum<=best_max and total<=best_sum:
                        chosen=index;best_max=maximum;best_sum=total
                out[(a<<8)+(b<<4)+c]=chosen
    return bytes(out)
