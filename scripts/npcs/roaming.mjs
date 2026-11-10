import {containsPosition} from '../../Assets/Map/citadel-collision.mjs';

export const NPC_RADIUS=.55;
// Deliberate stops on the existing map, not random coordinates. The hall stops
// are inside the citadel; fountains and training stops are beside their props.
export const LANDMARKS=[
  {name:'Citadel hall west',x:-3,z:-21},
  {name:'Citadel hall east',x:3,z:-21},
  {name:'Central square',x:0,z:8},
  {name:'West fountain',x:-20,z:7},
  {name:'East fountain',x:20,z:7},
  {name:'Dummy training',x:-20,z:29.5},
];
const distance=(a,b)=>Math.hypot(a.x-b.x,a.z-b.z);

export function createNavigation(layout,radius=NPC_RADIUS){
  // Exact swept-circle checks avoid corner cutting, even across thin walls.
  function clear(a,b,r=radius){
    if(!containsPosition(a,r,layout)||!containsPosition(b,r,layout))return false;
    const dx=b.x-a.x,dz=b.z-a.z,length2=dx*dx+dz*dz;
    for(const o of layout.obstacles){
      if(o.type==='circle'){
        const t=length2?Math.max(0,Math.min(1,((o.x-a.x)*dx+(o.z-a.z)*dz)/length2)):0;
        if(Math.hypot(a.x+t*dx-o.x,a.z+t*dz-o.z)<o.radius+r)return false;
      }else{
        let lo=0,hi=1;
        for(const [start,delta,min,max] of [[a.x,dx,o.minX-r,o.maxX+r],[a.z,dz,o.minZ-r,o.maxZ+r]]){
          if(Math.abs(delta)<1e-10){if(start<min||start>max){lo=2;break}}
          else{const t1=(min-start)/delta,t2=(max-start)/delta;lo=Math.max(lo,Math.min(t1,t2));hi=Math.min(hi,Math.max(t1,t2))}
        }
        if(lo<=hi)return false;
      }
    }
    return true;
  }
  const nodes=[],grid=new Map();
  for(let x=Math.ceil(layout.bounds.minX+radius);x<=layout.bounds.maxX-radius;x++){
    for(let z=Math.ceil(layout.bounds.minZ+radius);z<=layout.bounds.maxZ-radius;z++){
      const p={x,z};if(containsPosition(p,radius,layout)){p.id=nodes.length;nodes.push(p);grid.set(`${x},${z}`,p)}
    }
  }
  const edges=new Map();
  function neighbors(p){
    if(!edges.has(p.id)){
      const result=[];
      for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++){
        if(!dx&&!dz)continue;
        const q=grid.get(`${p.x+dx},${p.z+dz}`);if(q&&clear(p,q))result.push(q);
      }
      edges.set(p.id,result);
    }
    return edges.get(p.id);
  }
  function nearest(p){
    return nodes.filter(n=>distance(n,p)<=2).sort((a,b)=>distance(a,p)-distance(b,p)).find(n=>clear(p,n));
  }
  function route(start,end){
    if(clear(start,end))return [{x:end.x,z:end.z}];
    const first=nearest(start),last=nearest(end);if(!first||!last)return [];
    const open=new Set([first.id]),closed=new Set(),cost=new Map([[first.id,0]]),parent=new Map();
    while(open.size){
      let id,best=Infinity;
      for(const candidate of open){const score=cost.get(candidate)+distance(nodes[candidate],last);if(score<best){best=score;id=candidate}}
      if(id===last.id){
        const path=[end];let cursor=id;
        while(cursor!==undefined){path.unshift(nodes[cursor]);cursor=parent.get(cursor)}
        // Smooth only with the same swept collision test used while moving.
        const smooth=[];let from=start,index=0;
        while(index<path.length){let next=index;while(next+1<path.length&&clear(from,path[next+1]))next++;smooth.push({x:path[next].x,z:path[next].z});from=path[next];index=next+1}
        return smooth;
      }
      open.delete(id);closed.add(id);
      for(const next of neighbors(nodes[id])){
        if(closed.has(next.id))continue;
        const score=cost.get(id)+distance(nodes[id],next);
        if(score<(cost.get(next.id)??Infinity)){cost.set(next.id,score);parent.set(next.id,id);open.add(next.id)}
      }
    }
    return [];
  }
  return {clear,route};
}

export function createRoamer({position,navigation,play,random=Math.random,startIndex=2}){
  let state='idle',remaining=0,idleChange=0,idleIndex=0,near=false,lastDance=0,route=[],destination=startIndex,visits=[];
  const choose=items=>items[Math.floor(random()*items.length)];
  function idle(){state='idle';remaining=40+random()*30;idleChange=play(`Idle${idleIndex%4+1}`);idleIndex++}
  function react(name,player){
    // Face immediately BEFORE starting the emote, including reactions mid-walk.
    position.heading=Math.atan2(player.x-position.x,player.z-position.z);
    state='react';remaining=play(name,true);route=[];
  }
  idle();
  return {
    get state(){return state},get destination(){return LANDMARKS[destination].name},
    update(dt,{player,dancing=false,danceId=0}){
      const d=distance(position,player),visible=d<=7&&navigation.clear(position,player,.05);
      const entered=!near&&d<=4&&visible;
      if(d>6)near=false;
      if(entered)near=true;
      // One independent 50/50 roll per dance performance, also when the NPC
      // comes into range of an already dancing player. Dance supersedes joke.
      if(dancing&&danceId!==lastDance&&visible){lastDance=danceId;react(random()<.5?'Dance':'Laugh',player)}
      else if(entered&&state!=='react'&&random()<.3)react('Joke',player);
      if(state==='react'){
        remaining-=dt;if(remaining<=0)idle();return;
      }
      if(state==='idle'){
        remaining-=dt;idleChange-=dt;
        if(idleChange<=0){idleChange=play(`Idle${idleIndex%4+1}`);idleIndex++}
        if(remaining>0)return;
        if(!visits.length){visits=LANDMARKS.map((_,i)=>i).filter(i=>i!==destination)}
        destination=choose(visits);visits=visits.filter(i=>i!==destination);
        route=navigation.route(position,LANDMARKS[destination]);
        if(!route.length){idle();return}
        state='walk';play('Run');
      }
      const target=route[0];if(!target){idle();return}
      const length=distance(position,target),step=Math.min(length,1.65*dt);
      if(length<.025){route.shift();if(!route.length)idle();return}
      const next={x:position.x+(target.x-position.x)/length*step,z:position.z+(target.z-position.z)/length*step};
      // Yield to the player instead of marching through their body.
      if(distance(next,player)<1.15){play('Idle1');return}
      if(!navigation.clear(position,next)){idle();return}
      play('Run');position.heading=Math.atan2(target.x-position.x,target.z-position.z);
      position.x=next.x;position.z=next.z;
    },
  };
}
