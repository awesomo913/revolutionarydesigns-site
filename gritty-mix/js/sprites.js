// Botanical game textures. The atlas uses a chroma key, resolved once by the texture loader.
const BOTANICAL = {
  ready: false, failed: false, textures: {}, profiles: {}, urls: {}, scionUrls: {},
  regions: {
    'trichocereus-pachanoi': [94,4,182,323],
    'trichocereus-bridgesii': [380,0,206,327],
    'trichocereus-peruvianus': [680,0,224,330],
    'trichocereus-terscheckii': [981,0,254,329],
    'trichocereus-scopulicola': [73,331,216,310],
    'echinocactus-horizonthalonius': [313,335,322,307],
    'echinocactus-grusonii': [636,333,311,310],
    'tephrocactus-articulatus': [971,326,273,315],
    'lophophora-williamsii': [25,642,299,257],
    'astrophytum-asterias': [328,643,299,253],
    'haworthia-truncata': [628,651,328,241],
    'aztekium-ritteri': [956,637,290,266],
    'ariocarpus-fissuratus': [8,904,335,331],
    'pereskiopsis': [344,890,280,353],
    'myrtillocactus': [686,889,210,355],
    'hylocereus': [1006,885,207,360]
  },
  async init() {
    const load=src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Unable to load '+src));image.src=src;});
      try {
        const images=await Promise.all([load('assets/botanical-atlas-v1.png'),load('assets/nursery-trio-v2.webp'),load('assets/peyote-v3.webp'),load('assets/terracotta-grit-v1.webp')]);
        const revised={'lophophora-williamsii':[0,0,625,887],'astrophytum-asterias':[625,0,625,887],'trichocereus-pachanoi':[1250,0,524,887]};
        for(const [image,regions] of [[images[0],this.regions],[images[1],revised],[images[2],{'lophophora-williamsii':[0,0,images[2].width,images[2].height]}],[images[3],{vessel:[0,0,images[3].width,images[3].height]}]]) {
        for(const [id,region] of Object.entries(regions)) {
          const [sx,sy,w,h]=region,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
          const x=canvas.getContext('2d',{willReadFrequently:true});x.drawImage(image,sx,sy,w,h,0,0,w,h);
          const pixels=x.getImageData(0,0,w,h),p=pixels.data;
          let left=w,top=h,right=0,bottom=0;
          for(let i=0;i<p.length;i+=4){
            const spill=Math.min(p[i],p[i+2])-p[i+1];
            const alpha=spill>22?Math.max(0,1-(spill-22)/100):1;
            if(alpha<1){p[i]=Math.min(p[i],p[i+1]+35);p[i+2]=Math.min(p[i+2],p[i+1]+45);}
            p[i+3]=Math.round(alpha*255);
            if(alpha>.45){const px=(i/4)%w,py=Math.floor(i/4/w);left=Math.min(left,px);right=Math.max(right,px);top=Math.min(top,py);bottom=Math.max(bottom,py);}
          }
          x.putImageData(pixels,0,0);
          const texture=document.createElement('canvas');texture.width=right-left+1;texture.height=bottom-top+1;
          texture.getContext('2d').drawImage(canvas,left,top,texture.width,texture.height,0,0,texture.width,texture.height);
          if(id==='vessel'){this.potTexture=texture;this.potUrl=texture.toDataURL('image/png');}
          else {this.textures[id]=texture;this.profiles[id]=this.profile(texture);this.urls[id]=texture.toDataURL('image/png');}
        }
        }
        // Keep the Star Cactus crown above a straight horizontal midpoint cut.
        const star=this.textures['astrophytum-asterias'],half=document.createElement('canvas');
        half.width=star.width;half.height=Math.round(star.height*this.scionFraction('astrophytum-asterias'));
        half.getContext('2d').drawImage(star,0,0);
        this.scionUrls['astrophytum-asterias']=half.toDataURL('image/png');
        this.ready=true;this.refresh();
      }catch(error){this.failed=true;console.error('Botanical texture preparation failed',error);this.refresh();}
  },
  refresh(){
    if(typeof G!=='undefined'&&G.state&&typeof STUDIO!=='undefined'){G.renderNursery();if(typeof BENCH!=='undefined'&&BENCH.job)BENCH.draw(performance.now());}
  },
  column(id){return /trichocereus|myrtillocactus|hylocereus/.test(id);},
  profile(texture){
    // Follow the plant body, excluding isolated spines and transparent sprite margins.
    const w=texture.width,h=texture.height,p=texture.getContext('2d').getImageData(0,0,w,h).data,rows=[];
    for(let row=0;row<=80;row++){
      const y=Math.min(h-1,Math.round(row/80*(h-1))),weights=[];let total=0;
      for(let col=0;col<w;col++){const a=p[(y*w+col)*4+3]/255;weights.push(a);total+=a;}
      let sum=0,left=w/2,right=w/2;
      for(let col=0;col<w;col++){sum+=weights[col];if(sum<total*.035)left=col;if(sum<total*.965)right=col;}
      rows.push(total>2?[left/w,right/w]:[.47,.53]);
    }
    return rows;
  },
  edge(id,fraction){
    const rows=this.profiles[id],p=Math.max(0,Math.min(80,fraction*80)),i=Math.floor(p),f=p-i;
    return rows[i].map((v,k)=>v+((rows[Math.min(80,i+1)][k])-v)*f);
  },
  rootId(root){return root==='trichocereus-pachanoi-root'?'trichocereus-pachanoi':root||'trichocereus-pachanoi';},
  scionFraction(id){return /^(astrophytum-asterias|tephrocactus-articulatus)$/.test(id)?.5:.9;},
  nursery(c){
    if(!this.ready)return '<div class="sprite-loading" role="status">'+(this.failed?'Plant art could not load. Refresh to retry.':'Preparing botanical sprites…')+'</div>';
    const column=this.column(c.speciesId),size=c.stage==='seedling'?.6:c.stage==='juvenile'?.84:1;
    const root=this.rootId(c.rootstock),halfScion=c.grafted&&c.speciesId==='astrophytum-asterias';
    const image=halfScion?this.scionUrls[c.speciesId]:this.urls[c.speciesId];
    if(!image)return '';
    const sprite=(url,cls)=>`<img class="${cls}" src="${url}" alt="" draggable="false">`;
    return `<div class="botanical-pot ${c.grafted?'is-grafted':''} ${column?'is-column':'is-globular'} ${c.speciesId==='lophophora-williamsii'?'is-peyote':''}" style="--growth:${size}"><div class="botanical-shadow"></div>${sprite(this.potUrl,'botanical-vessel')}<div class="botanical-specimen">${c.grafted?sprite(this.urls[root],'nursery-stock')+sprite(image,'nursery-scion'+(halfScion?' is-half':'')):sprite(image,'nursery-plant')}</div>${sprite(this.potUrl,'botanical-vessel vessel-front')}</div>`;
  },
  workshop(x,j,time){
    if(!this.ready){x.fillStyle='#f5edc9';x.font='19px "DM Sans",sans-serif';x.fillText(this.failed?'Plant art unavailable — refresh to retry.':'Preparing botanical specimens…',95,190);return;}
    const c=COLLECTION.get(j.plant),species=c?.speciesId||'astrophytum-asterias';
    const root=this.rootId(j.root),stock=this.textures[root],scion=this.textures[species];
    if(!stock||!scion)return;
    const micro=root==='pereskiopsis',rootWidth=micro?184:root==='hylocereus'?148:162;
    const stockTop=280,stockBase=523,cx=320;
    // Remove the growing apex from the stock; the exposed cut has its own surface.
    const cutFraction=micro?.18:.23;
    // Contact shadow and foreground grit embed the stem in the soil plane.
    x.save();x.fillStyle='#211d1670';x.beginPath();x.ellipse(cx,516,micro?17:rootWidth*.43,8,0,0,Math.PI*2);x.fill();x.restore();
    x.drawImage(stock,0,stock.height*cutFraction,stock.width,stock.height*(1-cutFraction),cx-rootWidth/2,stockTop,rootWidth,stockBase-stockTop);
    // Foreground mineral particles overlap the very bottom of the stock.
    if(this.potTexture){x.save();x.beginPath();x.rect(190,522,260,150);x.clip();x.drawImage(this.potTexture,190,456,260,216);x.restore();}
    const cutWidth=micro?12:root==='hylocereus'?49:55;
    const cut=x.createLinearGradient(cx-cutWidth,stockTop,cx+cutWidth,stockTop+13);cut.addColorStop(0,'#c8d99c');cut.addColorStop(.6,'#e1e8af');cut.addColorStop(1,'#9fb77b');
    x.fillStyle=cut;x.beginPath();x.ellipse(cx,stockTop,cutWidth,micro?4:9,0,0,Math.PI*2);x.fill();
    x.strokeStyle='#668a4f';x.lineWidth=2;x.beginPath();x.ellipse(cx,stockTop,cutWidth*.55,6.5,0,0,Math.PI*2);x.stroke();
    const col=this.column(species),scionWidth=micro?(col?29:43):(col?80:133);
    const cropHeight=Math.round(scion.height*this.scionFraction(species));
    const scionHeight=cropHeight/scion.width*scionWidth;
    const position=BENCH.alignment().offset*(micro?.13:.55),sx=cx+(j.stage>=2?position:0);
    let bottom=j.stage<2?220+Math.sin(time*1.5)*3:j.stage===2?245:stockTop+1;
    const motion=!matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(j.stage===3&&motion&&time>0){const f=Math.min(1,Math.max(0,(time*1000-BENCH.transitionAt)/550));bottom=245+36*(1-Math.pow(1-f,3));}
    const top=bottom-scionHeight;
    this.graftBounds={left:Math.min(sx-scionWidth/2,cx-cutWidth)-14,right:Math.max(sx+scionWidth/2,cx+cutWidth)+14,top:top-14,bottom:stockTop+68};
    // A flat basal cut seats on the stock instead of an oval hovering above it.
    x.save();x.shadowColor='#102b2180';x.shadowBlur=j.stage>=3?6:0;x.shadowOffsetY=3;
    x.drawImage(scion,0,0,scion.width,cropHeight,sx-scionWidth/2,top,scionWidth,scionHeight);x.restore();
    if(j.stage<3){x.fillStyle='#cddca1';x.beginPath();x.ellipse(sx,bottom,scionWidth*.34,5,0,0,Math.PI*2);x.fill();}
    if(j.stage===1){x.save();x.translate(cx,stockTop);x.rotate(j.cut*Math.PI/180);x.fillStyle='#b9c8c0';x.beginPath();x.moveTo(-126,-10);x.lineTo(107,-10);x.lineTo(128,1);x.lineTo(-126,1);x.closePath();x.fill();x.fillStyle='#594831';x.fillRect(-191,-17,73,24);x.restore();}
    if(j.stage>=3&&j.stage<6)this.bands(x,{sx,top,bottom,width:scionWidth,tension:j.tension,method:j.method,stockX:cx,stockTop,stockHalf:micro?10:rootWidth*.38,species,root,rootWidth,cutFraction});
    if(j.stage===6){x.strokeStyle='#b8ca83';x.lineWidth=2;x.beginPath();x.ellipse(sx,stockTop+1,scionWidth*.34,3,0,0,Math.PI);x.stroke();}
  },
  bands(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf,species,root,rootWidth,cutFraction}){
    if(method==='parafilm'||method==='stocking'){
      this.wrapCap(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf,species,root,rootWidth,cutFraction});return;
    }
    // Tiny Pereskiopsis grafts use short, fine loops attached to a stock collar.
    if(stockHalf<15){
      const y=stockTop+28;
      x.save();x.lineCap='round';x.lineJoin='round';
      for(const offset of [-width*.12,width*.12]){
        x.beginPath();x.moveTo(stockX-9,y);
        x.quadraticCurveTo(sx+offset-width*.4,bottom,sx+offset-width*.2,top+3);
        x.quadraticCurveTo(sx+offset,top-2,sx+offset+width*.2,top+3);
        x.quadraticCurveTo(sx+offset+width*.4,bottom,stockX+9,y);
        x.strokeStyle='#d5ad75';x.lineWidth=2;x.stroke();x.strokeStyle='#f5d9a0';x.lineWidth=.6;x.stroke();
      }
      x.beginPath();x.ellipse(stockX,y,10,3,0,0,Math.PI);x.strokeStyle='#d5ad75';x.lineWidth=2;x.stroke();x.restore();return;
    }
    const slack=Math.max(0,55-tension)*.38;
    // Each band is a closed loop: over the crown, down both sides, and under the pot.
    for(const side of [-1,1]){
      const offset=side*Math.min(16,width*.13),apex=sx+offset;
      const left=side===-1?203:240,right=side===-1?401:439;
      const curve=()=>{x.beginPath();x.moveTo(left+45,664);x.lineTo(left,527);x.quadraticCurveTo(apex-width*.52-slack,bottom+32,apex-width*.25,top+12);x.quadraticCurveTo(apex,top-3,apex+width*.25,top+12);x.quadraticCurveTo(apex+width*.52+slack,bottom+32,right,527);x.lineTo(right-45,664);x.quadraticCurveTo((left+right)/2,683,left+45,664);};
      x.save();x.lineCap='round';x.lineJoin='round';
      curve();x.strokeStyle='#47322355';x.lineWidth=8;x.stroke();
      curve();x.strokeStyle='#d5ad75';x.lineWidth=6;x.stroke();
      curve();x.strokeStyle='#f5d9a0';x.lineWidth=1.5;x.stroke();
      x.restore();
    }
  },
  wrapCap(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf,species,root,rootWidth,cutFraction}){
    const mesh=method==='stocking',slack=Math.max(0,55-tension)/55;
    const height=bottom-top,apex=top-2,collarY=stockTop+(stockHalf<15?23:34);
    const margin=1.4+slack*2.2,left=[[sx,apex]],right=[[sx,apex]];
    // The material follows the actual sprite, including tall and offset scions.
    // Explicit apex points keep the cover above the crown rather than across it.
    for(let i=1;i<=24;i++){
      const f=i/24,edge=this.edge(species,f*this.scionFraction(species));
      const y=top+f*height;
      left.push([sx+(edge[0]-.5)*width-margin,y]);
      right.push([sx+(edge[1]-.5)*width+margin,y]);
    }
    for(let i=0;i<=4;i++){
      const y=stockTop+5+i*(collarY-stockTop-5)/4;
      const edge=stockHalf<15?[.5-10/rootWidth,.5+10/rootWidth]:this.edge(root,cutFraction+(y-stockTop)/243*(1-cutFraction));
      left.push([stockX+(edge[0]-.5)*rootWidth-margin,y]);
      right.push([stockX+(edge[1]-.5)*rootWidth+margin,y]);
    }
    const l=left.at(-1)[0],r=right.at(-1)[0],middle=(l+r)/2;
    const outline=[...left,[middle,collarY+4],...right.slice(1).reverse()];
    const cap=()=>{
      const last=outline.at(-1),first=outline[0];
      x.beginPath();x.moveTo((last[0]+first[0])/2,(last[1]+first[1])/2);
      for(let i=0;i<outline.length;i++){
        const p=outline[i],n=outline[(i+1)%outline.length];x.quadraticCurveTo(p[0],p[1],(p[0]+n[0])/2,(p[1]+n[1])/2);
      }
      x.closePath();
    };
    x.save();cap();
    const material=x.createLinearGradient(sx-width/2,0,sx+width/2,0);
    material.addColorStop(0,mesh?'#dac7af45':'#f4f5ef91');
    material.addColorStop(.22,mesh?'#e6d8bc15':'#fafff53c');
    material.addColorStop(.65,mesh?'#d4c3a51b':'#f5f8f150');
    material.addColorStop(1,mesh?'#e5d2b34a':'#eaf0e779');
    x.fillStyle=material;x.fill();x.strokeStyle=mesh?'#dfccaa70':'#fbfff48a';x.lineWidth=.85;x.stroke();
    x.save();cap();x.clip();
    if(mesh){
      // Fine stretched nylon, with a slightly curved weave over the rounded body.
      x.strokeStyle='#ecddbf85';x.lineWidth=.45;
      const spacing=stockHalf<15?2.5:3.5;
      for(const direction of [-1,1])for(let q=-350;q<350;q+=spacing){
        x.beginPath();x.moveTo(sx+q,apex-5);
        x.quadraticCurveTo(sx+q+direction*(collarY-apex)*.25+3,(apex+collarY)/2,sx+q+direction*(collarY-apex)*.5,collarY+8);x.stroke();
      }
    }else{
      // Stretched waxy film: broad translucent overlaps and fine gathered folds.
      // Avoid bright horizontal rings that read as a rigid plastic collar.
      x.beginPath();x.moveTo(sx-width*.18,apex-2);
      x.bezierCurveTo(sx+width*.18,top+height*.3,sx-width*.05,bottom-12,r-6,collarY+5);
      x.lineTo(r+4,collarY+5);
      x.bezierCurveTo(sx+width*.2,bottom-12,sx+width*.35,top+height*.3,sx+width*.08,apex-2);
      x.closePath();x.fillStyle='#f4faf233';x.fill();
      for(const side of [-1,1]){
        x.beginPath();x.moveTo(sx+side*width*.14,apex+5);
        x.bezierCurveTo(sx+side*width*.45,top+height*.4,sx+side*width*.3,bottom-5,middle+side*(r-l)*.3,collarY+2);
        x.strokeStyle='#fafff639';x.lineWidth=3.5;x.stroke();
        x.strokeStyle='#fafff38a';x.lineWidth=.7;x.stroke();
      }
      for(let i=0;i<3;i++){
        const y=stockTop+9+i*7;
        x.beginPath();x.moveTo(l-3,y-5);x.bezierCurveTo(middle-12,y+4,middle+12,y+8,r+3,y-1);
        x.lineTo(r+3,y+5);x.bezierCurveTo(middle+12,y+14,middle-12,y+10,l-3,y+1);x.closePath();
        x.fillStyle='#f5faf02c';x.fill();
        x.beginPath();x.moveTo(l-3,y-5);x.bezierCurveTo(middle-12,y+4,middle+12,y+8,r+3,y-1);
        x.strokeStyle='#fafff26b';x.lineWidth=.7;x.stroke();
      }
      for(let i=0;i<5;i++){
        x.beginPath();x.moveTo(r-2-i*2.2,collarY-1);
        x.quadraticCurveTo(r-8-i*2,stockTop+18,sx+width*(.2-i*.035),bottom-5-i*3);
        x.strokeStyle='#fafff566';x.lineWidth=.6;x.stroke();
      }
    }
    x.restore();
    if(mesh){
      x.beginPath();x.moveTo(l,collarY-2);x.quadraticCurveTo(middle,collarY+6,r,collarY-2);
      x.strokeStyle='#c6a16b';x.lineWidth=2.6;x.stroke();
      x.strokeStyle='#ead5a2';x.lineWidth=.7;x.stroke();
    }
    x.restore();
  }
};
BOTANICAL.init();
