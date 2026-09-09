// Botanical game textures. The atlas uses a chroma key, resolved once by the texture loader.
const BOTANICAL = {
  ready: false, failed: false, textures: {}, urls: {},
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
  init() {
    const image=new Image();
    image.onload=()=>{
      try {
        for(const [id,region] of Object.entries(this.regions)) {
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
        this.ready=true;this.refresh();
      }catch(error){this.failed=true;console.error('Botanical texture preparation failed',error);this.refresh();}
    };
    image.onerror=()=>{this.failed=true;this.refresh();};image.src='assets/botanical-atlas-v1.png';
  },
  refresh(){
    if(typeof G!=='undefined'&&G.state&&typeof STUDIO!=='undefined'){G.renderNursery();if(typeof BENCH!=='undefined'&&BENCH.job)BENCH.draw(performance.now());}
  },
  column(id){return /trichocereus|myrtillocactus|hylocereus/.test(id);},
  rootId(root){return root==='trichocereus-pachanoi-root'?'trichocereus-pachanoi':root||'trichocereus-pachanoi';},
  nursery(c){
    if(!this.ready)return '<div class="sprite-loading" role="status">'+(this.failed?'Plant art could not load. Refresh to retry.':'Preparing botanical sprites…')+'</div>';
    const column=this.column(c.speciesId),size=c.stage==='seedling'?.6:c.stage==='juvenile'?.84:1;
    const root=this.rootId(c.rootstock),image=this.urls[c.speciesId];
    if(!image)return '';
    const sprite=(url,cls)=>`<img class="${cls}" src="${url}" alt="" draggable="false">`;
    return `<div class="botanical-pot ${c.grafted?'is-grafted':''} ${column?'is-column':'is-globular'}" style="--growth:${size}"><div class="botanical-shadow"></div><div class="botanical-specimen">${c.grafted?sprite(this.urls[root],'nursery-stock')+sprite(image,'nursery-scion'):sprite(image,'nursery-plant')}</div><div class="botanical-soil"></div><div class="botanical-clay"></div><div class="botanical-rim"></div></div>`;
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
    const cropHeight=Math.round(scion.height*(species==='tephrocactus-articulatus'?.5:.9));
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
    if(j.stage>=3&&j.stage<6)this.bands(x,{sx,top,bottom,width:scionWidth,tension:j.tension,method:j.method});
    if(j.stage===6){x.strokeStyle='#b8ca83';x.lineWidth=2;x.beginPath();x.ellipse(sx,stockTop+1,scionWidth*.34,3,0,0,Math.PI);x.stroke();}
  },
  bands(x,{sx,top,bottom,width,tension,method}){
    const slack=Math.max(0,55-tension)*.38;
    // Each band is a closed loop: over the crown, down both sides, and under the pot.
    for(const side of [-1,1]){
      const offset=side*Math.min(16,width*.13),apex=sx+offset;
      const left=side===-1?203:240,right=side===-1?401:439;
      const curve=()=>{x.beginPath();x.moveTo(left+19,636);x.lineTo(left,514);x.quadraticCurveTo(apex-width*.52-slack,bottom+32,apex-width*.25,top+12);x.quadraticCurveTo(apex,top-3,apex+width*.25,top+12);x.quadraticCurveTo(apex+width*.52+slack,bottom+32,right,514);x.lineTo(right-19,636);x.quadraticCurveTo((left+right)/2,655,left+19,636);};
      x.save();x.lineCap='round';x.lineJoin='round';
      if(method==='parafilm'){
        curve();x.strokeStyle='#f2edda66';x.lineWidth=13;x.stroke();curve();x.strokeStyle='#ffffebaa';x.lineWidth=1;x.stroke();
      }else if(method==='stocking'){
        curve();x.strokeStyle='#d9c4a577';x.lineWidth=14;x.stroke();x.setLineDash([1,4]);curve();x.strokeStyle='#f0d6b1b0';x.lineWidth=12;x.stroke();
      }else{
        curve();x.strokeStyle='#4e392b55';x.lineWidth=8;x.stroke();
        curve();x.strokeStyle='#bc9158';x.lineWidth=5;x.stroke();
        curve();x.strokeStyle='#ebc687';x.lineWidth=2;x.stroke();
      }
      x.restore();
    }
  }
};
BOTANICAL.init();
