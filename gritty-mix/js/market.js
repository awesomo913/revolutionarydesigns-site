// Gritty Mix — Cactus Concession Stand Marketplace
// Buy supplies, sell propagated cacti

const MARKET = {
  inventory: {}, // items the player owns (e.g., soil-kit: 2)
  prices: {
    'soil-kit': 15,
    'pots': 25,
    'fert': 20,
    'graft-kit': 40,
    'seed-pack': 80
  },

  init() {
    if (!G.state.marketInv) G.state.marketInv = {};
    this.renderMarket();
    this.renderSellList();
    this.renderBalance();
  },

  quote(cactus) {
    let price = Math.max(1, cactus.value || 1);
    const modifiers = [];
    if (cactus.grafted) {
      price = Math.round(price * 1.3);
      modifiers.push(['Established graft', '+30%']);
    }
    if (cactus.cultivar) {
      price = Math.round(price * 2);
      modifiers.push(['Named cultivar', '×2']);
    }
    if (cactus.health > 80) {
      price = Math.round(price * 1.2);
      modifiers.push(['Excellent vitality', '+20%']);
    }
    if (cactus.stage === 'blooming') {
      price = Math.round(price * 1.5);
      modifiers.push(['In bloom', '+50%']);
    }
    return { price, modifiers };
  },

  stageProgress(cactus) {
    const stops = { seedling: [0, 40], juvenile: [40, 120], mature: [120, 250], blooming: [250, 250] };
    const [start, end] = stops[cactus.stage] || [0, 250];
    if (cactus.stage === 'blooming') return 100;
    return Math.max(5, Math.min(100, Math.round((cactus.growth - start) / (end - start) * 100)));
  },

  // Buy an item
  buy(itemId) {
    const price = this.prices[itemId];
    if (!price) return;
    if (G.state.coins < price) {
      G.logEvent('bad', '💰', `Not enough coins for ${itemId}!`);
      G.floatingText('💰 Not enough!', document.getElementById('market-buy'));
      return;
    }

    G.state.coins -= price;
    if (!G.state.marketInv) G.state.marketInv = {};
    G.state.marketInv[itemId] = (G.state.marketInv[itemId] || 0) + 1;

    const names = {
      'soil-kit': 'Basic Soil Kit',
      'pots': 'Terracotta Pots',
      'fert': 'Fertilizer Pack',
      'graft-kit': 'Grafting Kit',
      'seed-pack': 'Rare Seed Pack'
    };

    // If seed pack, add random rare seeds
    if (itemId === 'seed-pack') {
      const rarePool = ['lophophora-williamsii', 'astrophytum-asterias', 'tephrocactus-articulatus', 'echinocactus-horizonthalonius', 'trichocereus-scopulicola'];
      const pick = rarePool[Math.floor(Math.random() * rarePool.length)];
      const s = getSpecies(pick);
      if (!G.state.seeds) G.state.seeds = [];
      G.state.seeds.push({
        id: Date.now(),
        name: `${s?.name || 'Rare Cactus'} Seeds`,
        parentA: pick,
        parentB: pick,
        count: 10,
        quality: 70 + Math.floor(Math.random() * 25),
        harvested: G.state.day
      });
    }

    this.renderBalance();
    this.renderSellList();
    this.renderMarket();
    G.logEvent('good', '🛒', `Bought ${names[itemId] || itemId} for 💰${price}!`);
    G.floatingText('🛒 Purchased!', document.getElementById('market-buy'));

  },

  // Sell a cactus
  sell(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus) return;

    const species = getSpecies(cactus.speciesId);
    const { price } = this.quote(cactus);
    if (typeof STUDIO !== 'undefined') STUDIO.saleBurst(cactus, price);

    // Remove from collection
    COLLECTION.remove(instanceId);
    G.state.coins += price;

    this.renderBalance();
    this.renderSellList();
    G.logEvent('good', '💰', `Sold ${species?.name || 'Cactus'} at the Concession Stand for 💰${price}!`);
    G.floatingText(`+${price} coins`, document.getElementById('sell-list'));
    G.renderNursery();
  },

  // Render sellable plants list
  renderSellList() {
    const container = document.getElementById('sell-list');
    // Only show propagated plants: offsets, seedlings, or any cactus
    const sellable = G.state.collection.filter(c => 
      c.stage === 'seedling' || c.stage === 'juvenile' || c.stage === 'mature' || c.stage === 'blooming'
    );

    const summary = document.getElementById('market-sell-summary');
    if (summary) {
      const total = sellable.reduce((sum, cactus) => sum + this.quote(cactus).price, 0);
      summary.innerHTML = `<span><b>${sellable.length}</b> available</span><span><b>${total}</b> coin collection value</span>`;
    }

    if (sellable.length === 0) {
      container.innerHTML = '<div class="market-empty"><strong>Your sales shelf is empty.</strong><span>Raise seedlings or finish a graft, then return here to see the real plant and its offer.</span></div>';
      return;
    }

    container.innerHTML = sellable.map(c => {
      const s = getSpecies(c.speciesId);
      const { price, modifiers } = this.quote(c);
      const rootstock = c.grafted ? ROOTSTOCKS.find(root => root.id === c.rootstock) : null;
      const vitality = Math.max(0, Math.min(100, c.health));
      const progress = this.stageProgress(c);

      return `
        <article class="sell-item ${c.grafted ? 'is-graft' : ''}" data-sell-id="${c.instanceId}">
          <button class="sell-plant-preview" onclick="G.inspectCactus(${c.instanceId})" aria-label="Inspect ${s?.name || 'this plant'} before selling">
            ${BOTANICAL.nursery(c, 'market')}
            <span>Inspect specimen</span>
          </button>
          <div class="sell-copy">
            <div class="sell-kicker">${c.grafted ? `GRAFTED UNION${c.graftQuality ? ` · ${c.graftQuality}/100` : ''}` : s?.rarity?.toUpperCase() || 'NURSERY PLANT'}</div>
            <h5>${c.nickname || s?.name || 'Cactus'}</h5>
            <p><em>${s?.species || ''}</em>${rootstock ? ` on ${rootstock.name}` : ''}</p>
            <div class="sale-meters">
              <span>Vitality <i><b style="width:${vitality}%"></b></i><strong>${vitality}%</strong></span>
              <span>${c.stage === 'blooming' ? 'Blooming' : 'Next stage'} <i><b style="width:${progress}%"></b></i><strong>${progress}%</strong></span>
            </div>
            <div class="sale-modifiers">${modifiers.length ? modifiers.map(([label,value]) => `<span>${label} <b>${value}</b></span>`).join('') : '<span>Standard nursery offer</span>'}</div>
          </div>
          <div class="sell-offer">
            <span>MARKET OFFER</span>
            <strong>${price}<small> coins</small></strong>
            <button onclick="MARKET.sell(${c.instanceId})" class="btn-primary">Sell this plant</button>
          </div>
        </article>
      `;
    }).join('');
  },

  // Render balance display
  renderBalance() {
    const bal = document.getElementById('market-balance');
    if (bal) {
      bal.innerHTML = `💰 ${G.state.coins}`;
      bal.classList.remove('coin-pop');
      void bal.offsetWidth; // Force reflow to restart animation
      bal.classList.add('coin-pop');
    }
    document.getElementById('coin-counter').textContent = `💰 ${G.state.coins}`;
  },

  // Render market buy section
  renderMarket() {
    const items = {
      'soil-kit': ['Soil refresh', 'Restores 5 vitality to every plant.'],
      'pots': ['Fresh terracotta pot', 'Repot one plant for 15 vitality.'],
      'fert': ['Growth feed', 'Adds 10 growth points to one plant.'],
      'graft-kit': ['Graft aftercare kit', 'Restores 30 vitality to one established graft.'],
      'seed-pack': ['Rare seed packet', 'Ten seeds from a rare species. Added straight to your seed inventory.']
    };
    document.getElementById('market-buy').innerHTML = Object.entries(items).map(([id,item])=>`<div class="shop-item"><div class="info"><div class="name">${item[0]}</div><div class="species">${item[1]}${id !== 'seed-pack' ? ` · Owned: ${G.state.marketInv[id] || 0}` : ''}</div></div><div class="price">${this.prices[id]} coins</div><button onclick="MARKET.buy('${id}')" ${G.state.coins < this.prices[id] ? 'disabled' : ''}>Buy</button>${id !== 'seed-pack' ? `<button onclick="MARKET.use('${id}')" ${!G.state.marketInv[id] ? 'disabled' : ''}>Use</button>` : ''}</div>`).join('');
    if (!document.getElementById('supply-target')) {
      const label=document.createElement('label');label.className='workshop-label';label.htmlFor='supply-target';label.textContent='Apply supplies to';
      const select=document.createElement('select');select.id='supply-target';
      document.getElementById('market-buy').before(label,select);
    }
    const target=document.getElementById('supply-target'),selected=target.value;
    target.innerHTML=G.state.collection.filter(c=>c.health>0).map(c=>`<option value="${c.instanceId}">${getSpecies(c.speciesId).name} · ${c.health}% vitality</option>`).join('');
    if([...target.options].some(o=>o.value===selected))target.value=selected;
  },
  use(id) {
    if (!G.state.marketInv[id]) return;
    const plant=COLLECTION.get(+document.getElementById('supply-target').value);
    if (!plant || (BENCH.job?.plant === plant.instanceId && BENCH.job.stage > 0 && BENCH.job.stage < 6)) { STUDIO.toast('Choose a plant that is available in your nursery.');return; }
    if (id==='graft-kit' && !plant.grafted) { STUDIO.toast('Aftercare is for an established graft.');return; }
    if (id==='soil-kit') {
      const plants=G.state.collection.filter(c=>c.health>0&&c.health<100);
      if(!plants.length){STUDIO.toast('Your plants are already at full vitality.');return;}
      plants.forEach(c=>c.health=Math.min(100,c.health+5));
    } else if(id==='fert') { plant.growth+=10; }
    else if(id==='pots'||id==='graft-kit') {
      if(plant.health>=100){STUDIO.toast('This plant is already at full vitality.');return;}
      plant.health=Math.min(100,plant.health+(id==='pots'?15:30));
    } else return;
    G.state.marketInv[id]--;this.renderMarket();G.renderNursery();STUDIO.sync();STUDIO.toast('Supplies applied. A little boost for new growth.', 'reward');
  }
};
