// Gritty Mix — Soil Lab Engine
// Real soil science mechanics based on our study data

const SOIL = {
  currentMix: null,
  sliders: {},

  // Initialize soil UI
  init() {
    const container = document.getElementById('soil-sliders');
    const pctTotal = 100 / SOIL_COMPONENTS.length;

    SOIL_COMPONENTS.forEach((comp, i) => {
      const row = document.createElement('div');
      row.className = 'soil-row';
      row.innerHTML = `
        <label>${comp.name}</label>
        <input type="range" min="0" max="100" value="${Math.round(pctTotal)}" 
               data-component="${comp.id}" oninput="SOIL.updateSlider('${comp.id}')">
        <span class="pct" id="pct-${comp.id}">${Math.round(pctTotal)}%</span>
      `;
      container.appendChild(row);
      SOIL.sliders[comp.id] = Math.round(pctTotal);
    });

    this.updateStats();
  },

  // Called when a slider moves
  updateSlider(id) {
    const input = document.querySelector(`input[data-component="${id}"]`);
    const val = parseInt(input.value);
    SOIL.sliders[id] = val;
    document.getElementById(`pct-${id}`).textContent = val + '%';
    this.normalize(id);
    this.updateStats();
  },

  // Normalize all sliders to sum to 100%
  normalize(changedId) {
    const values = SOIL_COMPONENTS.map(c => SOIL.sliders[c.id] || 0);
    const total = values.reduce((a, b) => a + b, 0);
    if (total === 0) return;

    // Calculate what the changed slider's value SHOULD be
    // if we're rebalancing around it
    if (total !== 100) {
      const fixed = SOIL.sliders[changedId];
      const otherIds = SOIL_COMPONENTS.map(c => c.id).filter(id => id !== changedId);
      const otherTotal = total - fixed;
      const remaining = 100 - fixed;

      if (otherTotal > 0 && otherIds.length > 0) {
        // Scale other values proportionally
        otherIds.forEach(id => {
          const newVal = Math.round((SOIL.sliders[id] / otherTotal) * remaining);
          SOIL.sliders[id] = Math.max(0, Math.min(100, newVal));
          const input = document.querySelector(`input[data-component="${id}"]`);
          if (input) input.value = SOIL.sliders[id];
          document.getElementById(`pct-${id}`).textContent = SOIL.sliders[id] + '%';
        });
      }
    }
  },

  // Calculate soil stats from current mix
  updateStats() {
    let drainage = 0, aeration = 0, waterRet = 0, organic = 0;
    let totalPct = 0;

    SOIL_COMPONENTS.forEach(comp => {
      const pct = SOIL.sliders[comp.id] || 0;
      if (pct > 0) {
        const factor = pct / 100;
        drainage += comp.drainage * factor;
        aeration += comp.aeration * factor;
        waterRet += comp.waterRet * factor;
        organic += comp.organic * factor;
        totalPct += pct;
      }
    });

    if (totalPct > 0) {
      const factor = 100 / totalPct;
      drainage = Math.round(drainage * factor);
      aeration = Math.round(aeration * factor);
      waterRet = Math.round(waterRet * factor);
      organic = Math.round(organic * factor);
    }

    document.getElementById('stat-drainage').textContent = drainage;
    document.getElementById('stat-aeration').textContent = aeration;
    document.getElementById('stat-water').textContent = waterRet;
    document.getElementById('stat-organic').textContent = organic;

    return { drainage, aeration, waterRetention: waterRet, organic };
  },

  // Apply a preset recipe
  applyPreset(presetName) {
    const preset = SOIL_PRESETS[presetName];
    if (!preset) return;

    // Reset all to 0
    SOIL_COMPONENTS.forEach(comp => {
      SOIL.sliders[comp.id] = 0;
    });

    // Apply preset values
    let total = 0;
    Object.keys(preset).forEach(id => {
      SOIL.sliders[id] = preset[id];
      total += preset[id];
    });

    // Update UI
    SOIL_COMPONENTS.forEach(comp => {
      const input = document.querySelector(`input[data-component="${comp.id}"]`);
      if (input) input.value = SOIL.sliders[comp.id] || 0;
      document.getElementById(`pct-${comp.id}`).textContent = (SOIL.sliders[comp.id] || 0) + '%';
    });

    this.updateStats();

    // Highlight active preset
    document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.btn-preset[data-recipe="${presetName}"]`);
    if (btn) btn.classList.add('active');
  },

  // Save current mix to game state
  saveMix() {
    const mix = {};
    SOIL_COMPONENTS.forEach(comp => {
      const pct = SOIL.sliders[comp.id] || 0;
      if (pct > 0) mix[comp.id] = pct;
    });
    SOIL.currentMix = mix;
    G.state.currentMix = mix;
    G.logEvent('info', '🧪', `Saved soil mix: ${Object.keys(mix).length} components`);
    alert('Soil mix saved!');
  },

  // Check if a mix is good for a given species
  evaluateMix(speciesId, mix) {
    const species = getSpecies(speciesId);
    if (!species || !mix) return { score: 0, feedback: 'No soil mix set!' };

    // Calculate total components
    let total = 0;
    const stats = { drainage: 0, aeration: 0, waterRetention: 0, organic: 0 };
    
    Object.keys(mix).forEach(compId => {
      const comp = SOIL_COMPONENTS.find(c => c.id === compId);
      const pct = mix[compId];
      if (comp && pct > 0) {
        const factor = pct / 100;
        stats.drainage += comp.drainage * factor;
        stats.aeration += comp.aeration * factor;
        stats.waterRetention += comp.waterRet * factor;
        stats.organic += comp.organic * factor;
        total += pct;
      }
    });

    if (total === 0) return { score: 0, feedback: 'Empty mix!' };

    const scale = 100 / total;
    stats.drainage = Math.round(stats.drainage * scale);
    stats.aeration = Math.round(stats.aeration * scale);
    stats.waterRetention = Math.round(stats.waterRetention * scale);
    stats.organic = Math.round(stats.organic * scale);

    // Score against species preferences
    const pref = species.prefers;
    let score = 100;
    score -= Math.abs(stats.drainage - pref.drainage) * 0.5;
    score -= Math.abs(stats.aeration - pref.aeration) * 0.5;
    score -= Math.abs(stats.waterRetention - pref.waterRetention) * 0.5;
    score -= Math.abs(stats.organic - pref.organic) * 0.5;
    score = Math.max(0, Math.min(100, Math.round(score)));

    let feedback = score >= 80 ? 'Excellent mix!' :
                   score >= 60 ? 'Good mix, could improve.' :
                   score >= 40 ? 'Adequate but not ideal.' :
                                'Poor match. Consider adjusting.';

    return { score, feedback, stats };
  }
};
