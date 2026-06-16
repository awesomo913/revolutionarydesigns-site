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
      marketInv: {}
    };
  },

  // ========== GAME FLOW ==========

  // Start new game
  newGame() {
    this.state = this.defaultState();
    this.initialized = true;

    // Give starter cactus
    COLLECTION.add('trichocereus-pachanoi', { stage: 'juvenile', growth: 50, value: 15, water: 10, health: 80 });

    // Give starter coins
    this.state.coins = 10;

    this.logEvent('good', '🌵', 'Welcome to Gritty Mix! Your San Pedro cutting has arrived.');
    this.logEvent('info', '🧪', 'Visit the Lab to mix your first soil.');
    this.logEvent('info', '💾', 'Use Save to get your save code. Write it down!');

    this.showScreen('screen-game');
    this.switchTab('lab');
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
    this.initialized = true;
    this.logEvent('info', '📂', 'Game loaded from save code.');
    this.showScreen('screen-game');
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
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');

    if (tabId === 'nursery') this.renderNursery();
    if (tabId === 'lab') this.initSoilIfNeeded();
    if (tabId === 'events') this.renderEvents();
    if (tabId === 'bench') this.initBench();
    if (tabId === 'seeds') this.initSeeds();
    if (tabId === 'market') this.initMarket();
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

  // ========== GRAFTING BENCH — Step-by-Step Tutorial ==========

  benchStep: 0,
  benchRootstock: null,
  benchScion: null,
  benchCut: false,
  benchAligned: false,
  benchWrapped: false,
  benchHealed: false,
  benchAlignPct: 50,

  initBench() {
    this.benchStep = 0;
    this.benchRootstock = null;
    this.benchScion = null;
    this.benchCut = false;
    this.benchAligned = false;
    this.benchWrapped = false;
    this.benchHealed = false;

    const rootstockSelect = document.getElementById('rootstock-select');
    const scionSelect = document.getElementById('scion-select');

    rootstockSelect.innerHTML = '<option value="">— Choose rootstock —</option>' +
      ROOTSTOCKS.map(r => `<option value="${r.id}">${r.name} — ${r.desc}</option>`).join('');

    scionSelect.innerHTML = '<option value="">— Choose scion from nursery —</option>' +
      this.state.collection.map(c => {
        const s = getSpecies(c.speciesId);
        return s ? `<option value="${c.instanceId}">${s.name} (${c.stage}, ${Math.round(c.growth)}cm)</option>` : '';
      }).join('');

    // Reset UI
    document.getElementById('bench-step1').style.display = 'block';
    document.getElementById('bench-step2').style.display = 'none';
    document.getElementById('bench-step3').style.display = 'none';
    document.getElementById('bench-step4').style.display = 'none';
    document.getElementById('bench-step5').style.display = 'none';
    document.getElementById('bench-result').innerHTML = '';
    document.getElementById('bench-result').className = '';
    document.getElementById('bench-stage-label').textContent = '📋 Select your rootstock and scion to begin';

    // Reset step indicators
    document.querySelectorAll('.bench-step').forEach(s => {
      s.classList.remove('active', 'done');
      if (s.dataset.step === '1') s.classList.add('active');
    });

    this.benchDraw();
  },

  benchConfirmSelection() {
    const rootstockId = document.getElementById('rootstock-select').value;
    const scionId = document.getElementById('scion-select').value;

    if (!rootstockId || !scionId) {
      document.getElementById('bench-result').className = 'fail';
      document.getElementById('bench-result').innerHTML = 'Select both a rootstock and a scion cactus.';
      return;
    }

    this.benchRootstock = ROOTSTOCKS.find(r => r.id === rootstockId);
    this.benchScion = COLLECTION.get(parseInt(scionId));

    if (!this.benchRootstock || !this.benchScion) {
      document.getElementById('bench-result').className = 'fail';
      document.getElementById('bench-result').innerHTML = 'Invalid selection.';
      return;
    }

    this.benchStep = 1;
    document.getElementById('bench-step1').style.display = 'none';
    document.getElementById('bench-step2').style.display = 'block';
    document.getElementById('bench-stage-label').textContent = '✂️ Step 2: Make a clean flat cut across the rootstock top';
    document.getElementById('bench-result').innerHTML = '';

    // Update steps
    this.benchUpdateSteps(2);
    this.benchDraw();
  },

  benchMakeCut() {
    this.benchCut = true;
    this.benchStep = 2;
    document.getElementById('bench-step2').style.display = 'none';
    document.getElementById('bench-step3').style.display = 'block';
    document.getElementById('bench-stage-label').textContent = '🎯 Step 3: Align the vascular rings — drag the slider';
    document.getElementById('align-slider').value = 50;
    this.benchAlignPct = 50;
    document.getElementById('align-status').textContent = '⚠️ Not aligned';
    document.getElementById('align-status').style.color = 'var(--red)';
    document.getElementById('btn-confirm-align').disabled = true;

    this.benchUpdateSteps(3);
    this.benchDraw();

    this.logEvent('info', '✂️', `Clean cut made on ${this.benchRootstock.name} rootstock.`);
  },

  benchCheckAlign() {
    const val = parseInt(document.getElementById('align-slider').value);
    this.benchAlignPct = val;

    const distFromCenter = Math.abs(val - 50);
    // Generous alignment zone: slider values 35-65 (was 42-58)
    const isAligned = distFromCenter <= 15;

    const status = document.getElementById('align-status');
    const btn = document.getElementById('btn-confirm-align');

    if (isAligned) {
      status.textContent = '✅ Rings aligned! Lock it in.';
      status.style.color = '#4ade80';
      btn.disabled = false;
    } else if (distFromCenter <= 25) {
      status.textContent = '🔄 Close — keep going!';
      status.style.color = '#f59e0b';
      btn.disabled = true;
    } else {
      status.textContent = '⚠️ Adjust the slider toward the center';
      status.style.color = '#ef4444';
      btn.disabled = true;
    }

    this.benchDraw();
  },

  benchConfirmAlign() {
    if (Math.abs(this.benchAlignPct - 50) > 15) return;

    this.benchAligned = true;
    this.benchStep = 3;
    document.getElementById('bench-step3').style.display = 'none';
    document.getElementById('bench-step4').style.display = 'block';
    document.getElementById('bench-stage-label').textContent = '🔄 Step 4: Wrap and secure the graft';
    document.getElementById('bench-result').className = '';

    this.benchUpdateSteps(4);
    this.benchDraw();

    this.logEvent('good', '🎯', `Vascular rings aligned for ${getSpecies(this.benchScion.speciesId)?.name} graft.`);
  },

  benchWrap(method) {
    this.benchWrapped = true;
    this.benchStep = 4;
    document.getElementById('bench-step4').style.display = 'none';
    document.getElementById('bench-step5').style.display = 'block';
    document.getElementById('bench-stage-label').textContent = '⏳ Step 5: Let it heal — click to advance time';

    const methodNames = { bands: 'grafting bands', parafilm: 'parafilm wrap', stocking: 'pantyhose' };
    document.getElementById('bench-result').innerHTML = `🔄 Graft secured with ${methodNames[method] || 'bands'}. Now it needs time to heal.`;
    document.getElementById('bench-result').className = 'success';

    this.benchUpdateSteps(5);
    this.benchDraw();

    this.logEvent('good', '🔄', `Graft wrapped with ${methodNames[method] || 'bands'}.`);
  },

  benchHeal() {
    if (this.benchHealed) return;

    document.getElementById('heal-progress-wrap').style.display = 'block';
    const bar = document.getElementById('heal-bar');
    const status = document.getElementById('heal-status');
    bar.style.width = '0%';

    let pct = 0;
    const interval = setInterval(() => {
      pct += 2;
      bar.style.width = pct + '%';
      if (pct < 25) status.textContent = '🔬 Callus tissue forming at the graft union...';
      else if (pct < 50) status.textContent = '🌱 Vascular tissue beginning to connect...';
      else if (pct < 75) status.textContent = '💧 Water and nutrients flowing between stock and scion...';
      else if (pct < 100) status.textContent = '✅ Union strengthening — almost there!';
      else {
        clearInterval(interval);
        this.benchHealed = true;
        this.benchCompleteGraft();
        status.textContent = '✅ Graft healed! Scion is growing on the rootstock.';
      }
    }, 80);
  },

  benchCompleteGraft() {
    const scion = this.benchScion;
    const rootstock = this.benchRootstock;
    const species = getSpecies(scion.speciesId);

    scion.grafted = true;
    scion.rootstock = rootstock.id;
    scion.growth = Math.round(scion.growth * 1.5);
    scion.value = Math.round(scion.value * 2);
    scion.health = Math.min(100, scion.health + 20);

    document.getElementById('bench-stage-label').textContent = '✅ Graft successful!';
    document.getElementById('bench-result').className = 'success';
    document.getElementById('bench-result').innerHTML = `🌵 <strong>Graft successful!</strong> ${species?.name} on ${rootstock.name}.<br>Growth accelerated 1.5x! Value increased to 💰${scion.value}.<br><small>Tip: Remove any pups that appear below the graft.</small>`;
    document.getElementById('heal-status').textContent = '';

    this.benchDraw('healed');
    this.logEvent('good', '🌵', `Graft healed: ${species?.name} on ${rootstock.name}!`);
    this.renderNursery();
  },

  benchUpdateSteps(activeStep) {
    document.querySelectorAll('.bench-step').forEach(s => {
      const step = parseInt(s.dataset.step);
      s.classList.remove('active', 'done');
      if (step < activeStep) s.classList.add('done');
      else if (step === activeStep) s.classList.add('active');
    });
  },

  benchDraw(state) {
    const canvas = document.getElementById('bench-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = 360, H = 240;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, W, H);

    const rootstock = this.benchRootstock;
    const scion = this.benchScion;

    if (!rootstock || !scion) {
      ctx.fillStyle = '#888';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Select rootstock and scion to see the bench', 180, 120);
      return;
    }

    // === ROOTSTOCK (left side) ===
    const rsX = 80;
    const potTop = 190;
    const isPeres = rootstock.id === 'pereskiopsis';
    const rsW = isPeres ? 18 : rootstock.id === 'hylocereus' ? 22 : 32;
    const rsH = isPeres ? 90 : 100;
    const rsY = potTop - rsH;

    // Pot
    ctx.fillStyle = '#5c4033';
    ctx.fillRect(rsX - 20, potTop - 5, rsW + 40, 30);
    ctx.fillStyle = '#4a3328';
    ctx.fillRect(rsX - 25, potTop - 12, rsW + 50, 12);
    ctx.fillStyle = '#3a2a1a';
    ctx.fillRect(rsX - 15, potTop - 12, rsW + 30, 8);

    // Rootstock stem (uncut or cut)
    if (this.benchCut || state === 'healed') {
      // Cut top
      const cutY = rsY;
      ctx.fillStyle = '#6dc98a';
      ctx.fillRect(rsX, cutY, rsW, rsH);

      // Cut surface
      ctx.fillStyle = '#d4e8d0';
      ctx.beginPath();
      ctx.ellipse(rsX + rsW/2, cutY, rsW/2, 4, 0, 0, Math.PI * 2);
      ctx.fill();

      // Cut line
      ctx.strokeStyle = '#ff4444';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 2]);
      ctx.beginPath();
      ctx.moveTo(rsX - 30, cutY);
      ctx.lineTo(rsX + rsW + 30, cutY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#ff4444';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('✂️ Cut', rsX + rsW/2 + 40, cutY - 2);
    } else {
      // Uncut - full height
      ctx.fillStyle = '#5cb87a';
      ctx.fillRect(rsX, rsY - 20, rsW, rsH + 20);
    }

    // Rootstock label
    ctx.fillStyle = '#888';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    const rsNames = { pereskiopsis: 'Pereskiopsis', trichocereus: 'T. pachanoi', myrtillocactus: 'Myrtillocactus', hylocereus: 'Hylocereus' };
    ctx.fillText(rsNames[rootstock.id] || 'Rootstock', rsX + rsW/2, 225);

    // === SCION (above rootstock, position varies with alignment) ===
    const species = getSpecies(scion.speciesId);
    const rsRingX = rsX + rsW/2;
    const alignOffset = (this.benchAlignPct - 50) / 50 * 20; // -20 to +20 pixels
    const scionBaseX = rsRingX + alignOffset;

    // Scion drawn above the rootstock (moved down after cut)
    let scionY = 35;
    if (this.benchCut) scionY = rsY - 50 - 5;

    ctx.fillStyle = '#6dc98a';
    if (scion.stage === 'seedling') {
      ctx.fillRect(scionBaseX - 8, scionY, 16, 45);
      ctx.fillStyle = '#8ade80';
      ctx.beginPath();
      ctx.arc(scionBaseX, scionY - 6, 10, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillRect(scionBaseX - 14, scionY, 28, 55);
    }

    // Scion label
    ctx.fillStyle = '#888';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(species ? species.name : 'Scion', scionBaseX, 225);
    ctx.fillStyle = '#666';
    ctx.font = '8px sans-serif';
    ctx.fillText(Math.round(scion.growth) + 'cm', scionBaseX, 218);

    // === VASCULAR RINGS ===
    if (this.benchCut) {
      // Rootstock ring at cut
      const rsRingY = rsY;
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(rsRingX, rsRingY, rsW/2 - 2, 4, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = 'rgba(245,158,11,0.12)';
      ctx.fill();

      // Rootstock ring label
      ctx.fillStyle = '#f59e0b';
      ctx.font = '8px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Vascular ring', rsRingX, rsRingY - 6);

      // Scion ring at bottom
      const scRingY = scionY + (scion.stage === 'seedling' ? 45 : 55);
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.setLineDash([3, 2]);
      ctx.beginPath();
      ctx.ellipse(scionBaseX, scRingY, rsW/2 - 2, 3, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(245,158,11,0.12)';
      ctx.fill();

      // Alignment indicator
      const ringDist = Math.abs(scionBaseX - rsRingX);
      const isInAlignStep = !this.benchAligned && this.benchStep >= 2 && this.benchStep < 4;
      
      if (this.benchAligned || state === 'healed' || isInAlignStep) {
        const aligned = ringDist < 20;
        
        // Draw alignment zone indicator (green/red ring around the connection)
        if (isInAlignStep) {
          ctx.strokeStyle = 'rgba(74,222,128,0.15)';
          ctx.lineWidth = 12;
          ctx.beginPath();
          ctx.arc(rsRingX, rsRingY, 20, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.strokeStyle = aligned ? '#4ade80' : '#ef4444';
        ctx.lineWidth = 2;
        ctx.setLineDash(aligned || this.benchAligned ? [] : [4, 3]);
        ctx.beginPath();
        ctx.moveTo(scionBaseX, scRingY);
        ctx.lineTo(rsRingX, rsRingY);
        ctx.stroke();
        ctx.setLineDash([]);

        if (aligned && this.benchAligned) {
          ctx.fillStyle = '#4ade80';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('✅ Rings connected', 180, rsRingY + 15);
        }
      }
    }

    // === WRAPPING visual ===
    if (this.benchWrapped || state === 'healed') {
      const bandY = rsY;
      ctx.strokeStyle = '#ccc';
      ctx.lineWidth = 2;
      // Wrapping bands
      for (let i = 0; i < 3; i++) {
        const by = bandY + i * 8;
        ctx.strokeRect(rsX - 5, by, rsW + 10, 4);
      }
      ctx.fillStyle = '#ccc';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('🔄 Bands', rsX + rsW/2, bandY + 30);
    }

    // === HEALING visual ===
    if (state === 'healed') {
      // Healed union
      ctx.fillStyle = 'rgba(74,222,128,0.2)';
      ctx.fillRect(rsX - 2, rsY - 5, rsW + 4, 10);
      ctx.strokeStyle = '#4ade80';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(rsX + rsW/2, rsY, rsW/2, 6, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = '#4ade80';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('✅ Healed union', rsX + rsW/2, rsY + 20);
    }

    // === ARROW between rootstock and scion ===
    ctx.fillStyle = '#4ade80';
    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('→', 165, 110);
  },

  // ========== DAY CYCLE ==========

  nextDay() {
    // Day transition animation
    const overlay = document.createElement('div');
    overlay.className = 'day-overlay';
    overlay.innerHTML = `<div class="text">🌅 Day ${this.state.day + 1}</div>`;
    document.body.appendChild(overlay);
    setTimeout(() => overlay.remove(), 1900);

    this.state.day++;
    this.state.coins += Math.floor(this.state.collection.length * 0.5); // Passive income

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

  // Init seeds tab
  initSeeds() {
    BREED.init();
  },

  // Init market tab
  initMarket() {
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
      m.addEventListener('click', (e) => {
        if (e.target === m) m.classList.remove('show');
      });
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
