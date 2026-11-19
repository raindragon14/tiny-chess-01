import json as J,os as O,urllib.request as R
MATE,INF,BB,BH=30000,32000,37400,74800
PH=(0,0,1,1,2,4,0);SM=(0,1,3,3,5,9,0)
BO=(-17,-15,15,17);RO=(-16,-1,1,16);KO=BO+RO
OFF=(0,0,(-33,-31,-18,-14,14,18,31,33),BO,RO,KO,KO);CM={112:13,116:12,119:14,0:7,4:3,7:11}
Q=[q for q in range(120)if not q&8];FM=" PNBRQK  pnbrqk";PS="..nbrq";SF="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
class _A(Exception):pass
b=[0]*128;sd=cr=hm=nd=gp=re=bm=0;ep=-1;rs=[];tt={};kl=[0]*99;bg=BB
def U(s):return(8-int(s[1]))*16+ord(s[0])-97
def M(m,s=0):x=112*s;return"".join(chr(97+(q&7))+str(8-(q>>4))for q in((m&127)^x,(m>>7&127)^x))+PS[m>>14]*(m>16383)
def F():global b,cr,ep;b=[b[q^112]and b[q^112]^8 for q in range(128)];cr=(cr&3)<<2|cr>>2;ep^=112*(ep>-1)
def lf(f):
 global b,sd,cr,ep,hm,rs;b=[0]*128;t=f.split();q=0
 for c in t[0]:
  if c=="/":q+=8
  elif c>"9":b[q]=FM.index(c);q+=1
  else:q+=int(c)
 sd=t[1]=="b";cr=sum(1<<i for i,k in enumerate("KQkq")if k in t[2]);ep=U(t[3])if t[3]!="-"else -1;hm=len(t)>4 and int(t[4])
 if sd:F()
 rs=[(bytes(b),cr,ep)]
def mk(m):
 global cr,ep,hm;f,t,pr=m&127,m>>7&127,m>>14;p=b[f];sn=(b[:],cr,ep,hm);hm=0 if b[t]or p==1 else hm+1;ep_=-1
 if p==1 and t==ep:b[t+16]=0
 elif p==1 and f-t==32:ep_=f+t>>1
 b[f]=0;b[t]=pr or p
 if p==6 and abs(f-t)==2:r=f+3 if t>f else f-4;b[f+t>>1]=b[r];b[r]=0
 cr&=CM.get(f,15)&CM.get(t,15);ep=ep_;F();rs.append((bytes(b),cr,ep));return sn
def um(sn):global b,cr,ep,hm;b,cr,ep,hm=sn;rs.pop()
def _a(q,by=1):
 o=8*by
 if any(not q+d&136 and b[q+d]==pt+o for pt,ds in((1,(-17,-15)if by else(15,17)),(2,OFF[2]))for d in ds):return 1
 for d in KO:
  t=q+d
  if not t&136 and b[t]==6+o:return 1
  sl=4+o-(d in BO)
  while not t&136:
   p=b[t]
   if p:
    if p in(sl,5+o):return 1
    break
   t+=d
 return 0
def ic(c=0):return _a(b.index(6+8*c),c^1)
def gm(c=0):
 mv=[];pr=(5,)if c else(5,2,4,3)
 for q in Q:
  p=b[q]
  if 0<p<7:
   if p==1:
    t=q-16
    if not b[t]:
     if not c or t<8:mv.extend(q|t<<7|x<<14 for x in(pr if t<8 else(0,)))
     if not c and q>>4==6 and not b[q-32]:mv.append(q|q-32<<7)
    for t in(q-17,q-15):
     if not t&136 and(b[t]>8 or t==ep):mv.extend(q|t<<7|x<<14 for x in(pr if t<8 else(0,)))
   else:
    for d in OFF[p]:
     t=q+d
     while not t&136:
      if b[t]:
       if b[t]>8:mv.append(q|t<<7)
       break
      if not c:mv.append(q|t<<7)
      if p in(2,6):break
      t+=d
    if p==6 and not c and q==116:
     for bt,dr,ln in((1,1,2),(2,-1,3)):
      if cr&bt and not any(b[116+dr*i]for i in range(1,ln+1))and not any(_a(116+dr*i)for i in(0,1,2)):mv.append(116|(116+2*dr)<<7)
 return mv
def lm():
 o=[]
 for m in gm():
  sn=mk(m)
  if not ic(1):o.append(m)
  um(sn)
 return o
def _w():v=sum(SM[p&7]*(1 if p<8 else -1)for p in b if p)or re*(abs(re)>30);return -20*(v>0)+20*(v<0)
def ev():
 sc=ph=md=pa=kr=kc=0
 for q in Q:
  p=b[q]
  if p:
   pt=p&7;w=p<8;sg=w*2-1;sq=q if w else q^112;r,f=7-(sq>>4),sq&7;cn=min(r,7-r)+min(f,7-f)
   sc+=(SM[pt]*100+cn*6*(pt in(2,3,5)))*sg;ph+=PH[pt];md+=SM[pt]*sg;pa+=r*sg*(pt==1);kr-=r*sg*(pt==6);kc+=cn*sg*(pt==6)
 p=min(ph,24);return sc+int((pa*(336-8*p)+p*(10*kr-6*kc)+144*kc)/24)+(gp>149 and max(-60,min(60,md*18)))+10
