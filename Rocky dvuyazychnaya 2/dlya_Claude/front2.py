from PIL import Image, ImageDraw, ImageFont
import numpy as np
F='/home/claude/fonts/'; W,H=2588,3375; INK=(40,40,40); GR=(56,56,56)
B=lambda s:ImageFont.truetype(F+'BalsamiqSans-Bold.ttf',s); R=lambda s:ImageFont.truetype(F+'BalsamiqSans-Regular.ttf',s)
# --- принадлежит
a=np.asarray(Image.open('/mnt/user-data/uploads/This_Book_Belongs_To_8_5x11_2550x3300_300dpi.png').convert('L')).copy()
a[a>238]=255; a[845:1185,975:1650]=255; a[1235:1300,650:1950]=255
im=Image.fromarray(a).convert('RGB'); d=ImageDraw.Draw(im)
def c(dr,t,f,y,col,w): dr.text(((w-dr.textlength(t,font=f))/2,y),t,font=f,fill=col)
c(d,'This book',B(115),845,INK,2550); c(d,'belongs to',B(115),975,INK,2550)
c(d,'Este libro pertenece a',B(70),1140,GR,2550)
pg=Image.new('RGB',(W,H),'white'); pg.paste(im,((W-2550)//2,(H-3300)//2)); pg.save('obr/p_belongs.png')
# --- оглавление
v=Image.open('/mnt/user-data/uploads/Illustration_Village_Pencil_2588x3375_300dpi.png').convert('L')
s=0.80; vw,vh=int(W*s),int(H*s); v=v.resize((vw,vh),Image.LANCZOS)
x0,y0=W-vw,H-vh
p=np.full((H,W),255.0); p[y0:,x0:]=np.asarray(v)
yy=np.arange(H)[:,None]; xx=np.arange(W)[None,:]
k=np.clip((yy-1420)/260,0,1)*np.clip((xx-x0)/320,0,1)
p=255-(255-p)*k
pc=Image.fromarray(p.astype(np.uint8)).convert('RGB'); d=ImageDraw.Draw(pc)
c(d,'Contents',B(130),200,INK,W); c(d,'Contenido',B(86),360,GR,W)
rows=[('Lucky Rocky and His Friends','Rocky el Afortunado y sus amigos'),('About Friendship','Acerca de la amistad'),
('Lost Glasses','Los lentes perdidos'),('Rescuing a Little Mouse','El rescate del pequeño ratoncito'),('Hard-Working Bee','La laboriosa abejita')]
import json,sys
nums=json.load(open('obr/toc.json')) if len(sys.argv)>1 else ['00']*5
L,Rt=560,2030; y=600
for (e,s_),n in zip(rows,nums):
    d.text((L,y),e,font=B(56),fill=INK); d.text((L,y+78),s_,font=R(50),fill=GR)
    n=str(n); d.text((Rt-d.textlength(n,font=B(56)),y),n,font=B(56),fill=INK); y+=188
pc.save('obr/p_contents.png')
for n in ['p_belongs','p_contents']: Image.open(f'obr/{n}.png').resize((W//3,H//3)).save(f'obr/{n}_s.png')
