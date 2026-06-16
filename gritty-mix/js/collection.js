// Gritty Mix — Collection Manager (Nursery)

const COLLECTION = {
  nextId: 1,

  // Add a new cactus to the collection
  add(speciesId, options = {}) {
    const species = getSpecies(speciesId);
    if (!species) return null;

    const cactus = {
      instanceId: COLLECTION.nextId++,
      speciesId: speciesId,
      nickname: options.nickname || '',
      health: 100,
      growth: 0,
      stage: 'seedling',
      age: 0,
      water: 0,
      value: species.value,
      cultivar: options.cultivar || null,
      grafted: options.grafted || false,
      rootstock: options.rootstock || null
    };

    if (options.stage) cactus.stage = options.stage;
    if (options.growth) cactus.growth = options.growth;
    if (options.health) cactus.health = options.health;
    if (options.value) cactus.value = options.value;
    if (options.age) cactus.age = options.age;

    G.state.collection.push(cactus);
    G.logEvent('good', '🌱', `New ${species.name} added to nursery!`);
    return cactus;
  },

  // Remove a cactus by instanceId
  remove(instanceId) {
    const idx = G.state.collection.findIndex(c => c.instanceId === instanceId);
    if (idx === -1) return false;
    const removed = G.state.collection.splice(idx, 1)[0];
    G.logEvent('info', '🗑️', `${getSpecies(removed.speciesId)?.name || 'Cactus'} removed.`);
    return true;
  },

  // Tick: daily growth cycle for all cacti
  dailyTick() {
    G.state.collection.forEach(cactus => {
      const species = getSpecies(cactus.speciesId);
      if (!species) return;

      cactus.age++;

      // Water cycle
      cactus.water = Math.max(0, cactus.water - 1);
      if (cactus.water <= 0) {
        cactus.health = Math.max(0, cactus.health - 2);
      }

      // Growth based on health
      if (cactus.health >= 50) {
        const growthRate = cactus.grafted ? species.growthRate * 2 : species.growthRate;
        cactus.growth += growthRate * (cactus.health / 100);
      }

      // Stage progression
      if (cactus.growth >= 40 && cactus.stage === 'seedling') {
        cactus.stage = 'juvenile';
        G.logEvent('good', '🌿', `${species.name} has reached juvenile stage!`);
      } else if (cactus.growth >= 120 && cactus.stage === 'juvenile') {
        cactus.stage = 'mature';
        cactus.value = Math.round(cactus.value * 1.5);
        G.logEvent('good', '🌵', `${species.name} has reached maturity!`);
      } else if (cactus.growth >= 250 && cactus.stage === 'mature') {
        cactus.stage = 'blooming';
        cactus.value = Math.round(cactus.value * 2);
        G.logEvent('good', '🌸', `${species.name} is blooming!`);
      }

      // Health decline from poor conditions
      if (cactus.health < 30) {
        const penalty = Math.floor(Math.random() * 3) + 1;
        cactus.growth = Math.max(0, cactus.growth - penalty);
      }

      // Random health recovery if conditions good
      if (cactus.health < 100 && cactus.health >= 50) {
        if (Math.random() < 0.1) {
          cactus.health = Math.min(100, cactus.health + 5);
        }
      }

      // Value appreciation with age
      if (cactus.age > 0 && cactus.age % 30 === 0) {
        cactus.value = Math.round(cactus.value * 1.05);
      }
    });
  },

  // Render nursery grid
  render(sortBy) {
    const grid = document.getElementById('nursery-grid');
    let collection = [...G.state.collection];

    if (sortBy === 'value') {
      collection.sort((a, b) => b.value - a.value);
    } else if (sortBy === 'name') {
      collection.sort((a, b) => {
        const na = getSpecies(a.speciesId)?.name || '';
        const nb = getSpecies(b.speciesId)?.name || '';
        return na.localeCompare(nb);
      });
    }

    grid.innerHTML = '';

    if (collection.length === 0) {
      grid.innerHTML = '<div class="cactus-card"><div class="empty-slot">Your nursery is empty.<br>Visit the shop to get started!</div></div>';
      return;
    }

    collection.forEach(cactus => {
      const species = getSpecies(cactus.speciesId);
      if (!species) return;

      const card = document.createElement('div');
      card.className = 'cactus-card';
      card.onclick = () => G.inspectCactus(cactus.instanceId);

      const stageEmoji = cactus.stage === 'seedling' ? '🌱' : cactus.stage === 'juvenile' ? '🌿' : '🌵';
      const healthPct = Math.max(0, cactus.health);

      card.innerHTML = `
        <span class="emoji">${species.emoji}</span>
        <div class="name">${cactus.nickname || species.name}</div>
        <div class="species">${species.species}${cactus.cultivar ? ' (cv.)' : ''}</div>
        <div class="stats">
          ${cactus.stage} · ${Math.round(cactus.growth)}cm · 💰${cactus.value}
        </div>
        <div class="health-bar"><div class="health-fill" style="width:${healthPct}%"></div></div>
      `;

      grid.appendChild(card);
    });
  },

  // Get a cactus by instanceId
  get(instanceId) {
    return G.state.collection.find(c => c.instanceId === instanceId);
  },

  // Calculate total collection value
  totalValue() {
    return G.state.collection.reduce((sum, c) => sum + (c.value || 0), 0);
  },

  // Get free nursery slot count (default 20 max)
  count() {
    return G.state.collection.length;
  }
};
