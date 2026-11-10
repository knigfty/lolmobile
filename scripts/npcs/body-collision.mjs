// Shared swept circles for moving NPC bodies and player collision tests.
export function bodyPathClear(from,to,radius,bodies){
  const dx=to.x-from.x,dz=to.z-from.z,length2=dx*dx+dz*dz;
  return bodies.every(body=>{
    const p=body.group.position,r=radius+body.hitboxRadius;
    const t=length2?Math.max(0,Math.min(1,((p.x-from.x)*dx+(p.z-from.z)*dz)/length2)):0;
    return Math.hypot(from.x+t*dx-p.x,from.z+t*dz-p.z)>=r-1e-7;
  });
}
export function overlapsBody(position,radius,body){
  return Math.hypot(position.x-body.group.position.x,position.z-body.group.position.z)<radius+body.hitboxRadius-1e-7;
}
export function separateBody(position,radius,body,dx,dz){
  if(!overlapsBody(position,radius,body))return;
  let nx=position.x-body.group.position.x,nz=position.z-body.group.position.z,d=Math.hypot(nx,nz);
  if(d<1e-8){nx=-dx||1;nz=-dz;d=Math.hypot(nx,nz)}
  const r=radius+body.hitboxRadius;
  position.x=body.group.position.x+nx/d*r;position.z=body.group.position.z+nz/d*r;
}
