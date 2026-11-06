import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const damage=source.slice(source.indexOf('function damageTarget('),source.indexOf('function updateTargetHealth('));
const justice=source.slice(source.indexOf('function justice()'),source.indexOf('function spin()'));
function scenario(hp=10){
  const target={hp,group:{visible:true,position:{x:0,z:2}},healthBar:{visible:false}};
  const other={hp:10,group:{visible:true,position:{x:0,z:4}},healthBar:{visible:false}};
  const events=[],context={targets:[target,other],player:{position:{x:0,z:0},rotation:{},quaternion:{}},
    THREE:{Vector3:class{applyQuaternion(){return {x:0,z:1}}}},
    mixer:{},now:0,lockUntil:0,dancing:false,JUSTICE_RANGE:800,BASE_ATTACK_CONE_COS:.38,
    actions:{Spell4_Base:{getClip:()=>({duration:2})}},queueSpellCommand:()=>false,queueAttackCommand:()=>false,runSpellActive:()=>false,
    inputTime:()=>1,hitCount:0,hitsEl:{},updateTargetHealth:()=>{},toast:()=>{},
    action:()=>events.push('animation'),garenAudio:{justice:()=>events.push('cast'),justiceHit:()=>events.push('hit')},
    setTimeout:(fn,delay)=>{context.impact=fn;context.delay=delay;return 1}};
  runInNewContext(damage+justice+';justice();',context);
  return {context,target,other,events};
}
let s=scenario();assert.equal(s.target.hp,10);assert.deepEqual(s.events,['animation','cast']);
assert.equal(s.context.delay,900);s.context.impact();assert.equal(s.target.hp,5);assert.equal(s.other.hp,10);
assert.equal(s.context.hitCount,1);assert.equal(s.events.at(-1),'hit');
s=scenario(3);s.context.impact();assert.equal(s.target.hp,0);assert.equal(s.target.cool,5);
s=scenario();s.target.hp=0;s.context.impact();assert(!s.events.includes('hit'));assert.equal(s.context.hitCount,0);
s=scenario();s.target.group.visible=false;s.context.impact();assert(!s.events.includes('hit'));
s=scenario(0);assert.equal(s.context.targets[1].hp,10);s.context.impact();assert.equal(s.context.targets[1].hp,5);
console.log('Passed: delayed 5 HP single-target Justice impact, death handling, and no hit sound on dead/hidden targets.');
