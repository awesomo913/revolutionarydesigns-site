/* ════════════════════════════════════════════════════
   BAMBOO FOREST LIVE PREVIEW
   Canvas game pulled directly from the live site
════════════════════════════════════════════════════ */
(function initGame() {
  var cvs = document.getElementById('game-canvas');
  if (!cvs) return;
  var W = 960, H = 540;
  var ctx = cvs.getContext('2d');

  var biomes = [
    { name:'Bamboo Grove', skyTop:[165,210,240], skyBot:[255,225,215], platTop:'#378237', platBody:'#6e4321', mtnFar:[105,130,160], mtnFront:[80,110,75], groundStrip:[30,85,28], leafCol:'#90d060' },
    { name:'The Caldera', skyTop:[120,40,30], skyBot:[220,100,40], platTop:'#503220', platBody:'#2d1916', mtnFar:[40,25,30], mtnFront:[30,20,25], groundStrip:[180,60,20], leafCol:'#ff8030' },
    { name:'The Arid Rift', skyTop:[255,180,100], skyBot:[255,230,160], platTop:'#b89458', platBody:'#7a5030', mtnFar:[150,85,50], mtnFront:[194,160,100], groundStrip:[200,170,110], leafCol:'#d4b060' },
    { name:'Karst Caves', skyTop:[10,12,20], skyBot:[25,20,35], platTop:'#3a3550', platBody:'#1e1a2a', mtnFar:[40,35,50], mtnFront:[30,28,40], groundStrip:[20,18,30], leafCol:'#64dcff' },
    { name:'Fungal Hollows', skyTop:[30,15,50], skyBot:[60,30,80], platTop:'#6e3470', platBody:'#3a1a40', mtnFar:[120,50,130], mtnFront:[80,40,90], groundStrip:[50,25,60], leafCol:'#dc82dc' },
  ];
  var biomeIdx=0,biomeTimer=0,BIOME_DUR=480,FADE_DUR=40,curBiome=biomes[0];

  function seededRand(seed){var s=seed;return function(){s=(s*16807)%2147483647;return(s-1)/2147483646;};}
  function genBg(b){
    var r=seededRand(42),clouds=[];
    for(var i=0;i<5;i++)clouds.push({x:r()*(W-160)+80,y:40+r()*100,puffs:[]});
    clouds.forEach(function(c){for(var j=0;j<8;j++)c.puffs.push({dx:(r()-0.5)*60,dy:(r()-0.5)*16,rad:18+r()*14});});
    var mtns=[],r2=seededRand(101);
    for(var i=0;i<8;i++)mtns.push({x:i*(W/6)+(r2()-0.5)*80,h:120+r2()*120,w:180+r2()*140});
    var hills=[],r3=seededRand(201);
    for(var i=0;i<7;i++)hills.push({x:i*(W/5)+(r3()-0.5)*60,h:70+r3()*80,w:160+r3()*120});
    var bB=[],r4=seededRand(301);
    for(var i=0;i<30;i++)bB.push({x:i*(W/24)+(r4()-0.5)*24,h:55+r4()*40});
    var ch=[],r5=seededRand(401);
    for(var i=0;i<5;i++)ch.push({x:i*(W/4)+(r5()-0.5)*70,h:85+r5()*30,canopy:26+r5()*10});
    var fB=[],r6=seededRand(501);
    for(var i=0;i<12;i++)fB.push({x:i*(W/10)+(r6()-0.5)*40,h:110+r6()*60});
    return{clouds:clouds,mtns:mtns,hills:hills,backBamboo:bB,cherries:ch,frontBamboo:fB};
  }
  var bgData=genBg(curBiome);
  var GROUND=H-50,WORLD_W=3600,cam={x:0},t=0;
  var score=0,combo=0,comboTimer=0,hp=100;
  var sparkles=[],dustPuffs=[],floatTexts=[];

  var platforms=[
    {x:0,y:GROUND,w:320,h:60},{x:380,y:GROUND-25,w:180,h:85},{x:620,y:GROUND-55,w:150,h:115},
    {x:840,y:GROUND-20,w:220,h:80},{x:1140,y:GROUND,w:340,h:60},{x:1560,y:GROUND-45,w:160,h:105},
    {x:1780,y:GROUND-75,w:130,h:135},{x:1980,y:GROUND,w:280,h:60},{x:2340,y:GROUND-30,w:200,h:90},
    {x:2600,y:GROUND-65,w:150,h:125},{x:2820,y:GROUND,w:380,h:60},{x:3260,y:GROUND-40,w:180,h:100},
  ];
  function platYAt(bx){for(var i=0;i<platforms.length;i++){var p=platforms[i];if(bx>=p.x&&bx<=p.x+p.w)return p.y;}return GROUND;}

  var bambooInit=[160,440,700,920,1200,1350,1620,1840,2050,2400,2670,2900,3100,3320];
  var enemyInit=[{x:1180,dir:1,type:'slime'},{x:2020,dir:-1,type:'patrol'},{x:2860,dir:1,type:'fly'},{x:3300,dir:-1,type:'slime'}];
  var bamboos,enemies;

  function resetAll(){
    cam.x=0;score=0;combo=0;comboTimer=0;hp=100;
    sparkles=[];dustPuffs=[];floatTexts=[];
    panda.x=60;panda.y=GROUND-22;panda.vy=0;panda.onGround=true;
    panda.attacking=false;panda.atkTimer=0;panda.runFrame=0;
    bamboos=bambooInit.map(function(bx){return{x:bx,y:platYAt(bx)-40,alive:true,bob:Math.random()*6.28};});
    enemies=enemyInit.map(function(e){return{x:e.x,origX:e.x,y:platYAt(e.x)-16,dir:e.dir,type:e.type,hp:1,frame:Math.random()*6.28};});
  }
  var panda={x:60,y:GROUND-22,vy:0,onGround:true,facing:1,runFrame:0,attacking:false,atkTimer:0};
  resetAll();

  function lerpCol(a,b,t){return[a[0]+(b[0]-a[0])*t|0,a[1]+(b[1]-a[1])*t|0,a[2]+(b[2]-a[2])*t|0];}
  function rgb(c){return'rgb('+c[0]+','+c[1]+','+c[2]+')';}

  function drawSky(b){var g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,rgb(b.skyTop));g.addColorStop(1,rgb(b.skyBot));ctx.fillStyle=g;ctx.fillRect(0,0,W,H);}

  function drawClouds(bg,b){
    if(b.name==='Karst Caves')return;
    var cc=b.name==='The Caldera'?'rgba(100,50,40,0.6)':b.name==='Fungal Hollows'?'rgba(80,40,90,0.4)':'rgba(255,255,255,0.85)';
    bg.clouds.forEach(function(c){
      var cx=((c.x-cam.x*0.05)%(W+200)+W+200)%(W+200)-100;
      ctx.fillStyle=cc;
      c.puffs.forEach(function(p){ctx.beginPath();ctx.arc(cx+p.dx,c.y+p.dy,p.rad,0,6.28);ctx.fill();});
    });
  }

  function drawMtns(bg,b){
    ctx.fillStyle=rgb(b.mtnFar);
    bg.mtns.forEach(function(m){
      var mx=((m.x-cam.x*0.08)%(W+300)+W+300)%(W+300)-150;
      ctx.beginPath();ctx.moveTo(mx-m.w/2,H-40);ctx.lineTo(mx,H-40-m.h);ctx.lineTo(mx+m.w/2,H-40);ctx.fill();
      if(b.name==='Bamboo Grove'||b.name==='The Arid Rift'){ctx.fillStyle='rgba(230,238,248,0.7)';var sw=m.w/7;ctx.beginPath();ctx.moveTo(mx-sw,H-40-m.h+18);ctx.lineTo(mx,H-40-m.h);ctx.lineTo(mx+sw,H-40-m.h+18);ctx.fill();ctx.fillStyle=rgb(b.mtnFar);}
    });
    ctx.fillStyle=rgb(b.mtnFront);
    bg.hills.forEach(function(h){var hx=((h.x-cam.x*0.15)%(W+250)+W+250)%(W+250)-125;ctx.beginPath();ctx.moveTo(hx-h.w/2,H-30);ctx.lineTo(hx,H-30-h.h);ctx.lineTo(hx+h.w/2,H-30);ctx.fill();});
  }

  function drawBackBamboo(bg,b){
    if(b.name!=='Bamboo Grove')return;
    bg.backBamboo.forEach(function(s){var sx=((s.x-cam.x*0.2)%(W+60)+W+60)%(W+60)-30;ctx.fillStyle='#82aa9b';ctx.fillRect(sx-1,H-40-s.h,2,s.h);ctx.fillStyle='#5f877e';for(var jy=H-40-s.h+12;jy<H-40;jy+=22)ctx.fillRect(sx-2,jy,4,1);});
  }

  function drawCherryTrees(bg,b){
    if(b.name!=='Bamboo Grove')return;
    bg.cherries.forEach(function(tr){
      var tx=((tr.x-cam.x*0.3)%(W+200)+W+200)%(W+200)-100;
      ctx.fillStyle='#6e4b37';ctx.fillRect(tx-3,H-30-tr.h*0.67,6,tr.h*0.67);
      var pinks=['#ffc8dc','#ffd7e6','#fab9d2','#ffe1eb','#f0afc8'],cw=tr.canopy,cy=H-30-tr.h,pr=seededRand(tr.x*7|0);
      for(var j=0;j<10;j++){var ox=(pr()-0.5)*cw*2,oy=(pr()-0.5)*cw;ctx.fillStyle=pinks[j%5];ctx.beginPath();ctx.arc(tx+ox,cy+oy,cw*(0.55+pr()*0.35),0,6.28);ctx.fill();}
    });
  }

  function drawFrontBamboo(bg,b){
    if(b.name!=='Bamboo Grove')return;
    bg.frontBamboo.forEach(function(s){
      var sx=((s.x-cam.x*0.4)%(W+80)+W+80)%(W+80)-40,by=H-10-s.h;
      ctx.fillStyle='#5aa541';ctx.fillRect(sx+1,by,3,s.h);ctx.fillStyle='#8cd25f';ctx.fillRect(sx-3,by,5,s.h);ctx.fillStyle='#c3f082';ctx.fillRect(sx-2,by,2,s.h);
      ctx.fillStyle='#4b9137';for(var jy=by+14;jy<H-10;jy+=22)ctx.fillRect(sx-4,jy,8,2);
      ctx.fillStyle='#6eb94b';ctx.beginPath();ctx.moveTo(sx,by-6);ctx.lineTo(sx+18,by+4);ctx.lineTo(sx+2,by+10);ctx.fill();
      ctx.fillStyle='#a0d264';ctx.beginPath();ctx.moveTo(sx,by-4);ctx.lineTo(sx+14,by+2);ctx.lineTo(sx+3,by+8);ctx.fill();
      ctx.fillStyle='#64a041';ctx.beginPath();ctx.moveTo(sx,by-6);ctx.lineTo(sx-18,by+4);ctx.lineTo(sx-2,by+10);ctx.fill();
      ctx.fillStyle='#96cd5a';ctx.beginPath();ctx.moveTo(sx,by-4);ctx.lineTo(sx-14,by+2);ctx.lineTo(sx-3,by+8);ctx.fill();
    });
  }

  function drawSpecialBg(b){
    if(b.name==='Karst Caves'){var pr=seededRand(77);ctx.fillStyle='#282350';for(var i=0;i<15;i++){var sx=((pr()*W-cam.x*0.1)%W+W)%W,sh=40+pr()*60,sw=15+pr()*15;ctx.beginPath();ctx.moveTo(sx-sw/2,0);ctx.lineTo(sx+sw/2,0);ctx.lineTo(sx,sh);ctx.fill();}var cols=['#64dcff','#c8ffb4','#ffc878'];for(var i=0;i<80;i++){ctx.fillStyle=cols[i%3];ctx.fillRect((pr()*W)|0,(50+pr()*(H-100))|0,1,1);}}
    if(b.name==='Fungal Hollows'){var pr=seededRand(142);for(var i=0;i<6;i++){var cx=((i*W/5+(pr()-0.5)*60-cam.x*0.12)%(W+200)+W+200)%(W+200)-100,sh=140+pr()*80,cr=60+pr()*40,by2=H-10;ctx.fillStyle='#786e8c';ctx.fillRect(cx-8,by2-sh,16,sh);ctx.fillStyle='#783282';ctx.beginPath();ctx.moveTo(cx-cr,by2-sh);ctx.lineTo(cx,by2-sh-cr/2);ctx.lineTo(cx+cr,by2-sh);ctx.fill();ctx.fillStyle='#c864dc';ctx.beginPath();ctx.ellipse(cx,by2-sh-cr/4,cr/2,cr/5,0,0,6.28);ctx.fill();ctx.fillStyle='#fff096';for(var j=0;j<3;j++){ctx.beginPath();ctx.arc(cx+(pr()-0.5)*cr,by2-sh-(pr()*cr/3|0),4,0,6.28);ctx.fill();}}}
    if(b.name==='The Caldera'){for(var y=H-15;y<H;y++){var tt=(y-(H-15))/15;ctx.fillStyle='rgb('+(180+60*tt|0)+','+(60+40*tt|0)+','+(20+10*tt|0)+')';ctx.fillRect(0,y,W,1);}}
  }

  function drawPlatform(p,b){
    var px=p.x-cam.x;if(px>W+20||px+p.w<-20)return;
    ctx.fillStyle=b.platBody;ctx.fillRect(px,p.y,p.w,p.h);
    for(var gy=6;gy<p.h;gy+=4){ctx.fillStyle='rgba(0,0,0,0.08)';ctx.fillRect(px,p.y+gy,p.w,1);}
    ctx.fillStyle=b.platTop;ctx.fillRect(px,p.y,p.w,5);
    ctx.fillStyle='rgba(0,0,0,0.15)';ctx.fillRect(px,p.y+5,p.w,1);
    for(var g=0;g<p.w;g+=4){var bh=2+(g*7%5);ctx.fillStyle=b.platTop;ctx.fillRect(px+g,p.y-bh,2,bh+2);}
    ctx.fillStyle='rgba(0,0,0,0.2)';ctx.fillRect(px,p.y,2,p.h);ctx.fillRect(px+p.w-2,p.y,2,p.h);
  }

  function drawBamboo(b){
    if(!b.alive)return;var bx=b.x-cam.x;if(bx<-20||bx>W+20)return;
    var by=b.y+Math.sin(t*0.04+b.bob)*2;
    ctx.fillStyle='#4c9900';ctx.fillRect(bx-3,by,6,40);ctx.fillStyle='#5ab414';ctx.fillRect(bx-2,by,2,40);
    ctx.fillStyle='#327800';ctx.fillRect(bx-3,by+12,6,3);ctx.fillRect(bx-3,by+27,6,3);
    ctx.fillStyle='#329600';ctx.beginPath();ctx.moveTo(bx,by);ctx.lineTo(bx+12,by+6);ctx.lineTo(bx,by+8);ctx.fill();
    ctx.beginPath();ctx.moveTo(bx,by+3);ctx.lineTo(bx-12,by+9);ctx.lineTo(bx,by+11);ctx.fill();
    ctx.fillStyle='#ffd700';ctx.beginPath();ctx.arc(bx,by-4,5,0,6.28);ctx.fill();
    ctx.fillStyle='#fff5aa';ctx.beginPath();ctx.arc(bx-1,by-5,2,0,6.28);ctx.fill();
  }

  function drawPanda(sx,sy){
    var bobY=panda.onGround?Math.sin(panda.runFrame*8)*2:0,py=sy+bobY;
    ctx.save();ctx.translate(sx,py);if(panda.facing<0)ctx.scale(-1,1);
    var legOff=panda.onGround?Math.sin(panda.runFrame*10)*4:-3;
    ctx.fillStyle='#1e1e1e';ctx.beginPath();ctx.arc(-7,16+legOff,6,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(7,16-legOff,6,0,6.28);ctx.fill();
    ctx.fillStyle='#f0f0eb';ctx.beginPath();ctx.ellipse(0,4,12,12,0,0,6.28);ctx.fill();
    ctx.fillStyle='#dcdcd7';ctx.beginPath();ctx.ellipse(0,5,7,7,0,0,6.28);ctx.fill();
    ctx.fillStyle='#1e1e1e';var armOff=panda.onGround?Math.sin(panda.runFrame*10)*3:0;
    ctx.beginPath();ctx.ellipse(-11,2-armOff,4,7,0,0,6.28);ctx.fill();ctx.beginPath();ctx.ellipse(11,2+armOff,4,7,0,0,6.28);ctx.fill();
    ctx.fillStyle='#f0f0eb';ctx.beginPath();ctx.arc(0,-10,11,0,6.28);ctx.fill();
    ctx.fillStyle='#1e1e1e';ctx.beginPath();ctx.arc(-8,-18,5,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(8,-18,5,0,6.28);ctx.fill();
    ctx.fillStyle='#b48282';ctx.beginPath();ctx.arc(-8,-18,2,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(8,-18,2,0,6.28);ctx.fill();
    ctx.fillStyle='#1e1e1e';ctx.beginPath();ctx.ellipse(-4,-12,4,3.5,0,0,6.28);ctx.fill();ctx.beginPath();ctx.ellipse(4,-12,4,3.5,0,0,6.28);ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-3,-12,2.5,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(5,-12,2.5,0,6.28);ctx.fill();
    ctx.fillStyle='#000';ctx.beginPath();ctx.arc(-2,-12,1.5,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(6,-12,1.5,0,6.28);ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-3,-13,0.8,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(5,-13,0.8,0,6.28);ctx.fill();
    ctx.fillStyle='#3c2828';ctx.beginPath();ctx.ellipse(1,-7,2.5,1.5,0,0,6.28);ctx.fill();
    ctx.strokeStyle='#1e1e1e';ctx.lineWidth=0.8;ctx.beginPath();ctx.arc(0,-5.5,3,0.1,3.04);ctx.stroke();
    if(panda.attacking){ctx.fillStyle='rgba(255,200,80,0.65)';ctx.beginPath();ctx.arc(16,0,12,0,6.28);ctx.fill();ctx.strokeStyle='rgba(255,255,180,0.8)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(16,0,15,-0.6,0.8);ctx.stroke();}
    ctx.restore();
  }

  function drawEnemy(e){
    var ex=e.x-cam.x,ey=e.y;if(ex<-30||ex>W+30||e.hp<=0)return;
    if(e.type==='slime'){var sq=1+Math.sin(e.frame*4)*0.12;ctx.save();ctx.translate(ex,ey);ctx.scale(1/sq,sq);ctx.fillStyle='#50c028';ctx.beginPath();ctx.ellipse(0,0,14,12,0,0,6.28);ctx.fill();ctx.fillStyle='#78e050';ctx.beginPath();ctx.ellipse(0,-3,9,6,0,0,6.28);ctx.fill();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-4,-4,3.5,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(4,-4,3.5,0,6.28);ctx.fill();ctx.fillStyle='#222';ctx.beginPath();ctx.arc(-3,-3,2,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(5,-3,2,0,6.28);ctx.fill();ctx.restore();}
    else if(e.type==='fly'){var fy=ey+Math.sin(e.frame*3)*18-28;ctx.fillStyle='#c06060';ctx.beginPath();ctx.ellipse(ex,fy,12,10,0,0,6.28);ctx.fill();ctx.fillStyle='rgba(200,180,180,0.45)';var wF=Math.sin(e.frame*12)*3;ctx.beginPath();ctx.ellipse(ex-12,fy-8+wF,9,4,-0.3,0,6.28);ctx.fill();ctx.beginPath();ctx.ellipse(ex+12,fy-8-wF,9,4,0.3,0,6.28);ctx.fill();ctx.fillStyle='#ff4444';ctx.beginPath();ctx.arc(ex-3,fy-3,2,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(ex+3,fy-3,2,0,6.28);ctx.fill();}
    else{ctx.fillStyle='#a04040';var bx2=ex-10,by3=ey-22;ctx.fillRect(bx2,by3,20,22);ctx.fillStyle='#c06060';ctx.fillRect(bx2+2,by3+2,16,14);ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(ex-3,by3+8,2,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(ex+3,by3+8,2,0,6.28);ctx.fill();ctx.fillStyle='#1e1e1e';ctx.beginPath();ctx.arc(ex-2,by3+8,1,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(ex+4,by3+8,1,0,6.28);ctx.fill();}
  }

  function drawHUD(b){
    ctx.fillStyle='rgba(20,20,20,0.75)';var rr=8;ctx.beginPath();
    ctx.moveTo(8+rr,8);ctx.lineTo(260-rr,8);ctx.arcTo(260,8,260,8+rr,rr);ctx.lineTo(260,72-rr);ctx.arcTo(260,72,260-rr,72,rr);ctx.lineTo(8+rr,72);ctx.arcTo(8,72,8,72-rr,rr);ctx.lineTo(8,8+rr);ctx.arcTo(8,8,8+rr,8,rr);ctx.fill();
    ctx.strokeStyle='rgba(60,60,60,0.4)';ctx.lineWidth=1.5;ctx.stroke();
    ctx.fillStyle='#fff';ctx.font='bold 13px Consolas,monospace';ctx.textAlign='left';ctx.fillText('HP',18,30);
    ctx.fillStyle='#b41e1e';ctx.beginPath();ctx.roundRect(42,18,150,16,4);ctx.fill();
    var hw=Math.max(0,hp*1.46);if(hw>0){ctx.fillStyle='#1ece1e';ctx.beginPath();ctx.roundRect(43,19,hw,14,3);ctx.fill();}
    ctx.fillStyle='#fff';ctx.font='11px Consolas,monospace';ctx.fillText(hp+'',110,31);
    ctx.fillStyle='#ffd700';ctx.font='bold 14px Consolas,monospace';ctx.fillText('SCORE: '+score,18,52);
    if(combo>1){ctx.fillStyle='#ffee44';ctx.font='bold 12px Consolas,monospace';ctx.fillText(combo+'x COMBO!',18,66);}
    ctx.fillStyle='rgba(255,255,255,0.5)';ctx.font='12px Consolas,monospace';ctx.textAlign='right';ctx.fillText(b.name,250,66);ctx.textAlign='left';
  }

  function drawLeaves(b){
    for(var i=0;i<18;i++){var seed=i*31+7,lx=((seed*97+t*(0.3+(i%5)*0.1))%(W+60))-30,ly=(seed*53+Math.sin(t*0.015+i)*40)%(H-80)+20;ctx.globalAlpha=0.15+(i%4)*0.08;ctx.fillStyle=b.leafCol;ctx.beginPath();ctx.ellipse(lx,ly,3+i%3,1.5+(i%2),t*0.015+i,0,6.28);ctx.fill();}ctx.globalAlpha=1;
  }

  function update(){
    t++;biomeTimer++;
    if(biomeTimer>=BIOME_DUR){biomeTimer=0;biomeIdx=(biomeIdx+1)%biomes.length;curBiome=biomes[biomeIdx];}
    panda.runFrame+=0.06;panda.x+=2.4;panda.facing=1;
    var onPlat=false,nextPlat=null;
    for(var i=0;i<platforms.length;i++){var p=platforms[i];if(panda.x>=p.x-4&&panda.x<=p.x+p.w+4&&Math.abs((panda.y+22)-p.y)<8)onPlat=true;if(p.x>panda.x&&p.x<panda.x+180&&!nextPlat)nextPlat=p;}
    var needJump=(!onPlat&&panda.onGround)||(nextPlat&&nextPlat.y<panda.y+22-12&&nextPlat.x-panda.x<90);
    if(needJump&&panda.onGround){panda.vy=-11;panda.onGround=false;for(var d=0;d<5;d++)dustPuffs.push({x:panda.x,y:panda.y+20,vx:(Math.random()-0.5)*3,vy:-Math.random()*2.5,life:18});}
    if(!panda.onGround)panda.vy+=0.5;panda.y+=panda.vy;panda.onGround=false;
    for(var i=0;i<platforms.length;i++){var p=platforms[i];if(panda.x>p.x-10&&panda.x<p.x+p.w+10&&panda.y+22>=p.y-5&&panda.y+22<=p.y+10&&panda.vy>=0){panda.y=p.y-22;panda.vy=0;panda.onGround=true;}}
    for(var i=0;i<bamboos.length;i++){var b=bamboos[i];if(!b.alive)continue;if(Math.abs(panda.x-b.x)<22&&Math.abs(panda.y-b.y)<36){b.alive=false;score+=100*Math.max(1,combo);combo++;comboTimer=140;floatTexts.push({x:b.x,y:b.y-20,text:'+'+(100*Math.max(1,combo)),life:60,color:'#ffd700'});for(var s=0;s<6;s++)sparkles.push({x:b.x,y:b.y-8,vx:(Math.random()-0.5)*4,vy:-Math.random()*3.5,life:22+Math.random()*12,color:Math.random()>0.5?'#ffd700':'#4c9900'});}}
    if(comboTimer>0)comboTimer--;else combo=0;
    for(var i=0;i<enemies.length;i++){var e=enemies[i];if(e.hp<=0)continue;e.frame+=0.06;var spd=e.type==='fly'?0.5:e.type==='slime'?0.7:0.9;e.x+=e.dir*spd;if(Math.abs(e.x-e.origX)>65)e.dir*=-1;if(Math.abs(panda.x-e.x)<48&&Math.abs(panda.y-e.y)<40&&!panda.attacking){panda.attacking=true;panda.atkTimer=20;}if(panda.attacking&&Math.abs(panda.x-e.x)<36&&Math.abs(panda.y-e.y)<36){e.hp=0;score+=200*Math.max(1,combo);combo++;comboTimer=140;floatTexts.push({x:e.x,y:e.y-20,text:'+'+(200*Math.max(1,combo)),life:60,color:'#ff6644'});for(var s=0;s<8;s++)sparkles.push({x:e.x,y:e.y-8,vx:(Math.random()-0.5)*5,vy:-Math.random()*4.5,life:20,color:'#ff6644'});}}
    if(panda.atkTimer>0)panda.atkTimer--;if(panda.atkTimer===0)panda.attacking=false;
    cam.x+=(panda.x-W/3-cam.x)*0.08;if(cam.x<0)cam.x=0;
    if(panda.x>WORLD_W-100||panda.y>H+60)resetAll();
    for(var i=sparkles.length-1;i>=0;i--){sparkles[i].x+=sparkles[i].vx;sparkles[i].y+=sparkles[i].vy;sparkles[i].vy+=0.15;sparkles[i].life--;if(sparkles[i].life<=0)sparkles.splice(i,1);}
    for(var i=dustPuffs.length-1;i>=0;i--){dustPuffs[i].x+=dustPuffs[i].vx;dustPuffs[i].y+=dustPuffs[i].vy;dustPuffs[i].life--;if(dustPuffs[i].life<=0)dustPuffs.splice(i,1);}
    for(var i=floatTexts.length-1;i>=0;i--){floatTexts[i].y-=0.8;floatTexts[i].life--;if(floatTexts[i].life<=0)floatTexts.splice(i,1);}
  }

  function render(){
    var b=curBiome;
    drawSky(b);drawClouds(bgData,b);drawMtns(bgData,b);drawSpecialBg(b);drawBackBamboo(bgData,b);drawCherryTrees(bgData,b);drawFrontBamboo(bgData,b);
    platforms.forEach(function(p){drawPlatform(p,b);});
    bamboos.forEach(function(bm){drawBamboo(bm);});
    enemies.forEach(function(e){drawEnemy(e);});
    drawPanda(panda.x-cam.x,panda.y);
    for(var i=0;i<sparkles.length;i++){var s=sparkles[i];ctx.globalAlpha=Math.min(1,s.life/10);ctx.fillStyle=s.color;ctx.beginPath();ctx.arc(s.x-cam.x,s.y,2.5,0,6.28);ctx.fill();}ctx.globalAlpha=1;
    for(var i=0;i<dustPuffs.length;i++){var d=dustPuffs[i];ctx.globalAlpha=d.life/18*0.35;ctx.fillStyle='#c8b090';ctx.beginPath();ctx.arc(d.x-cam.x,d.y,3.5,0,6.28);ctx.fill();}ctx.globalAlpha=1;
    for(var i=0;i<floatTexts.length;i++){var ft=floatTexts[i];ctx.globalAlpha=Math.min(1,ft.life/30);ctx.fillStyle=ft.color;ctx.font='bold 16px Consolas,monospace';ctx.textAlign='center';ctx.fillText(ft.text,ft.x-cam.x,ft.y);ctx.textAlign='left';}ctx.globalAlpha=1;
    drawLeaves(b);drawHUD(b);
  }

  function loop(){update();render();requestAnimationFrame(loop);}
  loop();
})();


/* ════════════════════════════════════════════════════
   PROJECTS — GitHub API + opengraph preview images
════════════════════════════════════════════════════ */
/* ════════════════════════════════════════════════════
   PROJECT CANVAS ANIMATIONS — one per repo
════════════════════════════════════════════════════ */
var ANIM = {};

ANIM['Claude-Token-Saver'] = function(c,w,h,t){
  c.fillStyle='#080e08';c.fillRect(0,0,w,h);
  var words=['the','quick','brown','fox','is','an','AI','prompt'];
  words.forEach(function(word,i){
    var x=12,y=14+i*22,alpha=0.5+Math.sin(t*0.04+i)*0.3;
    c.fillStyle='rgba(60,130,60,'+alpha+')';c.fillRect(x,y,word.length*7+8,15);
    c.fillStyle='#9de89d';c.font='9px monospace';c.textAlign='left';c.fillText(word,x+4,y+11);
  });
  var p=((t*0.5)%100)/100;
  c.fillStyle='rgba(57,255,20,'+((p<0.5?p:1-p)*2)+')';c.font='bold 12px monospace';c.textAlign='center';
  c.fillText('━━━ compress ━━━',w/2,h*0.48);
  var merged=['[pack:8→1]','[lossless]'];
  merged.forEach(function(m,i){
    var bx=w*0.6,by=h*0.35+i*26;
    c.fillStyle='rgba(57,255,20,0.8)';c.fillRect(bx,by,w*0.35,18);
    c.fillStyle='#000';c.font='bold 9px monospace';c.textAlign='left';c.fillText(m,bx+4,by+13);
  });
  c.fillStyle='rgba(57,255,20,0.12)';c.beginPath();c.arc(w*0.77,h*0.78,26,0,6.28);c.fill();
  c.fillStyle='#39ff14';c.font='bold 16px monospace';c.textAlign='center';c.fillText('80%',w*0.77,h*0.82);
  c.fillStyle='#6f6';c.font='8px monospace';c.fillText('saved',w*0.77,h*0.92);
};

ANIM['gemini-analyzer'] = function(c,w,h,t){
  c.fillStyle='#07091a';c.fillRect(0,0,w,h);
  var cats=[{l:'code',col:'#4285f4'},{l:'question',col:'#ea4335'},{l:'answer',col:'#34a853'},{l:'meta',col:'#fbbc04'}];
  cats.forEach(function(cat,i){
    var bx=w*0.52+i*(w*0.12),barH=24+Math.sin(t*0.04+i*0.9)*18,bw=w*0.09;
    c.fillStyle=cat.col+'33';c.fillRect(bx,h*0.12,bw,h*0.6);
    c.fillStyle=cat.col;c.fillRect(bx,h*0.72-barH,bw,barH);
    c.font='7px monospace';c.textAlign='center';c.fillStyle='#aaa';c.fillText(cat.l,bx+bw/2,h*0.82);
  });
  for(var i=0;i<7;i++){
    var lx=((i*55-t*0.6)%(w*0.48+60))-30,ly=h*0.18+i*(h*0.09);
    c.strokeStyle='rgba(100,160,255,0.35)';c.lineWidth=1;c.beginPath();c.moveTo(lx,ly);c.lineTo(lx+38,ly);c.stroke();
    c.fillStyle='rgba(100,160,255,0.5)';c.beginPath();c.arc(lx+38,ly,2,0,6.28);c.fill();
  }
  c.fillStyle='#4285f4';c.font='bold 10px monospace';c.textAlign='left';c.fillText('Gemini export',w*0.04,h*0.1);
  c.fillStyle='#555';c.font='8px monospace';c.fillText('↳ categorizing...',w*0.04,h*0.2);
};

ANIM['KidsCodeAcademy'] = function(c,w,h,t){
  c.fillStyle='#0d0d1a';c.fillRect(0,0,w,h);
  var cols=['#ff6464','#ffcc44','#44dd88','#44aaff','#cc66ff'];
  [['move 10 steps','repeat 3'],['say "Hello!"','if touching?']].forEach(function(row,ri){
    row.forEach(function(txt,ci){
      var bx=w*0.04+ci*(w*0.3),by=h*0.1+ri*h*0.22,bw=w*0.26,bh=h*0.17;
      c.fillStyle=cols[ri*2+ci];c.beginPath();c.roundRect(bx,by,bw,bh,5);c.fill();
      c.fillStyle='rgba(0,0,0,0.25)';c.fillRect(bx,by+bh*0.55,bw,bh*0.45);c.beginPath();c.roundRect(bx,by,bw,bh,5);c.clip();
      c.fillStyle='#fff';c.font='bold 9px monospace';c.textAlign='left';c.fillText(txt,bx+8,by+bh*0.42);
      c.restore();c.save();
    });
  });
  var bounce=Math.abs(Math.sin(t*0.09))*18;
  var rx=w*0.74,ry=h*0.48-bounce;
  c.fillStyle='#ffcc44';c.beginPath();c.arc(rx,ry,14,0,6.28);c.fill();
  c.fillStyle='#333';c.beginPath();c.arc(rx-4,ry-2,2.5,0,6.28);c.fill();c.beginPath();c.arc(rx+4,ry-2,2.5,0,6.28);c.fill();
  c.strokeStyle='#333';c.lineWidth=2;c.beginPath();c.arc(rx,ry+3,5,0.1,3.0);c.stroke();
  c.fillStyle='#44aaff';c.fillRect(rx-9,ry+14,18,16);
  c.fillStyle='#2a88dd';c.fillRect(rx-9,ry+28,7,10);c.fillRect(rx+2,ry+28,7,10);
  if((t%40)<20){c.font='14px serif';c.textAlign='center';c.fillText('⭐',w*0.86,h*0.28);}
};

ANIM['card-collection-anime'] = function(c,w,h,t){
  c.fillStyle='#0d0715';c.fillRect(0,0,w,h);
  [{col:'#c62a88',suit:'♦',label:'ULTRA RARE'},{col:'#7c3aed',suit:'♠',label:'RARE'},{col:'#d97706',suit:'★',label:'HOLO'}].forEach(function(card,i){
    var angle=(i-1)*0.28+Math.sin(t*0.025+i)*0.06;
    c.save();c.translate(w/2,h*0.65);c.rotate(angle);
    var cw2=w*0.19,ch2=h*0.72;
    c.fillStyle='#1a1020';c.strokeStyle=card.col;c.lineWidth=2;
    c.beginPath();c.roundRect(-cw2/2,-ch2,cw2,ch2,5);c.fill();c.stroke();
    c.fillStyle=card.col+'44';c.fillRect(-cw2/2,-ch2,cw2,ch2);
    c.fillStyle=card.col;c.font='bold 22px serif';c.textAlign='center';c.fillText(card.suit,0,-ch2*0.55);
    c.fillStyle='rgba(255,255,255,0.6)';c.font='7px monospace';c.fillText(card.label,0,-ch2*0.3);
    c.restore();
  });
  for(var i=0;i<6;i++){
    var sx=w*0.1+Math.sin(t*0.06+i*2.4)*w*0.4,sy=h*0.08+Math.cos(t*0.05+i*1.9)*h*0.18;
    c.fillStyle='rgba(255,215,0,'+(Math.sin(t*0.1+i)+1)*0.4+')';c.beginPath();c.arc(sx,sy,2.5,0,6.28);c.fill();
  }
};

ANIM['TCGValueTracker'] = function(c,w,h,t){
  c.fillStyle='#080c0a';c.fillRect(0,0,w,h);
  function sr(s){s=(s*16807)%2147483647;return(s-1)/2147483646;}
  var pts=[];var s2=77;for(var i=0;i<35;i++){s2=(s2*16807)%2147483647;pts.push((s2-1)/2147483646);}
  var cH=h*0.6,cY=h*0.14,cX=w*0.06,cW=w*0.86,bW=cW/32;
  c.strokeStyle='rgba(255,255,255,0.05)';c.lineWidth=1;
  for(var i=0;i<4;i++){var gy=cY+i*(cH/3);c.beginPath();c.moveTo(cX,gy);c.lineTo(cX+cW,gy);c.stroke();}
  var off=Math.floor(t/3)%32;
  for(var i=0;i<30;i++){
    var idx=(i+off)%35,nidx=(idx+1)%35;
    var op=pts[idx],cp=pts[nidx],up=cp>=op;
    var cx=cX+i*bW+bW/2,oy=cY+cH-(op*cH*0.8+cH*0.1),cy=cY+cH-(cp*cH*0.8+cH*0.1);
    c.strokeStyle=up?'#22dd44':'#ff4444';c.lineWidth=1;
    c.beginPath();c.moveTo(cx,Math.min(oy,cy)-3);c.lineTo(cx,Math.max(oy,cy)+3);c.stroke();
    c.fillStyle=up?'#22dd44':'#ff4444';
    c.fillRect(cx-bW*0.28,Math.min(oy,cy),bW*0.56,Math.max(2,Math.abs(oy-cy)));
  }
  var last=pts[(off+29)%35],prev=pts[(off+28)%35];
  c.fillStyle='#ffd700';c.font='bold 10px monospace';c.textAlign='left';c.fillText('TCG Market',cX,h*0.88);
  c.fillStyle=last>prev?'#22dd44':'#ff4444';c.font='bold 11px monospace';c.textAlign='right';
  c.fillText((last>prev?'▲':'▼')+((Math.abs(last-prev)*100).toFixed(1))+'%',cX+cW,h*0.88);
};

ANIM['video-trimmer'] = function(c,w,h,t){
  c.fillStyle='#0d0a08';c.fillRect(0,0,w,h);
  var fCols=[['#1a3a1a','#4a8a4a'],['#3a1a1a','#8a4a4a'],['#1a1a3a','#4a4a8a'],['#3a2a1a','#8a6a3a'],['#2a1a3a','#6a4a8a']];
  for(var i=0;i<5;i++){
    var fx=w*0.04+i*(w*0.19),fy=h*0.1,fw=w*0.17,fh=h*0.48;
    c.fillStyle=fCols[i][0];c.fillRect(fx,fy,fw,fh);
    c.fillStyle=fCols[i][1];c.fillRect(fx+fw*0.15,fy+fh*0.2,fw*0.7,fh*0.55);
    c.strokeStyle='#2a2a2a';c.lineWidth=1;c.strokeRect(fx,fy,fw,fh);
    c.fillStyle='rgba(255,255,255,0.18)';c.font='8px monospace';c.textAlign='center';
    c.fillText('0:'+(i*3|0)+'0',fx+fw/2,fy+fh*0.9);
  }
  var tlY=h*0.72,tlX=w*0.04,tlW=w*0.92,tlH=9;
  c.fillStyle='#222';c.fillRect(tlX,tlY,tlW,tlH);
  c.fillStyle='rgba(255,100,50,0.28)';c.fillRect(tlX+tlW*0.22,tlY,tlW*0.54,tlH);
  c.strokeStyle='#ff6633';c.lineWidth=2;c.strokeRect(tlX+tlW*0.22,tlY-2,tlW*0.54,tlH+4);
  var ph=tlX+((t*0.55)%(tlW*0.88));
  c.fillStyle='#ff6633';c.fillRect(ph-1,tlY-7,2,tlH+14);
  c.beginPath();c.moveTo(ph-6,tlY-7);c.lineTo(ph+6,tlY-7);c.lineTo(ph,tlY-1);c.fill();
  c.fillStyle='#888';c.font='8px monospace';c.textAlign='left';c.fillText('00:00',tlX,h*0.88);
  c.textAlign='right';c.fillText('00:15',tlX+tlW,h*0.88);
  c.fillStyle='#ff6633';c.font='bold 9px monospace';c.textAlign='center';c.fillText('✂  trim',w/2,h*0.96);
};

ANIM['typingspeedtest-privacy'] = function(c,w,h,t){
  c.fillStyle='#080808';c.fillRect(0,0,w,h);
  var sentence='The quick brown fox jumps over the lazy dog'.split(' ');
  var wpm=Math.min(128,Math.floor(t*0.38));
  var shown=sentence.slice(0,Math.min(sentence.length,Math.floor(t/22)+1));
  c.fillStyle='rgba(255,255,255,0.07)';c.fillRect(w*0.06,h*0.1,w*0.88,h*0.55);
  c.fillStyle='#f0f0f0';c.font='13px monospace';c.textAlign='left';
  var line='',lineY=h*0.3,words=shown.slice();
  words.forEach(function(word,i){
    var test=line+(i?' ':'')+word;
    if(c.measureText(test).width>w*0.78&&i>0){c.fillText(line,w*0.1,lineY);line=word;lineY+=20;}else line=test;
  });
  c.fillText(line,w*0.1,lineY);
  if(t%28<18){var tw=c.measureText(line).width;c.fillStyle='#39ff14';c.fillRect(w*0.1+tw+2,lineY-12,2,14);}
  c.fillStyle='rgba(57,255,20,0.12)';c.beginPath();c.roundRect(w*0.28,h*0.72,w*0.44,h*0.22,8);c.fill();
  c.fillStyle='#39ff14';c.font='bold 24px monospace';c.textAlign='center';c.fillText(wpm,w/2,h*0.88);
  c.fillStyle='#666';c.font='9px monospace';c.fillText('WPM',w/2,h*0.96);
};

ANIM['animal-art-studio'] = function(c,w,h,t){
  c.fillStyle='#fafaf8';c.fillRect(0,0,w,h);
  var strokes=[
    {col:'#e85d04',p:[[0.28,0.32],[0.5,0.25],[0.72,0.32]]},
    {col:'#f4a261',p:[[0.22,0.52],[0.5,0.44],[0.78,0.52]]},
    {col:'#2a9d8f',p:[[0.38,0.68],[0.5,0.74],[0.62,0.68]]},
    {col:'#e9c46a',p:[[0.34,0.42],[0.5,0.36],[0.66,0.42]]},
    {col:'#264653',p:[[0.44,0.56],[0.5,0.62],[0.56,0.56]]},
  ];
  var prog=((t%200)/200);
  strokes.forEach(function(s,si){
    var sp=Math.max(0,Math.min(1,prog*5-si));if(sp<=0)return;
    c.strokeStyle=s.col;c.lineWidth=10+si*2;c.lineCap='round';c.lineJoin='round';c.globalAlpha=0.75;
    c.beginPath();c.moveTo(s.p[0][0]*w,s.p[0][1]*h);
    for(var i=1;i<s.p.length;i++){
      var prev=s.p[i-1],next=s.p[i];
      var frac=Math.min(1,sp*(s.p.length-1)-(i-1));
      c.lineTo(prev[0]*w+(next[0]-prev[0])*w*frac,prev[1]*h+(next[1]-prev[1])*h*frac);
    }
    c.stroke();c.globalAlpha=1;
  });
  c.fillStyle='rgba(100,64,40,0.28)';
  [[0.8,0.8,12],[0.72,0.72,6],[0.83,0.72,6],[0.75,0.67,5]].forEach(function(p){c.beginPath();c.arc(p[0]*w,p[1]*h,p[2],0,6.28);c.fill();});
  c.fillStyle='#888';c.fillRect(w*0.06+prog*w*0.32,h*0.06,4,h*0.28);
  c.fillStyle='#e85d04';c.beginPath();c.ellipse(w*0.08+prog*w*0.32,h*0.34,5,9,0,0,6.28);c.fill();
};

ANIM['ai-intel-hub'] = function(c,w,h,t){
  c.fillStyle='#040d12';c.fillRect(0,0,w,h);
  var nodes=[{x:.5,y:.5,r:11,l:'HUB'},{x:.18,y:.22,r:6,l:'news'},{x:.82,y:.18,r:6,l:'api'},{x:.12,y:.72,r:6,l:'rss'},{x:.88,y:.76,r:6,l:'data'},{x:.5,y:.08,r:5,l:'web'},{x:.5,y:.92,r:5,l:'ai'}];
  nodes.forEach(function(n,i){if(i===0)return;
    c.strokeStyle='rgba(0,216,255,0.12)';c.lineWidth=1;c.beginPath();c.moveTo(nodes[0].x*w,nodes[0].y*h);c.lineTo(n.x*w,n.y*h);c.stroke();
    var pr=((t*0.018+i*0.14)%1);
    var px=nodes[0].x*w+(n.x-nodes[0].x)*w*pr,py=nodes[0].y*h+(n.y-nodes[0].y)*h*pr;
    c.fillStyle='#00d8ff';c.beginPath();c.arc(px,py,2.5,0,6.28);c.fill();
  });
  nodes.forEach(function(n,i){
    var pulse=(Math.sin(t*0.06+i)+1)/2*0.4;
    c.fillStyle='rgba(0,216,255,'+(0.08+pulse)+')';c.beginPath();c.arc(n.x*w,n.y*h,n.r*2.2,0,6.28);c.fill();
    c.fillStyle='#00d8ff';c.beginPath();c.arc(n.x*w,n.y*h,n.r,0,6.28);c.fill();
    c.fillStyle='#040d12';c.font='bold '+(n.r*0.85)+'px monospace';c.textAlign='center';c.fillText(n.l,n.x*w,n.y*h+n.r*0.38);
  });
};

ANIM['GitHubAppInstaller'] = function(c,w,h,t){
  c.fillStyle='#0d0d0d';c.fillRect(0,0,w,h);
  var apps=[{name:'python-app',col:'#3572A5'},{name:'node-tool',col:'#f1e05a'},{name:'rust-cli',col:'#dea584'},{name:'go-server',col:'#00ADD8'}];
  apps.forEach(function(app,i){
    var p=Math.min(1,(t-i*50)/90);if(p<=0)return;
    var y=h*0.12+i*(h*0.21),bX=w*0.05,bW=w*0.72;
    c.fillStyle=app.col;c.beginPath();c.arc(bX+10,y+10,5,0,6.28);c.fill();
    c.fillStyle='#e0e0e0';c.font='10px monospace';c.textAlign='left';c.fillText(app.name,bX+22,y+14);
    c.fillStyle='#1e1e1e';c.beginPath();c.roundRect(bX,y+20,bW,8,4);c.fill();
    c.fillStyle='#6cc644';c.beginPath();c.roundRect(bX,y+20,bW*p,8,4);c.fill();
    if(p>=1){c.fillStyle='#6cc644';c.font='14px monospace';c.textAlign='left';c.fillText('✓',bX+bW+8,y+30);}
    else{c.fillStyle='#555';c.font='8px monospace';c.textAlign='right';c.fillText((p*100|0)+'%',bX+bW+18,y+30);}
  });
  c.fillStyle='#444';c.font='9px monospace';c.textAlign='center';c.fillText('GitHub App Installer',w/2,h*0.94);
};

ANIM['ClaudeCodingCourse'] = function(c,w,h,t){
  c.fillStyle='#0f1117';c.fillRect(0,0,w,h);
  c.fillStyle='#1e1e2e';c.fillRect(0,0,w,h*0.13);
  [[12,'#ff5f56'],[26,'#ffbd2e'],[40,'#27c93f']].forEach(function(d){c.fillStyle=d[1];c.beginPath();c.arc(d[0],h*0.065,4.5,0,6.28);c.fill();});
  c.fillStyle='#777';c.font='9px monospace';c.textAlign='center';c.fillText('lesson_01.py',w/2,h*0.09);
  var lines=[{t:'import claude',col:'#c792ea'},{t:'',col:''},{t:'# Ask Claude anything',col:'#546e7a'},{t:'response = claude.ask(',col:'#82aaff'},{t:'  "Write me a function"',col:'#c3e88d'},{t:')',col:'#82aaff'}];
  var vis=Math.min(lines.length,Math.floor(t/28)+1);
  lines.slice(0,vis).forEach(function(l,i){
    if(!l.t)return;c.fillStyle=l.col;c.font='10px monospace';c.textAlign='left';c.fillText(l.t,w*0.05,h*0.22+i*h*0.12);
  });
  if(vis<lines.length&&t%22<14){var ll=lines[vis-1];var tw=c.measureText(ll.t||'').width;c.fillStyle='#f0f0f0';c.fillRect(w*0.05+tw+2,h*0.22+(vis-1)*h*0.12-10,2,12);}
};

ANIM['PiSenseDesigner'] = function(c,w,h,t){
  c.fillStyle='#080810';c.fillRect(0,0,w,h);
  c.fillStyle='rgba(197,26,74,0.14)';c.beginPath();c.arc(w*0.85,h*0.2,24,0,6.28);c.fill();
  c.fillStyle='#c51a4a';c.font='bold 20px serif';c.textAlign='center';c.fillText('π',w*0.85,h*0.27);
  [{l:'TEMP',col:'#ff6644',fn:function(x){return Math.sin(x*0.05+t*0.03);}},{l:'HUMID',col:'#4488ff',fn:function(x){return Math.sin(x*0.03+t*0.02+1);}},{l:'PRESS',col:'#44ff88',fn:function(x){return Math.sin(x*0.04+t*0.025+2)*0.5+0.3;}}].forEach(function(s,i){
    var sy=h*(0.26+i*0.24),amp=h*0.08;
    c.strokeStyle=s.col;c.lineWidth=1.5;c.beginPath();
    for(var x=0;x<w*0.68;x+=2){var y=sy+s.fn(x)*amp;if(x===0)c.moveTo(x+w*0.05,y);else c.lineTo(x+w*0.05,y);}
    c.stroke();
    c.fillStyle=s.col;c.font='8px monospace';c.textAlign='left';
    c.fillText(s.l+': '+(s.fn(w*0.68)*50+50).toFixed(1),w*0.76,sy+4);
  });
};

ANIM['VideoTranscriber'] = function(c,w,h,t){
  c.fillStyle='#08080f';c.fillRect(0,0,w,h);
  c.fillStyle='rgba(68,102,255,0.07)';c.fillRect(w*0.05,h*0.08,w*0.9,h*0.35);
  var bars=48;
  for(var i=0;i<bars;i++){
    var bh2=(Math.sin(i*0.4+t*0.1)*Math.cos(i*0.3+t*0.07)+1)*0.5;
    var bx=w*0.05+i*(w*0.9/bars);var playing=i<(t%bars);
    c.fillStyle=playing?'#4466ff':'#223';c.fillRect(bx,h*0.26-bh2*h*0.1,w*0.9/bars-1,bh2*h*0.2);
  }
  var words3=['VIDEO','TRANSCRIBED','BY','AI','INTO','TEXT','AUTOMATICALLY'].slice(0,Math.min(7,Math.floor(t/22)+1));
  c.fillStyle='rgba(255,255,255,0.07)';c.fillRect(w*0.05,h*0.5,w*0.9,h*0.38);
  c.fillStyle='#e0e0e0';c.font='12px monospace';c.textAlign='left';
  var wordStr=words3.join(' ');c.fillText(wordStr,w*0.08,h*0.73);
  if(t%22<14&&words3.length<7){var tw2=c.measureText(wordStr).width;c.fillStyle='#4466ff';c.fillRect(w*0.08+tw2+2,h*0.62,2,14);}
  c.fillStyle='#4466ff';c.font='bold 9px monospace';c.textAlign='center';c.fillText('▶ AUTO TRANSCRIBE',w/2,h*0.95);
};

ANIM['crypto-paper-sim'] = function(c,w,h,t){
  c.fillStyle='#060a06';c.fillRect(0,0,w,h);
  c.fillStyle='#f7931a';c.font='bold 14px monospace';c.textAlign='left';c.fillText('₿',w*0.05,h*0.15);
  c.fillStyle='#e0e0e0';c.font='bold 10px monospace';c.fillText('BTC / PAPER SIM',w*0.12,h*0.15);
  function price(i){var v=0.5;for(var j=0;j<4;j++)v+=Math.sin(i*0.13+j*1.7+t*0.007)*0.11;return Math.max(0.05,Math.min(0.95,v));}
  var cH=h*0.65,cY=h*0.17,cX=w*0.05,cW=w*0.9,bW2=cW/32;
  c.strokeStyle='rgba(255,255,255,0.05)';c.lineWidth=1;
  for(var i=0;i<4;i++){var gy=cY+i*(cH/3);c.beginPath();c.moveTo(cX,gy);c.lineTo(cX+cW,gy);c.stroke();}
  var off=Math.floor(t/4)%32;
  for(var i=0;i<30;i++){
    var idx2=(i+off)%35,nidx=(idx2+1)%35;
    var op2=price(idx2+t*0.02),cp2=price(nidx+t*0.02),up=cp2>=op2;
    var cx2=cX+i*bW2+bW2/2,oy=cY+cH-(op2*cH*0.88),cy2=cY+cH-(cp2*cH*0.88);
    c.strokeStyle=up?'#22dd44':'#ff4444';c.lineWidth=1;
    c.beginPath();c.moveTo(cx2,Math.min(oy,cy2)-3);c.lineTo(cx2,Math.max(oy,cy2)+3);c.stroke();
    c.fillStyle=up?'#22dd44':'#ff4444';c.fillRect(cx2-bW2*0.28,Math.min(oy,cy2),bW2*0.56,Math.max(2,Math.abs(oy-cy2)));
  }
  var lastP=price(off+29+t*0.02),prevP=price(off+28+t*0.02);
  c.fillStyle='rgba(255,255,255,0.05)';c.fillRect(cX,h*0.84,cW,h*0.12);
  c.fillStyle='#888';c.font='8px monospace';c.textAlign='left';c.fillText('PAPER P&L',cX+6,h*0.93);
  c.fillStyle=lastP>prevP?'#22dd44':'#ff4444';c.font='bold 11px monospace';c.textAlign='right';
  c.fillText((lastP>prevP?'+':'')+((lastP-prevP)*100).toFixed(2)+'%',cX+cW-6,h*0.93);
};

ANIM['ModelTransparencyTest'] = function(c,w,h,t){
  c.fillStyle='#0a0710';c.fillRect(0,0,w,h);
  var metrics=[{l:'Accuracy',v:[0.92,0.87,0.78]},{l:'Reasoning',v:[0.85,0.91,0.72]},{l:'Honesty',v:[0.96,0.88,0.81]}];
  var mCols=['#7c3aed','#3b82f6','#ec4899'],mLabels=['A','B','C'];
  c.fillStyle='#555';c.font='8px monospace';c.textAlign='left';c.fillText('Model transparency benchmark',w*0.05,h*0.1);
  var p=Math.min(1,t/80);
  metrics.forEach(function(m,mi){
    var y=h*0.2+mi*h*0.26;
    c.fillStyle='#444';c.font='9px monospace';c.textAlign='left';c.fillText(m.l,w*0.05,y);
    m.v.forEach(function(v,vi){
      var bx=w*0.05+vi*(w*0.3),by=y+8,bW3=w*0.27,bH=11;
      c.fillStyle='#181020';c.fillRect(bx,by,bW3,bH);
      c.fillStyle=mCols[vi];c.fillRect(bx,by,bW3*v*p,bH);
      c.fillStyle=mCols[vi];c.font='8px monospace';c.textAlign='center';
      c.fillText(mLabels[vi]+': '+(v*100|0)+'%',bx+bW3/2,by+bH+10);
    });
  });
};

ANIM['prompt-architect'] = function(c,w,h,t){
  c.fillStyle='#080c14';c.fillRect(0,0,w,h);
  var blocks=[{l:'[SYSTEM]',col:'#7c3aed',y:0.08},{l:'[CONTEXT]',col:'#2563eb',y:0.28},{l:'[INSTRUCTION]',col:'#0891b2',y:0.5},{l:'[FORMAT]',col:'#059669',y:0.7}];
  var p=Math.min(1,t/110);
  blocks.forEach(function(b,i){
    var bp=Math.max(0,Math.min(1,p*4-i));
    var x=w*(0.05+i*0.015),bw=w*(0.9-i*0.03),bh=h*0.15;
    var y=h*b.y;
    c.fillStyle=b.col.replace('#','rgba(')+'33)'.replace(/rgba\(([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})33\)/,function(_,r,g,b2){return 'rgba('+parseInt(r,16)+','+parseInt(g,16)+','+parseInt(b2,16)+',0.18)';});
    c.fillStyle=b.col+'22';
    c.strokeStyle=b.col;c.lineWidth=1;
    c.beginPath();c.roundRect(x,y,bw*bp,bh,4);c.fill();c.stroke();
    if(bp>0.5){c.fillStyle=b.col;c.font='bold 9px monospace';c.textAlign='left';c.fillText(b.l,x+8,y+bh*0.6);}
  });
  c.fillStyle='rgba(255,255,255,0.35)';c.font='8px monospace';c.textAlign='center';c.fillText('→ optimized prompt',w/2,h*0.92);
};

ANIM['FreeCoder'] = function(c,w,h,t){
  c.fillStyle='#000d00';c.fillRect(0,0,w,h);
  c.fillStyle='#111';c.fillRect(0,0,w,h*0.12);
  c.fillStyle='#39ff14';c.font='9px monospace';c.textAlign='left';c.fillText('freecoder agent v1.0',w*0.05,h*0.082);
  var lines=[{t:'> analyzing codebase...',d:0,col:'#777'},{t:'> found 3 issues to fix',d:40,col:'#ff6644'},{t:'> patching null_check.py',d:80,col:'#39ff14'},{t:'  def safe_parse(data):',d:110,col:'#f0f0f0'},{t:'    if not data: return {}',d:130,col:'#f0f0f0'},{t:'    return json.loads(data)',d:150,col:'#f0f0f0'},{t:'> tests: 12/12 passed ✓',d:190,col:'#39ff14'}];
  lines.forEach(function(l,i){
    if(t<l.d)return;
    c.fillStyle=l.col;c.font='9px monospace';c.textAlign='left';c.fillText(l.t,w*0.05,h*0.22+i*h*0.107);
  });
  var last=lines.filter(function(l){return t>=l.d;}).length-1;
  if(last>=0&&t%22<14){var tw=c.measureText(lines[last].t).width;c.fillStyle='#39ff14';c.fillRect(w*0.05+tw+2,h*0.22+last*h*0.107-10,2,11);}
};

// Default animation for any unlisted repo
ANIM['__default__'] = function(c,w,h,t){
  c.fillStyle='#0f1117';c.fillRect(0,0,w,h);
  for(var i=0;i<8;i++){
    var x=w*0.1+Math.sin(t*0.03+i*0.9)*w*0.35,y=h*0.2+Math.cos(t*0.025+i*1.1)*h*0.3;
    c.fillStyle='rgba(57,255,20,'+(0.1+i*0.06)+')';c.beginPath();c.arc(x,y,4-i*0.3,0,6.28);c.fill();
  }
  c.strokeStyle='rgba(57,255,20,0.12)';c.lineWidth=1;c.beginPath();c.moveTo(w*0.1,h*0.5);c.bezierCurveTo(w*0.3,h*0.2+Math.sin(t*0.02)*h*0.2,w*0.7,h*0.8+Math.sin(t*0.015)*h*0.2,w*0.9,h*0.5);c.stroke();
};

(function loadProjects() {
  var LANG_COLORS = {
    Python:'#3572A5',JavaScript:'#f1e05a',TypeScript:'#2b7489',
    HTML:'#e34c26',CSS:'#563d7c',Rust:'#dea584',Go:'#00ADD8',
    'C++':'#f34b7d',C:'#555',Shell:'#89e051',Ruby:'#701516',
    Java:'#b07219',Kotlin:'#7F52FF',Swift:'#F05138',
  };
  var SKIP = ['BambooForest','awesomo913.github.io','fleet-route-command','revolutionarydesigns-site','typingspeedtest-privacy','GitHubAppInstaller','TCGValueTracker'];

  function humanName(n){return n.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/[-_]/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase();});}

  function card(repo) {
    var name = humanName(repo.name);
    var desc = repo.description || '';
    var lang = repo.language || '';
    var stars = repo.stargazers_count || 0;
    var color = LANG_COLORS[lang] || '#888';

    var featured = ['Claude-Token-Saver','gemini-analyzer','KidsCodeAcademy','card-collection-anime','video-trimmer','animal-art-studio'];
    var isFeatured = featured.indexOf(repo.name) !== -1;
    var featuredStyle = isFeatured ? 'box-shadow:0 4px 0 rgba(120,90,58,.16),0 0 0 2px rgba(208,122,54,.55);' : '';
    return '<article class="proj-card" style="' + featuredStyle + '" onclick="window.open(\'' + repo.html_url + '\',\'_blank\')">' +
      '<div class="proj-img">' +
        '<canvas class="proj-canvas" data-anim="' + repo.name + '" width="640" height="320"></canvas>' +
      '</div>' +
      '<div class="proj-body">' +
        '<div class="proj-meta-row">' +
          (lang ? '<span class="lang-dot" style="background:' + color + '"></span><span class="lang-name">' + lang + '</span>' : '') +
          (stars > 0 ? '<span class="stars">★ ' + stars + '</span>' : '') +
        '</div>' +
        '<div class="proj-name">' + name + '</div>' +
        (desc ? '<div class="proj-desc">' + desc + '</div>' : '') +
        '<a href="' + repo.html_url + '" class="proj-link" target="_blank" rel="noopener" onclick="event.stopPropagation()">View on GitHub ↗</a>' +
      '</div>' +
    '</article>';
  }

  function startAnimations() {
    var canvases = document.querySelectorAll('.proj-canvas');
    var ctxs = [];
    canvases.forEach(function(cvs) {
      var ctx = cvs.getContext('2d');
      var fn = ANIM[cvs.dataset.anim] || ANIM['__default__'];
      ctxs.push({ctx:ctx, fn:fn, w:cvs.width, h:cvs.height, el:cvs, active:true});
    });
    // Pause off-screen + hidden tab
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(entry){
          ctxs.forEach(function(item){ if(item.el === entry.target) item.active = entry.isIntersecting; });
        });
      }, {threshold:0.1});
      canvases.forEach(function(c){ io.observe(c); });
    }
    document.addEventListener('visibilitychange', function(){
      ctxs.forEach(function(item){ item.active = document.visibilityState === 'visible'; });
    });
    var t = 0;
    function frame() {
      t++;
      ctxs.forEach(function(item){ if(item.active) item.fn(item.ctx, item.w, item.h, t); });
      requestAnimationFrame(frame);
    }
    frame();
  }

  var grid = document.getElementById('proj-grid');
  var loading = document.getElementById('proj-loading');

  fetch('https://api.github.com/users/awesomo913/repos?sort=updated&per_page=100')
    .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
    .then(function(repos){
      var filtered = repos
        .filter(function(r){ return !r.fork && !r.private && SKIP.indexOf(r.name) === -1; })
        .sort(function(a,b){
          // Featured repos first
          var featured = ['Claude-Token-Saver','gemini-analyzer','KidsCodeAcademy','card-collection-anime','video-trimmer','animal-art-studio'];
          var niche = ['crypto-paper-sim','ModelTransparencyTest','ClaudeCodingCourse'];
          var ai = featured.indexOf(a.name), bi = featured.indexOf(b.name);
          var an = niche.indexOf(a.name), bn = niche.indexOf(b.name);
          if (ai !== -1 && bi === -1) return -1;
          if (bi !== -1 && ai === -1) return 1;
          if (an !== -1 && bn === -1) return 1;
          if (bn !== -1 && an === -1) return -1;
          return new Date(b.updated_at) - new Date(a.updated_at);
        });
      if(loading) loading.remove();
      grid.insertAdjacentHTML('beforeend', filtered.map(card).join(''));
      startAnimations();
    })
    .catch(function(){
      if(loading) loading.remove();
      grid.innerHTML = '<div class="proj-error">Couldn\'t load projects. <a href="https://github.com/awesomo913" target="_blank" rel="noopener">View on GitHub ↗</a></div>';
    });
})();
