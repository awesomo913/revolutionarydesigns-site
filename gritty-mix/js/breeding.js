// Gritty Mix — Breeding & Seedling System
// Cross-pollinate cacti, harvest seeds, germinate in takeaway chambers

const BREED = {
  activeFruit: null, // {parentA, parentB, progress, maxDays}

  // Initialize breeding UI
  init() {
    this.renderBreedSelects();
    this.renderSeedInventory();
    this.renderGermChambers();
    this.renderSowSelect();
  },

  // Populate parent selects with blooming cacti
  renderBreedSelects() {
    const a = document.getElementById('breed-parent-a');
    const b = document.getElementById('breed-parent-b');
    const bloomers = G.state.collection.filter(c => c.stage === 'blooming' || c.stage === 'mature');

    const opts = bloomers.map(c => {
      const s = getSpecies(c.speciesId);
      const name = s ? s.name : 'Unknown';
      return `<option value="${c.instanceId}">${s?.emoji || '🌵'} ${name} (${Math.round(c.growth)}cm·💰${c.value})</option>`;
    }).join('');

    const empty = '<option value="">— No blooming cacti —</option>';
    a.innerHTML = bloomers.length ? '<option value="">— Select parent —</option>' + opts : empty;
    b.innerHTML = bloomers.length ? '<option value="">— Select parent —</option>' + opts : empty;
  },

  // Pollinate two cacti
  pollinate() {
    const idA = parseInt(document.getElementById('breed-parent-a').value);
    const idB = parseInt(document.getElementById('breed-parent-b').value);
    const result = document.getElementById('breed-result');

    if (!idA || !idB) {
      result.innerHTML = '⚠️ Select two blooming cacti to cross-pollinate.';
      return;
    }
    if (idA === idB) {
      result.innerHTML = '⚠️ Select two different cacti. Self-pollination rarely works.';
      return;
    }

    const parentA = COLLECTION.get(idA);
    const parentB = COLLECTION.get(idB);
    if (!parentA || !parentB) {
      result.innerHTML = '⚠️ Invalid selection.';
      return;
    }

    const sA = getSpecies(parentA.speciesId);
    const sB = getSpecies(parentB.speciesId);

    result.innerHTML = `🌸 Pollinated! ${sA?.name || '?'} × ${sB?.name || '?'} — fruit is developing...`;
    result.style.color = 'var(--green)';

    // Start fruit ripening
    this.activeFruit = {
      parentA: parentA.speciesId,
      parentB: parentB.speciesId,
      progress: 0,
      maxDays: 30 + Math.floor(Math.random() * 30)
    };

    document.getElementById('fruit-progress').style.display = 'block';
    document.getElementById('seed-harvest').style.display = 'none';
    this.updateFruitProgress();
    G.logEvent('good', '🌸', `Cross-pollinated ${sA?.name} × ${sB?.name}! Fruit growing...`);
    G.floatingText('🌸 Cross-pollinated!', document.getElementById('breed-section'));
  },

  // Called each day tick
  dailyTick() {
    if (!this.activeFruit) return;
    this.activeFruit.progress++;
    this.updateFruitProgress();
  },

  updateFruitProgress() {
    const pct = Math.min(100, Math.round((this.activeFruit.progress / this.activeFruit.maxDays) * 100));
    document.getElementById('fruit-bar').style.width = pct + '%';

    let status = '';
    if (pct < 20) status = '🌸 Flower wilting, ovary swelling...';
    else if (pct < 40) status = '🍏 Green fruit growing...';
    else if (pct < 60) status = '🍎 Fruit getting plumper...';
    else if (pct < 80) status = '🍊 Fruit changing color...';
    else if (pct < 100) status = '🍓 Almost ripe! A few more days...';
    else {
      status = '🍓 Fruit is ripe! Harvest your seeds!';
      document.getElementById('seed-harvest').style.display = 'block';
      document.getElementById('btn-pollinate').disabled = true;
    }
    document.getElementById('fruit-status').textContent = status;
  },

  // Harvest seeds from ripe fruit
  harvest() {
    if (!this.activeFruit) return;
    const sA = getSpecies(this.activeFruit.parentA);
    const sB = getSpecies(this.activeFruit.parentB);

    // Generate seeds - quantity based on parents
    const count = 5 + Math.floor(Math.random() * 15);
    const hybridName = `${sA?.name || '?'} × ${sB?.name || '?'}`;

    const seed = {
      id: Date.now(),
      name: hybridName,
      parentA: this.activeFruit.parentA,
      parentB: this.activeFruit.parentB,
      count: count,
      quality: 50 + Math.floor(Math.random() * 40),
      harvested: G.state.day
    };

    if (!G.state.seeds) G.state.seeds = [];
    G.state.seeds.push(seed);

    document.getElementById('seed-harvest').style.display = 'none';
    document.getElementById('fruit-progress').style.display = 'none';
    document.getElementById('btn-pollinate').disabled = false;
    document.getElementById('breed-result').innerHTML = `🍓 Harvested ${count} seeds from ${hybridName}! 🌰`;
    document.getElementById('breed-result').style.color = 'var(--green)';

    this.activeFruit = null;
    this.renderSeedInventory();
    this.renderSowSelect();
    G.logEvent('good', '🍓', `Harvested ${count} seeds from ${hybridName}!`);
    G.floatingText('🍓 ' + count + ' seeds!', document.getElementById('seed-inv-section'));
  },

  // Render seed inventory
  renderSeedInventory() {
    const inv = document.getElementById('seed-inventory');
    const seeds = G.state.seeds || [];

    if (seeds.length === 0) {
      inv.innerHTML = '<p style="color:var(--muted);font-size:13px">No seeds yet. Cross-pollinate blooming cacti to get some.</p>';
      return;
    }

    inv.innerHTML = seeds.map(s => `
      <div class="seed-entry">
        <span class="seed-icon">🌰</span>
        <span class="seed-name">${s.name}</span>
        <span class="seed-count">×${s.count}</span>
        <span class="seed-quality" style="color:${s.quality > 70 ? 'var(--green)' : s.quality > 40 ? 'var(--orange)' : 'var(--red)'}">
          ${s.quality}%
        </span>
      </div>
    `).join('');
  },

  // Render sow select dropdown
  renderSowSelect() {
    const sel = document.getElementById('sow-select');
    const seeds = G.state.seeds || [];
    if (seeds.length === 0) {
      sel.innerHTML = '<option value="">— No seeds available —</option>';
      return;
    }
    sel.innerHTML = '<option value="">— Select seed —</option>' +
      seeds.map((s, i) => `<option value="${i}">🌰 ${s.name} (×${s.count})</option>`).join('');
  },

  // Sow seeds in germination chamber
  sow() {
    const idx = parseInt(document.getElementById('sow-select').value);
    const seeds = G.state.seeds || [];

    if (isNaN(idx) || !seeds[idx]) {
      document.getElementById('breed-result').innerHTML = '⚠️ Select seeds to sow.';
      document.getElementById('breed-result').style.color = 'var(--red)';
      return;
    }

    const seed = seeds[idx];
    if (seed.count < 5) {
      document.getElementById('breed-result').innerHTML = '⚠️ Need at least 5 seeds to sow.';
      return;
    }

    // Create a germination chamber
    const chamber = {
      id: Date.now(),
      seedName: seed.name,
      parentA: seed.parentA,
      parentB: seed.parentB,
      seedsUsed: 5,
      day: 0,
      maxDays: 7 + Math.floor(Math.random() * 7),
      stage: 'sown', // sown -> germinating -> seedling -> ready
      quality: seed.quality
    };

    if (!G.state.chambers) G.state.chambers = [];
    G.state.chambers.push(chamber);

    seed.count -= 5;
    if (seed.count <= 0) {
      G.state.seeds.splice(idx, 1);
    }

    this.renderSeedInventory();
    this.renderSowSelect();
    this.renderGermChambers();
    G.logEvent('good', '🌱', `Sowed ${chamber.seedName} seeds in germination chamber!`);
    G.floatingText('🌱 Seeds sown!', document.getElementById('germ-section'));
  },

  // Tick germination chambers
  tickChambers() {
    const chambers = G.state.chambers || [];
    chambers.forEach(ch => {
      if (ch.stage === 'ready') return;
      ch.day++;

      if (ch.day >= ch.maxDays && ch.stage === 'sown') {
        ch.stage = 'germinating';
        G.logEvent('good', '🌱', `Germination! ${ch.seedName} seeds are sprouting!`);
      } else if (ch.day >= ch.maxDays + 10 && ch.stage === 'germinating') {
        ch.stage = 'seedling';
        G.logEvent('good', '🌿', `${ch.seedName} seedlings are growing!`);
      } else if (ch.day >= ch.maxDays + 25 && ch.stage === 'seedling') {
        ch.stage = 'ready';
        G.logEvent('good', '🌿', `${ch.seedName} seedlings ready to pot up!`);
        G.floatingText('🌿 Ready to pot!', document.getElementById('germ-section'));
      }
    });
    this.renderGermChambers();
  },

  // Pot up a ready chamber into individual cacti
  potUp(chamberId) {
    const chambers = G.state.chambers || [];
    const idx = chambers.findIndex(c => c.id === chamberId);
    if (idx === -1) return;

    const ch = chambers[idx];
    if (ch.stage !== 'ready') return;

    // Create new cactus from the seedlings
    // Pick one of the parent species (or hybrid)
    const parentSpecies = Math.random() < 0.5 ? ch.parentA : ch.parentB;
    const seedlings = 3 + Math.floor(Math.random() * 5);

    for (let i = 0; i < seedlings; i++) {
      const variation = Math.floor(Math.random() * 10) - 5; // -5 to +5
      COLLECTION.add(parentSpecies, {
        stage: 'seedling',
        growth: Math.max(1, 2 + variation),
        health: 40 + Math.floor(Math.random() * 20),
        value: 5 + Math.floor(Math.random() * 10)
      });
    }

    G.state.chambers.splice(idx, 1);
    this.renderGermChambers();
    G.logEvent('good', '🪴', `Potted up ${seedlings} seedlings from ${ch.seedName}!`);
    G.floatingText('🪴 ' + seedlings + ' potted!', document.getElementById('nursery-grid'));
  },

  // Render germination chambers
  renderGermChambers() {
    const container = document.getElementById('germ-chambers');
    const chambers = G.state.chambers || [];

    if (chambers.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);font-size:13px">No active germination chambers.</p>';
      return;
    }

    container.innerHTML = chambers.map(ch => {
      const pct = Math.min(100, Math.round((ch.day / (ch.maxDays + 25)) * 100));
      const stageEmoji = ch.stage === 'sown' ? '🌰' : ch.stage === 'germinating' ? '🌱' : ch.stage === 'seedling' ? '🌿' : '🪴';
      const stageName = ch.stage === 'sown' ? 'Sown' : ch.stage === 'germinating' ? 'Germinating' : ch.stage === 'seedling' ? 'Growing' : 'Ready!';

      return `
        <div class="germ-chamber">
          <div class="germ-header">
            <span class="germ-icon">${stageEmoji}</span>
            <span class="germ-name">${ch.seedName}</span>
            <span class="germ-stage">${stageName}</span>
          </div>
          <div class="sim-progress"><div class="bar" style="width:${pct}%"></div></div>
          <div class="germ-info">Day ${ch.day} · Quality: ${ch.quality}%</div>
          ${ch.stage === 'ready' ? `<button onclick="BREED.potUp(${ch.id})" class="btn-secondary" style="margin-top:4px">🪴 Pot Up</button>` : ''}
        </div>
      `;
    }).join('');
  }
};
