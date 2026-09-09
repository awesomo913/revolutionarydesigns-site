// Botanical game textures. The atlas uses a chroma key, resolved once by the texture loader.
const BOTANICAL = {
  ready: false, failed: false, textures: {}, urls: {}, scionUrls: {},
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
        const images=await Promise.all([load('assets/botanical-atlas-v1.png'),load('assets/nursery-trio-v2.webp')]);
        const revised={'lophophora-williamsii':[0,0,625,887],'astrophytum-asterias':[625,0,625,887],'trichocereus-pachanoi':[1250,0,524,887]};
        for(const [image,regions] of [[images[0],this.regions],[images[1],revised]]) {
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
          this.textures[id]=texture;this.urls[id]=texture.toDataURL('image/png');
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
  rootId(root){return root==='trichocereus-pachanoi-root'?'trichocereus-pachanoi':root||'trichocereus-pachanoi';},
  scionFraction(id){return /^(astrophytum-asterias|tephrocactus-articulatus)$/.test(id)?.5:.9;},
  nursery(c){
    if(!this.ready)return '<div class="sprite-loading" role="status">'+(this.failed?'Plant art could not load. Refresh to retry.':'Preparing botanical sprites…')+'</div>';
    const column=this.column(c.speciesId),size=c.stage==='seedling'?.6:c.stage==='juvenile'?.84:1;
    const root=this.rootId(c.rootstock),halfScion=c.grafted&&c.speciesId==='astrophytum-asterias';
    const image=halfScion?this.scionUrls[c.speciesId]:this.urls[c.speciesId];
    if(!image)return '';
    const sprite=(url,cls)=>`<img class="${cls}" src="${url}" alt="" draggable="false">`;
    return `<div class="botanical-pot ${c.grafted?'is-grafted':''} ${column?'is-column':'is-globular'} ${c.speciesId==='lophophora-williamsii'?'is-peyote':''}" style="--growth:${size}"><div class="botanical-shadow"></div><div class="botanical-specimen">${c.grafted?sprite(this.urls[root],'nursery-stock')+sprite(image,'nursery-scion'+(halfScion?' is-half':'')):sprite(image,'nursery-plant')}</div><div class="botanical-soil"></div><div class="botanical-clay"></div><div class="botanical-rim"></div></div>`;
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
    x.save();x.fillStyle='#473e2a';x.beginPath();x.ellipse(cx,524,micro?10:rootWidth*.34,4,0,0,Math.PI*2);x.fill();
    for(let i=0;i<7;i++){const spread=micro?16:rootWidth*.65,px=cx+(i/6-.5)*spread,py=521+(i%3)*1.6;x.fillStyle=i%2?'#aa9e78':'#c2b68e';x.beginPath();x.ellipse(px,py,2.3,1.6,i*.7,0,Math.PI*2);x.fill();}x.restore();
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
    // A flat basal cut seats on the stock instead of an oval hovering above it.
    x.save();x.shadowColor='#102b2180';x.shadowBlur=j.stage>=3?6:0;x.shadowOffsetY=3;
    x.drawImage(scion,0,0,scion.width,cropHeight,sx-scionWidth/2,top,scionWidth,scionHeight);x.restore();
    if(j.stage<3){x.fillStyle='#cddca1';x.beginPath();x.ellipse(sx,bottom,scionWidth*.34,5,0,0,Math.PI*2);x.fill();}
    if(j.stage===1){x.save();x.translate(cx,stockTop);x.rotate(j.cut*Math.PI/180);x.fillStyle='#b9c8c0';x.beginPath();x.moveTo(-126,-10);x.lineTo(107,-10);x.lineTo(128,1);x.lineTo(-126,1);x.closePath();x.fill();x.fillStyle='#594831';x.fillRect(-191,-17,73,24);x.restore();}
    if(j.stage>=3&&j.stage<6)this.bands(x,{sx,top,bottom,width:scionWidth,tension:j.tension,method:j.method,stockX:cx,stockTop,stockHalf:micro?10:rootWidth*.38});
    if(j.stage===6){x.strokeStyle='#b8ca83';x.lineWidth=2;x.beginPath();x.ellipse(sx,stockTop+1,scionWidth*.34,3,0,0,Math.PI);x.stroke();}
  },
  bands(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf}){
    if(method==='parafilm'||method==='stocking'){
      this.wrapCap(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf});return;
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
      const curve=()=>{x.beginPath();x.moveTo(left+19,636);x.lineTo(left,514);x.quadraticCurveTo(apex-width*.52-slack,bottom+32,apex-width*.25,top+12);x.quadraticCurveTo(apex,top-3,apex+width*.25,top+12);x.quadraticCurveTo(apex+width*.52+slack,bottom+32,right,514);x.lineTo(right-19,636);x.quadraticCurveTo((left+right)/2,655,left+19,636);};
      x.save();x.lineCap='round';x.lineJoin='round';
      curve();x.strokeStyle='#47322355';x.lineWidth=8;x.stroke();
      curve();x.strokeStyle='#d5ad75';x.lineWidth=6;x.stroke();
      curve();x.strokeStyle='#f5d9a0';x.lineWidth=1.5;x.stroke();
      x.restore();
    }
  },
  wrapCap(x,{sx,top,bottom,width,tension,method,stockX,stockTop,stockHalf}){
    // Film and stocking end at the stock collar, not at the pot base.
    const mesh=method==='stocking',slack=Math.max(0,55-tension)/55;
    const half=width/2+2+slack*4,collarY=stockTop+Math.max(22,Math.min(48,stockHalf*.7));
    const neck=stockHalf+2,apex=top-2-slack*4;
    const cap=()=>{
      x.beginPath();x.moveTo(stockX-neck,collarY);
      x.bezierCurveTo(stockX-neck-3,stockTop+12,sx-half-3,bottom+5,sx-half,top+(bottom-top)*.52);
      x.bezierCurveTo(sx-half*.88,apex,sx+half*.88,apex,sx+half,top+(bottom-top)*.52);
      x.bezierCurveTo(sx+half+3,bottom+5,stockX+neck+3,stockTop+12,stockX+neck,collarY);
      x.quadraticCurveTo(stockX,collarY+9,stockX-neck,collarY);x.closePath();
    };
    x.save();cap();
    const material=x.createLinearGradient(sx-half,0,sx+half,0);
    material.addColorStop(0,mesh?'#dcc5a947':'#fcf9de55');material.addColorStop(.35,mesh?'#dfccaf18':'#f8ffe918');material.addColorStop(.8,mesh?'#ead7b52b':'#faffed33');material.addColorStop(1,mesh?'#c8ae8d50':'#f8f4d66b');
    x.fillStyle=material;x.fill();x.strokeStyle=mesh?'#e2cda56b':'#fff9db7a';x.lineWidth=1.3;x.stroke();
    x.save();cap();x.clip();
    if(mesh){
      // Crossed threads cover the whole stretched fabric rather than dotted straps.
      x.strokeStyle='#e9d6b88c';x.lineWidth=.8;
      const spacing=stockHalf<15?4:6;
      for(const direction of [-1,1])for(let q=-350;q<350;q+=spacing){x.beginPath();x.moveTo(sx+q,apex-10);x.lineTo(sx+q+direction*(collarY-apex)*.48,collarY+12);x.stroke();}
    }else{
      // Thin film: overlapping edges and a few folds converge toward the collar.
      for(const side of [-1,1])for(const fraction of [.35,.7]){
        x.beginPath();x.moveTo(sx+side*half*fraction,apex+7);
        x.bezierCurveTo(sx+side*half*.8,top+(bottom-top)*.65,stockX+side*neck*.7,stockTop+14,stockX+side*neck*.9,collarY+5);
        x.strokeStyle='#fffce256';x.lineWidth=fraction>.5?2:1;x.stroke();
      }
      x.beginPath();x.moveTo(stockX-neck,stockTop+15);x.quadraticCurveTo(stockX,stockTop+24,stockX+neck,stockTop+16);x.strokeStyle='#fff7de66';x.lineWidth=1;x.stroke();
    }
    x.restore();
    // A self-adhered film collar or an elastic around the gathered stocking.
    for(let i=0;i<(mesh?1:3);i++){
      const y=collarY-6+i*3;
      x.beginPath();x.moveTo(stockX-neck,y);x.quadraticCurveTo(stockX,y+9,stockX+neck,y);
      x.strokeStyle=mesh?'#dbb67b':'#f2ebcb80';x.lineWidth=mesh?3:4;x.stroke();
      x.strokeStyle=mesh?'#fff0be99':'#fffde56b';x.lineWidth=.8;x.stroke();
    }
    x.restore();
  }
};
BOTANICAL.init();
