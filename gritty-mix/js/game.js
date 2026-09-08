// Gritty Mix — Main Game Engine

const G = {
  state: null,
  initialized: false,

  // Default game state
  defaultState() {
    return {
      day: 1,
      coins: 0,
      collection: [],
      currentMix: null,
      lastEvents: [],
      nurserySort: 'value',
      seeds: [],
      chambers: [],
      marketInv: {},
      claimedStarter: false
    };
  },

  // ========== GAME FLOW ==========

  // Start new game
  newGame() {
    this.state = this.defaultState();
    BREED.activeFruit = null;
    this.initialized = true;

    // Give starter cactus
    COLLECTION.add('trichocereus-pachanoi', { stage: 'juvenile', growth: 50, value: 15, water: 10, health: 80 });

    // Give starter seeds
    this.giveStarterSeeds();

    // Give 2 free random seed packs (processed immediately)
    const rarePool = ['lophophora-williamsii', 'astrophytum-asterias', 'tephrocactus-articulatus', 'echinocactus-horizonthalonius', 'trichocereus-scopulicola'];
    for (let i = 0; i < 2; i++) {
      const pick = rarePool[Math.floor(Math.random() * rarePool.length)];
      const s = getSpecies(pick);
      this.state.seeds.push({
        id: Date.now() + i + Math.floor(Math.random() * 10000),
        name: `${s?.name || 'Rare Cactus'} Seeds`,
        parentA: pick,
        parentB: pick,
        count: 10,
        quality: 70 + Math.floor(Math.random() * 25),
        germination: 'Surface sow on sterile gritty mix. Keep warm (22-28°C). Germination 2-6 weeks.',
        harvested: this.state.day
      });
    }

    // Give starter coins
    this.state.coins = 35;
    COLLECTION.add('astrophytum-asterias', { stage: 'juvenile', growth: 45, water: 12, health: 90 });

    this.logEvent('good', '🌵', 'Welcome to Gritty Mix! Your San Pedro cutting has arrived.');
    this.logEvent('info', '🧪', 'Visit the Lab to mix your first soil.');
    this.logEvent('info', '💾', 'Your nursery autosaves on this device. Export a code for backup.');

    this.showScreen('screen-game');
    this.switchTab('lab');
    SOIL.applyPreset('trichocereus');
    this.refreshAll();
    this.setupModalClicks();
  },

  // Load game from save code
  showEnterCode() {
    document.getElementById('code-input').value = '';
    this.showScreen('screen-enter-code');
  },

  loadFromCode() {
    const code = document.getElementById('code-input').value.trim();
    if (!code) {
      alert('Please enter a save code.');
      return;
    }

    const state = SAVE.decode(code);
    if (!state) {
      alert('Invalid save code. Please check and try again.');
      return;
    }

    this.state = state;
    BREED.activeFruit = state.activeFruit || null;
    this.initialized = true;
    this.logEvent('info', '📂', 'Game loaded from save code.');
    this.showScreen('screen-game');
    this.switchTab('nursery');
    this.refreshAll();
    this.setupModalClicks();
  },

  showSaveCode() {
    if (!this.state) {
      alert('No game to save. Start a new game first!');
      return;
    }
    const code = SAVE.encode(this.state);
    document.getElementById('save-code-output').value = code;
    document.getElementById('modal-save').classList.add('show');
  },

  copySaveCode() {
    const text = document.getElementById('save-code-output').value;
    SAVE.copyToClipboard(text);
  },

  // ========== SCREEN MANAGEMENT ==========

  showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
  },

  switchTab(tabId) {
    // Move the highlight AND the active content together so they can never desync.
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const tabBtn = document.querySelector(`.tab[data-tab="${tabId}"]`);
    const tabContent = document.getElementById(`tab-${tabId}`);
    if (tabBtn) tabBtn.classList.add('active');
    if (tabContent) tabContent.classList.add('active');

    // Game tabs need an active game. The game screen isn't reachable without state
    // in normal flow, so guard defensively WITHOUT destroying the tab's DOM
    // (replacing innerHTML here wipes #rootstock-select etc. and breaks later renders).
    if (!this.state && ['nursery', 'lab', 'bench', 'seeds', 'market', 'events'].includes(tabId)) {
      return;
    }

    if (tabId === 'nursery') this.renderNursery();
    if (tabId === 'lab') this.initSoilIfNeeded();
    if (tabId === 'events') this.renderEvents();
    if (tabId === 'bench') this.initBench();
    if (tabId === 'seeds') this.initSeeds();
    if (tabId === 'market') this.initMarket();
  },

  // ========== SOIL LAB ==========

  initSoilIfNeeded() {
    if (!this.state) { return; }
    if (!document.querySelector('#soil-sliders input')) {
      SOIL.init();
      if (this.state.currentMix) {
        this.loadMixToSliders(this.state.currentMix);
      }
    }
  },

  loadMixToSliders(mix) {
    if (!mix) return;
    SOIL_COMPONENTS.forEach(comp => {
      const val = mix[comp.id] || 0;
      SOIL.sliders[comp.id] = val;
      const input = document.querySelector(`input[data-component="${comp.id}"]`);
      if (input) input.value = val;
      const pctEl = document.getElementById(`pct-${comp.id}`);
      if (pctEl) pctEl.textContent = val + '%';
    });
    SOIL.updateStats();
  },

  setSoilPreset(name) {
    SOIL.applyPreset(name);
  },

  saveSoilMix() {
    SOIL.saveMix();
  },

  // ========== NURSERY ==========

  renderNursery() {
    if (!this.state) { return; }
    COLLECTION.render(this.state.nurserySort);
    document.getElementById('day-counter').textContent = `Day ${this.state.day}`;
    document.getElementById('coin-counter').textContent = `💰 ${this.state.coins}`;
  },

  sortNursery(by) {
    this.state.nurserySort = by;
    COLLECTION.render(by);
  },

  inspectCactus(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus) return;

    const species = getSpecies(cactus.speciesId);
    if (!species) return;

    const mixScore = SOIL.evaluateMix(cactus.speciesId, this.state.currentMix);
    const stageEmoji = cactus.stage === 'seedling' ? '🌱' : cactus.stage === 'juvenile' ? '🌿' : '🌸';

    document.getElementById('inspect-title').textContent = `${species.emoji} ${cactus.nickname || species.name}`;
    document.getElementById('inspect-details').innerHTML = `
      <div class="inspect-section">
        <h4>Species</h4>
        <p><em>${species.species}</em> · ${species.rarity} · Native: ${species.native}</p>
      </div>
      <div class="inspect-section">
        <h4>Growth</h4>
        <p>${stageEmoji} ${cactus.stage} · ${Math.round(cactus.growth)}cm / ${species.maxSize}cm max · Age: ${cactus.age} days</p>
        <p>Growth Rate: ${'★'.repeat(species.growthRate)}${'☆'.repeat(3-species.growthRate)}</p>
      </div>
      <div class="inspect-section">
        <h4>Health</h4>
        <p>❤️ ${cactus.health}/100 · 💧 ${cactus.water} days of water left</p>
      </div>
      ${cactus.affliction ? `<div class="inspect-section"><h4>⚠️ Affliction</h4><p style="color:var(--red)"><strong>${(EVENTS.find(e=>e.id===cactus.affliction)||{}).icon||''} ${(EVENTS.find(e=>e.id===cactus.affliction)||{}).title||'Problem'}</strong> — ${(EVENTS.find(e=>e.id===cactus.affliction)||{}).msg||''}</p></div>` : ''}
      <div class="inspect-section">
        <h4>Soil Match</h4>
        <p>${mixScore.feedback} (Score: ${mixScore.score}/100)</p>
      </div>
      <div class="inspect-section">
        <h4>Value</h4>
        <p>💰 ${cactus.value} ${cactus.cultivar ? '· Rare cultivar!' : ''} ${cactus.grafted ? '· Grafted' : ''}</p>
      </div>
      <div class="inspect-section">
        <h4>Care</h4>
        <p>☀️ ${species.light} · 🌡️ ${species.minTemp}°C to ${species.maxTemp}°C</p>
        <p>💧 Water every ${species.waterFreq} days · Difficulty: ${'★'.repeat(species.difficulty)}${'☆'.repeat(5-species.difficulty)}</p>
      </div>
      ${cactus.cultivar ? `<div class="inspect-section"><h4>Clone Info</h4><p>${CULTIVARS.find(c => c.id === cactus.cultivar)?.desc || 'Rare clone'}</p></div>` : ''}
      <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap">
        ${cactus.affliction ? `<button onclick="G.openTreatment(${cactus.instanceId})" class="btn-primary">🩹 Treat</button>` : ''}
        <button onclick="G.waterCactus(${cactus.instanceId})" class="btn-secondary">💧 Water</button>
        <button onclick="G.removeCactus(${cactus.instanceId})" class="btn-secondary" style="color:var(--red)">🗑️ Remove</button>
      </div>
    `;

    document.getElementById('modal-inspect').classList.add('show');
  },

  // ========== PEST / FUNGAL TREATMENT MINI-GAME ==========
  // Tied to the Codex guides: pick the right fix to save the plant.
  openTreatment(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus || !cactus.affliction) return;
    const tx = TREATMENTS[cactus.affliction];
    const ev = EVENTS.find(e => e.id === cactus.affliction);
    if (!tx) return;
    const opts = tx.options.map(o =>
      `<button onclick="G.applyTreatment(${instanceId},'${o.id}')" class="btn-secondary" style="display:block;width:100%;text-align:left;margin:6px 0">${o.label}</button>`
    ).join('');
    document.getElementById('inspect-title').textContent = `🩹 Treat: ${ev ? ev.title : 'Problem'}`;
    document.getElementById('inspect-details').innerHTML = `
      <div class="inspect-section"><p>${ev ? ev.msg : ''}</p></div>
      <div class="inspect-section"><h4>Choose the right treatment</h4>${opts}</div>
      <button onclick="G.inspectCactus(${instanceId})" class="btn-secondary" style="margin-top:8px">← Back</button>
    `;
  },

  applyTreatment(instanceId, choiceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus || !cactus.affliction) return;
    const tx = TREATMENTS[cactus.affliction];
    const ev = EVENTS.find(e => e.id === cactus.affliction);
    const name = getSpecies(cactus.speciesId)?.name || 'Cactus';
    const fixed = ev ? ev.title : 'the problem';
    if (tx && choiceId === tx.correct) {
      cactus.health = Math.min(100, cactus.health + 20);
      cactus.affliction = null;
      this.logEvent('good', '✅', `${name}: treated ${fixed} correctly. +20 health.`);
    } else {
      cactus.health = Math.max(0, cactus.health - 10);
      this.logEvent('bad', '❌', `${name}: wrong treatment for ${fixed}. -10 health — try again.`);
    }
    this.closeModal('modal-inspect');
    this.renderNursery();
  },

  waterCactus(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus) return;
    if (cactus.water > 2) { STUDIO.toast('Still hydrated. Let the soil dry first.'); return; }
    cactus.water = getSpecies(cactus.speciesId)?.waterFreq || 10;
    cactus.health = Math.min(100, cactus.health + 5);
    this.logEvent('good', '💧', `${getSpecies(cactus.speciesId)?.name || 'Cactus'} watered.`);
    this.closeModal('modal-inspect');
    this.renderNursery();
  },

  removeCactus(instanceId) {
    if (BENCH.job?.plant === instanceId && BENCH.job.stage > 0 && BENCH.job.stage < 6) {
      STUDIO.toast('This specimen is at the bench. Finish or reset the graft first.'); return;
    }
    if (confirm('Remove this cactus from your nursery?')) {
      COLLECTION.remove(instanceId);
      this.closeModal('modal-inspect');
      this.renderNursery();
    }
  },

  // ========== SHOP ==========

  openShop() {
    const container = document.getElementById('shop-items');
    const items = getShopItems();

    container.innerHTML = items.map(item => {
      const owned = this.state.collection.some(c => c.speciesId === item.species);
      const affordable = this.state.coins >= item.cost;

      return `
        <div class="shop-item">
          <div class="info">
            <div class="name">${item.speciesData.emoji} ${item.speciesData.name}</div>
            <div class="species">${item.speciesData.species} · ${item.speciesData.rarity}</div>
            <div class="species">Difficulty: ${'★'.repeat(item.speciesData.difficulty)}</div>
          </div>
          <div class="price">💰 ${item.cost === 0 ? 'FREE' : item.cost}</div>
          <button onclick="G.buyItem('${item.species}')" 
                  ${owned || (!affordable && item.cost > 0) ? 'disabled' : ''}
                  ${owned ? 'style="opacity:0.5"' : ''}>
            ${owned ? '✅ Owned' : '🌱 Buy'}
          </button>
        </div>
      `;
    }).join('');

    document.getElementById('modal-shop').classList.add('show');
  },

  buyItem(speciesId) {
    const item = SHOP_ITEMS.find(i => i.species === speciesId);
    if (!item) return;
    if (this.state.collection.some(c => c.speciesId === speciesId)) return;
    if (this.state.coins < item.cost) {
      alert('Not enough coins!');
      return;
    }

    this.state.coins -= item.cost;
    const cactus = COLLECTION.add(speciesId, { stage: 'seedling', growth: 5 });
    if (cactus) {
      this.closeModal('modal-shop');
      this.renderNursery();
    }
  },

  // Grafting is a persistent state machine in bench.js.
  initBench() { BENCH.init(); },

  nextDay() {
    this.state.day++;
    this.state.coins += Math.min(12, this.state.collection.filter(c => c.health >= 50).length); // Passive income

    COLLECTION.dailyTick();
    EVENT_ENGINE.checkEvents();
    BREED.dailyTick();
    BREED.tickChambers();

    this.renderNursery();
    this.renderEvents();
    document.getElementById('day-counter').textContent = `Day ${this.state.day}`;
    document.getElementById('coin-counter').textContent = `💰 ${this.state.coins}`;

    // Auto-save reminder every 7 days
    if (this.state.day % 7 === 0) {
      this.logEvent('info', '💾', `Day ${this.state.day}. A week of growing. Export a code for a portable backup.`);
    }

    // Birthday event
    if (this.state.day % 30 === 0) {
      this.state.coins += 25;
      this.logEvent('good', '🎂', `Month ${Math.floor(this.state.day/30)}! Bonus coins!`);
    }
  },

  // ========== EVENTS LOG ==========

  logEvent(type, icon, text) {
    if (!this.state.lastEvents) this.state.lastEvents = [];
    const flavors = {
      'good': ['', '✨ ', '🌟 ', '💫 ', '⭐ ', '🎉 '],
      'bad': ['', '⚠️ ', '❗ ', '😬 '],
      'info': ['', '📌 ', '💡 ', '🔔 ']
    };
    const flairs = flavors[type] || [''];
    const flair = flairs[Math.floor(Math.random() * flairs.length)];
    this.state.lastEvents.push({ type, text: `${flair}${icon} ${text}`, day: this.state.day });

    // Limit log to 50 entries
    if (this.state.lastEvents.length > 50) {
      this.state.lastEvents = this.state.lastEvents.slice(-50);
    }
  },

  // Dopamine floating text
  floatingText(text, parentEl) {
    const el = document.createElement('div');
    el.className = 'floating-text';
    el.textContent = text;
    el.style.left = Math.random() * 60 + 20 + '%';
    el.style.top = '40%';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1300);
  },

  // Give starter seed pack to new players
  giveStarterSeeds() {
    if (!this.state.seeds) this.state.seeds = [];
    const starterSeeds = [
      { name: 'San Pedro Seeds', parentA: 'trichocereus-pachanoi', parentB: 'trichocereus-pachanoi', count: 5, quality: 85, germination: 'Surface sow on sterile gritty mix. Keep at 22-28°C. Germination 1-3 weeks.' },
      { name: 'Peruvian Torch Seeds', parentA: 'trichocereus-peruvianus', parentB: 'trichocereus-peruvianus', count: 3, quality: 80, germination: 'Surface sow on sterile gritty mix. Keep at 22-28°C. Germination 1-3 weeks.' },
      { name: 'Bridgesii Seeds', parentA: 'trichocereus-bridgesii', parentB: 'trichocereus-bridgesii', count: 3, quality: 80, germination: 'Surface sow on sterile gritty mix. Keep at 20-26°C. Germination 1-4 weeks.' },
      { name: 'Pachanoi Seeds', parentA: 'trichocereus-pachanoi', parentB: 'trichocereus-pachanoi', count: 2, quality: 85, germination: 'Surface sow on sterile gritty mix. Keep at 22-28°C. Germination 1-3 weeks.' },
      { name: 'TBM Seeds (Monstrose)', parentA: 'trichocereus-bridgesii', parentB: 'trichocereus-bridgesii', count: 2, quality: 70, germination: 'Monstrose variation. Surface sow, keep at 22-26°C. Lower germination rate.' }
    ];
    starterSeeds.forEach(s => {
      this.state.seeds.push({
        id: Date.now() + Math.floor(Math.random() * 10000),
        name: s.name,
        parentA: s.parentA,
        parentB: s.parentB,
        count: s.count,
        quality: s.quality,
        germination: s.germination,
        harvested: this.state.day
      });
    });
    this.state.claimedStarter = true;
  },

  // Claim starter seed pack button (for players who missed initial allocation)
  claimStarterPack() {
    if (this.state.claimedStarter) {
      alert('You already claimed your free starter pack!');
      return;
    }
    this.giveStarterSeeds();
    this.logEvent('good', '🌰', 'Claimed Free Starter Seed Pack! Start breeding today!');
    BREED.renderSeedInventory();
    BREED.renderSowSelect();
    document.getElementById('starter-pack-btn').style.display = 'none';
  },

  // Init seeds tab
  initSeeds() {
    if (!this.state) { return; }
    BREED.init();
    // Show/hide starter pack button based on claim status
    const btn = document.getElementById('starter-pack-btn');
    if (btn) {
      btn.style.display = this.state.claimedStarter ? 'none' : 'block';
    }
  },

  // Init market tab
  initMarket() {
    if (!this.state) { return; }
    MARKET.init();
  },

  renderEvents() {
    EVENT_ENGINE.renderLog();
  },

  // ========== MODALS ==========

  closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
  },

  // Close modal when clicking backdrop
  setupModalClicks() {
    document.querySelectorAll('.modal').forEach(m => {
      m.onclick = (e) => {
        if (e.target === m) m.classList.remove('show');
      };
    });
  },

  // ========== REFRESH ALL ==========

  refreshAll() {
    this.renderNursery();
    this.renderEvents();
    if (document.querySelector('#soil-sliders input')) {
      if (this.state.currentMix) this.loadMixToSliders(this.state.currentMix);
    }
    // Add next day button to game header
    const status = document.querySelector('.game-status');
    if (!document.getElementById('next-day-btn')) {
      const btn = document.createElement('button');
      btn.id = 'next-day-btn';
      btn.className = 'btn-primary';
      btn.textContent = '🌅 Next Day';
      btn.onclick = () => G.nextDay();
      btn.style.fontSize = '13px';
      btn.style.padding = '6px 12px';
      status.appendChild(btn);
    }
  }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Title screen visible by default
});
