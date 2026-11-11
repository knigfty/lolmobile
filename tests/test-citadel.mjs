import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {constrainPosition,containsPosition} from '../Assets/Map/Citadel/citadel-collision.mjs';
const layout=JSON.parse(readFileSync(new URL('../Assets/Map/Citadel/Metadata/citadel-layout.json',import.meta.url)));
const radius=.4;
assert(containsPosition({x:layout.spawn[0],z:layout.spawn[2]},radius,layout));
for(const direction of [{x:1,z:0},{x:-1,z:0},{x:0,z:1},{x:0,z:-1},{x:1,z:1},{x:-1,z:-1}]){
 const p={x:0,z:12};
 for(let step=0;step<3000;step++){
  const before={...p};p.x+=direction.x*.18;p.z+=direction.z*.18;
  constrainPosition(p,radius,layout);
  if(!containsPosition(p,radius,layout))Object.assign(p,before);
  assert(containsPosition(p,radius,layout),`Escaped walls at ${JSON.stringify(p)}`);
 }
}
// Approach the keep, fountains, and wings from multiple angles, including corners.
for(const obstacle of layout.obstacles){
 for(let angle=0;angle<16;angle++){
  const a=angle*Math.PI/8;
  const cx=obstacle.type==='circle'?obstacle.x:(obstacle.minX+obstacle.maxX)/2;
  const cz=obstacle.type==='circle'?obstacle.z:(obstacle.minZ+obstacle.maxZ)/2;
  const p={x:cx+Math.cos(a)*18,z:cz+Math.sin(a)*18};
  if(!containsPosition(p,radius,layout))continue;
  for(let i=0;i<150;i++){
   const before={...p};p.x-=Math.cos(a)*.18;p.z-=Math.sin(a)*.18;
   constrainPosition(p,radius,layout);
   if(!containsPosition(p,radius,layout))Object.assign(p,before);
   assert(containsPosition(p,radius,layout));
  }
 }
}
// Movement reaches well beyond the retired 10.9 radius without exiting the castle.
const p={x:0,z:12};for(let i=0;i<90;i++){p.z+=.18;constrainPosition(p,radius,layout)}assert(p.z>27);
const glb=readFileSync(new URL('../Assets/Map/Citadel/Models/demacian_citadel.glb',import.meta.url));
assert.equal(glb.toString('ascii',0,4),'glTF');assert.equal(glb.readUInt32LE(8),glb.length);
const jsonLength=glb.readUInt32LE(12),gltf=JSON.parse(glb.toString('utf8',20,20+jsonLength));
assert(!gltf.buffers.some(b=>b.uri));assert(gltf.images.every(i=>i.bufferView!==undefined));
const binStart=28+jsonLength;
for(const mesh of gltf.meshes)for(const primitive of mesh.primitives){
 const a=gltf.accessors[primitive.attributes.POSITION],n=gltf.accessors[primitive.attributes.NORMAL];
 const pv=gltf.bufferViews[a.bufferView],nv=gltf.bufferViews[n.bufferView];
 for(let i=0;i<a.count;i++){
  const y=glb.readFloatLE(binStart+pv.byteOffset+i*12+4);
  assert(Number.isFinite(y));
  if(mesh.name==='CourtyardPaving'){assert.equal(y,0);assert(glb.readFloatLE(binStart+nv.byteOffset+i*12+4)>.99)}
 }
}
console.log('Passed: closed-wall movement, keep/wing/tower/fountain collision, larger playable area, embedded GLB, upward courtyard surface.');
