import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createDummyAnimations} from '../scripts/objects/dummy-animations.mjs';
const bytes=readFileSync(new URL('../Assets/Objects/target_dummy.glb',import.meta.url));
const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
const clips=gltf.animations.map(a=>({name:a.name,duration:Math.max(...a.samplers.map(s=>gltf.accessors[s.input].max[0]))}));
class Action{
 constructor(clip){this.clip=clip;this.resets=0}
 reset(){this.resets++;return this}setLoop(){return this}setEffectiveTimeScale(){return this}setEffectiveWeight(){return this}
 play(){this.mixer.active=this;return this}crossFadeFrom(){return this}getClip(){return this.clip}
}
class Mixer{
 clipAction(clip){const action=new Action(clip);action.mixer=this;return action}
 addEventListener(_,fn){this.finished=fn}stopAllAction(){this.active=null}update(dt){this.elapsed=(this.elapsed||0)+dt}
 finish(action=this.active){this.finished({action})}
}
function target(offset=0){const mixer=new Mixer();let deaths=0;const animator=createDummyAnimations({mixer,clips,LoopOnce:2200,idleOffset:offset,onDeathFinished:()=>deaths++});return {mixer,animator,get deaths(){return deaths}}}
const a=target(),b=target(1);a.animator.spawn();b.animator.spawn();
assert.equal(a.mixer.active.clip.name,'Spawn');a.mixer.finish();assert.equal(a.mixer.active.clip.name,'Idle1_Base');
b.mixer.finish();assert.equal(b.mixer.active.clip.name,'Idle2_Base');
a.animator.hit();assert.equal(a.mixer.active.clip.name,'Hit');assert.equal(b.animator.state,'idle');
const resets=a.mixer.active.resets;a.animator.hit();assert.equal(a.mixer.active.resets,resets+1);
a.mixer.finish();assert.equal(a.animator.state,'idle');a.mixer.finish();assert.equal(a.mixer.active.clip.name,'TargetDummy_Idle120.anm');
a.animator.die();assert.equal(a.mixer.active.clip.name,'Death');assert.equal(a.animator.deathDuration,1.5);
a.animator.hit();assert.equal(a.mixer.active.clip.name,'Death');assert.equal(a.deaths,0);
a.mixer.finish();assert.equal(a.deaths,1);assert.equal(a.animator.state,'death');
a.animator.spawn();assert.equal(a.mixer.active.clip.name,'Spawn');a.mixer.finish();assert.equal(a.animator.state,'idle');
a.animator.update(.2);assert.equal(a.mixer.elapsed,.2);assert.equal(b.mixer.elapsed,undefined);
assert.throws(()=>createDummyAnimations({mixer:new Mixer(),clips:[],LoopOnce:2200}),/missing Spawn/);
console.log('Passed: uploaded clips, spawn/idle/hit/death/respawn transitions, hit restart, idle variants, independent dummy animation state.');
