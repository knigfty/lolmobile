import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {containsPosition,groundHeight,constrainPosition} from '../Assets/Map/citadel-collision.mjs';
import {createNavigation,NPC_RADIUS,LANDMARKS} from '../scripts/npcs/roaming.mjs';
const layout=JSON.parse(readFileSync(new URL('../Assets/Map/Metadata/citadel-layout.json',import.meta.url)));
assert.equal(groundHeight({x:0,z:0},layout),0);
assert.equal(groundHeight({x:0,z:-25.9},layout),1.12);
assert.equal(containsPosition({x:0,z:-27},.4,layout),false,'chair remains solid');
for(const radius of [.4,NPC_RADIUS]){
  let previous=0;const visited=new Set();
  for(let z=-24;z>=-25.95;z-=.01){
    const p={x:0,z};assert.ok(containsPosition(p,radius,layout));
    constrainPosition(p,radius,layout);assert.ok(Math.abs(p.z-z)<1e-7);
    const y=groundHeight(p,layout);assert.ok(y>=previous);assert.ok(y-previous<=.240001);previous=y;visited.add(y);
  }
  assert.equal(visited.size,6,'ground and all five treads');
  for(let z=-25.95;z<=-24;z+=.01){const y=groundHeight({x:0,z},layout);assert.ok(y<=previous);previous=y}
  assert.equal(previous,0);
  const nav=createNavigation(layout,radius);
  for(const start of LANDMARKS){const route=nav.route(start,{x:0,z:-25.9});assert.ok(route.length,`${start.name} reaches platform`)}
}
// Existing rendered geometry and new height metadata must agree: no GLB edit needed.
const bytes=readFileSync(new URL('../Assets/Map/Models/demacian_citadel.glb',import.meta.url));
const size=bytes.readUInt32LE(12),gltf=JSON.parse(bytes.toString('utf8',20,20+size));
const mesh=gltf.meshes.find(m=>m.name==='ThroneSteps');assert.ok(mesh);
const heights=[];
for(const primitive of mesh.primitives){
 const a=gltf.accessors[primitive.attributes.POSITION],v=gltf.bufferViews[a.bufferView];
 for(let i=0;i<a.count;i++)heights.push(bytes.readFloatLE(28+size+(v.byteOffset??0)+(a.byteOffset??0)+i*12+4));
}
for(const s of layout.walkable_surfaces)assert.ok(heights.some(y=>Math.abs(y-s.height)<1e-5));
console.log('Passed: player/NPC climb and descent, all five geometry-matched tread heights, solid throne, all landmark-to-platform routes.');
