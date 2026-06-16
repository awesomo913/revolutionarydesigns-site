// Gritty Mix — Random Events Engine

const EVENT_ENGINE = {
  lastEventDay: {},

  // Check and trigger random events for a day
  checkEvents() {
    const day = G.state.day;
    const collection = G.state.collection;
    if (collection.length === 0) return;

    // 40% chance of an event per day
    if (Math.random() > 0.4) return;

    // Pick a random cactus
    const cactus = collection[Math.floor(Math.random() * collection.length)];
    const species = getSpecies(cactus.speciesId);
    if (!species) return;

    // Don't repeat the same event type per cactus too often
    const eventRoll = Math.random();

    let event = null;

    if (eventRoll < 0.15 && cactus.health > 60) {
      // Good events
      const goodEvents = ['offset', 'bloom', 'nectaries'];
      const type = goodEvents[Math.floor(Math.random() * goodEvents.length)];
      event = EVENTS.find(e => e.id === type);
      if (event) {
        cactus.health = Math.min(100, cactus.health + 5);
        if (type === 'offset') {
          // Add a new offset as a separate cactus
          const offset = COLLECTION.add(cactus.speciesId, {
            stage: 'seedling',
            growth: 0,
            health: 50,
            value: Math.round(cactus.value * 0.3)
          });
          if (offset) {
            G.logEvent('good', event.icon, `${species.name} produced a pup! New cactus added.`);
            return;
          }
        }
      }
    } else if (eventRoll < 0.40 && cactus.health > 40) {
      // Bloom for flowering plants
      if (cactus.stage === 'mature' || cactus.stage === 'blooming') {
        event = EVENTS.find(e => e.id === 'bloom');
        if (event) {
          cactus.stage = 'blooming';
          cactus.value = Math.round(cactus.value * 1.2);
          G.state.coins += Math.floor(cactus.value * 0.1);
        }
      }
    } else if (eventRoll < 0.70 && cactus.health > 30) {
      // Bad events (pests etc) - higher chance on stressed plants
      const badEvents = ['spider-mites', 'mealybugs', 'scale', 'sunburn', 'fungus-gnats'];
      const type = badEvents[Math.floor(Math.random() * badEvents.length)];
      event = EVENTS.find(e => e.id === type);
      if (event) {
        cactus.health = Math.max(0, cactus.health - 15);
      }
    } else if (eventRoll < 0.85) {
      // Info events
      if (Math.random() < 0.5) {
        event = EVENTS.find(e => e.id === 'corking');
      }
    } else {
      // Root rot - serious, triggered by overwatering
      if (cactus.water > 8 && cactus.health > 20) {
        event = EVENTS.find(e => e.id === 'root-rot');
        if (event) {
          cactus.health = Math.max(0, cactus.health - 30);
        }
      }
    }

    if (event) {
      const name = species.name;
      G.logEvent(event.type, event.icon, `${name}: ${event.msg}`);
      G.state.lastEvents.push({ type: event.type, text: event.msg, day: day });
    }
  },

  // Render event log
  renderLog() {
    const log = document.getElementById('event-log');
    const events = G.state.lastEvents || [];

    if (events.length === 0) {
      log.innerHTML = '<div class="event-entry empty">No events yet. Start your day to see what happens!</div>';
      return;
    }

    // Show last 20
    const recent = events.slice(-20).reverse();
    log.innerHTML = recent.map(e => `
      <div class="event-entry ${e.type}">
        <div class="time">Day ${e.day || '?'}</div>
        <div class="msg">${e.text}</div>
      </div>
    `).join('');
  }
};
