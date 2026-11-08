"""Check exported triangles, independently of the navigation metadata."""
from pathlib import Path
import json,struct
import numpy as np
root=Path(__file__).resolve().parents[1]
b=(root/'Assets/Map/Models/demacian_citadel.glb').read_bytes()
length=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+length]);base=28+length

def accessor(i,width,dtype):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
 return np.frombuffer(b,dtype=dtype,count=a['count']*width,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
triangles=[]
for m in g['meshes']:
 for p in m['primitives']:
  xyz=accessor(p['attributes']['POSITION'],3,'<f4');idx=accessor(p['indices'],1,'<u4').ravel()
  assert np.isfinite(xyz).all()
  if m['name']=='Architecture__Mountain':assert xyz[:,2].max()<=-158,'Mountain intrudes into playable grounds'
  triangles.append(xyz[idx].reshape(-1,3,3))
t=np.concatenate(triangles).astype(float)
a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a
# Segment/triangle intersection at champion body height catches visible walls that
# collision metadata could accidentally omit, including portal or mountain mistakes.
route=[(0,112),(0,46),(12,46),(12,-60),(0,-60),(0,-138)]
for height in [.3,1,2]:
 for (ax,az),(bx,bz) in zip(route,route[1:]):
  origin=np.array([ax,height,az]);direction=np.array([bx-ax,0,bz-az])
  h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h)
  mask=abs(det)>1e-8;inv=np.zeros_like(det);inv[mask]=1/det[mask]
  delta=origin-a;u=inv*np.einsum('ij,ij->i',delta,h)
  q=np.cross(delta,e1);v=inv*(q@direction);distance=inv*np.einsum('ij,ij->i',e2,q)
  hits=mask&(u>=0)&(v>=0)&(u+v<=1)&(distance>1e-6)&(distance<1-1e-6)
  assert not hits.any(),f'Visible geometry blocks walking route at height {height}: {(ax,az),(bx,bz)}'
print(f'Passed: {len(t):,} exported triangles finite; mountain outside playable bounds; walking route clear in actual GLB at three champion heights.')
