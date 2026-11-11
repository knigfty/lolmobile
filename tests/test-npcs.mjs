import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createNavigation,createRoamer,LANDMARKS,NPC_RADIUS} from '../scripts/npcs/roaming.mjs';
import {containsPosition} from '../Assets/Map/citadel-collision.mjs';
const layout=JSON.parse(readFileSync(new URL('../Assets/Map/Metadata/citadel-layout.json',import.meta.url)));
layout.obstacles.push(...[[-23,20],[-17,20],[-20,23],[-23,26],[-17,26]].map(([x,z])=>({type:'circle',x,z,radius:.8})));
const nav=createNavigation(layout);
for(const a of LANDMARKS)for(const b of LANDMARKS){
  assert.ok(containsPosition(a,NPC_RADIUS,layout),a.name);
  const path=nav.route(a,b);assert.ok(path.length,`${a.name} -> ${b.name}`);
  let from=a;for(const to of path){assert.ok(nav.clear(from,to));from=to}
  assert.equal(from.x,b.x);assert.equal(from.z,b.z);
}
assert.equal(nav.clear({x:-20,z:-3},{x:-20,z:7}),false,'cannot cross fountain');
assert.equal(nav.clear({x:0,z:-21},{x:15,z:-21}),false,'cannot cross citadel wall');
const remote={x:100,z:100};
function actor(roll=.2,position={x:0,z:8,heading:0},navigation=nav){
  let calls=[],rolls=0;const brain=createRoamer({position,navigation,random:()=>{rolls++;return roll},play:(name)=>{calls.push({name,heading:position.heading});return 2}});
  return {brain,position,calls,get rolls(){return rolls},tick:(player,options={})=>brain.update(.1,{player,...options})};
}
let a=actor();const player={x:3,z:8};a.tick(player);
assert.equal(a.calls.at(-1).name,'Joke');assert.equal(a.calls.at(-1).heading,0,'does not snap before playing');
assert.ok(a.position.heading>0&&a.position.heading<Math.PI/2,'turn eases toward player');
const rolled=a.rolls;for(let i=0;i<10;i++)a.tick(player);assert.equal(a.rolls,rolled,'no repeated proximity rolls');
a=actor(.3);a.tick(player);assert.equal(a.brain.state,'idle','30% boundary excludes .3');
const failureRolls=a.rolls;for(let i=0;i<10;i++)a.tick(player);assert.equal(a.rolls,failureRolls,'failed chance does not reroll');
a.tick(remote);a.tick(player);assert.equal(a.rolls,failureRolls+1,'new approach rolls again');
for(const [roll,expected] of [[.49,'Dance'],[.5,'Laugh']]){
  a=actor(roll);a.tick(player,{dancing:true,danceId:1});assert.equal(a.calls.at(-1).name,expected);
  assert.ok(a.position.heading>0&&a.position.heading<Math.PI/2);const count=a.calls.filter(c=>c.name===expected).length;
  for(let i=0;i<100;i++)a.tick(player,{dancing:true,danceId:1});
  assert.equal(a.calls.filter(c=>c.name===expected).length,count,'once per performance');
  a.tick({x:a.position.x+3,z:a.position.z},{dancing:true,danceId:2});assert.equal(a.calls.filter(c=>c.name===expected).length,count+1);
}
a=actor(.1,{x:0,z:-12,heading:0});a.tick({x:4,z:-12},{dancing:true,danceId:1});
assert.equal(a.brain.state,'idle','no emotes through the hall wall');
// Reactions pause movement and return to idling before the next journey.
a=actor();for(let i=0;i<81;i++)a.brain.update(.05,{player:remote});assert.equal(a.brain.state,'walk');
const close={x:a.position.x+2,z:a.position.z};a.tick(close);assert.equal(a.brain.state,'react');
const saved={...a.position};for(let i=0;i<10;i++)a.tick(close);assert.equal(a.position.x,saved.x);assert.equal(a.position.z,saved.z);
for(let i=0;i<15;i++)a.tick(close);assert.notEqual(a.brain.state,'react');
// Long simulation: every step stays walkable; only landmark stops; mostly idle.
a=actor(.6);let idle=0,total=0;const visited=new Set();
for(let i=0;i<24000;i++){
  a.brain.update(.05,{player:remote});total++;if(a.brain.state==='idle'){idle++;visited.add(a.brain.destination)}
  assert.ok(containsPosition(a.position,NPC_RADIUS,layout));
}
assert.equal(visited.size,LANDMARKS.length);assert.ok(idle/total>.5,`idle fraction ${idle/total}`);
const activity=a.brain.activity;assert.ok(Math.abs(activity.movingTime/activity.elapsed-.3)<.025,JSON.stringify(activity));
for(const file of ['lux','jarvan_iv']){
  const bytes=readFileSync(new URL(`../Assets/Champs/${file}.glb`,import.meta.url));
  const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
  for(const name of ['Idle1','Idle2','Idle3','Idle4','Run','Joke','Dance','Laugh'])assert.ok(gltf.animations.some(a=>a.name===name),`${file} ${name}`);
}
console.log(`Passed: all 49 landmark routes, collision safety, actual GLB clips, 30%/50% boundaries, facing, encounter/dance debounce, wall occlusion, emote recovery, 20-minute roaming (${Math.round(idle/total*100)}% idle).`);

// Solid bodies stop motion in either direction, including a swept large step.
const {bodyPathClear,overlapsBody,separateBody}=await import('../scripts/npcs/body-collision.mjs');
const body={group:{position:{x:0,z:0}},hitboxRadius:NPC_RADIUS};
assert.equal(bodyPathClear({x:-3,z:0},{x:3,z:0},.4,[body]),false);
assert.equal(bodyPathClear({x:-3,z:2},{x:3,z:2},.4,[body]),true);
for(let angle=0;angle<Math.PI*2;angle+=.2){
  const p={x:Math.cos(angle)*2,z:Math.sin(angle)*2};
  for(let i=0;i<50;i++){
    p.x-=Math.cos(angle)*.1;p.z-=Math.sin(angle)*.1;
    separateBody(p,.4,body,-Math.cos(angle)*.1,-Math.sin(angle)*.1);
    assert.equal(overlapsBody(p,.4,body),false);
  }
}
const blockedPosition={x:0,z:8,heading:0};let replans=0;
const blockedBrain=createRoamer({position:blockedPosition,navigation:nav,play:()=>2,random:()=>.6,
  canMove:()=>false,replan:()=>{replans++;return []}});
for(let i=0;i<200;i++)blockedBrain.update(.05,{player:remote});
assert.deepEqual(blockedPosition,{x:0,z:8,heading:0});
assert.equal(blockedBrain.activity.movingTime,0,'blocked time is not moving time');assert.ok(replans>0);
console.log('Passed: solid body contacts from all angles, swept NPC collision, blocked-time accounting and replanning.');
