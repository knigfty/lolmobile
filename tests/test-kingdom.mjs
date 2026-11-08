import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {containsPosition,constrainPosition} from '../Assets/Map/citadel-collision.mjs';
const layout=JSON.parse(readFileSync(new URL('../Assets/Map/Metadata/citadel-layout.json',import.meta.url)));
const radius=.4;
const free=(x,z)=>containsPosition({x,z},radius,layout);
// Flood-fill the walkable grid using collision-checked segment samples. This tests
// connectivity across the entire exterior, all six colonnade gaps, and the hall.
const step=2,b=layout.bounds;
const key=(x,z)=>`${x},${z}`;
const queue=[[layout.spawn[0],layout.spawn[2]]],visited=new Set([key(...queue[0])]);
function clear(ax,az,bx,bz){
 const n=Math.ceil(Math.hypot(bx-ax,bz-az)/.2);
 for(let i=0;i<=n;i++)if(!free(ax+(bx-ax)*i/n,az+(bz-az)*i/n))return false;
 return true;
}
for(let i=0;i<queue.length;i++){
 const [x,z]=queue[i];
 for(const [dx,dz] of [[step,0],[-step,0],[0,step],[0,-step]]){
  const nx=x+dx,nz=z+dz,k=key(nx,nz);
  if(nx<b.minX||nx>b.maxX||nz<b.minZ||nz>b.maxZ||visited.has(k)||!clear(x,z,nx,nz))continue;
  visited.add(k);queue.push([nx,nz]);
 }
}
function reachable(x,z){return queue.some(([qx,qz])=>Math.hypot(qx-x,qz-z)<3&&clear(qx,qz,x,z))}
for(const [name,p] of Object.entries(layout.landmarks))assert(reachable(p[0],p[2]),`Unreachable ${name}`);
for(const [i,p] of layout.colonnade_passages.entries()){
 assert(reachable(p.x,p.z),`Unreachable colonnade opening ${i}`);
 // Cross radially through the actual gap using the same collision checks as movement.
 const nx=p.x/62**2,nz=(p.z+5)/84**2,len=Math.hypot(nx,nz);
 assert(clear(p.x-nx/len*6,p.z-nz/len*6,p.x+nx/len*6,p.z+nz/len*6),`Blocked passage ${i}`);
}
assert(clear(0,-72,0,-138),'Front portal must open continuously into hall');
assert(!free(-19,-88)&&!free(19,-88),'Facade must remain solid');
assert(!free(32,-120)&&!free(0,-152),'Hall side and back walls must remain solid');
// Traverse a real walking route from spawn, around monument, into the hall and back.
const route=[[0,112],[0,46],[12,46],[12,-60],[0,-60],[0,-120],[0,-60],[12,-60],[12,46],[0,46],[0,112]];
const p={x:0,z:112};
for(const [x,z] of route.slice(1)){
 const dx=x-p.x,dz=z-p.z,n=Math.ceil(Math.hypot(dx,dz)/.15);
 for(let i=0;i<n;i++){p.x+=dx/n;p.z+=dz/n;constrainPosition(p,radius,layout);assert(free(p.x,p.z));}
 assert(Math.hypot(p.x-x,p.z-z)<.01,`Walking route blocked at ${x},${z}`);
}
for(const [x,z] of [[-23,20],[-17,20],[-20,23],[-23,26],[-17,26]])assert(free(x,z),'Existing training target blocked');
const report=JSON.parse(readFileSync(new URL('../Assets/Map/Metadata/citadel-validation.json',import.meta.url)));
assert(report.triangles<100000);assert(report.meshes<200);assert(report.bytes<9*1024*1024);
console.log(`Passed: ${visited.size} reachable grid cells; gardens, six colonnade passages, front portal and hall; round-trip movement; solid walls; geometry budgets.`);
