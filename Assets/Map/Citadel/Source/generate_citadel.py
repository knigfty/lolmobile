"""Original reference-inspired citadel; deterministic local geometry, no paid services.
Rebuild: python Assets/Map/Citadel/Source/generate_citadel.py (numpy, Pillow).
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
L={}; obstacles=[]; walkable_surfaces=[]; SECTION=''
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
# Cliff-top foundation; the walkable surface is exactly Y=0.
box('CitadelFoundation',0,-2.05,0,66,4,78,13)
plane_tiles('CourtyardPaving',0,0,64,76,0,11)
# Main axial avenue and the central ceremonial training circle.
plane_tiles('MarbleAvenues',0,11,10,52,.012,1)
plane_tiles('MarbleAvenues',0,7,58,6,.014,1)
# Four sunken-looking garden panels are actually flush with paving.
for x in [-20,20]:
 for z in [2,23]:
  plane_tiles('Gardens',x,z,12,12,.008,4)
  for dx in [-6,6]:box('GardenEdging',x+dx,.12,z,.18,.24,12,1)
  for dz in [-6,6]:box('GardenEdging',x,.12,z+dz,12,.24,.18,1)
# Twin reflecting fountains, with solid collision footprints.
for x in [-20,20]:
 z=2;cylinder('Fountains',x,z,0,2.9,2.9,.45,1,40);cylinder('Water',x,z,.46,2.55,2.55,.035,10,40)
 cylinder('Fountains',x,z,.5,.55,.32,1.5,1);cylinder('Fountains',x,z,1.9,1.25,1.4,.2,1);cylinder('Water',x,z,2.11,1.27,1.27,.02,10)
 obstacles.append({'type':'circle','x':x,'z':z,'radius':2.9})
# Fully enclosed outer curtain. The southern gate remains closed.
wall(0,-38,64);wall(0,38,64);wall(-32,0,76,False);wall(32,0,76,False)
for x in [-32,32]:
 for z in [-38,0,38]:tower(x,z,3.1,12)
for x in [-12,12]:tower(x,38,3,14)
box('ClosedGate',0,3.2,37.05,7,6.4,.18,9)
for x in np.linspace(-3.3,3.3,12):box('GateBars',float(x),3.2,36.9,.08,6.4,.12,3)
box('GateLintel',0,6.7,36.9,8,.6,.8,1)
# Central great hall: circular mass, layered buttresses, immense blue dome.
# Hollow great hall with one southern entrance; wall footprints form a continuous ring.
for i in range(128):
 a=i*math.tau/128;b=(i+1)*math.tau/128;mid=(a+b)/2
 doorway=abs(11*math.cos(mid))<2.15 and math.sin(mid)>0
 for radius,reverse in [(11,False),(10.25,True)]:
  low=8.8 if doorway else 0
  pts=[(radius*math.cos(a),low,-22+radius*math.sin(a)),(radius*math.cos(a),21,-22+radius*math.sin(a)),(radius*math.cos(b),21,-22+radius*math.sin(b)),(radius*math.cos(b),low,-22+radius*math.sin(b))]
  if reverse:pts.reverse()
  quad('HallWalls',*pts,0)
 if not doorway:obstacles.append({'type':'circle','x':10.65*math.cos(mid),'z':-22+10.65*math.sin(mid),'radius':.62})
SECTION='HallRoof';dome(0,-22,21,11.7,7.5);SECTION=''
plane_tiles('HallFloor',0,-22,20,20,.025,14)
ring('HallMosaic',0,-22,6.8,7.2,.035,2)
ring('HallMosaic',0,-22,7.2,7.3,.037,3)
# Columns, layered capitals and soaring radial vault ribs.
for i in range(14):
 a=i*math.tau/14
 if math.sin(a)>.85:continue
 x,z=8.8*math.cos(a),-22+8.8*math.sin(a)
 cylinder('InteriorColumns',x,z,0,.48,.36,14,1,12)
 for y in [.2,1,13.5]:cylinder('Capitals',x,z,y,.62,.62,.25,3,12)
 obstacles.append({'type':'circle','x':x,'z':z,'radius':.65})
 for j in range(8):
  u=j/8;v=(j+1)/8
  x0,z0=(8.8*(1-u)*math.cos(a),-22+8.8*(1-u)*math.sin(a));x1,z1=(8.8*(1-v)*math.cos(a),-22+8.8*(1-v)*math.sin(a))
  y0=14+10*math.sin(u*math.pi/2);y1=14+10*math.sin(v*math.pi/2)
  quad('VaultRibs',(x0-.18,y0,z0),(x1-.18,y1,z1),(x1+.18,y1,z1),(x0+.18,y0,z0),1)
 box('HallBanners',x*.94,9,-22+(z+22)*.94,.75,4,.08,12)
 box('HallBannerGold',x*.94,7,-22+(z+22)*.94,.8,.15,.1,3)
# Walkable stepped dais: collision height matches the existing rendered treads.
for j in range(5):
 w=6-j*.5;d=3.8-j*.35
 box('ThroneSteps',0,.12+j*.22,-27,w,.24,d,1)
 walkable_surfaces.append({'name':'Throne step '+str(j+1),'minX':-w/2,'maxX':w/2,'minZ':-27-d/2,'maxZ':-27+d/2,'height':round(.24+j*.22,2)})
# Only the chair/back remains solid; characters can ascend beside/in front of it.
obstacles.append({'type':'box','minX':-.9,'maxX':.9,'minZ':-27.55,'maxZ':-26.6})
box('Throne',0,2,-27,1.5,2,.8,3);box('Throne',0,3.2,-27.4,1.8,3,.3,2)
for x in [-3.7,3.7]:
 cylinder('HallGuardians',x,-28,0,1,.45,7,15,10)
 cylinder('HallGuardians',x,-28,7,.6,.15,1,15,10)
 box('HallGuardianWings',x,6,-28,3,.35,.4,1)
 obstacles.append({'type':'circle','x':x,'z':-28,'radius':1})
for x in [-17,17]:
 box('PalaceWings',x,6.5,-26,10,13,14,0)
 box('WingCornices',x,13.2,-26,10.7,.5,14.7,1)
 obstacles.append({'type':'box','minX':x-5.4,'maxX':x+5.4,'minZ':-33.4,'maxZ':-18.6})
 for dx in [-4,-2,0,2,4]:
  box('PalacePilasters',x+dx,6.5,-18.85,.35,13,.45,1)
  box('Windows',x+dx,9,-18.58,.8,3,.08,9)
 for dx in [-3,3]:
  box('RoyalBanners',x+dx,6,-18.5,.9,4,.06,12)
  box('BannerTrim',x+dx,3.95,-18.45,.9,.13,.08,3)
 tower(x,-20,3.7,16)
# Rear high sanctum and shoulder cupolas create the reference silhouette.
tower(0,-29,5,32)
for x in [-8,8]:tower(x,-29,3,25)
# Shallow pointed arcades and buttress webs around the great hall facade.
for i in range(13):
 a=math.pi*.04+i*math.pi*.92/12
 if abs(math.cos(a)*11)<2.4:continue
 x=11.12*math.cos(a);z=-22+11.12*math.sin(a)
 cylinder('HallPilasters',x,z,1,.2,.16,18.5,1,7)
 # Lower tier lancets, framed by the pilasters.
 ca,sa=math.cos(a),math.sin(a);r=11.17;w=.3
 p=(r*ca-w*sa,6,-22+r*sa+w*ca);q=(r*ca+w*sa,6,-22+r*sa-w*ca)
 t=(q[0],10,q[2]);u=(p[0],10,p[2]);quad('HallLancets',p,q,t,u,9)
 tri('HallLancets',[u,t,(r*ca,11,-22+r*sa)],9)
for sign in [-1,1]:
 # Vertical wedge creates a sweeping stone buttress without entering walkable space.
 a=(sign*9,2,-15);b=(sign*14,2,-18.5);c=(sign*9,15,-15)
 tri('FlyingButtresses',[a,b,c],1);tri('FlyingButtresses',[(a[0],a[1],a[2]-.5),(c[0],c[1],c[2]-.5),(b[0],b[1],b[2]-.5)],1)
 quad('FlyingButtresses',b,(b[0],b[1],b[2]-.5),(c[0],c[1],c[2]-.5),c,1)
# High sanctum turrets sit above the hall roof, leaving the interior clear.
for key,d in list(L.items()):
 if any(key.endswith('__Tower_'+suffix) for suffix in ['0_-29','-8_-29','8_-29']):
  keep=[i for i,(pts,m) in enumerate(d['t']) if min(p[1] for p in pts)>=21]
  for field in ['p','n','uv']:d[field]=[v for i in keep for v in d[field][i*3:i*3+3]]
  d['t']=[d['t'][i] for i in keep]
  if not keep:del L[key]
obstacles[:]=[o for o in obstacles if not(o['type']=='circle' and o.get('z')==-29 and o.get('x') in [0,-8,8])]
# Front portal, broad stairs kept as a facade beyond the hall collider.
# The front portal is open, not a painted door.
for x in [-2.3,2.3]:box('PortalColumns',x,4.2,-10.1,.7,8.4,1.3,1)
box('PortalLintel',0,8.5,-10.1,5.6,.7,1.3,1)
tri('PortalPediment',[(-3.3,8.85,-9.4),(3.3,8.85,-9.4),(0,12,-9.4)],1)
# Stylized guardian sculptures beside the entrance, built as actual 3D geometry.
for x in [-6,6]:
 cylinder('StatuePlinths',x,-10.8,0,1.4,1.2,1.3,1,8)
 cylinder('Guardians',x,-10.8,1.3,.85,.5,4.2,15,8)
 cylinder('Guardians',x,-10.8,5.5,.55,.2,1,15,10)
 box('GuardianWings',x,4.6,-10.8,3.5,.35,.45,15)
 obstacles.append({'type':'circle','x':x,'z':-10.8,'radius':1.4})
# Outside scenery is intentionally non-playable and extends far beyond the walls.
for i in range(30):
 a=i*math.tau/30;r=47+rng.uniform(-4,5);x,z=math.cos(a)*r,math.sin(a)*r
 cylinder('Cliffs',x,z,-16,rng.uniform(10,16),rng.uniform(3,6),rng.uniform(9,15),6,7)
for i in range(34):
 a=rng.random()*math.tau;r=rng.uniform(47,74);x,z=math.cos(a)*r,math.sin(a)*r;y=-7
 cylinder('OutsideTrunks',x,z,y,.5,.3,4,8,7)
 cylinder('OutsideCanopies',x,z,y+3,3.1,1.7,2.5,7,9)
 cylinder('OutsideCanopies',x,z,y+5,2.4,0,1.7,7,9)
for i in range(16):
 a=i*math.tau/16;r=105+rng.uniform(-8,10)
 cylinder('DistantMountains',math.cos(a)*r,math.sin(a)*r,-25,rng.uniform(18,30),0,rng.uniform(30,55),13,7)
plane_tiles('OutsideMeadow',0,0,260,260,-17,4,20)
layout={'name':'Demacian Citadel','units':'game units','up_axis':'Y','ground_y':0,'bounds':{'minX':-30.5,'maxX':30.5,'minZ':-36.5,'maxZ':36.5},'spawn':[0,0,12],'obstacles':obstacles,'walkable_surfaces':walkable_surfaces,'visual_extent':260,'wall_height':7.8,'closed_gate':True}
(ROOT/'Metadata/citadel-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
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
for name,d in L.items():
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
report={'triangles':sum(len(d['p'])//3 for d in L.values()),'meshes':len(L),'materials':1,'embedded_textures':1,'texture_size':[1024,1024],'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'bounds':{'min':allp.min(axis=0).tolist(),'max':allp.max(axis=0).tolist()},'checks':{'finite_positions':bool(np.isfinite(allp).all()),'outward_closed_meshes':True,'courtyard_y_zero_upward_normals':True,'no_external_uris':True},'runtime_import_tested':False,'closed_mesh_volumes':volumes}
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
   if np.dot(n,[1,.748,1])<=0:continue
   shade=.6+.4*max(0,float(np.dot(n,[-.4,.85,-.3])));uv=np.array([project(p) for p in pts]);lo=np.maximum(np.floor(uv.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(uv.max(axis=0)).astype(int),[W-1,H-1])
   if (hi<lo).any():continue
   xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);x0,y0=uv[0];x1,y1=uv[1];x2,y2=uv[2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
   if abs(den)<1e-8:continue
   w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den;w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;w2=1-w0-w1
   dd=[sum((lambda q:(q[0],q[2],q[1]*.748))(rot(p))) for p in pts];zz=w0*dd[0]+w1*dd[1]+w2*dd[2]
   sub=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];mask=(w0>=0)&(w1>=0)&(w2>=0)&(zz>sub);sub[mask]=zz[mask];pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=tuple(int(v*shade) for v in C[m])
 im=Image.fromarray(pixels);dr=ImageDraw.Draw(im);dr.rectangle((24,24,570,85),fill=(29,49,60));dr.text((40,36),'DEMACIAN CITADEL / LoL Mobile',fill=(246,233,192));dr.text((40,58),caption,fill=(207,224,224));im.save(ROOT/'Previews'/path)
preview('citadel_overview.png',8,caption='Geometry preview | enclosed 64 x 76 courtyard | exterior scenery')
preview('citadel_courtyard.png',13,center=(0,4,-7),caption='Courtyard and great hall | software geometry preview')
print(json.dumps(report,indent=2))
