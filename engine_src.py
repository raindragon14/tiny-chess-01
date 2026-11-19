import json as J,os as O,urllib.request as R
MATE,INF,BB,BH=30000,32000,52000,104000
SF="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FM=" PNBRQK  pnbrqk";PS="..nbrq";PW=(0,0,1,1,2,4,0);MV=(0,82,337,365,477,1025,0);EV=(0,94,281,297,512,936,0)
BO=(-17,-15,15,17);RO=(-16,-1,1,16);KO=BO+RO;OFF=(0,0,(-33,-31,-18,-14,14,18,31,33),BO,RO,KO,KO)
Q=[q for q in range(120)if not q&136];CM={116:12,119:14,112:13,4:3,7:11,0:7}
_PT='CFGF@BCD@BBB?AAB@BAA?BA@8>=A>@ECAEFEABCC@ABC@ABB??AA=@>?@A=??BCAACDCAACCABBCABCBACBA?@@@CCBECCEEACCC@@BC?A@A?@AA=@AA@?ABACCCBACABBCB@@AAA@AAAAAA@ABA??@A?BA?A@AA@CA@?@@?>@?>?@?>AA@=ACA?MKJJGGEECBAAAAAAAAAAAAAB<>???@?A?@AA@ABC@ABB?AAB>@@A>>@@@@@A@AAAAAAAAABBAABB@AAB?@AA@A@AAABBABAAAAAAAAAAAAAAAAAAA@AA@AAAABBCACCDABBDBCCDACCCA@BA???@????>@A@ABCBBCCBACCC@ABC@ABB?AAB>?@?'
PT=[[0]*128 for _ in range(16)];_ix=0
for _k in(0,1):
 for _p in range(1,7):
  for _r in range(_p<2,8-(_p<2)):
   for _f in range(4):
    _v=(MV,EV)[_k][_p]+ord(_PT[_ix])*16-1040;_ix+=1
    for _c in(_f,7-_f):_q=_r*16+_c;_w=_v if _k else _v<<16;PT[_p][_q]+=_w;PT[_p|8][_q^112]-=_w
class _A(Exception):pass
b=[0]*128;sd=cr=hm=nd=gp=bm=ph=ps=dw=0;ep=-1;ks=[116,4];rs=[];tt={};kl=[0]*99;ht={};bg=BH
def U(s):return(8-int(s[1]))*16+ord(s[0])-97
def M(m):return"".join(chr(97+(q&7))+str(8-(q>>4))for q in(m&127,m>>7&127))+PS[m>>14]*(m>16383)
def _rk():return bytes(b)+bytes((cr,ep&127,sd))
def lf(f):
 global b,sd,cr,ep,hm,ph,ps,rs
 b=[0]*128;ps=ph=0;t=f.split();q=0
 for c in t[0]:
  if c=="/":q+=8
  elif c>"9":
   p=FM.index(c);b[q]=p;ps+=PT[p][q];ph+=PW[p&7]
   if p&7==6:ks[p>>3]=q
   q+=1
  else:q+=int(c)
 sd=t[1]=="b";cr=sum(1<<i for i,k in enumerate("KQkq")if k in t[2]);ep=U(t[3])if t[3]!="-"else -1;hm=len(t)>4 and int(t[4]);rs=[_rk()]
def mk(m):
 global sd,cr,ep,hm,ph,ps
 f,t,pr=m&127,m>>7&127,m>>14;p=b[f];c=sd;cp=b[t];sn=(m,cp,cr,ep,hm,ps,ph,ks[c])
 hm=0 if cp or p&7==1 else hm+1;b[f]=0
 if cp:ph-=PW[cp&7]
 elif p&7==1 and t==ep:cs=t+16-32*c;ps-=PT[b[cs]][cs];b[cs]=0
 np=pr+8*c if pr else p;b[t]=np;ps+=PT[np][t]-PT[p][f]-PT[cp][t];ph+=PW[pr]
 if p&7==6:
  ks[c]=t
  if abs(f-t)==2:rf,rt=f-4+7*(t>f),f-1+2*(t>f);rp=b[rf];b[rf]=0;b[rt]=rp;ps+=PT[rp][rt]-PT[rp][rf]
 cr&=CM.get(f,15)&CM.get(t,15);ep=(f+t)>>1 if p&7==1 and abs(f-t)==32 else -1;sd^=1;rs.append(_rk());return sn
