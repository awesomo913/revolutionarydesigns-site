// Persistent, guarded workshop. Animation never owns game state or grants rewards.
const BENCH = {
  names: ['Pair', 'Cut', 'Align', 'Secure', 'Heal'],
  frame: 0,
  transitionAt: 0,
  get job() { return G.state?.graft; },
  fresh() { return { stage: 0, root: '', plant: 0, cut: 12, position: 50, tension: 25, method: 'bands', scores: {}, days: 0 }; },
  init() {
    if (!G.state) return;
    if (!G.state.graft) G.state.graft = this.fresh();
    if (this.job.stage > 0 && this.job.stage < 6 && COLLECTION.get(this.job.plant)?.speciesId === 'haworthia-truncata') {
      G.state.graft = this.fresh();
      STUDIO.toast('Haworthia stays in the nursery. Choose a cactus for this grafting bench.');
    }
    if (this.job.stage > 0 && this.job.stage < 6 && !COLLECTION.get(this.job.plant)) {
      G.state.graft = this.fresh();
      STUDIO.toast('That specimen is no longer in your nursery. Choose a new pair.');
    }
    this.render();
    this.animate();
  },
  reset() {
    if (this.job?.stage === 5) { STUDIO.toast('Your graft is healing. Finish this union before starting another.'); return; }
    G.state.graft = this.fresh();
    this.render(); STUDIO.save(); this.animate();
  },
  eligible(c) { return c.health >= 50 && !c.grafted && !c.affliction && c.speciesId !== 'haworthia-truncata'; },
  choose() {
    if (this.job?.stage !== 0) return;
    const root = document.getElementById('rootstock-select').value;
    const plant = +document.getElementById('scion-select').value;
    const c = COLLECTION.get(plant);
    if (!ROOTSTOCKS.some(r => r.id === root) || !c || !this.eligible(c)) {
      this.feedback('Choose a rootstock and a healthy, ungrafted scion.'); return;
    }
    Object.assign(this.job, { root, plant, stage: 1 });
    this.step('Pair selected. Let’s prepare the union.');
  },
  set(key, value) {
    const stages = { cut: 1, position: 2, tension: 3 };
    if (this.job.stage !== stages[key]) return;
    const limits = key === 'cut' ? [-20, 20] : [0, 100];
    this.job[key] = Math.max(limits[0], Math.min(limits[1], +value || 0));
    this.updateFeedback(); this.draw(0); STUDIO.save();
  },
  alignment() {
    const j = this.job;
    const rootRadius = j.root === 'pereskiopsis' ? 46 : 68;
    const scionRadius = 31;
    const offset = (j.position - 50) * 2.4;
    const target = rootRadius - scionRadius + 18;
    const intersects = Math.abs(offset) > Math.abs(rootRadius - scionRadius) && Math.abs(offset) < rootRadius + scionRadius;
    return { rootRadius, scionRadius, offset, score: intersects ? Math.max(0, Math.round(100 - Math.abs(Math.abs(offset) - target) * 1.7)) : 0 };
  },
  cutScore() { return Math.round(100 - Math.abs(this.job.cut) * 3); },
  tensionScore() { return Math.max(0, Math.round(100 - Math.abs(this.job.tension - 55) * 2.5)); },
  lockCut() {
    if (this.job.stage !== 1) return;
    if (this.cutScore() < 70) { this.feedback('Level the blade a little more before making the cut.'); return; }
    this.job.scores.cut = this.cutScore(); this.job.stage = 2;
    this.step('Clean cut. Now connect the vascular rings.', 'cut');
  },
  lockAlignment() {
    if (this.job.stage !== 2 || this.alignment().score < 65) return;
    this.job.scores.align = this.alignment().score; this.job.stage = 3;
    this.step('Connection found. Secure it without crushing the scion.');
  },
  describeWrap() {
    const descriptions={bands:'Elastic loops pass over the scion and anchor beneath the pot, holding the cut faces together.',parafilm:'Thin, stretched film conforms over the scion and joins a self-adhering collar around the stock.',stocking:'Fine nylon mesh stretches over the crown and gathers below the union, held by an elastic collar.'};
    if(this.job.root==='pereskiopsis')descriptions.bands='Fine elastic loops pass over the small scion and attach to a collar around the slender stock.';
    const note=document.getElementById('wrap-description');if(note)note.textContent=descriptions[this.job.method]||descriptions.bands;
  },
  secure() {
    if (this.job.stage !== 3 || this.tensionScore() < 65) return;
    this.job.method = document.getElementById('wrap-method').value;
    this.job.scores.wrap = this.tensionScore(); this.job.stage = 4;
    this.step('A stable union. Your graft is ready for recovery.');
  },
  heal() {
    if (this.job.stage !== 4) return;
    this.job.stage = 5; this.job.days = 0;
    this.step('Recovery started. Seven game days to establish the union.');
  },
  tick() {
    const j = this.job;
    if (!j || j.stage !== 5) return;
    const plant = COLLECTION.get(j.plant);
    if (!plant || plant.grafted) { G.state.graft = this.fresh(); return; }
    // The workshop provides recovery care; other plants still follow ordinary care rules.
    plant.health = Math.max(70, plant.health);
    plant.affliction = null;
    j.days++;
    if (j.days >= 7) {
      j.stage = 6; // Commit before any render/reward, so repeated actions cannot pay twice.
      j.quality = Math.round(j.scores.cut * .25 + j.scores.align * .5 + j.scores.wrap * .25);
      j.grade = j.quality >= 94 ? 'Masterful union' : j.quality >= 83 ? 'Beautiful connection' : 'A promising start';
      j.reward = Math.round(j.quality / 3);
      plant.grafted = true; plant.rootstock = j.root; plant.graftQuality = j.quality;
      plant.value = Math.round(plant.value * (1.4 + j.quality / 160));
      G.state.coins += j.reward;
      G.logEvent('good', '✦', `${j.grade}: ${j.quality}/100. ${getSpecies(plant.speciesId).name} graft established. +${j.reward} coins.`);
      STUDIO.progress().grafts = (STUDIO.progress().grafts || 0) + 1;
      STUDIO.progress().xp += 35;
      STUDIO.toast(`${j.grade} · +${j.reward} coins · +35 XP`, 'reward');
    }
    if (document.getElementById('tab-bench').classList.contains('active')) this.render();
  },
  step(message, sound = 'step') {
    this.transitionAt = performance.now(); this.render();
    G.logEvent('info', '✦', message); STUDIO.play(sound);
    if(sound==='cut') STUDIO.spark();
    STUDIO.sync();
    if (innerWidth <= 760) requestAnimationFrame(() => document.querySelector('.workshop').scrollIntoView({block:'start',behavior:'instant'}));
  },
  feedback(message) { document.getElementById('bench-feedback').textContent = message; },
  updateFeedback() {
    const j = this.job;
    let score = 0, text = '';
    if (j.stage === 1) { score = this.cutScore(); text = `${j.cut}° blade angle · ${score}% clean cut. Aim for a level cut.`; }
    if (j.stage === 2) { score = this.alignment().score; text = `${score}% connection · ${score >= 65 ? 'Rings intersect. You can lock this position.' : 'Slide off-center until the two ring outlines cross.'}`; }
    if (j.stage === 3) { score = this.tensionScore(); text = `${j.tension}% tension · ${score}% stability. ${j.tension < 41 ? 'Too loose — the scion could slip.' : j.tension > 69 ? 'Too tight — ease the pressure.' : 'Secure, with room to breathe.'}`; }
    this.feedback(text);
    const button = document.getElementById('bench-action');
    if (button && j.stage >= 1 && j.stage <= 3) button.disabled = score < (j.stage === 1 ? 70 : 65);
    this.renderScores();
  },
  renderScores() {
    const j = this.job;
    document.getElementById('bench-quality').innerHTML = ['cut', 'align', 'wrap'].map((k, i) => `<div><span>${['Clean cut', 'Connection', 'Stability'][i]}</span><b>${j.scores[k] == null ? '—' : j.scores[k] + '%'}</b></div>`).join('');
  },
  render() {
    const j = this.job, s = j.stage, current = Math.min(s, 4);
    const root = ROOTSTOCKS.find(r => r.id === j.root);
    const plant = COLLECTION.get(j.plant);
    document.getElementById('workshop-steps').innerHTML = this.names.map((name, i) => `<li class="${i < current || s === 6 ? 'done' : i === current ? 'current' : ''}" ${i === current ? 'aria-current="step"' : ''}><span>${i < current || s === 6 ? '✓' : '0' + (i + 1)}</span>${name}</li>`).join('');
    const headings = ['Better together.', 'A clean beginning.', 'Find the connection.', 'Just enough pressure.', 'Give it time.', 'The union is forming.', j.grade || 'A living connection.'];
    const instructions = [
      'Choose a rootstock and a healthy, ungrafted cactus. Haworthia stays in the nursery. Practice stock and tools are included.',
      'Adjust the blade until it sits level. The cut line moves with your hand; a flatter cut earns a better finish.',
      'Drag the gold ring or use the slider. The ring outlines must intersect. Stacking unequal rings exactly in the center leaves a gap.',
      'Choose a wrap, then adjust its tension. Aim for the gold zone: enough contact to hold, without excess pressure.',
      'Your technique is recorded. Start recovery, then tend your nursery while the union establishes over seven game days.',
      'Your specimen is receiving recovery care. Advance the game clock here or continue tending the rest of your nursery.',
      'Your plant is back in the nursery. Its rootstock now affects growth, and your craftsmanship increases its value.'
    ];
    document.getElementById('bench-kicker').textContent = s === 6 ? 'UNION ESTABLISHED' : `0${current + 1} / ${this.names[current].toUpperCase()}`;
    document.getElementById('bench-heading').textContent = headings[s];
    document.getElementById('bench-instruction').textContent = instructions[s];
    document.getElementById('scene-status').textContent = s === 6 ? 'ESTABLISHED' : this.names[current].toUpperCase();
    document.getElementById('specimen-number').textContent = String(j.plant || '01').padStart(2, '0');
    document.getElementById('scene-caption').textContent = plant ? `${getSpecies(plant.speciesId).name} / ${root?.name || ''}` : 'One root system. A new possibility.';
    let html = '';
    const slider = (label, key, min, max, value, ends) => `<label class="workshop-label" for="graft-${key}">${label}</label><input id="graft-${key}" class="precision-slider" type="range" min="${min}" max="${max}" value="${value}" oninput="BENCH.set('${key}',this.value)"><div class="range-ends"><span>${ends[0]}</span><span>${ends[1]}</span></div>`;
    if (s === 0) {
      html = `<label class="workshop-label" for="rootstock-select">Rootstock / the foundation</label><select id="rootstock-select">${ROOTSTOCKS.map(r => `<option value="${r.id}" ${r.id === 'trichocereus-pachanoi-root' ? 'selected' : ''}>${r.name} · ${r.speedBonus}× game growth</option>`).join('')}</select><label class="workshop-label" for="scion-select">Scion / your specimen</label><select id="scion-select">${G.state.collection.filter(c => this.eligible(c)).map(c => `<option value="${c.instanceId}">${getSpecies(c.speciesId).name} · ${c.stage}</option>`).join('') || '<option value="">No eligible plants — visit the nursery</option>'}</select><button class="btn-primary" onclick="BENCH.choose()">Bring to the bench →</button>`;
    } else if (s === 1) {
      html = slider('Blade angle', 'cut', -20, 20, j.cut, ['−20°', 'LEVEL / 0°', '+20°'].filter((x,i)=>i!==1)) + '<button id="bench-action" class="btn-primary" onclick="BENCH.lockCut()">Make the cut →</button>';
    } else if (s === 2) {
      html = slider('Scion position / top-down view', 'position', 0, 100, j.position, ['Left', 'Right']) + '<button id="bench-action" class="btn-primary" onclick="BENCH.lockAlignment()">Lock the connection →</button>';
    } else if (s === 3) {
      html = `<label class="workshop-label" for="wrap-method">Securing method</label><select id="wrap-method" onchange="BENCH.job.method=this.value;BENCH.describeWrap();BENCH.draw(0);STUDIO.save()"><option value="bands">Grafting bands</option><option value="parafilm">Parafilm</option><option value="stocking">Nylon stocking</option></select><p id="wrap-description" class="wrap-description" aria-live="polite"></p>` + slider('Wrap tension', 'tension', 0, 100, j.tension, ['Loose', 'Tight']) + '<button id="bench-action" class="btn-primary" onclick="BENCH.secure()">Secure the union →</button>';
    } else if (s === 4) {
      html = '<div class="recovery-card"><b>07</b><span>game days of recovery<br>Care provided at the bench</span></div><button class="btn-primary" onclick="BENCH.heal()">Begin recovery →</button>';
    } else if (s === 5) {
      html = `<div class="recovery-card"><b>${j.days}<small>/7</small></b><span>game days complete<br>${j.days < 3 ? 'Contact forming' : j.days < 6 ? 'Tissue knitting together' : 'Almost established'}</span></div><div class="xp-track"><i style="width:${j.days / 7 * 100}%"></i></div><button class="btn-primary" onclick="G.nextDay()">Tend for one day →</button><button class="btn-secondary" onclick="STUDIO.advance(7-BENCH.job.days)">Tend through recovery →</button>`;
    } else {
      html = `<div class="union-score"><strong>${j.quality}<small>/100</small></strong><span>CRAFTSMANSHIP</span></div><p class="reward-line">+${j.reward} coins · +35 XP · ${root?.speedBonus || 2}× growth</p><button class="btn-primary" onclick="G.switchTab('nursery')">See your growing collection →</button><button class="btn-secondary" onclick="BENCH.reset()">Create another union</button>`;
    }
    document.getElementById('bench-controls').innerHTML = html;
    if(s===0){
      const preview=()=>{
        j.root=document.getElementById('rootstock-select').value;
        j.plant=+document.getElementById('scion-select').value||0;
        const selected=COLLECTION.get(j.plant),stock=ROOTSTOCKS.find(r=>r.id===j.root);
        document.getElementById('scene-caption').textContent=selected?`${getSpecies(selected.speciesId).name} / ${stock?.name||''}`:'Choose a healthy cactus from your nursery.';
        this.draw(0);STUDIO.save();
      };
      document.getElementById('rootstock-select').onchange=preview;
      document.getElementById('scion-select').onchange=preview;
      preview();
    }
    if (s === 3) { document.getElementById('wrap-method').value = j.method; this.describeWrap(); }
    this.feedback(''); this.updateFeedback(); this.draw(0);
    const canvas = document.getElementById('bench-canvas');
    canvas.style.cursor = s === 2 ? 'ew-resize' : 'default';
    let dragging = false;
    canvas.onpointerdown = event => {
      if (this.job.stage !== 2) return;
      const rect=canvas.getBoundingClientRect(),px=(event.clientX-rect.left)/rect.width*canvas.width,py=(event.clientY-rect.top)/rect.height*canvas.height;
      const phone=canvas.width===600;
      if (Math.hypot(px-((phone?300:720)+this.alignment().offset*(phone?1.65:1)),py-(phone?185:245))>(phone?95:60)) return;
      dragging=true;canvas.setPointerCapture(event.pointerId);
    };
    canvas.onpointermove = event => {
      if(!dragging || this.job.stage !== 2)return;
      const rect=canvas.getBoundingClientRect(),px=(event.clientX-rect.left)/rect.width*canvas.width,phone=canvas.width===600;
      this.set('position',Math.round(50+(px-(phone?300:720))/(2.4*(phone?1.65:1))));
      document.getElementById('graft-position').value=this.job.position;
    };
    canvas.onpointerup = canvas.onpointercancel = () => { dragging=false; };
  },
  animate() {
    cancelAnimationFrame(this.frame);
    const loop = time => {
      if (!document.getElementById('tab-bench').classList.contains('active') || document.hidden) { this.frame = 0; return; }
      this.draw(time);
      if (!matchMedia('(prefers-reduced-motion: reduce)').matches) this.frame = requestAnimationFrame(loop);
    };
    this.frame = requestAnimationFrame(loop);
  },
  draw(time) {
    if (!this.job) return;
    const c = document.getElementById('bench-canvas'), j = this.job;
    const phone = matchMedia('(max-width: 760px)').matches;
    if(!this.surface){this.surface=document.createElement('canvas');this.surface.width=960;this.surface.height=740;}
    const targetWidth=phone?600:960,targetHeight=phone?400:740;
    if(c.width!==targetWidth||c.height!==targetHeight){c.width=targetWidth;c.height=targetHeight;}
    const x = phone ? this.surface.getContext('2d') : c.getContext('2d');
    const w = 960, h = 740, s = j.stage, a = this.alignment();
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const t = reduced ? 0 : time / 1000;
    x.clearRect(0, 0, w, h);
    const bg = x.createLinearGradient(0, 0, w, h); bg.addColorStop(0, '#537e4c'); bg.addColorStop(1, '#244f39'); x.fillStyle = bg; x.fillRect(0, 0, w, h);
    x.strokeStyle = '#d8c99e0a'; x.lineWidth = 1;
    for (let i = 0; i < w; i += 48) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, h); x.stroke(); }
    for (let i = 0; i < h; i += 48) { x.beginPath(); x.moveTo(0, i); x.lineTo(w, i); x.stroke(); }
    const halo = x.createRadialGradient(320, 300, 10, 320, 300, 340); halo.addColorStop(0, '#a3b78523'); halo.addColorStop(1, '#a3b78500'); x.fillStyle = halo; x.fillRect(0, 0, w, h);
    const line = (x1,y1,x2,y2,color,width=1) => { x.strokeStyle=color; x.lineWidth=width; x.beginPath(); x.moveTo(x1,y1); x.lineTo(x2,y2); x.stroke(); };
    const text = (str,px,py,size=16,color='#b6c6af') => { x.fillStyle=color; x.font=`${size}px "DM Sans", sans-serif`; x.fillText(str,px,py); };
    // The same textured clay and mineral mix as the nursery, at bench scale.
    if(BOTANICAL.potTexture){
      x.save();x.fillStyle='#091b1466';x.beginPath();x.ellipse(320,672,122,15,0,0,Math.PI*2);x.fill();
      x.drawImage(BOTANICAL.potTexture,190,456,260,216);x.restore();
    }else{
    // Glazed clay pot, mineral surface and a ribbed, dimensional rootstock.
    x.fillStyle='#03110b88'; x.beginPath(); x.ellipse(322,645,185,27,0,0,Math.PI*2); x.fill();
    const pot=x.createLinearGradient(190,0,445,0); pot.addColorStop(0,'#855139'); pot.addColorStop(.38,'#bd8962'); pot.addColorStop(1,'#694531');
    x.fillStyle=pot; x.beginPath(); x.moveTo(180,510); x.lineTo(460,510); x.lineTo(427,634); x.quadraticCurveTo(320,666,213,634); x.closePath(); x.fill();
    x.strokeStyle='#d7a47b55'; x.lineWidth=2; for(let i=0;i<5;i++){x.beginPath();x.ellipse(320,548+i*18,130-i*4,12,0,0,Math.PI);x.stroke();}
    x.fillStyle='#b88c65'; x.beginPath(); x.ellipse(320,510,145,35,0,0,Math.PI*2); x.fill();
    x.fillStyle='#473e2a'; x.beginPath(); x.ellipse(320,510,128,26,0,0,Math.PI*2); x.fill();
    for(let i=0;i<70;i++){let px=206+(i*67%225),py=495+(i*17%29);x.fillStyle=['#b9aa86','#8b8269','#dbceab','#6e6650'][i%4];x.beginPath();x.ellipse(px,py,4+i%3,3, i,0,Math.PI*2);x.fill();}
    }
    BOTANICAL.workshop(x,j,t);
    if(s===3&&BOTANICAL.ready&&!phone){
      // Inspect the securing material at working scale, especially on tiny scions.
      x.save();x.beginPath();x.rect(0,0,555,740);x.clip();x.fillStyle=bg;x.fillRect(0,0,555,740);
      const b=BOTANICAL.graftBounds,zoom=Math.min(3.1,460/(b.right-b.left),525/(b.bottom-b.top));
      const cx=(b.left+b.right)/2,cy=(b.top+b.bottom)/2;
      x.beginPath();x.rect(15,72,520,600);x.clip();x.translate(275,372);x.scale(zoom,zoom);x.translate(-cx,-cy);
      BOTANICAL.workshop(x,j,t);x.restore();
      text('GRAFT / CLOSE VIEW',48,61,15,'#e1d8bd');
    }
    // Magnified cross-section: true ring outlines move without any snap-to-center trick.
    const vx=720,vy=245;
    x.fillStyle='#1c4532';x.beginPath();x.arc(vx,vy,148,0,7);x.fill();x.strokeStyle='#c2d9a788';x.lineWidth=1;x.stroke();
    line(vx-128,vy,vx+128,vy,'#65796644');line(vx,vy-128,vx,vy+128,'#65796644');
    x.fillStyle='#6f926d21';x.beginPath();x.arc(vx,vy,a.rootRadius+20,0,7);x.fill();x.strokeStyle='#a7bd92';x.lineWidth=4;x.beginPath();x.arc(vx,vy,a.rootRadius,0,7);x.stroke();
    const ox=s>=2?a.offset:0;
    x.fillStyle='#efc16e18';x.beginPath();x.arc(vx+ox,vy,a.scionRadius+12,0,7);x.fill();x.strokeStyle='#e7bd73';x.lineWidth=4;x.beginPath();x.arc(vx+ox,vy,a.scionRadius,0,7);x.stroke();
    text('VASCULAR RINGS / TOP VIEW',588,61,15,'#e1d8bd');
    text('Rootstock',613,431,17);line(590,425,604,425,'#a7bd92',4);text('Scion',768,431,17);line(746,425,760,425,'#e7bd73',4);
    text(s>=2?`${a.score}% connection`:'Move the scion to connect',604,479,23,'#e8d4a6');
    text(s>=5?`RECOVERY   ${Math.min(7,j.days)} / 7 DAYS`:'PRECISION IS A PRACTICE.',592,577,15);
    text(s===6?'A NEW CHAPTER OF GROWTH.':'TAKE YOUR TIME. MAKE IT YOURS.',592,608,13,'#91a891');
    if(!reduced){for(let i=0;i<12;i++){let px=(i*79+Math.sin(t*.22+i)*14)%960,py=(i*113-t*7)%740;if(py<0)py+=740;x.fillStyle=`rgba(225,199,138,${.10+Math.sin(t+i)*.06})`;x.beginPath();x.arc(px,py,1.7,0,7);x.fill();}}
    if(s===3&&!phone)text('SECURING MATERIAL / DETAIL',90,703,14);
    else {text('ROOT / FOUNDATION',86,703,14);text('SCION / NEW GROWTH',341,703,14);}
    if(phone) this.drawPhone(c.getContext('2d'),a);
  },
  drawPhone(x,a) {
    const j=this.job,s=j.stage;
    const bg=x.createLinearGradient(0,0,600,400);bg.addColorStop(0,'#578350');bg.addColorStop(1,'#244f39');x.fillStyle=bg;x.fillRect(0,0,600,400);
    const text=(value,px,py,size=24,color='#f5f2d5')=>{x.font=`${size}px "DM Sans",sans-serif`;x.fillStyle=color;x.fillText(value,px,py);};
    if(s===2){
      text('MAGNIFIED / DRAG THE GOLD RING',24,34,22);
      const cx=300,cy=185,scale=1.65;
      x.strokeStyle='#d2e6b62e';x.lineWidth=1;
      x.beginPath();x.moveTo(35,cy);x.lineTo(565,cy);x.moveTo(cx,55);x.lineTo(cx,318);x.stroke();
      x.fillStyle='#d8efab19';x.beginPath();x.arc(cx,cy,(a.rootRadius+17)*scale,0,Math.PI*2);x.fill();
      x.strokeStyle='#e1ecc0';x.lineWidth=6;x.beginPath();x.arc(cx,cy,a.rootRadius*scale,0,Math.PI*2);x.stroke();
      x.fillStyle='#f9c85c26';x.beginPath();x.arc(cx+a.offset*scale,cy,a.scionRadius*scale,0,Math.PI*2);x.fill();
      x.strokeStyle='#ffd372';x.lineWidth=7;x.beginPath();x.arc(cx+a.offset*scale,cy,a.scionRadius*scale,0,Math.PI*2);x.stroke();
      text('Rootstock',32,355,23,'#e1ecc0');text('Scion',220,355,23,'#ffd372');text(`${a.score}% contact`,372,355,25,'#fff3c4');
    } else {
      // Crop the specimen, rather than shrinking the entire desktop diagram and its labels.
      if(s===3&&BOTANICAL.ready){
        const b=BOTANICAL.graftBounds,zoom=Math.min(3.1,240/(b.right-b.left),340/(b.bottom-b.top));
        x.save();x.beginPath();x.rect(0,0,252,400);x.clip();x.translate(126,200);x.scale(zoom,zoom);x.translate(-(b.left+b.right)/2,-(b.top+b.bottom)/2);
        BOTANICAL.workshop(x,j,0);x.restore();
      }else x.drawImage(this.surface,130,60,390,620,0,0,252,400);
      text(s===0?'YOUR NEXT':s===1?'CLEAN CUT':s===3?'WRAP TENSION':s===6?'ESTABLISHED':'RECOVERY',285,70,22);
      text(s===0?'CONNECTION':s===1?`${j.cut}° blade`:s===3?`${j.tension}%`:s===6?`${j.quality}/100`:`${j.days} / 7 days`,285,126,30,'#ffe3a4');
      const lines=s===0?['Select your pair.','Tools included.']:s===1?['Level the blade.','Aim for 0°.']:s===3?['Find the gold zone.','Firm, not tight.']:s===6?['New growth ahead.','Your craft paid off.']:['A living union.','Care is provided.'];
      lines.forEach((line,i)=>text(line,285,207+i*38,22));
      text('GRITTY MIX',285,350,21,'#d1e4b6');
    }
  }
};
document.addEventListener('visibilitychange', () => { if (!document.hidden && BENCH.job) BENCH.animate(); });
window.addEventListener('resize', () => {
  if (BENCH.job && document.getElementById('tab-bench').classList.contains('active')) BENCH.draw(performance.now());
});
