// Presentation, feedback and progression. Saved game data remains portable in SAVE codes.
const STUDIO = {
  key: 'gritty-mix-greenhouse-v2', sound: false, audio: null, batch: false,
  missions: [
    { id: 'soil', title: 'Build a better foundation', detail: 'Save your first soil recipe', tab: 'lab', coins: 20, xp: 30, test: s => !!s.currentMix },
    { id: 'sow', title: 'Start something small', detail: 'Sow a seed packet in the chamber', tab: 'seeds', coins: 15, xp: 25, test: s => s.chambers.length > 0 || s.progress.sown },
    { id: 'graft', title: 'Make a living connection', detail: 'Complete your first graft', tab: 'bench', coins: 30, xp: 60, test: s => s.collection.some(c => c.grafted) || s.progress.grafts > 0 },
    { id: 'pot', title: 'A new generation', detail: 'Pot up a ready seedling chamber', tab: 'seeds', coins: 30, xp: 45, test: s => s.progress.potted > 0 },
    { id: 'collect', title: 'Room to grow', detail: 'Care for eight plants at once', tab: 'nursery', coins: 40, xp: 50, test: s => s.collection.length >= 8 },
    { id: 'bloom', title: 'Worth the wait', detail: 'Grow your first blooming plant', tab: 'nursery', coins: 45, xp: 60, test: s => s.collection.some(c => c.stage === 'blooming') },
    { id: 'sell', title: 'Share what you grow', detail: 'Sell a plant at the market', tab: 'market', coins: 20, xp: 30, test: s => s.progress.sales > 0 }
  ],
  progress() {
    if (!G.state.progress) G.state.progress = { xp: 0, claimed: [], grafts: 0, sown: 0, potted: 0, sales: 0 };
    return G.state.progress;
  },
  start() {
    let existing = false;
    try { existing = !!localStorage.getItem(this.key); } catch (_) {}
    if (existing && !confirm('Start a new nursery? Your existing device save will be replaced. Cancel to continue it or export a backup first.')) return;
    G.newGame();
    this.toast('Two specimens. Your own greenhouse. Let’s grow.', 'reward');
  },
  resume() {
    try {
      const code = localStorage.getItem(this.key);
      if (!code || !SAVE.decode(code)) { this.toast('No readable device save. You can import a backup code.'); return; }
      document.getElementById('code-input').value = code;
      G.loadFromCode(); this.toast('Welcome back. Your nursery is just as you left it.');
    } catch (_) { this.toast('Device storage is unavailable. Import a save code to continue.'); }
  },
  save() {
    if (!G.state || this.batch) return;
    G.state.activeFruit = BREED.activeFruit;
    try { localStorage.setItem(this.key, SAVE.encode(G.state)); document.getElementById('save-status').textContent = 'Saved on this device'; }
    catch (_) { document.getElementById('save-status').textContent = 'Device save unavailable · Export a code'; }
  },
  sync() {
    if (!G.state || this.batch) return;
    const p = this.progress();
    for (const m of this.missions) {
      if (!p.claimed.includes(m.id) && m.test(G.state)) {
        p.claimed.push(m.id); p.xp += m.xp; G.state.coins += m.coins;
        G.logEvent('good', '✦', `${m.title}: +${m.coins} coins / +${m.xp} XP.`);
        this.toast(`${m.title} · +${m.coins} coins / +${m.xp} XP`, 'reward');
      }
    }
    const level = 1 + Math.floor(p.xp / 100);
    document.getElementById('cultivator-level').textContent = level;
    document.getElementById('rank-name').textContent = ['New roots', 'Green fingers', 'Growing confidence', 'Union maker', 'Greenhouse keeper', 'Master cultivator'][Math.min(level - 1, 5)];
    document.getElementById('xp-fill').style.width = p.xp % 100 + '%';
    document.getElementById('xp-label').textContent = `${p.xp % 100} / 100 XP to level ${level + 1}`;
    document.getElementById('plant-count').textContent = G.state.collection.length;
    document.getElementById('coin-counter').textContent = `${G.state.coins} coins`;
    document.getElementById('day-counter').textContent = `Day ${G.state.day}`;
    const mission = this.missions.find(m => !p.claimed.includes(m.id));
    document.getElementById('mission-title').textContent = mission?.title || 'Your greenhouse, flourishing';
    document.getElementById('mission-detail').textContent = mission ? `${mission.detail} · +${mission.coins} coins / ${mission.xp} XP` : 'All seven discoveries complete. Keep collecting and refining your grafts.';
    const next = document.getElementById('next-day-btn');
    if (next) next.textContent = 'Next day →';
    this.save();
  },
  openMission() { G.switchTab(this.missions.find(m => !this.progress().claimed.includes(m.id))?.tab || 'nursery'); },
  toast(message, sound = 'step') {
    if (this.batch) return;
    const stack = document.getElementById('feedback-stack');
    if (!stack) return;
    while (stack.children.length >= (innerWidth < 760 ? 1 : 2)) stack.firstElementChild.remove();
    const item = document.createElement('div'); item.className = `feedback-toast ${sound === 'reward' ? 'reward' : ''}`;
    item.textContent = message; stack.appendChild(item);
    setTimeout(() => item.remove(), 4200);
    this.play(sound);
    if (sound === 'reward' || sound === 'soil') this.spark();
  },
  spark() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const origin = document.activeElement?.getBoundingClientRect();
    const ox = origin?.width ? Math.min(innerWidth - 30, Math.max(30, origin.x + origin.width / 2)) : innerWidth * .65;
    const oy = origin?.height ? Math.min(innerHeight - 40, Math.max(40, origin.y + origin.height / 2)) : innerHeight * .45;
    for (let i = 0; i < 16; i++) {
      const el = document.createElement('i'); el.className = 'growth-particle';
      const angle = i / 16 * Math.PI * 2;
      el.style.cssText = `left:${ox}px;top:${oy}px;--dx:${Math.cos(angle) * (45 + i * 3)}px;--dy:${Math.sin(angle) * (45 + i * 3) - 35}px;--turn:${i * 33}deg;`;
      document.body.appendChild(el); setTimeout(() => el.remove(), 1000);
    }
  },
  toggleSound() {
    this.sound = !this.sound;
    const button = document.getElementById('sound-toggle'); button.textContent = this.sound ? 'Sound on' : 'Sound off'; button.setAttribute('aria-pressed', String(this.sound));
    if (this.sound) this.play('reward');
  },
  play(kind) {
    if (!this.sound || document.hidden) return;
    try {
      if (!this.audio) this.audio = new (window.AudioContext || window.webkitAudioContext)();
      const ctx = this.audio; if (ctx.state === 'suspended') ctx.resume();
      const notes = kind === 'reward' ? [392, 494, 587, 784] : kind === 'water' ? [660, 880, 740] : kind === 'cut' ? [170, 100] : kind === 'soil' ? [220, 330, 440] : [440, 554];
      notes.forEach((frequency, i) => {
        const osc = ctx.createOscillator(), gain = ctx.createGain(), t = ctx.currentTime + i * .085;
        osc.type = kind === 'cut' ? 'triangle' : 'sine'; osc.frequency.setValueAtTime(frequency, t); osc.frequency.exponentialRampToValueAtTime(frequency * .98, t + .25);
        gain.gain.setValueAtTime(0, t); gain.gain.linearRampToValueAtTime(.045, t + .008); gain.gain.exponentialRampToValueAtTime(.0001, t + .38);
        osc.connect(gain); gain.connect(ctx.destination); osc.start(t); osc.stop(t + .4);
      });
    } catch (_) { this.sound = false; document.getElementById('sound-toggle').textContent = 'Sound unavailable'; document.getElementById('sound-toggle').setAttribute('aria-pressed', 'false'); }
  },
  waterAll(quiet = false) {
    if (!G.state) return;
    let count = 0;
    for (const c of G.state.collection) if (c.water <= 2 && c.health > 0) {
      c.water = getSpecies(c.speciesId)?.waterFreq || 10; c.health = Math.min(100, c.health + 5); count++;
    }
    if (count) G.logEvent('good', '◌', `Watered ${count} thirsty plant${count === 1 ? '' : 's'}.`);
    G.renderNursery(); this.sync();
    if (!quiet) this.toast(count ? `${count} plants watered. A little care goes a long way.` : 'Everyone is hydrated. No watering needed.', 'water');
    return count;
  },
  advance(days) {
    // A care shortcut, never an unattended timer. Stop at problems needing a decision.
    let elapsed = 0; this.batch = true;
    try {
      for (let i = 0; i < Math.min(7, Math.max(0, days)); i++) {
        if (G.state.collection.some(c => c.affliction && c.instanceId !== BENCH.job?.plant)) break;
        this.waterAll(true); G.nextDay(); elapsed++;
      }
    } finally { this.batch = false; }
    this.sync(); G.renderNursery();
    if (document.getElementById('tab-bench').classList.contains('active')) BENCH.render();
    this.toast(elapsed ? `Tended for ${elapsed} days. ${BENCH.job?.stage === 6 ? BENCH.job.grade + '!' : 'Your plants are growing.'}` : 'A plant needs treatment. Inspect it in the nursery before advancing.', elapsed ? 'reward' : 'step');
  },
  plantArt(c) { return BOTANICAL.nursery(c); },
  install() {
    const stack = document.createElement('div'); stack.id = 'feedback-stack'; stack.setAttribute('role', 'status'); stack.setAttribute('aria-live', 'polite'); document.body.appendChild(stack);
    try { const saved=!!localStorage.getItem(this.key); document.getElementById('continue-game').hidden=!saved; if(saved){const start=document.getElementById('start-game');start.className='btn-secondary';start.textContent='New nursery';} } catch (_) {}
    // Centralize persistence after successful synchronous game actions, including purchases and care.
    const wrap = (object, name, after) => { const original = object[name]; object[name] = function (...args) { const result = original.apply(this, args); if (after) after(...args); STUDIO.sync(); return result; }; };
    ['newGame','loadFromCode','saveSoilMix','applyTreatment','removeCactus','buyItem','claimStarterPack'].forEach(k => wrap(G, k));
    wrap(G, 'waterCactus', () => this.play('water'));
    const next = G.nextDay;
    G.nextDay = function () {
      if (!this.state) return;
      const before = this.state.collection.reduce((n,c) => n+c.growth,0), coins = this.state.coins;
      const stages = new Map(this.state.collection.map(c => [c.instanceId,c.stage]));
      next.call(this); BENCH.tick();
      if (this.state.collection.some(c => c.health >= 50)) STUDIO.progress().xp += 2;
      const growth = this.state.collection.reduce((n,c) => n+c.growth,0) - before;
      const milestones = this.state.collection.filter(c => stages.has(c.instanceId) && stages.get(c.instanceId) !== c.stage);
      document.getElementById('daily-recap').textContent = `Day ${this.state.day} · +${Math.max(0,growth).toFixed(1)} growth points · +${this.state.coins-coins} coins${milestones.length ? ' · ' + milestones.length + ' plants reached a new stage!' : ''}${this.state.collection.some(c=>c.affliction) ? ' · A plant needs treatment — inspect your nursery.' : ''}`;
      STUDIO.sync(); if (!STUDIO.batch) { STUDIO.play(milestones.length ? 'reward' : 'step'); if (milestones.length) STUDIO.toast('A new stage of growth. Visit your nursery.', 'reward'); }
    };
    wrap(BREED, 'pollinate'); wrap(BREED, 'harvest');
    const sow = BREED.sow; BREED.sow = function () { const n = G.state.chambers.length; sow.call(this); if(G.state.chambers.length > n) STUDIO.progress().sown++; STUDIO.sync(); };
    const pot = BREED.potUp; BREED.potUp = function (id) { const n = G.state.chambers.length; pot.call(this,id); if(G.state.chambers.length < n) STUDIO.progress().potted++; STUDIO.sync(); };
    const sell = MARKET.sell; MARKET.sell = function (id) { if (BENCH.job?.plant === id && BENCH.job.stage > 0 && BENCH.job.stage < 6) { STUDIO.toast('This plant is at the grafting bench. Finish its union first.'); return; } const n=G.state.collection.length; sell.call(this,id); if(G.state.collection.length<n) STUDIO.progress().sales++; STUDIO.sync(); };
    wrap(MARKET, 'buy');
    G.floatingText = (text) => this.toast(text, 'reward');
    const switchTab = G.switchTab;
    G.switchTab = function (tab) {
      switchTab.call(this,tab); STUDIO.sync(); if(tab==='nursery') STUDIO.addCareControls();
      if (document.getElementById('screen-game').classList.contains('active')) requestAnimationFrame(() => document.getElementById('tab-'+tab)?.scrollIntoView({block:'start',behavior:'instant'}));
    };
    // Accessible dialogs: focus enters on opening, is contained, and returns to its trigger.
    let returnFocus = null;
    document.querySelectorAll('.modal').forEach(modal => {
      modal.setAttribute('role','dialog'); modal.setAttribute('aria-modal','true');
      const heading=modal.querySelector('h2'); if(!heading.id) heading.id=modal.id+'-heading'; modal.setAttribute('aria-labelledby',heading.id);
      new MutationObserver(() => { if(modal.classList.contains('show')) { returnFocus=document.activeElement; modal.querySelector('button,textarea')?.focus(); } else if(returnFocus?.isConnected) returnFocus.focus(); }).observe(modal,{attributes:true,attributeFilter:['class']});
      modal.addEventListener('keydown',e=> { if(e.key==='Escape'){G.closeModal(modal.id);return;} if(e.key!=='Tab')return; const nodes=[...modal.querySelectorAll('button:not(:disabled),textarea,a[href],input,select')].filter(n=>n.getClientRects().length);const first=nodes[0],last=nodes.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();} });
    });
    document.addEventListener('visibilitychange',()=>{if(document.hidden)this.save();});
    window.addEventListener('pagehide',()=>this.save());
  },
  addCareControls() {
    if (document.getElementById('tend-week')) return;
    const b = document.createElement('button'); b.id='tend-week'; b.className='btn-small'; b.textContent='Tend for a week →'; b.onclick=()=>this.advance(7); document.querySelector('.nursery-controls').appendChild(b);
  }
};
STUDIO.install();
