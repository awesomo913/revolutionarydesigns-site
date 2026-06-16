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
      nurserySort: 'value'
    };
  },

  // ========== GAME FLOW ==========

  // Start new game
  newGame() {
    this.state = this.defaultState();
    this.initialized = true;

    // Give starter cactus
    COLLECTION.add('trichocereus-pachanoi', { stage: 'juvenile', growth: 50, value: 15 });

    // Give starter coins
    this.state.coins = 10;

    this.logEvent('good', '🌵', 'Welcome to Gritty Mix! Your San Pedro cutting has arrived.');
    this.logEvent('info', '🧪', 'Visit the Lab to mix your first soil.');
    this.logEvent('info', '💾', 'Use Save to get your save code. Write it down!');

    this.showScreen('screen-game');
    this.switchTab('lab');
    this.refreshAll();
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
    this.initialized = true;
    this.logEvent('info', '📂', 'Game loaded from save code.');
    this.showScreen('screen-game');
    this.refreshAll();
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
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');

    if (tabId === 'nursery') this.renderNursery();
    if (tabId === 'lab') this.initSoilIfNeeded();
    if (tabId === 'events') this.renderEvents();
    if (tabId === 'bench') this.initBench();
  },

  // ========== SOIL LAB ==========

  initSoilIfNeeded() {
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
      document.getElementById(`pct-${comp.id}`).textContent = val + '%';
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
        <p>❤️ ${cactus.health}/100 · 💧 ${cactus.water} days since water</p>
      </div>
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
      <div style="display:flex;gap:8px;margin-top:16px">
        <button onclick="G.waterCactus(${cactus.instanceId})" class="btn-secondary">💧 Water</button>
        <button onclick="G.removeCactus(${cactus.instanceId})" class="btn-secondary" style="color:var(--red)">🗑️ Remove</button>
      </div>
    `;

    document.getElementById('modal-inspect').classList.add('show');
  },

  waterCactus(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus) return;
    cactus.water = getSpecies(cactus.speciesId)?.waterFreq || 10;
    cactus.health = Math.min(100, cactus.health + 5);
    this.logEvent('good', '💧', `${getSpecies(cactus.speciesId)?.name || 'Cactus'} watered.`);
    this.closeModal('modal-inspect');
    this.renderNursery();
  },

  removeCactus(instanceId) {
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

  // ========== GRAFTING BENCH ==========

  initBench() {
    const rootstockSelect = document.getElementById('rootstock-select');
    const scionSelect = document.getElementById('scion-select');

    // Rootstocks
    rootstockSelect.innerHTML = '<option value="">— Select —</option>' +
      ROOTSTOCKS.map(r => `<option value="${r.id}">${r.name} — ${r.desc}</option>`).join('');

    // Scions (cacti in collection)
    scionSelect.innerHTML = '<option value="">— Select —</option>' +
      this.state.collection.map(c => {
        const s = getSpecies(c.speciesId);
        return s ? `<option value="${c.instanceId}">${s.name} (${c.stage}, ${Math.round(c.growth)}cm)</option>` : '';
      }).join('');
  },

  performGraft() {
    const rootstockId = document.getElementById('rootstock-select').value;
    const scionId = parseInt(document.getElementById('scion-select').value);
    const result = document.getElementById('graft-result');

    if (!rootstockId || !scionId) {
      result.className = 'fail';
      result.innerHTML = 'Select both a rootstock and a scion cactus.';
      return;
    }

    const rootstock = ROOTSTOCKS.find(r => r.id === rootstockId);
    const scion = COLLECTION.get(scionId);

    if (!rootstock || !scion) {
      result.className = 'fail';
      result.innerHTML = 'Invalid selection.';
      return;
    }

    const species = getSpecies(scion.speciesId);
    if (rootstock.difficulty > 2 && Math.random() < 0.3) {
      result.className = 'fail';
      result.innerHTML = `Graft failed! Vascular rings didn't align. Try a simpler rootstock.`;
      this.logEvent('bad', '🪚', `Graft failed: ${species?.name} onto ${rootstock.name}`);
      return;
    }

    // Success!
    scion.grafted = true;
    scion.rootstock = rootstock.id;
    scion.growth = Math.round(scion.growth * 1.3);
    scion.value = Math.round(scion.value * 1.5);
    scion.health = Math.min(100, scion.health + 15);

    result.className = 'success';
    result.innerHTML = `✅ Graft successful! ${species?.name} on ${rootstock.name}. Growth accelerated!`;
    this.logEvent('good', '🪚', `Grafted ${species?.name} onto ${rootstock.name}!`);

    this.renderNursery();
    this.initBench();
  },

  // ========== DAY CYCLE ==========

  nextDay() {
    this.state.day++;
    this.state.coins += Math.floor(this.state.collection.length * 0.5); // Passive income

    COLLECTION.dailyTick();
    EVENT_ENGINE.checkEvents();

    this.renderNursery();
    this.renderEvents();
    document.getElementById('day-counter').textContent = `Day ${this.state.day}`;
    document.getElementById('coin-counter').textContent = `💰 ${this.state.coins}`;

    // Auto-save reminder every 7 days
    if (this.state.day % 7 === 0) {
      this.logEvent('info', '💾', `Day ${this.state.day}. Remember to save your code!`);
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
    this.state.lastEvents.push({ type, text: `${icon} ${text}`, day: this.state.day });
  },

  renderEvents() {
    EVENT_ENGINE.renderLog();
  },

  // ========== MODALS ==========

  closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
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
