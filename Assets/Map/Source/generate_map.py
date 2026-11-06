"""Deterministic original geometry and textures. Requires Python, numpy and Pillow."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import json, struct, math, random, hashlib
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(71)
colors=[(76,106,66),(141,148,130),(159,143,104),(85,94,85),(96,69,43),(32,77,56),(48,98,64),(173,148,83)]
tex=Image.new('RGB',(512,512)); px=tex.load()
for y in range(512):
 for x in range(512):
  k=(y//256)*4+x//128; c=colors[k]; n=rng.randrange(-9,10)
  if k in (1,2,3) and (x%64<2 or (y+(x//64%2)*24)%48<2): n-=24
  if k==4 and x%17<3:n-=16
  px[x,y]=tuple(max(0,min(255,v+n)) for v in c)
tex.save(ROOT/'Textures/forest_courtyard_basecolor.png')
# Each layer is a single mesh. Flat normals retain the deliberately faceted style.
layers={}
def tri(name,pts,mat):
 a,b,c=np.array(pts,float); n=np.cross(b-a,c-a); l=np.linalg.norm(n)
 if l<1e-10:return
 n/=l; data=layers.setdefault(name,{'p':[],'n':[],'uv':[],'t':[]})
 data['t'].append((pts,mat))
 # Texture coordinates remain inset in each atlas swatch.
 uv=[((mat%4+.08)/4,(mat//4+.12)/2),((mat%4+.92)/4,(mat//4+.12)/2),((mat%4+.5)/4,(mat//4+.88)/2)]
 data['p'].extend(pts);data['n'].extend([n.tolist()]*3);data['uv'].extend(uv)
def quad(name,a,b,c,d,m):tri(name,[a,b,c],m);tri(name,[a,c,d],m)
def box(name,x,y,z,w,h,d,m):
 v=[(x+sx*w/2,y+sy*h/2,z+sz*d/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]]
 for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad(name,v[a],v[b],v[c],v[d],m)
def frustum(name,x,z,y,r0,r1,h,m,N=10):
 for i in range(N):
  a=i*math.tau/N;b=(i+1)*math.tau/N
  p=(x+r0*math.cos(a),y,z+r0*math.sin(a));q=(x+r0*math.cos(b),y,z+r0*math.sin(b));s=(x+r1*math.cos(a),y+h,z+r1*math.sin(a));t=(x+r1*math.cos(b),y+h,z+r1*math.sin(b))
  quad(name,p,s,t,q,m);tri(name,[(x,y+h,z),t,s],m);tri(name,[(x,y,z),p,q],m)
def ring(name,r0,r1,y,m,N=96):
 for i in range(N):
  a=i*math.tau/N;b=(i+1)*math.tau/N
  quad(name,(r0*math.cos(a),y,r0*math.sin(a)),(r0*math.cos(b),y,r0*math.sin(b)),(r1*math.cos(b),y,r1*math.sin(b)),(r1*math.cos(a),y,r1*math.sin(a)),m)
box('Terrain',0,-.4,0,34,.8,34,0)
# Walkable surfaces are at y=0, with small decorative offsets to avoid z fighting.
frustum('Courtyard',0,0,-.22,5.2,5.2,.23,1,64)
ring('GoldInlay',4.75,4.84,.014,7);ring('BoundaryInlay',11.65,11.85,.012,2)
for a in [0,math.pi/2,math.pi,math.pi*1.5]:
 x,z=math.cos(a)*8.6,math.sin(a)*8.6
 box('Paths',x,.008,z,7.4 if abs(x)>1 else 2.8,.012,2.8 if abs(x)>1 else 7.4,2)
for i in range(8):
 a=i*math.tau/8
 box('CourtMarkers',math.cos(a)*4.1,.022,math.sin(a)*4.1,.28,.022,.28,7)
# All blocking scenery sits outside the existing playable boundary.
for i in range(40):
 a=i*math.tau/40
 if i%10 in (0,1,9):continue
 r=14+rng.uniform(-.6,.6);x,z=math.cos(a)*r,math.sin(a)*r
 h=rng.uniform(.7,1.5)
 frustum('Rocks',x,z,0,rng.uniform(.65,1.1),.35,h,3,7)
 if i%2==0:
  x,z=x*1.08,z*1.08
  frustum('TreeTrunks',x,z,0,.22,.15,2.1,4,7)
  for j in range(3):frustum('TreeCanopies',x,z,1.2+j*.7,1.25-j*.24,0,1.8,5+i%2,7)
for x in [-9.8,9.8]:
 for z in [-9.8,9.8]:
  box('Ruins',x,.2,z,1.65,.4,1.65,1)
  box('Ruins',x,1.35,z,.85,2.3,.85,1)
  box('Ruins',x,2.55,z,1.2,.2,1.2,7)
# GLB 2.0 writer: float accessors + embedded PNG, no external URIs.
g={'asset':{'version':'2.0','generator':'lgmobile original procedural courtyard'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'buffers':[],'bufferViews':[],'accessors':[],'images':[],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],'materials':[{'name':'CourtyardAtlas','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.95}}]}
bin=bytearray()
def view(data,target=None):
 while len(bin)%4:bin.append(0)
 v={'buffer':0,'byteOffset':len(bin),'byteLength':len(data)}
 if target:v['target']=target
 g['bufferViews'].append(v);bin.extend(data);return len(g['bufferViews'])-1
def acc(values,size):
 ar=np.array(values,dtype='<f4');v=view(ar.tobytes(),34962)
 g['accessors'].append({'bufferView':v,'componentType':5126,'count':len(ar),'type':{2:'VEC2',3:'VEC3'}[size],'min':ar.min(axis=0).tolist(),'max':ar.max(axis=0).tolist()});return len(g['accessors'])-1
for name,d in layers.items():
 attrs={'POSITION':acc(d['p'],3),'NORMAL':acc(d['n'],3),'TEXCOORD_0':acc(d['uv'],2)}
 i=len(g['meshes']);g['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'material':0,'mode':4}]});g['nodes'].append({'name':name,'mesh':i});g['scenes'][0]['nodes'].append(i)
g['images'].append({'name':'forest_courtyard_basecolor','bufferView':view((ROOT/'Textures/forest_courtyard_basecolor.png').read_bytes()),'mimeType':'image/png'})
g['buffers']=[{'byteLength':len(bin)}]
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);bin+=b'\0'*((-len(bin))%4)
out=struct.pack('<4sII',b'glTF',2,28+len(j)+len(bin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(bin),b'BIN\0')+bin
(ROOT/'Models/forest_courtyard.glb').write_bytes(out)
# Orthographic shaded preview from the same geometry (software raster illustration).
im=Image.new('RGB',(1200,1000),(20,31,35));draw=ImageDraw.Draw(im)
def project(p):
 x,y,z=p;return (600+(x-z)*21,470+(x+z)*10-y*34)
pixels=np.array(im); depth=np.full((1000,1200),-np.inf)
for pts,m in [t for d in layers.values() for t in d['t']]:
 a,b,c=np.array(pts);n=np.cross(b-a,c-a);n=n/max(np.linalg.norm(n),1e-8)
 shade=.65+.35*max(0,float(np.dot(n,[-.4,.85,-.3])))
 uv=np.array([project(p) for p in pts]);lo=np.maximum(np.floor(uv.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(uv.max(axis=0)).astype(int),[1199,999])
 if (hi<lo).any():continue
 xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
 x0,y0=uv[0];x1,y1=uv[1];x2,y2=uv[2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
 if abs(den)<1e-8:continue
 w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den;w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;w2=1-w0-w1
 dd=[p[0]+p[2]+p[1]*20/34 for p in pts];zz=w0*dd[0]+w1*dd[1]+w2*dd[2]
 sub=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];mask=(w0>=0)&(w1>=0)&(w2>=0)&(zz>sub)
 sub[mask]=zz[mask];pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=tuple(int(v*shade) for v in colors[m])
im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
draw.text((35,30),'FOREST COURTYARD / LoL Mobile',fill=(231,215,167));draw.text((35,52),'Original low-poly arena | 34 x 34 units | Y up',fill=(181,197,184))
im.save(ROOT/'Previews/forest_courtyard.png')
report={'format':'glTF 2.0 binary','triangles':sum(len(d['p'])//3 for d in layers.values()),'meshes':len(layers),'materials':1,'embedded_textures':1,'texture_size':[512,512],'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'bounds':{'min':[-17,-.8,-17],'max':[17,5,17]},'checks':{'header_length':len(out)==struct.unpack_from('<I',out,8)[0],'external_uris':False,'finite_positions':all(np.isfinite(d['p']).all() for d in layers.values())},'runtime_import_tested':False}
(ROOT/'Metadata/validation.json').write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'Metadata/layout.json').write_text(json.dumps({'up_axis':'Y','origin':[0,0,0],'playable_radius':11.5,'visual_boundary_radius':11.75,'spawn':[0,0,0],'collision_included':False,'scenery_min_radius':12.5},indent=2)+'\n')
print(json.dumps(report,indent=2))
