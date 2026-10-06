import sys, os
from PIL import Image, ImageDraw, ImageFont
names=[l.strip() for l in open(sys.argv[1]) if l.strip()]
pre=sys.argv[2]; per=int(sys.argv[3]) if len(sys.argv)>3 else 24
T=230; cols=6
f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',10)
for s in range(0,len(names),per):
    ch=names[s:s+per]; rows=(len(ch)+cols-1)//cols
    sh=Image.new('RGB',(cols*(T+4),rows*(T+16)),(20,20,20)); d=ImageDraw.Draw(sh)
    for k,n in enumerate(ch):
        im=Image.open((sys.argv[4] if len(sys.argv)>4 else 'work/sprites/')+n).convert('RGBA'); im.thumbnail((T,T))
        bg=Image.new('RGBA',im.size,(70,70,90,255)); bg.alpha_composite(im)
        x,y=(k%cols)*(T+4),(k//cols)*(T+16)
        sh.paste(bg.convert('RGB'),(x,y+14)); d.text((x,y),f'{s+k} '+n.replace('sprite__','')[:44],font=f,fill=(255,255,0))
    sh.save(f'{pre}_{s//per:02d}.png')
print((len(names)+per-1)//per)