def um(sn):
 global sd,cr,ep,hm,ph,ps
 m,cp,cr,ep,hm,ps,ph,ok=sn;rs.pop();sd^=1;c=sd;f,t,pr=m&127,m>>7&127,m>>14;np=b[t];p=8*c+1 if pr else np
 if p&7==6:
  ks[c]=ok
  if abs(f-t)==2:rf,rt=f-4+7*(t>f),f-1+2*(t>f);b[rf]=b[rt];b[rt]=0
 b[f]=p;b[t]=cp
 if not cp and p&7==1 and t==ep:b[t+16-32*c]=9-8*c
def _atk(q,by):
 o=by<<3;p1=1+o;p2=2+o
 for d in((-17,-15)if by else(15,17)):
  if not(t:=q+d)&136 and b[t]==p1:return 1
 for d in OFF[2]:
  if not(t:=q+d)&136 and b[t]==p2:return 1
 p6=6+o;p5=5+o
 for d in KO:
  t=q+d
  if not t&136 and b[t]==p6:return 1
  sl=4+o-(d in BO)
  while not t&136:
   if p:=b[t]:
    if p==sl or p==p5:return 1
    break
   t+=d
 return 0
def ic(c=0):return _atk(ks[sd^c],sd^c^1)
def gm(c=0):
 mv=[];A=mv.append;col=sd;pts=(5,)if c else(5,2,4,3);fd=-16+32*col;sr_=6-5*col
 for q in Q:
  p=b[q]
  if p and p>>3==col:
   pt=p&7
   if pt==1:
    t=q+fd
    if not b[t]:
     if t<8 or t>111:mv.extend(q|t<<7|x<<14 for x in pts)
     elif not c:
      A(q|t<<7)
      if q>>4==sr_ and not b[t+fd]:A(q|(t+fd)<<7)
    for t in(q+fd-1,q+fd+1):
     if not t&136 and((b[t]and b[t]>>3!=col)or t==ep):
      if t<8 or t>111:mv.extend(q|t<<7|x<<14 for x in pts)
      else:A(q|t<<7)
   else:
    for d in OFF[pt]:
     t=q+d
     while not t&136:
      if bt:=b[t]:
       if bt>>3!=col:A(q|t<<7)
       break
      if not c:A(q|t<<7)
      if pt in(2,6):break
      t+=d
 k0=116-112*col
 if not c and ks[col]==k0:
  for cb,dr in((1+3*col,1),(2+6*col,-1)):
   if cr&cb and not any(b[k0+dr*i]for i in range(1,3+(dr<0)))and not any(_atk(k0+dr*i,col^1)for i in(0,1,2)):A(k0|(k0+2*dr)<<7)
 return mv
def lm():
 o=[]
 for m in gm(0):
  sn=mk(m)
  if not ic(1):o.append(m)
  um(sn)
 return o
