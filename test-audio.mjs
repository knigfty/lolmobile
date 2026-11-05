import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('./garen-audio.js',import.meta.url),'utf8');
const {createGarenAudio}=await import('data:text/javascript,'+encodeURIComponent(source.replaceAll('import.meta.url',JSON.stringify(new URL('./garen-audio.js',import.meta.url).href))));
let now=0;const played=[];
class MockAudio{constructor(url){this.url=url;this.paused=false;assert(existsSync(new URL(url)))}play(){played.push(this);return Promise.resolve()}pause(){this.paused=true}}
const audio=createGarenAudio({AudioClass:MockAudio,time:()=>now,random:()=>.999});

const isSfx=clip=>clip.url.includes('_SFX_');
const voices=()=>played.filter(clip=>!isSfx(clip)&&!clip.paused&&!clip.ended);
const complete=clip=>{clip.ended=true;clip.onended?.()};
audio.move();assert.equal(played.length,1);audio.move();assert.equal(played.length,1);
now=4;complete(played[0]);now=18;audio.move();assert.equal(played.length,1);
now=19;audio.move();assert.equal(played.length,2);
audio.runSpell();assert(played[1].paused);const runVoice=played.at(-2),runSfx=played.at(-1);
audio.spell1();assert(runVoice.paused);assert(!runSfx.paused);
const strikeVoice=played.at(-1);audio.spell1Hit();const strikeSfx=played.at(-1);
assert(!strikeVoice.paused);audio.endSpell1();assert(strikeVoice.paused);
assert(!strikeSfx.paused&&!runSfx.paused);
let count=played.length;audio.attack('Attack1');assert.equal(played.length,count+2);
const attackVoice=played.at(-2);audio.hit('Attack1');assert(!attackVoice.paused);
audio.attack('Attack2');assert(attackVoice.paused);assert.equal(voices().length,1);
audio.justice();const ultimateVoice=played.at(-2);assert.equal(voices().length,1);
count=played.length;audio.attack('Attack1');assert.equal(played.length,count+1);
assert(isSfx(played.at(-1)));assert(!ultimateVoice.paused);
audio.runSpell();audio.spell1();audio.spell1Hit();audio.spin();
assert.equal(voices().length,1);assert.equal(voices()[0],ultimateVoice);
// No action, transition, priority, or hit may pause any SFX.
assert(played.filter(isSfx).every(clip=>!clip.paused));
complete(ultimateVoice);audio.stop();
// Run boost expiry only ends its voice; the cast SFX keeps its natural tail.
audio.runSpell();const expiredVoice=played.at(-2),expiredSfx=played.at(-1);
audio.endRunSpell();assert(expiredVoice.paused);assert(!expiredSfx.paused);
// Interrupted movement starts its cooldown when cut off.
now=100;audio.move();const move=played.at(-1);now=102;audio.attack('Attack1');assert(move.paused);
audio.stop();now=116;count=played.length;audio.move();assert.equal(played.length,count);
now=117;audio.move();assert.equal(played.length,count+1);audio.stop();
console.log('Passed: independent full-duration SFX, single prioritized voice, equal-priority replacement, Q sequence, boost expiry, movement cooldown, and asset paths.');
