// Each target owns a mixer, actions and completion listener; clips may be shared.
export function createDummyAnimations({mixer,clips,LoopOnce,onDeathFinished,idleOffset=0}){
  const actions=new Map(clips.map(clip=>[clip.name,mixer.clipAction(clip)]));
  const idleNames=clips.filter(clip=>/idle/i.test(clip.name)).map(clip=>clip.name);
  for(const name of ['Spawn','Hit','Death'])if(!actions.has(name))throw new Error(`Target dummy is missing ${name}`);
  if(!idleNames.length)throw new Error('Target dummy is missing idle animations');
  let current=null,state='spawn',idleIndex=idleOffset%idleNames.length;
  function play(name,nextState){
    const next=actions.get(name),previous=current;
    state=nextState;current=next;
    next.reset().setLoop(LoopOnce,1);next.clampWhenFinished=true;
    next.setEffectiveTimeScale(1).setEffectiveWeight(1).play();
    if(previous&&previous!==next)next.crossFadeFrom(previous,.08,false);
  }
  function idle(){play(idleNames[idleIndex++%idleNames.length],'idle')}
  mixer.addEventListener('finished',event=>{
    if(event.action!==current)return;
    if(state==='death'){onDeathFinished();return}
    idle();
  });
  return {
    spawn(){mixer.stopAllAction();current=null;play('Spawn','spawn')},
    hit(){if(state!=='death')play('Hit','hit')},
    die(){if(state!=='death')play('Death','death')},
    update(dt){mixer.update(dt)},
    get state(){return state},
    get deathDuration(){return actions.get('Death').getClip().duration}
  };
}
