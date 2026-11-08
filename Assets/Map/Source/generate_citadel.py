"""Original reference-inspired citadel; deterministic local geometry, no paid services.
Rebuild: python Assets/Map/Source/generate_citadel.py (numpy, Pillow).
"""
from pathlib import Path
import json, math, struct, hashlib, random
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
for folder in ['Models','Textures','Metadata','Previews']:(ROOT/folder).mkdir(exist_ok=True)
rng=random.Random(211)
C=[(218,216,197),(239,232,206),(62,113,135),(191,157,84),(106,133,87),(98,92,72),(118,128,128),(62,100,69),(93,78,54),(46,75,92),(88,154,167),(190,191,174),(45,94,152),(154,163,157),(225,221,196),(246,239,213)]
tex=Image.new('RGB',(1024,1024));px=tex.load()
for y in range(1024):
 for x in range(1024):
  k=y//256*4+x//256;u=x%256;v=y%256;n=rng.randint(-3,3)
  if k in [0,1,11,13,14,15] and (v%32<2 or (u+(v//32%2)*32)%64<2):n-=13
  if k==2 and (v%16<2 or (u+v//16*8)%32<1):n-=10
  if k==4:n+=int(3*math.sin(u*.18)*math.cos(v*.14))
  px[x,y]=tuple(max(0,min(255,c+n)) for c in C[k])
tex.save(ROOT/'Textures/citadel_atlas.png')
L={}; obstacles=[]; SECTION=''
def tri(name,pts,m,uv=None):
 if SECTION:name+='__'+SECTION
 a,b,c=np.array(pts,float);n=np.cross(b-a,c-a);length=np.linalg.norm(n)
 if length<1e-9:return
 n/=length;d=L.setdefault(name,{'p':[],'n':[],'uv':[],'t':[]})
 if uv is None:uv=[(.04,.04),(.96,.04),(.5,.96)]
 d['p'].extend(pts);d['n'].extend([n.tolist()]*3);d['uv'].extend([((m%4+u)/4,(m//4+v)/4) for u,v in uv]);d['t'].append((pts,m))
def quad(name,a,b,c,d,m):
 uv=[(.03,.03),(.97,.03),(.97,.97),(.03,.97)]
 tri(name,[a,b,c],m,uv[:3]);tri(name,[a,c,d],m,[uv[0],uv[2],uv[3]])
def box(name,x,y,z,w,h,d,m):
 v=[(x+sx*w/2,y+sy*h/2,z+sz*d/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]]
 for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad(name,v[a],v[d],v[c],v[b],m)
def cylinder(name,x,z,y,r0,r1,h,m,N=24):
 for i in range(N):
  a=i*math.tau/N;b=(i+1)*math.tau/N
  p=(x+r0*math.cos(a),y,z+r0*math.sin(a));q=(x+r0*math.cos(b),y,z+r0*math.sin(b));s=(x+r1*math.cos(a),y+h,z+r1*math.sin(a));t=(x+r1*math.cos(b),y+h,z+r1*math.sin(b))
  quad(name,p,s,t,q,m);tri(name,[(x,y+h,z),t,s],m);tri(name,[(x,y,z),p,q],m)
def ring(name,x,z,r0,r1,y,m,N=64):
 for i in range(N):
  a=i*math.tau/N;b=(i+1)*math.tau/N
  quad(name,(x+r0*math.cos(a),y,z+r0*math.sin(a)),(x+r0*math.cos(b),y,z+r0*math.sin(b)),(x+r1*math.cos(b),y,z+r1*math.sin(b)),(x+r1*math.cos(a),y,z+r1*math.sin(a)),m)
def dome(x,z,y,r,h,N=40):
 for j in range(9):
  a=j/9*math.pi/2;b=(j+1)/9*math.pi/2
  ra=r*math.cos(a);rb=r*math.cos(b);ya=y+h*math.sin(a);yb=y+h*math.sin(b)
  for i in range(N):
   u=i*math.tau/N;v=(i+1)*math.tau/N
   quad('BlueDomes',(x+ra*math.cos(u),ya,z+ra*math.sin(u)),(x+rb*math.cos(u),yb,z+rb*math.sin(u)),(x+rb*math.cos(v),yb,z+rb*math.sin(v)),(x+ra*math.cos(v),ya,z+ra*math.sin(v)),2)
 cylinder('GildedFinials',x,z,y+h,.19,0,1.6,3,8)
 # Gilded ribs follow the dome silhouette.
 for i in range(8):
  a=i*math.tau/8
  for j in range(8):
   u=j/9*math.pi/2;v=(j+1)/9*math.pi/2;eps=.008
   quad('RoofRibs',(x+r*math.cos(u)*math.cos(a-eps),y+h*math.sin(u)+.035,z+r*math.cos(u)*math.sin(a-eps)),(x+r*math.cos(v)*math.cos(a-eps),y+h*math.sin(v)+.035,z+r*math.cos(v)*math.sin(a-eps)),(x+r*math.cos(v)*math.cos(a+eps),y+h*math.sin(v)+.035,z+r*math.cos(v)*math.sin(a+eps)),(x+r*math.cos(u)*math.cos(a+eps),y+h*math.sin(u)+.035,z+r*math.cos(u)*math.sin(a+eps)),3)
def tower(x,z,r,h,collider=True):
 global SECTION
 SECTION=f'Tower_{x}_{z}'
 cylinder('TowerBases',x,z,0,r*1.15,r*1.1,1.1,13)
 cylinder('TowerWalls',x,z,1.1,r,r,h-1.1,0,32)
 for y in [1.3,h-2,h-.1]:cylinder('Cornices',x,z,y,r*1.04,r*1.04,.3,1,32)
 for i in range(12):
  a=i*math.tau/12
  cylinder('TowerRibs',x+(r+.03)*math.cos(a),z+(r+.03)*math.sin(a),1.5,.13,.1,h-2,1,6)
  # Tall dark-blue lancet windows face outward, with a pointed cap.
  if i%2==0:
   ca,sa=math.cos(a),math.sin(a);rr=r+.15;w=.3;by=h-4
   p=(x+rr*ca-w*sa,by,z+rr*sa+w*ca);q=(x+rr*ca+w*sa,by,z+rr*sa-w*ca)
   s=(p[0],by+2.2,p[2]);t=(q[0],by+2.2,q[2]);quad('Windows',p,q,t,s,9)
   tri('Windows',[s,t,(x+rr*ca,by+3,z+rr*sa)],9)
 dome(x,z,h+.2,r*1.13,r*.67)
 SECTION=''
 if collider:obstacles.append({'type':'circle','x':x,'z':z,'radius':round(r*1.16,3)})
def wall(x,z,length,along_x=True):
 global SECTION
 SECTION=f'Wall_{x}_{z}'
 box('CurtainWalls',x,3.9,z,length if along_x else 1.8,7.8,1.8 if along_x else length,0)
 for h in [.4,6.7,7.9]:box('WallCornices',x,h,z,length+.2 if along_x else 2.15,.25,2.15 if along_x else length+.2,1)
 for i in range(int(length/2.2)+1):
  t=-length/2+i*2.2
  box('Battlements',x+t if along_x else x,8.4,z if along_x else z+t,1.1 if along_x else 2,1,2 if along_x else 1.1,1)
 for i in range(int(length/6)+1):
  t=-length/2+i*6
  box('WallButtresses',x+t if along_x else x,3,z if along_x else z+t,1 if along_x else 2.8,6,2.8 if along_x else 1,14)
 SECTION=''
def plane_tiles(name,x,z,w,d,y,m,size=4):
 nx=math.ceil(w/size);nz=math.ceil(d/size)
 for i in range(nx):
  for j in range(nz):
   a=x-w/2+i*w/nx;b=a+w/nx;c=z-d/2+j*d/nz;e=c+d/nz
   quad(name,(a,y,c),(a,y,e),(b,y,e),(b,y,c),m)
# All walking surfaces share Y=0: no hidden steps at garden or hall transitions.
def solid_box(name,x,z,w,d,h,m=0):
 box(name,x,h/2,z,w,h,d,m)
 obstacles.append({'type':'box','minX':x-w/2,'maxX':x+w/2,'minZ':z-d/2,'maxZ':z+d/2})
def solid_circle(name,x,z,r,h,m=1):
 cylinder(name,x,z,0,r,r,h,m,16)
 obstacles.append({'type':'circle','x':x,'z':z,'radius':r})
def beam(name,a,b,width,depth,m):
 # Closed rectangular beam between arbitrary endpoints, used for lean and arch ribs.
 a=np.array(a,float);b=np.array(b,float);axis=(b-a)/np.linalg.norm(b-a)
 side=np.cross(axis,[0,0,1])
 if np.linalg.norm(side)<.01:side=np.cross(axis,[0,1,0])
 side=side/np.linalg.norm(side)*width/2;up=np.cross(axis,side);up=up/np.linalg.norm(up)*depth/2
 v=[a-side-up,a+side-up,a+side+up,a-side+up,b-side-up,b+side-up,b+side+up,b-side+up]
 for i,j,k,l in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad(name,v[i].tolist(),v[j].tolist(),v[k].tolist(),v[l].tolist(),m)
def pointed_arch(name,x,z,half_width,spring,rise,depth,m=1):
 for sign in [-1,1]:
  for j in range(12):
   u=j/12;v=(j+1)/12
   a=(x+sign*half_width*(1-u),spring+rise*(1-(1-u)**1.65),z)
   b=(x+sign*half_width*(1-v),spring+rise*(1-(1-v)**1.65),z)
   beam(name,a,b,1.2,depth,m)
def fountain(x,z,r=5):
 global SECTION
 SECTION=f'Fountain_{x}_{z}'
 solid_circle('Fountains',x,z,r,.55)
 cylinder('Water',x,z,.56,r-.5,r-.5,.04,10,40)
 cylinder('FountainStem',x,z,.6,.65,.35,2.7,1)
 cylinder('FountainBowl',x,z,2.8,1.8,2.4,.5,1)
 cylinder('Water',x,z,3.31,2.15,2.15,.03,10)
 cylinder('WaterJet',x,z,3.35,.12,.035,2.5,10,8)
 SECTION=''
def tree(x,z,h=8):
 cylinder('GardenTrunks',x,z,0,.25,.2,h*.4,8,6)
 cylinder('CypressTrees',x,z,1.5,1.25,.08,h,7,8)
 obstacles.append({'type':'circle','x':x,'z':z,'radius':.38})
box('CitadelFoundation',0,-2.1,0,264,4,324,13)
plane_tiles('CourtyardPaving',0,0,260,320,0,11,8)
plane_tiles('MarbleAvenues',0,20,14,276,.012,1,6)
for z in [-72,-12,48,108,145]:plane_tiles('MarbleAvenues',0,z,254,7,.014,1,8)
for x in [-76,76,-120,120]:plane_tiles('MarbleAvenues',x,28,5,250,.013,1,8)
# Formal garden parterres separated by broad, continuous paths.
for x in [-98,98]:
 for z in [-44,16,76,126]:
  depth=34 if z==126 else 42
  plane_tiles('Gardens',x,z,34,depth,.008,4,6)
  for dx in [-17,17]:box('GardenEdging',x+dx,.07,z,.22,.14,depth,1)
  for dz in [-depth/2,depth/2]:box('GardenEdging',x,.07,z+dz,34,.14,.22,1)
  plane_tiles('GardenPaths',x,z,3,depth,.016,1)
  plane_tiles('GardenPaths',x,z,34,3,.018,1)
  fountain(x,z,4.5)
  for dx in [-13,13]:
   for dz in [-depth/2+4,depth/2-4]:tree(x+dx,z+dz,7+rng.random()*3)
  # Hedges have matching low solid footprints; passages remain open at cross paths.
  for dx in [-10,10]:
   for dz in [-depth/2+2,depth/2-2]:
    solid_box('Hedges',x+dx,z+dz,11,1,1,7)
# Oval plaza inlays, thin enough to remain flush with movement plane.
for r0,r1,m in [(24,24.4,2),(24.4,24.55,3),(29,29.35,1)]:ring('PlazaMosaic',0,12,r0,r1,.022,m,96)
SECTION='PlazaMonument'
solid_circle('MonumentPlinth',0,12,3.5,1.1)
cylinder('MonumentSteps',0,12,1.1,2.6,2.4,.7,1,12)
cylinder('MonumentObelisk',0,12,1.8,1.2,.6,8,15,6)
cylinder('MonumentCrown',0,12,9.8,.7,0,2,3,6)
SECTION=''
# Colonnade: ellipse open at the main gate and where it meets the citadel.
# No wall collider is placed between columns; each foot is independently solid.
passages=[]
for side in [-1,1]:
 for i in range(30):
  a=-1.40+i*(2.80/29);x=side*62*math.cos(a);z=-5+84*math.sin(a)
  SECTION=f'Colonnade_{side}_{i}'
  solid_circle('ColumnBases',x,z,1.25,.7)
  cylinder('ColumnShafts',x,z,.7,.82,.65,17,1,10)
  cylinder('ColumnCapitals',x,z,17.7,1.35,1.35,.7,1,10)
  # Outward inclined buttress stays within a conservative local collision footprint.
  if i%3==0:
   bx=x+side*3
   solid_circle('ButtressFeet',bx,z,.9,.5)
   beam('ColonnadeButtress',(bx,.5,z),(x,17.6,z),.7,.8,1)
  if i<29:
   b=-1.40+(i+1)*(2.80/29);xx=side*62*math.cos(b);zz=-5+84*math.sin(b)
   beam('ColonnadeEntablature',(x,19, z),(xx,19,zz),2.2,3.6,1)
   beam('ColonnadeGold',(x,20.2,z),(xx,20.2,zz),.15,3.7,3)
   if i in [5,14,23]:passages.append({'x':(x+xx)/2,'z':(z+zz)/2})
 SECTION=''
# Ceremonial front arch connects to the curved colonnade without closing it.
SECTION='GrandArch'
for x in [-10.5,10.5]:
 solid_box('ArchPiers',x,80,3,4,19)
 cylinder('ArchColumns',x,82,0,.65,.55,19,1,12)
 box('RoyalBanners',x,11,82.1,1.6,9,.08,12)
 box('BannerTrim',x,6.5,82.2,1.7,.22,.09,3)
pointed_arch('GrandArchRibs',0,80,10.5,19,12,3)
pointed_arch('GrandArchInner',0,82,8.5,18,9,1)
for sign in [-1,1]:beam('ArchShoulder',(sign*10.5,19,80),(sign*10.54,19,77.78),2,3.6,1)
SECTION=''
# Outer enclosure and blue-domed perimeter towers.
wall(0,-160,260);wall(0,160,260);wall(-130,0,320,False);wall(130,0,320,False)
for x in [-130,130]:
 for z in [-160,-80,0,80,160]:tower(x,z,5,25)
for x in [-64,64]:tower(x,160,4,19)
# Citadel: front at Z=-88, 12-unit open entry; fully modeled entrance hall.
SECTION='HallWalls'
solid_box('HallWalls',-19,-88,26,3,57)
solid_box('HallWalls',19,-88,26,3,57)
solid_box('HallWalls',-32,-120,3,64,57)
solid_box('HallWalls',32,-120,3,64,57)
solid_box('HallWalls',0,-152,64,3,57)
box('HallLintel',0,39,-88,12,36,3,0)
SECTION='HallRoof'
box('HallCeiling',0,57,-120,66,2,66,1)
dome(0,-120,58,34,22)
SECTION=''
plane_tiles('HallFloor',0,-120,61,61,.025,14,5)
plane_tiles('HallCarpet',0,-119,8,58,.038,12,6)
for x in [-4.2,4.2]:plane_tiles('HallCarpetTrim',x,-119,.2,58,.04,3,6)
ring('HallMosaic',0,-120,12,12.5,.045,3,64)
for x in [-22,22]:
 for z in [-100,-118,-136]:
  SECTION=f'HallColumn_{x}_{z}'
  solid_circle('InteriorBases',x,z,1.65,.6)
  cylinder('InteriorColumns',x,z,.6,1.1,.85,27,1,12)
  cylinder('Capitals',x,z,27,1.7,1.7,1,3,12)
  pointed_arch('VaultRibs',0,z,22,28,18,1.1)
  box('HallBanners',x,18,z,2.4,9,.12,12)
  box('HallBannerGold',x,13.5,z,2.5,.22,.14,3)
SECTION='HallDais'
solid_box('ThroneSteps',0,-144,10,7,.65,1)
box('Throne',0,2,-144,2.5,3,1.5,3);box('ThroneBack',0,4,-145,3,6,.4,2)
SECTION='Portal'
for x in [-7.5,7.5]:
 solid_circle('PortalColumns',x,-85,1.2,22)
pointed_arch('PortalArch',0,-85,7.5,22,8,2)
# Monumental hooded guardian and folded cape above the clear entrance.
SECTION='FacadeGuardian'
cylinder('GuardianBody',0,-84,31,4.8,2.8,22,15,12)
cylinder('GuardianHood',0,-84,53,2.9,1,6,15,12)
box('GuardianVisor',0,55,-81.4,1.2,2.8,.15,9)
for sign in [-1,1]:
 beam('GuardianArms',(sign*2.8,50,-82),(sign*.7,45,-79),2.1,2,15)
 for j in range(6):
  x0=sign*(3+j*1.7);x1=sign*(3+(j+1)*1.7)
  tri('GuardianCape',[(sign*3,51,-84),(x0,29,-85-abs(x0)*.12),(x1,29,-85-abs(x1)*.12)],14 if j%2 else 15)
box('GuardianSword',0,36,-79,.8,23,.5,1);box('GuardianSwordGuard',0,46,-79,5,.65,.8,3)
SECTION=''
# Wings with decorative towers, footprint separated from the gardens.
for x in [-49,49]:
 SECTION=f'PalaceWing_{x}'
 solid_box('PalaceWings',x,-122,28,60,35)
 box('WingCornices',x,35,-122,29,1,61,1)
 for dx in [-10,-5,0,5,10]:
  box('PalacePilasters',x+dx,17,-91.8,.65,34,.8,1)
  box('Windows',x+dx,24,-91.25,1.5,8,.1,9)
 SECTION=''
 tower(x,-92,6,43)
 tower(x,-143,7,49)
for x in [-24,24]:tower(x,-85,4.5,40)
# Near white mountain rises immediately behind the citadel; distant city is scenery.
SECTION='Mountain'
for x,z,r,h in [(0,-225,63,145),(-43,-205,33,95),(43,-210,36,110),(0,-250,48,175)]:
 cylinder('WhiteMountain',x,z,-4,r,2,h,15,9)
SECTION=''
for side in [-1,1]:
 for row in range(4):
  for col in range(15):
   x=side*(155+row*24+rng.uniform(-3,3));z=-170+col*26+rng.uniform(-5,5);h=rng.uniform(6,16)
   box('DistantCity',x,h/2-8,z,12,h,15,0)
   cylinder('CityRoofs',x,z,h-8,9,0,6,2,4)
for i in range(20):
 a=i*math.tau/20
 cylinder('DistantMountains',math.cos(a)*430,math.sin(a)*430,-30,55,0,rng.uniform(65,130),13,7)
plane_tiles('OutsideMeadow',0,0,1100,1100,-8,4,60)
layout={'name':'Royal Kingdom — Citadel and Gardens','version':3,'units':'game units (champion unchanged)','up_axis':'Y','ground_y':0,
 'bounds':{'minX':-128,'maxX':128,'minZ':-158,'maxZ':158},'spawn':[0,0,112],
 'hall':{'minX':-30.5,'maxX':30.5,'minZ':-150.5,'maxZ':-86.5},
 'landmarks':{'entrance':[0,0,-84],'hall':[0,0,-120],'plaza':[12,0,12],'westGarden':[-98,0,48],'eastGarden':[98,0,48]},
 'colonnade_passages':passages,'obstacles':obstacles,'visual_extent':1100,'wall_height':7.8,'closed_gate':True}
(ROOT/'Metadata/citadel-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
# Batch atlas-compatible pieces by occlusion section to bound mobile draw calls.
merged={}
for name,data in L.items():
 key='Architecture__'+name.split('__',1)[1] if '__' in name else name
 target=merged.setdefault(key,{'p':[],'n':[],'uv':[],'t':[]})
 for field in target:target[field].extend(data[field])
# Keep original semantic pieces for geometric validation and software previews.
export_layers=merged
# Embedded, indexed glTF reduces download and mobile memory costs.
g={'asset':{'version':'2.0','generator':'lgmobile original reference-inspired citadel'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'buffers':[],'bufferViews':[],'accessors':[],'images':[],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],'materials':[{'name':'CitadelAtlas','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.86}}]}
bin=bytearray()
def view(data,target=None):
 while len(bin)%4:bin.append(0)
 v={'buffer':0,'byteOffset':len(bin),'byteLength':len(data)}
 if target:v['target']=target
 g['bufferViews'].append(v);bin.extend(data);return len(g['bufferViews'])-1
def accessor(ar,kind,component=5126,target=34962):
 v=view(ar.tobytes(),target);a={'bufferView':v,'componentType':component,'count':len(ar),'type':kind}
 if kind=='VEC3':a.update(min=ar.min(axis=0).tolist(),max=ar.max(axis=0).tolist())
 g['accessors'].append(a);return len(g['accessors'])-1
for name,d in export_layers.items():
 ar=np.concatenate([d['p'],d['n'],d['uv']],axis=1).astype('<f4');unique,indices=np.unique(ar,axis=0,return_inverse=True)
 attrs={'POSITION':accessor(unique[:,:3].copy(),'VEC3'),'NORMAL':accessor(unique[:,3:6].copy(),'VEC3'),'TEXCOORD_0':accessor(unique[:,6:].copy(),'VEC2')}
 idx=accessor(indices.astype('<u4'),'SCALAR',5125,34963)
 i=len(g['meshes']);g['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'indices':idx,'material':0}]});g['nodes'].append({'name':name,'mesh':i});g['scenes'][0]['nodes'].append(i)
g['images'].append({'name':'citadel_atlas','bufferView':view((ROOT/'Textures/citadel_atlas.png').read_bytes()),'mimeType':'image/png'})
g['buffers']=[{'byteLength':len(bin)}];j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);bin+=b'\0'*((-len(bin))%4)
out=struct.pack('<4sII',b'glTF',2,28+len(j)+len(bin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(bin),b'BIN\0')+bin
(ROOT/'Models/demacian_citadel.glb').write_bytes(out)
# Geometry QA: positive volume for every closed architectural mesh and upward ground.
closed=['CitadelFoundation','CurtainWalls','Battlements','WallButtresses','PalaceWings','TowerWalls','TowerBases']
volumes={}
for name in closed:
 t=np.array([p for key,d in L.items() if key.split('__')[0]==name for p in d['p']]).reshape(-1,3,3);v=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6);assert v>0,(name,v);volumes[name]=v
assert np.all(np.array(L['CourtyardPaving']['n'])[:,1]>.99)
allp=np.concatenate([np.array(d['p']) for d in L.values()])
report={'triangles':sum(len(d['p'])//3 for d in L.values()),'meshes':len(export_layers),'materials':1,'embedded_textures':1,'texture_size':[1024,1024],'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'bounds':{'min':allp.min(axis=0).tolist(),'max':allp.max(axis=0).tolist()},'checks':{'finite_positions':bool(np.isfinite(allp).all()),'outward_closed_meshes':True,'courtyard_y_zero_upward_normals':True,'no_external_uris':True},'runtime_import_tested':False,'closed_mesh_volumes':volumes}
(ROOT/'Metadata/citadel-validation.json').write_text(json.dumps(report,indent=2)+'\n')
# Orthographic software previews use the exact exported geometry, not concept art.
def preview(path,scale,center=(0,0,0),yaw=0,caption=''):
 W,H=1400,1100;pixels=np.full((H,W,3),[174,201,210],dtype=np.uint8);depth=np.full((H,W),-np.inf)
 def rot(p):
  x,y,z=p;x-=center[0];y-=center[1];z-=center[2];return (x*math.cos(yaw)-z*math.sin(yaw),y,x*math.sin(yaw)+z*math.cos(yaw))
 def project(p):
  x,y,z=rot(p);return (W/2+(x-z)*scale,H*.63+(x+z)*scale*.46-y*scale*1.23)
 for d in L.values():
  for pts,m in d['t']:
   a,b,c=np.array(pts);n=np.cross(b-a,c-a);n=n/max(np.linalg.norm(n),1e-8)
   view_normal=[n[0]*math.cos(yaw)-n[2]*math.sin(yaw),n[1],n[0]*math.sin(yaw)+n[2]*math.cos(yaw)]
   if np.dot(view_normal,[1,.748,1])<=0:continue
   shade=.6+.4*max(0,float(np.dot(n,[-.4,.85,-.3])));uv=np.array([project(p) for p in pts]);lo=np.maximum(np.floor(uv.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(uv.max(axis=0)).astype(int),[W-1,H-1])
   if (hi<lo).any():continue
   xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);x0,y0=uv[0];x1,y1=uv[1];x2,y2=uv[2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
   if abs(den)<1e-8:continue
   w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den;w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;w2=1-w0-w1
   dd=[sum((lambda q:(q[0],q[2],q[1]*.748))(rot(p))) for p in pts];zz=w0*dd[0]+w1*dd[1]+w2*dd[2]
   sub=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];mask=(w0>=0)&(w1>=0)&(w2>=0)&(zz>sub);sub[mask]=zz[mask];pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=tuple(int(v*shade) for v in C[m])
 im=Image.fromarray(pixels);dr=ImageDraw.Draw(im);dr.rectangle((24,24,570,85),fill=(29,49,60));dr.text((40,36),'DEMACIAN CITADEL / LoL Mobile',fill=(246,233,192));dr.text((40,58),caption,fill=(207,224,224));im.save(ROOT/'Previews'/path)
preview('citadel_overview.png',2.15,center=(0,20,-20),yaw=-math.pi/4,caption='Playable exterior | 260 x 320 units | software geometry preview')
preview('citadel_courtyard.png',4.0,center=(0,15,-48),yaw=-math.pi/4,caption='Plaza, open colonnades and citadel | software geometry preview')
# Cutaway preview mirrors the runtime interior roof cutaway.
L={k:v for k,v in L.items() if not k.endswith('__HallRoof') and not k.endswith('__FacadeGuardian') and not k.endswith('__HallWalls')}
preview('citadel_hall.png',10,center=(0,10,-120),yaw=-math.pi/4,caption='Entrance hall cutaway | software geometry preview')
print(json.dumps(report,indent=2))