def ev():
 p=min(ph,24);bp=(b.count(3)>1)-(b.count(11)>1);v=ps+32768;m_s=(v>>16)+30*bp;e_s=(v&65535)-32768+50*bp;sc=int((m_s*p+e_s*(24-p))/24)
 if p<7 and abs(e_s)>349:k=ks[e_s>0];sc+=(max(abs(2*(k>>4)-7),abs(2*(k&7)-7))*5+(14-abs((ks[0]>>4)-(ks[1]>>4))-abs((ks[0]&7)-(ks[1]&7)))*4)*((e_s>0)*2-1)
 if gp>149:sc+=max(-80,min(80,e_s//5))
 return(sc if sd<1 else -sc)+12
def _m(v,y):return v+y*(v>29000)-y*(v<-29000)
def _n(d,a,b_,y,pv,an=1,k=-1):
 global nd,bm,sd,ep;nd+=1
 if nd>=bg:raise _A
 if y and(hm>99 or(ph<3 and sum(1+9*((b[q]&7)in(1,4,5))for q in Q if 0<b[q]&7<6)<2)or rs[-1]in rs[-3::-2][:hm//2]):return dw
 if k<0:k=ic()
 d+=k and 0<d<8 and y<24;qs=d<1;se=ev()if not k else -INF
 if qs:
  if not k:
   if se>=b_:return b_
   a=max(a,se)
  elif d<-4:return se
 te=tt.get(rs[-1]);tm=0
 if te and not qs:
  td,tf,ts,tm=te
  if y*(not pv)*(td>=d):
   ts=_m(ts,-y)
   if tf<1 or(tf<2 and ts>=b_)or(tf>1 and ts<=a):return ts
 nn=y and not(pv or k or qs)
 if nn:
  if d<7 and se-75*d>=b_ and se<29000:return se
  if an and d>2 and se>=b_ and any(b[q]>>3==sd and 1<b[q]&7<6 for q in Q):
   oe=ep;sd^=1;ep=-1;rs.append(_rk());sc=-_n(d-4-(d>>2),-b_,-b_+1,y+1,0,0,-1);rs.pop();sd^=1;ep=oe
   if sc>=b_:return b_ if sc<29000 else sc
 if not qs and d>3 and not tm:d-=1
 oa=a;bm2=0;bs=a if qs else -INF;lg=0;k1=kl[y];tm2=(tm or bm*(y<1))*(not qs);qm=qs and not k;mv=gm(qm);hs=sd<<14;G=ht.get
 mv.sort(key=lambda m:-(9e7*(m==tm2)or(5e7+(b[m>>7&127]&7)*9-(b[m&127]&7)+(m>>14)*2 if b[m>>7&127]or m>16383 else(4e7 if m==k1 else G(hs|m,0)))))
 ll=3+d*d
 for m in mv:
  pr=m>>14;t=m>>7&127;cp=b[t];iq=not(cp or pr or(b[m&127]&7==1 and t==ep))
  if qm and(se+(v:=MV[cp&7]or 82)+900*(pr>0)+195<=a or(not pr and v+30<MV[b[m&127]&7]and _atk(t,sd^1))):continue
  pn=nn and iq and bs>-29000 and d<5
  if pn and lg>=ll:continue
  sn=mk(m)
  if ic(1):um(sn);continue
  gc=-1 if qs else ic(0)
  if pn and not gc and se+95*d<=a:um(sn);continue
  lg+=1
  if qs or lg==1:sc=-_n(d-1,-b_,-a,y+1,0 if qs else pv,1,gc)
  else:
   r=d>2 and lg>2 and iq*(not k)and max(0,min(d-2,1+(d>4)+(lg>5)-pv-(m==k1)-gc-(G(hs|m,0)>4000)))
   sc=-_n(d-1-r,-a-1,-a,y+1,0,1,gc)
   if sc>a and(r or pv*(sc<b_)):sc=-_n(d-1,-b_,-a,y+1,pv,1,gc)
  um(sn)
  if sc>bs:
   bs=sc;bm2=m
   if sc>a:
    a=sc
    if y<1 and not qs:bm=m
    if sc>=b_:
     if iq and not qs:kl[y]=m;hk=hs|m;ht[hk]=G(hk,0)+d*d
     break
 if not lg:return(-MATE+y)if k else(a if qs else dw)
 if qs:return a
 if y<1:bm=bm2
 tt[rs[-1]]=(d,0 if oa<bs<b_ else(1 if bs>=b_ else 2),_m(bs,y),bm2);return bs
def sr(ba=BB,bh=BH):
 global b,ks,rs,kl,nd,dw,bg,bm,sd,cr,ep,hm,ph,ps
 lg=lm();nd=0
 if len(lg)<2:return(lg[0]if lg else 0),0
 if len(tt)>5e5:tt.clear()
 if len(ht)>5e4:ht.clear()
 lg4=len(lg)>4;kl=[0]*99;re=ev();dw=-25*(re>40)+25*(re<-40);bg=min(bh,ba*(lg4+1)>>((gp>120)*lg4));bm=lg[0];bs=0;s0=(b[:],ks[:],rs[:],sd,cr,ep,hm,ps,ph)
 for d in range(1,64):
  if d>1 and nd>=bg>>1:break
  a,b_=(bs-35,bs+35)if d>3 and abs(bs)<29000 else(-INF,INF);bb4=bm
  try:
   sc=_n(d,a,b_,0,1,1,-1)
   if sc<=a or sc>=b_:sc=_n(d,-INF,INF,0,1,1,-1)
   bs=sc
  except _A:
   b,ks,rs,sd,cr,ep,hm,ps,ph=s0
   if b_<INF:bm=bb4
   return bm,bs
  if abs(bs)>29000:break
 return bm,bs
def main():
 global gp;u=O.getenv("MAKEFUN_ENV_URL","http://127.0.0.1:8077")
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
  g=d.get("game",0);tt.clear();ht.clear()
  while lu:=d.get("legal_moves"):
   lf(d.get("start_fen")or SF);mh=d.get("moves")or[]
   for z in mh:mk(U(z[:2])|U(z[2:4])<<7|PS.find(z[4:])<<14)
   gp=d.get("plies",len(mh))
   try:m,_=sr();ch=M(m)
   except:ch=lu[0]
   try:
    s,d=P("/move",{"game":g,"move":ch if ch in lu else lu[0]})
    if s>399 and(d:=P("/game",{})[1]).get("game")!=g:break
   except:
    try:P("/resign",{"game":g})
    except:0
    break
if __name__=="__main__":main()
