// Small cached map: redraw architecture only once, player marker at 10 Hz.
export function kingdomZone(position,layout){
 const h=layout.hall;
 if(h&&position.x>h.minX&&position.x<h.maxX&&position.z>h.minZ&&position.z<h.maxZ)return 'Citadel entrance hall';
 if(Math.abs(position.x)>72)return position.x<0?'West gardens':'East gardens';
 if(position.z>85)return 'Royal courtyard';
 return 'Ceremonial plaza';
}
export function createKingdomNavigation(layout){
 const canvas=document.getElementById('kingdom-map'),label=document.getElementById('kingdom-zone');
 const context=canvas.getContext('2d'),back=document.createElement('canvas');
 back.width=canvas.width;back.height=canvas.height;
 const c=back.getContext('2d'),b=layout.bounds,pad=10;
 const sx=(canvas.width-pad*2)/(b.maxX-b.minX),sz=(canvas.height-pad*2)/(b.maxZ-b.minZ);
 const x=v=>pad+(v-b.minX)*sx,z=v=>pad+(v-b.minZ)*sz;
 c.fillStyle='#172e38';c.fillRect(0,0,back.width,back.height);
 c.fillStyle='#597061';c.fillRect(pad,pad,back.width-2*pad,back.height-2*pad);
 c.fillStyle='#d8ceb0';c.fillRect(x(-65),z(-86),130*sx,170*sz);
 c.fillStyle='#b0a78d';c.fillRect(x(layout.hall.minX),z(layout.hall.minZ),61*sx,64*sz);
 c.fillStyle='#243942';
 for(const o of layout.obstacles){
  if(o.type==='circle'){c.beginPath();c.ellipse(x(o.x),z(o.z),Math.max(.5,o.radius*sx),Math.max(.5,o.radius*sz),0,0,Math.PI*2);c.fill()}
  else c.fillRect(x(o.minX),z(o.minZ),(o.maxX-o.minX)*sx,(o.maxZ-o.minZ)*sz);
 }
 c.fillStyle='#eee3c7';c.font='9px system-ui';c.textAlign='center';c.fillText('CITADEL',canvas.width/2,z(-120));
 c.fillText('N',canvas.width/2,8);
 let elapsed=1;
 return (position,heading,dt)=>{
  elapsed+=dt;if(elapsed<.1)return;elapsed=0;
  context.drawImage(back,0,0);context.save();context.translate(x(position.x),z(position.z));context.rotate(-heading);
  context.fillStyle='#ffe69d';context.strokeStyle='#15242c';context.lineWidth=1.2;
  context.beginPath();context.moveTo(0,5);context.lineTo(-3,-3);context.lineTo(3,-3);context.closePath();context.fill();context.stroke();context.restore();
  label.textContent=kingdomZone(position,layout);
 };
}