def _m(v,s):return v+s*(v>29500)-s*(v<-29500)
def _n(d,a,b_,y,pv,ps=0):
 global nd,bm;nd+=1
 if nd>=bg:raise _A
 if y and(hm>99 or sum(1+9*(p&7 in(1,4,5))for p in b if 0<p&7<6)<2 or rs[-1]in rs[-3::-2][:hm//2]):return _w()
 k=ic();d+=k and 0<d<8 and y<16;qs=d<1
 if qs:
  sp=ev()
  if not k:
   if sp>=b_:return b_
   a=max(a,sp)
  elif d<-5:return sp
 te=tt.get(rs[-1]);tm=0
 if te and not qs:
  td,tf,ts,tm=te
  if y*(not pv)*(td>=d):
   ts=_m(ts,-y)
   if tf==0 or(tf==1 and ts>=b_)or(tf==2 and ts<=a):return ts
 oa=a;bm2=0;bs=a if qs else -INF;lg=0;k1=kl[y];qm=qs and not k;tm2=tm or bm*(y<1)
 mv=gm(qm);mv.sort(key=lambda m:-(9e6 if m==tm2 else(5e6+SM[b[m>>7&127]&7]*99-SM[b[m&127]]+(m>>14)if b[m>>7&127]or m>16383 else 4e6*(m==k1))))
 for m in mv:
  if qm and(m>>14)%5:continue
  iq=not(b[m>>7&127]or m>16383 or b[m&127]==1 and(m>>7&127)==ep);sn=mk(m)
  if ic(1):um(sn);continue
  lg+=1
  if qs or lg==1:sc=-_n(d-1,-b_,-a,y+1,0 if qs else pv)
  else:
   r=min(d-2,1+(d>4)+(lg>6)-pv)if y*iq*(not k)*(d>2)*(lg>2)else 0
   sc=-_n(d-1-r,-a-1,-a,y+1,0)
   if sc>a and(r or pv*(sc<b_)):sc=-_n(d-1,-b_,-a,y+1,pv)
  um(sn)
  if sc>bs:
   bs=sc;bm2=m
   if sc>a:
    a=sc
    if y<1 and sc>ps:bm=m
    if sc>=b_:
     if iq*(not qs):kl[y]=m
     break
 if not lg:return(-MATE+y)if k else(a if qs else _w())
 if qs:return a
 if y<1:bm=bm2
 tt[rs[-1]]=(d,0 if oa<bs<b_ else(1 if bs>=b_ else 2),_m(bs,y),bm2);return bs
def sr(bb=BB,bh=BH):
 global b,cr,ep,hm,rs,nd,re,bg,bm,kl;lg=lm();nd=0
 if len(lg)<2:return(lg or[0])[0],0
 if len(tt)>8e5:tt.clear()
 kl=[0]*99;re=ev();bg=min(bb*(1+(len(lg)<5)),bh);bm=lg[0];bs=0;ps=-INF;sn0=(b[:],cr,ep,hm,rs[:])
 for d in range(1,64):
  if d>1 and nd>bg*.45:break
  try:bs=_n(d,-INF,INF,0,1,ps)
  except _A:b,cr,ep,hm,rs=sn0;return bm,bs
  ps=bs
  if abs(bs)>29900:break
 return bm,bs
def main():
 global sd,gp;u=O.getenv("MAKEFUN_ENV_URL","http://127.0.0.1:8077")
 def P(p,d):
  for i in(0,1):
   try:
    with R.urlopen(R.Request(u+p,J.dumps(d).encode(),{"Content-Type":"application/json","Connection":"close"}),timeout=9)as r:return r.status,J.loads(r.read()or b"{}")
   except R.HTTPError as e:return e.code,{}
   except:
    if i:raise
 while 1:
  s,d=P("/game",{})
  if s>399 or d.get("status")=="done":break
  g=d.get("game",0)
  while d.get("status")not in("over","done"):
   lu=d.get("legal_moves")
   if not lu:break
   lf(d.get("start_fen")or SF);mh=d.get("moves")or[]
   for m in mh:x=112*sd;mk((U(m[:2])^x)|(U(m[2:4])^x)<<7|PS.find(m[4:])<<14);sd^=1
   gp=d.get("plies",len(mh))
   try:m,_=sr();ch=M(m,sd)
   except:ch=lu[0]
   try:
    s,d=P("/move",{"game":g,"move":ch if ch in lu else lu[0]})
    if s>399:
     _,d=P("/game",{})
     if d.get("game")!=g:break
   except:
    try:P("/resign",{"game":g})
    except:0
    break
if __name__=="__main__":main()
