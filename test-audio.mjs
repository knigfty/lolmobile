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
audio.justice();const ultimateVoice=played.at(-3);assert.equal(voices().length,1);
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

// Spin cast layers three independent clips; hit/end SFX do not cut any off.
count=played.length;audio.spin();assert.equal(played.length,count+3);
assert(played.at(-1).url.endsWith('SFX_E_OnBuffActivate_2.ogg'));
const spinClips=played.slice(-3);audio.spinHit();
assert(played.at(-1).url.endsWith('SFX_E_hit_3.ogg'));
audio.spinEnd();assert(played.at(-1).url.endsWith('SFX_E_OnBuffDeactivate_2.ogg'));
assert(spinClips.every(clip=>!clip.paused));audio.stop();
audio.dance();const intro=played.at(-1);
assert(intro.url.endsWith('SFX_Dance_buffactivate.ogg'));
let dancing=true;audio.danceLoop(()=>dancing);const music=played.at(-1);
assert(music.url.endsWith('SFX_Dance_loop.ogg'));assert(!intro.paused);
count=played.length;complete(music);assert.equal(played.length,count+1);
const tail=played.at(-1);dancing=false;audio.attack('Attack1');assert(!tail.paused);
count=played.length;complete(tail);assert.equal(played.length,count);audio.stop();
// Integration: hit sound is once per pulse, outside the multiple-target loop.
const arena=readFileSync(new URL('./index.html',import.meta.url),'utf8');
const pulse=arena.slice(arena.indexOf('function spinPulse()'),arena.indexOf('// Recognize the held combo'));
assert(pulse.includes('for(const t of hits)damageTarget(t);\n  if(hits.length)garenAudio.spinHit();'));
assert(arena.includes('garenAudio.spinEnd();'));
assert(arena.includes("garenAudio.danceLoop(()=>dancing&&current==='Dance_Loop_BASE')"));
console.log('Passed: Spin cast/end/hit layers, once-per-pulse hit hook, dance intro/loop and full-duration cancellation tail.');

audio.dance();audio.danceLoop(()=>true);const previousDance=played.at(-1);
audio.dance();audio.danceLoop(()=>true);count=played.length;
complete(previousDance);assert.equal(played.length,count);audio.stop();
console.log('Passed: restarting dance cannot revive an older music loop.');

for(const [randomValue,variant] of [[0,0],[.5,1],[.999,2]]){
  const rAudio=createGarenAudio({AudioClass:MockAudio,time:()=>now,random:()=>randomValue});
  count=played.length;rAudio.justice();assert.equal(played.length,count+3);
  assert(played.at(-1).url.endsWith(`SFX_R_OnHit_${variant}.ogg`));
  assert(played.at(-2).url.endsWith(`SFX_R_OnCast_${variant}.ogg`));
  assert(!isSfx(played.at(-3)));assert(played.slice(-3).every(clip=>!clip.paused));
  rAudio.stop();
}
console.log('Passed: Justice layers existing voice/cast SFX with all three random OnHit variants at cast time.');
