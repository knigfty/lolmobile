import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('./garen-audio.js',import.meta.url),'utf8');
const {createGarenAudio}=await import('data:text/javascript,'+encodeURIComponent(source.replaceAll('import.meta.url',JSON.stringify(new URL('./garen-audio.js',import.meta.url).href))));
let now=0;const played=[];
class MockAudio{constructor(url){this.url=url;this.paused=false;assert(existsSync(new URL(url)))}play(){played.push(this);return Promise.resolve()}pause(){this.paused=true}}
const audio=createGarenAudio({AudioClass:MockAudio,time:()=>now,random:()=>.999});
audio.move();assert.equal(played.length,1);audio.move();assert.equal(played.length,1);
now=4;played[0].onended();now=18;audio.move();assert.equal(played.length,1);now=19;audio.move();assert.equal(played.length,2);
audio.runSpell();assert(played[1].paused);assert.equal(played.length,4);
audio.move();audio.attack('Attack1');assert.equal(played.length,4);
audio.justice();assert(played[2].paused&&played[3].paused);assert.equal(played.length,6);
audio.spell1();assert.equal(played.length,6);audio.stop();
for(const name of ['Attack1','Attack2']){audio.attack(name);audio.hit(name);audio.stop()}
for(const method of ['runSpell','spell1','spell1Hit','spin','justice']){audio[method]();audio.stop()}
console.log('Audio priorities, paired playback, interruption, cooldown, and asset paths passed.');

// Deliberately leave media unfinished: animation transitions must release it.
audio.runSpell();const runClips=played.slice(-2);
audio.spell1();assert(runClips.every(clip=>clip.paused));
const strikeVoice=played.at(-1);audio.spell1Hit();const strikeHit=played.at(-1);
audio.endSpell1();assert(strikeVoice.paused&&strikeHit.paused);
let count=played.length;audio.attack('Attack1');assert.equal(played.length,count+2);
audio.hit('Attack1');assert.equal(played.length,count+3);audio.stop();
audio.runSpell();const expiredRun=played.slice(-2);audio.endRunSpell();
assert(expiredRun.every(clip=>clip.paused));count=played.length;
audio.attack('Attack2');assert.equal(played.length,count+2);audio.stop();
console.log('Run spell → Spell1 → basic attack and unused boost expiry passed.');
