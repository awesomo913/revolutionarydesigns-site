// Gritty Mix — Save/Load Code System
// No accounts, no emails. No external libraries. Your save is a code.
// Uses native browser btoa/atob for encoding — zero dependencies.

const SAVE = {
  VERSION: 1,

  encode(state) {
    const compact = {
      v: SAVE.VERSION,
      d: state.day || 1,
      c: state.coins || 0,
      m: state.currentMix || null,
      p: this._packCollection(state.collection || []),
      e: this._packEvents(state.lastEvents || []),
      n: state.nurserySort || 'value',
      s: state.seeds || [],
      h: state.chambers || [],
      i: state.marketInv || {},
      sc: state.claimedStarter || false
    };
    const json = JSON.stringify(compact);
    const encoded = btoa(unescape(encodeURIComponent(json)));
    return this._formatCode(encoded);
  },

  decode(code) {
    try {
      const cleaned = code.replace(/[\s\-]/g, '');
      const json = decodeURIComponent(escape(atob(cleaned)));
      const data = JSON.parse(json);
      if (!data.v || data.v > SAVE.VERSION) return null;
      return {
        day: data.d || 1,
        coins: data.c || 0,
        currentMix: data.m || null,
        collection: this._unpackCollection(data.p || []),
        lastEvents: this._unpackEvents(data.e || []),
        nurserySort: data.n || 'value',
        seeds: data.s || [],
        chambers: data.h || [],
        marketInv: data.i || {},
        claimedStarter: data.sc || false
      };
    } catch(e) {
      return null;
    }
  },

  _formatCode(code) {
    const groups = [];
    for (let i = 0; i < code.length; i += 4) {
      groups.push(code.substring(i, i + 4));
    }
    return groups.join('-');
  },

  _packCollection(collection) {
    return collection.map(c => ({
      i: c.instanceId, s: c.speciesId, n: c.nickname || '',
      h: c.health, g: c.growth, st: c.stage || 'seedling',
      a: c.age || 0, w: c.water || 0, v: c.value || 0,
      cv: c.cultivar || null, gd: c.grafted || false, rs: c.rootstock || null
    }));
  },

  _unpackCollection(packed) {
    return packed.map(c => ({
      instanceId: c.i, speciesId: c.s, nickname: c.n || '',
      health: c.h, growth: c.g, stage: c.st || 'seedling',
      age: c.a || 0, water: c.w || 0, value: c.v || 0,
      cultivar: c.cv || null, grafted: c.gd || false, rootstock: c.rs || null
    }));
  },

  _packEvents(events) {
    return events.slice(-20).map(e => ({
      t: e.text, d: e.day || 0, p: e.type || 'info'
    }));
  },

  _unpackEvents(packed) {
    return packed.map(e => ({
      text: e.t, day: e.d, type: e.p || 'info'
    }));
  },

  copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        alert('Save code copied to clipboard!');
      }).catch(() => {
        this._fallbackCopy(text);
      });
    } else {
      this._fallbackCopy(text);
    }
  },

  _fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    alert('Save code copied!');
  }
};
