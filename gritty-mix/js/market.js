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
    G.logEvent('good', '🛒', `Bought ${names[itemId] || itemId} for 💰${price}!`);
    G.floatingText('🛒 Purchased!', document.getElementById('market-buy'));

    // Update buy buttons
    document.querySelectorAll('#market-buy .shop-item button').forEach(b => {
      b.textContent = '🛒 Buy';
      b.disabled = false;
    });
  },

  // Sell a cactus
  sell(instanceId) {
    const cactus = COLLECTION.get(instanceId);
    if (!cactus) return;

    const species = getSpecies(cactus.speciesId);
    let price = cactus.value;

    // Bonus for grafted, cultivars, high health
    if (cactus.grafted) price = Math.round(price * 1.3);
    if (cactus.cultivar) price = Math.round(price * 2);
    if (cactus.health > 80) price = Math.round(price * 1.2);
    if (cactus.stage === 'blooming') price = Math.round(price * 1.5);

    // Remove from collection
    COLLECTION.remove(instanceId);
    G.state.coins += price;

    this.renderBalance();
    this.renderSellList();
    G.logEvent('good', '💰', `Sold ${species?.name || 'Cactus'} at the Concession Stand for 💰${price}!`);
    G.floatingText(`💰 +${price} coins!`, document.getElementById('sell-list'));
    G.renderNursery();
  },

  // Render sellable plants list
  renderSellList() {
    const container = document.getElementById('sell-list');
    // Only show propagated plants: offsets, seedlings, or any cactus
    const sellable = G.state.collection.filter(c => 
      c.stage === 'seedling' || c.stage === 'juvenile' || c.stage === 'mature' || c.stage === 'blooming'
    );

    if (sellable.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);font-size:13px">No plants to sell. Propagate offsets or grow seedlings.</p>';
      return;
    }

    container.innerHTML = sellable.map(c => {
      const s = getSpecies(c.speciesId);
      let price = c.value;
      if (c.grafted) price = Math.round(price * 1.3);
      if (c.cultivar) price = Math.round(price * 2);
      if (c.health > 80) price = Math.round(price * 1.2);

      return `
        <div class="sell-item">
          <span class="sell-emoji">${s?.emoji || '🌵'}</span>
          <span class="sell-name">${s?.name || 'Cactus'} ${c.grafted ? '(grafted)' : ''}</span>
          <span class="sell-stage">${c.stage} · ${Math.round(c.growth)}cm</span>
          <span class="sell-price">💰${price}</span>
          <button onclick="MARKET.sell(${c.instanceId})" class="btn-small">💰 Sell</button>
        </div>
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
    // Already static HTML - just update button states
  }
};
