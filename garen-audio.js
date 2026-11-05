// SFX are independent one-shots and always play to completion.
// A single voice channel replaces equal/lower priorities and rejects lower ones.
export function createGarenAudio({AudioClass=globalThis.Audio,time=()=>performance.now()/1000,random=Math.random}={}){
  const priority={idle:0,move:1,attack:2,spell:3,ultimate:4};
  const active=new Set();let movementReadyAt=0;
  const variant=(stem,count)=>`${stem}_${Math.floor(random()*count)}.ogg`;
  function finish(entry,cooldown=true){
    if(!active.delete(entry))return;
    entry.audio.onended=entry.audio.onerror=null;
    if(entry.movement&&cooldown)movementReadyAt=time()+15;
  }
  function stop(entry){entry.audio.pause();entry.audio.currentTime=0;finish(entry)}
  function end(group){for(const entry of [...active])if(!entry.sfx&&entry.group===group)stop(entry)}
  function event(level,files,movement=false,group=null){
    const rank=priority[level];
    for(const file of files){
      const sfx=file.includes('_SFX_');
      if(!sfx){
        if([...active].some(entry=>!entry.sfx&&entry.rank>rank))continue;
        if(movement&&(time()<movementReadyAt||[...active].some(entry=>entry.movement)))continue;
        for(const entry of [...active])if(!entry.sfx)stop(entry);
      }
      const audio=new AudioClass(new URL(`./Assets/Audio/Garen_Audio/${file}`,import.meta.url).href);
      const entry={audio,rank,movement,group,sfx};active.add(entry);
      audio.onended=audio.onerror=()=>finish(entry);
      try{Promise.resolve(audio.play()).catch(()=>finish(entry))}catch{finish(entry)}
    }
    return true;
  }
  const pick=(stem,count)=>variant(`Garen_Original_${stem}`,count);
  return {
    attack(name){event('attack',[pick('BasicAttack',4),pick(`SFX_${name==='Attack2'?'BasicAttack2':'BasicAttack'}_OnCast`,4)])},
    hit(name){event('attack',[pick(`SFX_${name==='Attack2'?'BasicAttack2':'BasicAttack'}_OnHit_flesh`,4)])},
    move(){event('move',[pick('Move',16)],true)},
    runSpell(){event('spell',[pick('Q',2),pick('SFX_Q_OnCast',3)],false,'runSpell')},
    spell1(){end('runSpell');event('spell',[pick('QAttack',4)],false,'spell1')},
    spell1Hit(){event('spell',[pick('SFX_Q_Attack_OnCast_1',4)],false,'spell1')},
    spin(){event('spell',[pick('E',3),pick('SFX_E_OnCast',3)])},
    justice(){event('ultimate',[pick('R',6),pick('SFX_R_OnCast',3)])},
    endRunSpell(){end('runSpell')},
    endSpell1(){end('spell1')},
    stop(){for(const entry of [...active])stop(entry)}
  };
}
