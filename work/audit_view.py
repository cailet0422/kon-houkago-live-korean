import sys, os
sys.path.insert(0,'tools')
import numpy as np
from PIL import Image, ImageDraw
import audit_cut
names=sys.argv[1:]
res={r[2]:r for r in audit_cut.audit()}
for n in names:
    o_,e_,_,outside,edge,rects=res[n]
    k=Image.open(f'assets_ko/sprite/{n}.png').convert('RGBA')
    bg=Image.new('RGBA',k.size,(50,50,50,255)); bg.alpha_composite(k)
    a=np.asarray(bg).copy()
    a[outside]=(255,0,0,255); a[edge]=(255,255,0,255)
    im=Image.fromarray(a); d=ImageDraw.Draw(im)
    for x,y,w,h,sid in rects: d.rectangle((x,y,x+w-1,y+h-1),outline=(0,255,0,255))
    s=max(1,min(3,1400//max(im.size)))
    im.resize((im.width*s,im.height*s),Image.NEAREST).save(f'work/annot/aud_{n}.png')
    print(n, im.size, len(rects))
