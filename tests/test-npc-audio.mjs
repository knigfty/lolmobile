import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {createNpcAudio} from '../scripts/audio/npc-audio.mjs';
import {createRoamer} from '../scripts/npcs/roaming.mjs';
let now=0;const played=[];
class MockAudio{
  constructor(url){this.url=url;assert.ok(existsSync(new URL(url)),url)}
  play(){played.push(this);return Promise.resolve()}
  pause(){this.paused=true}
}
const make=champion=>createNpcAudio({champion,AudioClass:MockAudio,time:()=>now,random:()=>.999});
const close={audible:true,distance:2};
const finish=()=>played.at(-1).onended?.();
const j4=make('Jarvan IV'),lux=make('Lux');
assert.equal(j4.move(),false,'no sound before proximity update');
j4.update(close);j4.move();assert.ok(played.at(-1).url.endsWith('Move_Standard_09.m4a'));finish();
now=14.999;assert.equal(j4.move(),false);now=15;assert.equal(j4.move(),true);
const movement=played.at(-1);j4.emote('Joke');assert.ok(movement.paused);assert.ok(played.at(-1).url.endsWith('Joke_General_02.m4a'));finish();
now=29.999;assert.equal(j4.emote('Laugh'),false,'joke and laugh share cooldown');
now=30;assert.equal(j4.emote('Laugh'),true);assert.ok(played.at(-1).url.endsWith('Laugh_General_04.m4a'));
const laugh=played.at(-1);j4.update({...close,distance:6});assert.ok(laugh.volume>0&&laugh.volume<1);
j4.update({audible:false,distance:8});assert.ok(laugh.paused);assert.equal(j4.move(),false);assert.equal(j4.emote('Joke'),false);
j4.update(close);assert.equal(j4.emote('Joke'),false,'re-entry does not reset cooldown');
now=45;j4.emote('Joke');const joke=played.at(-1);j4.endEmote();assert.ok(joke.paused);
assert.equal(j4.emote('Dance'),false,'no unrelated clip substituted for missing dance audio');
// Lux greeting is specific to Garen, once per approach, with a five-minute timer.
now=100;lux.update({...close,playerChampion:'Lux'});assert.equal(lux.move(),true);finish();
lux.update({audible:false,distance:8});lux.update(close);
assert.ok(played.at(-1).url.endsWith('First_Encounter_Garen.m4a'));finish();
let count=played.length;now=399.999;lux.update({audible:false,distance:8});lux.update(close);assert.equal(played.length,count);
now=400;lux.update(close);assert.equal(played.length,count,'standing nearby does not retrigger');
lux.update({audible:false,distance:8});lux.update(close);assert.equal(played.length,count+1);
const greeting=played.at(-1);assert.equal(lux.move(),false);assert.equal(lux.emote('Laugh'),false);assert.ok(!greeting.paused);
lux.update({...close,enabled:false});assert.ok(greeting.paused);assert.equal(lux.move(),false);
// Independent champions/categories and stale events cannot clear a newer voice.
now=500;lux.update({...close,playerChampion:'Jarvan IV'});lux.move();const old=played.at(-1),stale=old.onended;
lux.emote('Joke');const current=played.at(-1);stale();assert.equal(lux.move(),false);assert.ok(!current.paused);
j4.update(close);assert.equal(j4.emote('Laugh'),true,'Lux does not consume J4 cooldown');
j4.stop();lux.stop();
// All variants resolve to uploaded assets, not just the random endpoint.
for(const champion of ['Lux','Jarvan IV'])for(let i=0;i<15;i++){
  now+=1000;const a=createNpcAudio({champion,AudioClass:MockAudio,time:()=>now,random:()=>i/15});
  a.update({...close,playerChampion:'Other'});a.move();finish();a.emote('Joke');finish();now+=15;a.emote('Laugh');finish();
}
// Failed playback is handled and throttled rather than retried every frame.
class RejectedAudio extends MockAudio{play(){played.push(this);return Promise.reject(new Error('autoplay blocked'))}}
const rejected=createNpcAudio({champion:'Lux',AudioClass:RejectedAudio,time:()=>now});
rejected.update({...close,playerChampion:'Other'});rejected.move();await Promise.resolve();assert.equal(rejected.move(),false);
// Reactions cannot start at range, and end when range or sight is lost.
for(const roll of [.1,.8]){
  let visible=true;const calls=[];
  const b=createRoamer({position:{x:0,z:0,heading:0},navigation:{clear:()=>visible,route:()=>[]},random:()=>roll,play:n=>{calls.push(n);return 5}});
  b.update(.1,{player:{x:8,z:0},dancing:true,danceId:1});assert.equal(b.state,'idle');
  b.update(.1,{player:{x:2,z:0},dancing:true,danceId:1});assert.equal(b.state,'react');
  b.update(.1,{player:{x:8,z:0}});assert.equal(b.state,'idle');
  b.update(.1,{player:{x:2,z:0},dancing:true,danceId:2});assert.equal(b.state,'react');
  visible=false;b.update(.1,{player:{x:2,z:0}});assert.equal(b.state,'idle');
}
console.log('Passed: NPC asset variants, exact cooldown boundaries, shared joke/laugh timer, independent champions, Garen-only encounters, range/visibility cancellation, volume falloff, priority and autoplay failure.');
