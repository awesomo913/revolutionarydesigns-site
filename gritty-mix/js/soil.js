// Gritty Mix — Soil Lab Engine
// Real soil science mechanics based on our study data

const SOIL = {
  currentMix: null,
  sliders: {},

  // Initialize soil UI
  init() {
    const container = document.getElementById('soil-sliders');
    const pctTotal = 100 / SOIL_COMPONENTS.length;

    // Draw placeholder on canvas
    const canvas = document.getElementById('soil-canvas');
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, 300, 220);
      ctx.fillStyle = '#666';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Adjust sliders to see', 150, 105);
      ctx.fillText('your soil mix', 150, 125);
    }

    SOIL_COMPONENTS.forEach((comp, i) => {
      const row = document.createElement('div');
      row.className = 'soil-row';
      row.innerHTML = `
        <label for="soil-${comp.id}">${comp.name}</label>
        <input id="soil-${comp.id}" type="range" min="0" max="100" value="${Math.round(pctTotal)}"
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
    const others = SOIL_COMPONENTS.map(c => c.id).filter(id => id !== changedId);
    const remaining = 100 - SOIL.sliders[changedId];
    const total = others.reduce((n,id) => n + SOIL.sliders[id], 0);
    const parts = others.map(id => ({ id, raw: total ? SOIL.sliders[id] / total * remaining : remaining / others.length }));
    parts.forEach(p => SOIL.sliders[p.id] = Math.floor(p.raw));
    let extra = remaining - parts.reduce((n,p) => n + Math.floor(p.raw), 0);
    parts.sort((a,b) => (b.raw % 1) - (a.raw % 1));
    for (let i = 0; i < extra; i++) SOIL.sliders[parts[i].id]++;
    others.forEach(id => {
      document.querySelector(`input[data-component="${id}"]`).value = SOIL.sliders[id];
      document.getElementById(`pct-${id}`).textContent = SOIL.sliders[id] + '%';
    });
    document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
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

    this.drawPot(drainage, aeration, waterRet, organic);

    return { drainage, aeration, waterRetention: waterRet, organic };
  },

  // Draw a visual pot cross-section showing soil layers
  drawPot(drainage, aeration, waterRet, organic) {
    const canvas = document.getElementById('soil-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = 600, H = 440;
    canvas.width = W; canvas.height = H;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle='#0c211a'; ctx.fillRect(0,0,W,H);
    const pot=ctx.createLinearGradient(90,0,480,0);
    pot.addColorStop(0,'#84583e');pot.addColorStop(.4,'#bc916a');pot.addColorStop(1,'#765039');
    ctx.fillStyle=pot;ctx.beginPath();ctx.moveTo(93,85);ctx.lineTo(507,85);ctx.lineTo(460,369);ctx.quadraticCurveTo(300,399,140,369);ctx.closePath();ctx.fill();
    ctx.save();ctx.beginPath();ctx.moveTo(112,97);ctx.lineTo(488,97);ctx.lineTo(447,354);ctx.quadraticCurveTo(300,383,153,354);ctx.closePath();ctx.clip();ctx.fillStyle='#3c3a2b';ctx.fillRect(100,90,400,300);
    const colors=['#cdc7ac','#9b6a4b','#e3ded0','#949e91','#987f53','#5f5841','#bb9364','#a8b7a0','#ccbc94','#7a5d41'];
    const total=Object.values(SOIL.sliders).reduce((a,b)=>a+b,0)||1;
    const pool=[]; SOIL_COMPONENTS.forEach((comp,i)=>{for(let n=0;n<Math.round((SOIL.sliders[comp.id]||0)/total*100);n++)pool.push(colors[i]);});
    for(let i=0;i<540;i++){
      const px=104+(i*137.507%390),py=95+(i*47.73%285),size=3+i%7;
      ctx.fillStyle=pool[i%pool.length]||'#989176';ctx.beginPath();ctx.ellipse(px,py,size,size*.65,i,0,Math.PI*2);ctx.fill();
    }
    ctx.restore();
    ctx.strokeStyle='#b3bf8a77';ctx.setLineDash([4,6]);ctx.beginPath();ctx.moveTo(88,77);ctx.lineTo(515,77);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle='#d6d6b8';ctx.font='17px "DM Sans",sans-serif';ctx.textAlign='center';ctx.fillText('MINERAL STRUCTURE / MIXED THROUGH',300,42);
    ctx.fillStyle='#dec08c';ctx.font='16px "DM Sans",sans-serif';ctx.fillText('Drainage '+drainage+'%    /    Aeration '+aeration+'%',300,428);
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
    STUDIO.toast('Recipe saved. Your nursery has a new foundation.', 'soil');
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
