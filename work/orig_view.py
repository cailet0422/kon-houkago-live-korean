import sys
sys.path.insert(0,'tools')
from PIL import Image, ImageDraw
import sprite_rects
R=sprite_rects.load()
for n in sys.argv[1:]:
    im=Image.open(f'work/sprites/sprite__{n}.png').convert('RGBA')
    bg=Image.new('RGBA',im.size,(50,50,50,255)); bg.alpha_composite(im); d=ImageDraw.Draw(bg)
    for x,y,w,h,s in R[f'PSP_GAME/USRDIR/sprite/{n}.uvr']: d.rectangle((x,y,x+w-1,y+h-1),outline=(0,255,0,255))
    s=max(1,min(3,1400//max(im.size)))
    bg.resize((im.width*s,im.height*s),Image.NEAREST).save(f'work/annot/orig_{n}.png')
