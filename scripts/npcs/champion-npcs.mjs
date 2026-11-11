import * as THREE from 'three';
import {groundHeight} from '../../Assets/Map/citadel-collision.mjs';
import {createNavigation,createRoamer,LANDMARKS,NPC_RADIUS,NPC_INTERACTION_RANGE} from './roaming.mjs';

import {createNpcAudio,syncEmoteAnimation} from '../audio/npc-audio.mjs';

import {bodyPathClear} from './body-collision.mjs';

export async function loadChampionNpcs({loader,scene,layout,targets}){
  // Dummies remain obstacles even while temporarily defeated, so routes do not
  // get invalidated by a respawn. Both NPCs share one cached navigation grid.
  const navigationLayout={...layout,obstacles:[...layout.obstacles,...targets.map(t=>({
    type:'circle',x:t.group.position.x,z:t.group.position.z,radius:t.hitboxRadius,
  }))]};
  const navigation=createNavigation(navigationLayout);
  const bodies=[];let playerBody=null;
  const definitions=[{name:'Lux',file:'lux.glb',start:0,headHeight:1.72},{name:'Jarvan IV',file:'jarvan_iv.glb',start:1,headHeight:1.9}];
  const assets=await Promise.all(definitions.map(d=>loader.loadAsync(`./Assets/Champs/${d.file}`)));
  const npcs=assets.map((gltf,index)=>{
    const definition=definitions[index],model=gltf.scene,group=new THREE.Group();
    group.name=definition.name;group.userData.npc=true;
    const root=model.getObjectByName('Root')||model.getObjectByName('root');
    const head=model.getObjectByName('Head')||model.getObjectByName('head');
    model.updateMatrixWorld(true);
    const bounds=new THREE.Box3().setFromObject(model);
    const headY=head?.getWorldPosition(new THREE.Vector3()).y;
    if(!Number.isFinite(headY)||headY<=bounds.min.y)throw new Error(`${definition.name}: invalid skeleton height`);
    // Normalize using the head, not the spear/staff's highest point.
    const visual=new THREE.Group();visual.scale.setScalar(definition.headHeight/(headY-bounds.min.y));
    model.position.y-=bounds.min.y;visual.add(model);group.add(visual);
    model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.frustumCulled=false;
      for(const material of Array.isArray(o.material)?o.material:[o.material])material.side=THREE.DoubleSide;
    }});
    const clips=gltf.animations.map(source=>{
      const clip=source.clone();
      // The navigation controller owns horizontal travel. Keep vertical body
      // motion, but remove root drift from exported locomotion and emotes.
      for(const track of clip.tracks){
        if(root&&track.name===`${root.name}.position`){
          for(let i=0;i<track.values.length;i+=3){track.values[i]=root.position.x;track.values[i+2]=root.position.z}
        }
      }
      return clip;
    });
    const mixer=new THREE.AnimationMixer(model),actions=new Map(clips.map(c=>[c.name,mixer.clipAction(c)]));
    for(const name of ['Idle1','Idle2','Idle3','Idle4','Run','Joke','Dance','Laugh']){
      if(!actions.has(name))throw new Error(`${definition.name}: missing ${name} animation`);
    }
    const start=LANDMARKS[definition.start],position={x:start.x,z:start.z,heading:0};
    const audio=createNpcAudio({champion:definition.name});
    let current=null,syncedEmote=false;
    function play(name,once=false){
      const action=actions.get(name),speed=1;
      if(action!==current||once){
        const voiced=name==='Joke'||name==='Laugh';
        if(voiced&&!audio.emote(name))return 0;
        if(name==='Dance'&&!audio.dance())return 0;
        if(!voiced)audio.endEmote();
        syncedEmote=voiced;
        action.reset().setLoop(once?THREE.LoopOnce:THREE.LoopRepeat,once?1:Infinity);
        action.clampWhenFinished=once;action.setEffectiveTimeScale(syncedEmote?0:speed).setEffectiveWeight(1).play();
        if(current)action.crossFadeFrom(current,.25,false);
        current=action;
      }
      return action.getClip().duration/speed;
    }
    const body={group,hitboxRadius:NPC_RADIUS};bodies.push(body);
    const blockers=()=>[...bodies.filter(other=>other!==body),...(playerBody?[playerBody]:[])];
    const brain=createRoamer({position,navigation,play,startIndex:definition.start,
      reactionActive:()=>syncedEmote?Boolean(audio.emotePlayback):null,
      canMove:(from,to)=>bodyPathClear(from,to,NPC_RADIUS,blockers()),
      replan:(from,to)=>createNavigation({...navigationLayout,obstacles:[...navigationLayout.obstacles,
        ...blockers().map(b=>({type:'circle',x:b.group.position.x,z:b.group.position.z,radius:b.hitboxRadius+.1})),
      ]}).route(from,to),
    });
    group.position.set(position.x,groundHeight(position,layout),position.z);scene.add(group);
    function updateAnimation(dt){
      // The media clock owns voiced emotes, including buffering and late metadata.
      // Stretch one animation cycle over the chosen recording's actual duration.
      const media=audio.emotePlayback;
      if(syncedEmote)syncEmoteAnimation(current,media);
      mixer.update(dt);
    }
    return {group,position,brain,mixer,audio,updateAnimation};
  });
  return {
    bodies,
    stopAudio(){for(const npc of npcs)npc.audio.stop()},
    update(dt,player,dancing,danceId,playerRadius=.4){
      playerBody={group:player,hitboxRadius:playerRadius};
      for(const npc of npcs){
        const distance=Math.hypot(npc.position.x-player.position.x,npc.position.z-player.position.z);
        npc.audio.update({distance,audible:distance<NPC_INTERACTION_RANGE&&navigation.clear(npc.position,player.position,.05),
          enabled:!document.hidden&&document.hasFocus()&&navigator.userActivation?.hasBeenActive!==false,playerChampion:'Garen'});
        const previousX=npc.position.x,previousZ=npc.position.z;
        npc.brain.update(dt,{player:player.position,dancing,danceId});
        // Only actual travel triggers movement VO, never blocked Run attempts.
        if(npc.position.x!==previousX||npc.position.z!==previousZ)npc.audio.move();
        npc.group.position.x=npc.position.x;npc.group.position.z=npc.position.z;
        npc.group.position.y=groundHeight(npc.position,layout);
        npc.group.rotation.y=npc.position.heading;npc.updateAnimation(dt);
      }
    },
  };
}
