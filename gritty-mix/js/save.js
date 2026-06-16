// Gritty Mix — Save/Load Code System
// No accounts, no emails. Your save is a code.

const SAVE = {
  VERSION: 1,

  // Encode game state into a shareable code string
  encode(state) {
    // Sanitize: only keep what's needed
    const compact = {
      v: SAVE.VERSION,
      d: state.day || 1,
      c: state.coins || 0,
      m: state.currentMix || null,
      p: this._packCollection(state.collection || []),
      e: state.lastEvents || [],
      n: state.nurserySort || 'value'
    };
    const json = JSON.stringify(compact);
    const compressed = LZString.compressToBase64(json);
    // Format for readability: groups of 4 chars
    return this._formatCode(compressed);
  },

  // Decode a save code string back into game state
  decode(code) {
    try {
      const cleaned = code.replace(/[\s\-]/g, '').replace(/=$/, '');
      const json = LZString.decompressFromBase64(cleaned);
      if (!json) return null;
      const data = JSON.parse(json);
      if (!data.v || data.v > SAVE.VERSION) return null;

      return {
        day: data.d || 1,
        coins: data.c || 0,
        currentMix: data.m || null,
        collection: this._unpackCollection(data.p || []),
        lastEvents: data.e || [],
        nurserySort: data.n || 'value'
      };
    } catch(e) {
      return null;
    }
  },

  // Format code with dash separators every 4 characters
  _formatCode(code) {
    const groups = [];
    for (let i = 0; i < code.length; i += 4) {
      groups.push(code.substring(i, i + 4));
    }
    return groups.join('-');
  },

  // Pack collection to compact array format
  _packCollection(collection) {
    return collection.map(c => ({
      i: c.instanceId,
      s: c.speciesId,
      n: c.nickname || '',
      h: c.health,
      g: c.growth,
      st: c.stage || 'seedling',
      a: c.age || 0,
      w: c.water || 0,
      v: c.value || 0,
      cv: c.cultivar || null,
      gd: c.grafted || false,
      rs: c.rootstock || null
    }));
  },

  // Unpack compact collection back to full objects
  _unpackCollection(packed) {
    return packed.map(c => ({
      instanceId: c.i,
      speciesId: c.s,
      nickname: c.n || '',
      health: c.h,
      growth: c.g,
      stage: c.st || 'seedling',
      age: c.a || 0,
      water: c.w || 0,
      value: c.v || 0,
      cultivar: c.cv || null,
      grafted: c.gd || false,
      rootstock: c.rs || null
    }));
  },

  // Copy save code to clipboard
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
