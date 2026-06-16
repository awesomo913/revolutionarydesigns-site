// Gritty Mix — Save/Load Code System
// No accounts, no emails. Your save is a code.
// Bundled LZString (no external dependency — self-contained)

// lz-string inline for compressToBase64/decompressFromBase64
(function(){function o(o,r){if(!t[o]){t[o]={};for(var n=0;n<o.length;n++)t[o][o.charAt(n)]=n}return t[o][r]}var r=String.fromCharCode,n="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/$",i={compressToBase64:function(o){if(null==o)return"";var r=i._compress(o,6,function(o){return n.charAt(o)});return r+"="},decompressFromBase64:function(r){if(null==r)return"";if(r==="")return null;return i._decompress(r.length,8,function(i){return o(n,r.charAt(i))})},compress:function(o){return i._compress(o,16,function(o){return r(o)})},_compress:function(o,r,n){if(null==o)return"";var i,t,e,s={},p={},u="",c="",f="",l=2,h=3,w=2,d=[],m=0,v=0;for(v=0;v<o.length;v+=1)if(u+=o.charAt(v),null!=s[u])c+=u;else s[u]=l++,p[c]&&(d.push(p[c]-1),m++,p[c]===(m<<w)>>>0&&(w++)),p[u]=h++,c=u,u="";if(c){null!=p[c]?(d.push(p[c]-1),m++):d.push(r.charCodeAt(c)),m++}for(t=d.length,i="",e=0;e<t;e++)i+=r(d[e]>>0&(1<<w)-1),d[e]>>>=w;for(;i.length<r.length*8/6;)i+=r(0);return i},decompress:function(o){return i._decompress(o.length,32768,function(r){return o.charCodeAt(r)})},_decompress:function(o,t,n){var i,e,s,p,u,c,f,l,h=t,w=4,d=[3],m=[],v=0,a=0;for(i=0;i<3;i+=1)d[i]=i;for(p=0,e=Math.pow(2,2),s=1;s!=e;)u=n(p),p++,v=(v<<8|u)>>>0,a+=8,w>a?void 0:(c=v>>>(a-=w)&(1<<w)-1,w>c?c===3?(l=(a-4>=0?v>>>(a-=4)&(1<<4)-1:0)+(v<<(4-a)&(1<<4)-1),a-=4,w=4,0):(f=c>0?c:d[c],l=f.length,m.push(f)):(c<16?w=4:c<20?(l=1,c-=12):(l=c-6,w<5?w++:w),c=v>>>(a-=w)&(1<<w)-1,w++,l?l+=c=(c+(v<<w-2&(1<<w-2)-1)<<1>>>0):(c=(c+(v<<w-1&(1<<w-1)-1)<<1>>>0),c||(e=Math.pow(2,w),s=1)),l++,f=d[c+(4+(w<<2)-l<<1)],0),m.push.apply(m,f),d.push(m),m=[],s++),s<e);return m.join("")}};var t={};"undefined"!=typeof module&&null!=module&&(module.exports=i);window.LZString=i})();

const SAVE = {
  VERSION: 1,

  encode(state) {
    const compact = {
      v: SAVE.VERSION,
      d: state.day || 1,
      c: state.coins || 0,
      m: state.currentMix || null,
      p: this._packCollection(state.collection || []),
      e: state.lastEvents || [],
      n: state.nurserySort || 'value',
      s: state.seeds || [],
      h: state.chambers || [],
      i: state.marketInv || {}
    };
    const json = JSON.stringify(compact);
    const compressed = LZString.compressToBase64(json);
    return this._formatCode(compressed);
  },

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
        nurserySort: data.n || 'value',
        seeds: data.s || [],
        chambers: data.h || [],
        marketInv: data.i || {}
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
