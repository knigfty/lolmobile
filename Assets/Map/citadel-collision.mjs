// Closed courtyard: bounds are the inner wall faces, before player-radius inset.
// Building footprints come from the same layout file exported with the GLB.
export function containsPosition(position,radius,layout){
  const b=layout.bounds,epsilon=1e-6;
  if(position.x<b.minX+radius-epsilon||position.x>b.maxX-radius+epsilon||position.z<b.minZ+radius-epsilon||position.z>b.maxZ-radius+epsilon)return false;
  for(const obstacle of layout.obstacles){
    if(obstacle.type==='circle'){
      if(Math.hypot(position.x-obstacle.x,position.z-obstacle.z)<obstacle.radius+radius-epsilon)return false;
    }else if(position.x>obstacle.minX-radius+epsilon&&position.x<obstacle.maxX+radius-epsilon&&position.z>obstacle.minZ-radius+epsilon&&position.z<obstacle.maxZ+radius-epsilon)return false;
  }
  return true;
}
export function constrainPosition(position,radius,layout){
  const b=layout.bounds;
  for(let pass=0;pass<8;pass++){
    position.x=Math.max(b.minX+radius,Math.min(b.maxX-radius,position.x));
    position.z=Math.max(b.minZ+radius,Math.min(b.maxZ-radius,position.z));
    for(const o of layout.obstacles){
      if(o.type==='circle'){
        const dx=position.x-o.x,dz=position.z-o.z,d=Math.hypot(dx,dz),r=o.radius+radius;
        if(d<r){position.x=o.x+(d>1e-8?dx/d:0)*r;position.z=o.z+(d>1e-8?dz/d:1)*r}
      }else{
        const minX=o.minX-radius,maxX=o.maxX+radius,minZ=o.minZ-radius,maxZ=o.maxZ+radius;
        if(position.x>minX&&position.x<maxX&&position.z>minZ&&position.z<maxZ){
          const edges=[position.x-minX,maxX-position.x,position.z-minZ,maxZ-position.z];
          const edge=edges.indexOf(Math.min(...edges));
          if(edge===0)position.x=minX;else if(edge===1)position.x=maxX;else if(edge===2)position.z=minZ;else position.z=maxZ;
        }
      }
    }
  }
  return position;
}

// Feet follow the highest tread under the actor. Geometry and metadata share
// these footprints; no radius expansion, which would lift actors before a step.
export function groundHeight(position,layout){
  let height=layout.ground_y??0;
  for(const surface of layout.walkable_surfaces??[]){
    if(position.x>=surface.minX&&position.x<=surface.maxX&&position.z>=surface.minZ&&position.z<=surface.maxZ)height=Math.max(height,surface.height);
  }
  return height;
}
