// One voice per NPC; cooldowns are independent per NPC and event category.
export const NPC_AUDIO_COOLDOWNS={move:15,emote:15,encounter:300};
export function createNpcAudio({champion,AudioClass=globalThis.Audio,time=()=>performance.now()/1000,random=Math.random}){
  const lux=champion==='Lux',folder=lux?'Lux_Audio':'JarvanIV_Audio';
  const ready={move:0,emote:0,encounter:0};
  let active=null,volume=0,near=false,encounterPending=false;
  function stop(){
    if(!active)return;
    const {audio}=active;active=null;
    audio.onended=audio.onerror=null;audio.pause();audio.currentTime=0;
  }
  function play(file,category,rank){
    if(volume<=0||time()<ready[category]||(active&&active.rank>=rank))return false;
    stop();
    const audio=new AudioClass(new URL(`../../Assets/Audio/${folder}/${file}`,import.meta.url).href);
    const entry={audio,rank,category};active=entry;audio.volume=volume;
    // Reserve on start, including failed attempts, to avoid per-frame retries
    // when a browser blocks autoplay. Leaving range never resets cooldowns.
    ready[category]=time()+NPC_AUDIO_COOLDOWNS[category];
    const finish=()=>{if(active===entry){active=null;audio.onended=audio.onerror=null}};
    audio.onended=audio.onerror=finish;
    try{Promise.resolve(audio.play()).catch(finish)}catch{finish()}
    return true;
  }
  const variant=(stem,count)=>`${stem}_${String(1+Math.floor(random()*count)).padStart(2,'0')}.m4a`;
  return {
    update({audible,distance,playerChampion='Garen',enabled=true}){
      const inRange=audible&&enabled;
      if(inRange&&!near&&lux&&playerChampion==='Garen')encounterPending=true;
      near=inRange;
      volume=inRange?Math.min(1,Math.max(0,(7-distance)/3)):0;
      if(!inRange||volume===0){encounterPending=false;stop();return}
      if(active)active.audio.volume=volume;
      if(encounterPending){
        // A new approach during cooldown is consumed, not queued for five minutes.
        encounterPending=false;
        play('Interactions/First_Encounter_Garen.m4a','encounter',3);
      }
    },
    move(){return play(variant('Movement/Move_Standard',lux?15:9),'move',1)},
    emote(name){
      if(name!=='Joke'&&name!=='Laugh')return false; // No dance sound in either base-skin pack.
      return play(variant(`Taunt_Joke/${name}_General`,name==='Joke'?2:4),'emote',2);
    },
    get emotePlayback(){return active?.category==='emote'?active.audio:null},
    dance(){
      if(volume<=0||time()<ready.emote||(active&&active.rank>=2))return false;
      stop();ready.emote=time()+NPC_AUDIO_COOLDOWNS.emote;return true;
    },
    endEmote(){if(active?.category==='emote')stop()},
    stop,
  };
}

// Pause on the first pose until metadata arrives; follow the media clock even
// during buffering. The animation therefore never runs ahead of the recording.
export function syncEmoteAnimation(action,media){
  action.time=Number.isFinite(media?.duration)&&media.duration>0
    ?Math.min(1,Math.max(0,media.currentTime/media.duration))*action.getClip().duration:0;
}
