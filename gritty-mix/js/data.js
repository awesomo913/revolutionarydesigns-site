// Gritty Mix — Game Database
// All data sourced from real cactus cultivation knowledge

const SPECIES = [
  {
    id: 'trichocereus-pachanoi',
    name: 'San Pedro',
    species: 'Trichocereus pachanoi',
    emoji: '🌵',
    difficulty: 2,
    growthRate: 2,
    maxSize: 600,
    value: 15,
    prefers: { drainage: 80, aeration: 75, waterRetention: 15, organic: 15 },
    minTemp: -5,
    maxTemp: 40,
    waterFreq: 10,
    light: 'Full sun',
    description: 'The classic columnar cactus. 4-8 rounded ribs, short yellow/black spines. Fast grower.',
    graftRootstock: true,
    bloomColor: 'white',
    rarity: 'common',
    native: 'Ecuador, Peru'
  },
  {
    id: 'trichocereus-bridgesii',
    name: 'Bolivian Torch',
    species: 'Trichocereus bridgesii',
    emoji: '🌵',
    difficulty: 2,
    growthRate: 2,
    maxSize: 500,
    value: 20,
    prefers: { drainage: 80, aeration: 75, waterRetention: 15, organic: 15 },
    minTemp: -3,
    maxTemp: 38,
    waterFreq: 10,
    light: 'Full sun',
    description: '4-6 wider ribs, v-notch notches above areoles, long spines. Known for high mescaline content.',
    graftRootstock: true,
    bloomColor: 'white',
    rarity: 'common',
    native: 'Bolivia'
  },
  {
    id: 'trichocereus-peruvianus',
    name: 'Peruvian Torch',
    species: 'Trichocereus peruvianus / macrogonus',
    emoji: '🌵',
    difficulty: 3,
    growthRate: 2,
    maxSize: 600,
    value: 25,
    prefers: { drainage: 80, aeration: 75, waterRetention: 15, organic: 15 },
    minTemp: -2,
    maxTemp: 38,
    waterFreq: 10,
    light: 'Full sun',
    description: '6-8 ribs, longer golden spines. Thicker stems than pachanoi. Glaucous blue-green skin.',
    graftRootstock: true,
    bloomColor: 'white',
    rarity: 'common',
    native: 'Peru'
  },
  {
    id: 'trichocereus-terscheckii',
    name: 'Argentine Saguaro',
    species: 'Trichocereus terscheckii',
    emoji: '🌵',
    difficulty: 3,
    growthRate: 1,
    maxSize: 1200,
    value: 30,
    prefers: { drainage: 85, aeration: 80, waterRetention: 10, organic: 10 },
    minTemp: -8,
    maxTemp: 40,
    waterFreq: 14,
    light: 'Full sun',
    description: 'Tree-like cactus reaching 12m. 8-14 ribs, yellow spines. Very cold hardy.',
    graftRootstock: false,
    bloomColor: 'white',
    rarity: 'uncommon',
    native: 'Argentina, Bolivia'
  },
  {
    id: 'trichocereus-scopulicola',
    name: 'Scopulicola',
    species: 'Trichocereus scopulicola',
    emoji: '🌵',
    difficulty: 4,
    growthRate: 1,
    maxSize: 300,
    value: 40,
    prefers: { drainage: 85, aeration: 80, waterRetention: 10, organic: 10 },
    minTemp: 0,
    maxTemp: 35,
    waterFreq: 12,
    light: 'Full sun to part shade',
    description: 'Rare. Almost spineless, dark green, 4-6 ribs. Said to be a bridgesii variety.',
    graftRootstock: false,
    bloomColor: 'white',
    rarity: 'rare',
    native: 'Bolivia (disputed)'
  },
  {
    id: 'echinocactus-horizonthalonius',
    name: "Turk's Head",
    species: 'Echinocactus horizonthalonius',
    emoji: '🌵',
    difficulty: 5,
    growthRate: 1,
    maxSize: 30,
    value: 50,
    prefers: { drainage: 90, aeration: 85, waterRetention: 5, organic: 5 },
    minTemp: 5,
    maxTemp: 45,
    waterFreq: 18,
    light: 'Full sun',
    description: 'Slow-growing globular cactus. Helical ribs, heavy pink spines, magenta flowers. Extremely slow.',
    graftRootstock: false,
    bloomColor: 'magenta',
    rarity: 'rare',
    native: 'Chihuahuan/Sonoran Desert, Mexico'
  },
  {
    id: 'echinocactus-grusonii',
    name: 'Golden Barrel',
    species: 'Kroenleinia grusonii',
    emoji: '🌵',
    difficulty: 2,
    growthRate: 1,
    maxSize: 100,
    value: 15,
    prefers: { drainage: 75, aeration: 70, waterRetention: 20, organic: 20 },
    minTemp: 0,
    maxTemp: 40,
    waterFreq: 10,
    light: 'Full sun',
    description: "Classic golden barrel. 20-30 ribs, bright yellow spines. Endangered in the wild but ubiquitous in cultivation.",
    graftRootstock: false,
    bloomColor: 'yellow',
    rarity: 'common',
    native: 'Central Mexico'
  },
  {
    id: 'tephrocactus-articulatus',
    name: 'Paper Spine Cactus',
    species: 'Tephrocactus articulatus',
    emoji: '🌵',
    difficulty: 3,
    growthRate: 2,
    maxSize: 40,
    value: 20,
    prefers: { drainage: 85, aeration: 80, waterRetention: 10, organic: 10 },
    minTemp: 2,
    maxTemp: 40,
    waterFreq: 12,
    light: 'Full sun',
    description: 'Segmented stems with flat papery spines. Produces extrafloral nectaries ("crying"). Easy to propagate.',
    graftRootstock: false,
    bloomColor: 'white',
    rarity: 'uncommon',
    native: 'Argentina'
  },
  {
    id: 'lophophora-williamsii',
    name: 'Peyote',
    species: 'Lophophora williamsii',
    emoji: '🌵',
    difficulty: 5,
    growthRate: 1,
    maxSize: 12,
    value: 60,
    prefers: { drainage: 90, aeration: 85, waterRetention: 5, organic: 5 },
    minTemp: 5,
    maxTemp: 40,
    waterFreq: 20,
    light: 'Part shade',
    description: 'Small spineless globular cactus. Extremely slow-growing. Pink flowers. CITES Appendix II.',
    graftRootstock: false,
    bloomColor: 'pink',
    rarity: 'rare',
    native: 'Chihuahuan Desert, Texas/Mexico'
  },
  {
    id: 'astrophytum-asterias',
    name: 'Star Cactus',
    species: 'Astrophytum asterias',
    emoji: '🌟',
    difficulty: 4,
    growthRate: 1,
    maxSize: 10,
    value: 35,
    prefers: { drainage: 85, aeration: 80, waterRetention: 10, organic: 10 },
    minTemp: 3,
    maxTemp: 40,
    waterFreq: 14,
    light: 'Full sun to part shade',
    description: 'Domed, spineless cactus with white flecks. Yellow flowers with red centers. Critically endangered in the wild.',
    graftRootstock: false,
    bloomColor: 'yellow',
    rarity: 'rare',
    native: 'Rio Grande Valley, Texas / Mexico'
  },
  {
    id: 'haworthia-truncata',
    name: 'Truncata',
    species: 'Haworthia truncata',
    emoji: '🌿',
    difficulty: 3,
    growthRate: 1,
    maxSize: 8,
    value: 25,
    prefers: { drainage: 70, aeration: 65, waterRetention: 25, organic: 30 },
    minTemp: 5,
    maxTemp: 35,
    waterFreq: 10,
    light: 'Bright indirect to morning sun',
    description: 'Distichous fan of truncated leaves with translucent windows. Native to South Africa.',
    graftRootstock: false,
    bloomColor: 'white',
    rarity: 'uncommon',
    native: 'South Africa (Little Karoo)'
  },
  {
    id: 'aztekium-ritteri',
    name: 'Aztekium',
    species: 'Aztekium ritteri',
    emoji: '🌵',
    difficulty: 5,
    growthRate: 1,
    maxSize: 10,
    value: 100,
    prefers: { drainage: 95, aeration: 90, waterRetention: 3, organic: 2 },
    minTemp: 8,
    maxTemp: 40,
    waterFreq: 21,
    light: 'Part shade',
    description: 'The holy grail of cactus collecting. Deeply ribbed, gray-green, endemic to one small valley in Nuevo Leon, Mexico.',
    graftRootstock: false,
    bloomColor: 'pink',
    rarity: 'grail',
    native: 'Nuevo Leon, Mexico (single valley)'
  },
  {
    id: 'ariocarpus-fissuratus',
    name: 'Living Rock',
    species: 'Ariocarpus fissuratus',
    emoji: '🪨',
    difficulty: 5,
    growthRate: 1,
    maxSize: 15,
    value: 80,
    prefers: { drainage: 95, aeration: 90, waterRetention: 3, organic: 2 },
    minTemp: 5,
    maxTemp: 45,
    waterFreq: 21,
    light: 'Full sun',
    description: 'Mimics limestone rocks. Triangular tubercles, no spines. Magenta flowers. CITES Appendix I.',
    graftRootstock: false,
    bloomColor: 'magenta',
    rarity: 'grail',
    native: 'Chihuahuan Desert'
  }
];

// Rare cultivar clones (can be found via grafting/auction events)
const CULTIVARS = [
  { id: 'tbm-clone-b', name: 'TBM Clone B', base: 'trichocereus-bridgesii', desc: 'Monstrose bridgesii — short form, bubble-like clusters', valueMult: 3, rarity: 'rare' },
  { id: 'ogunbodede', name: 'Ogunbodede', base: 'trichocereus-pachanoi', desc: 'Legendary clone from Nigeria. Fat, glaucous, 4 ribs', valueMult: 5, rarity: 'grail' },
  { id: 'psycho0', name: 'Psycho0', base: 'trichocereus-bridgesii', desc: 'Vigorous bridgesii clone. High alkaloid content', valueMult: 2.5, rarity: 'rare' },
  { id: 'lumberjack', name: 'Lumberjack', base: 'trichocereus-peruvianus', desc: 'Fat peruvianus clone. Sought after for growth rate', valueMult: 3, rarity: 'rare' },
  { id: 'fields-bridge', name: "Fields Bridge", base: 'trichocereus-bridgesii', desc: 'Classic clone from Sacred Succulents', valueMult: 2, rarity: 'uncommon' },
  { id: 'juuls-giant', name: "Juul's Giant", base: 'trichocereus-pachanoi', desc: 'Massive pachanoi clone. Thick stems, fast grower', valueMult: 2.5, rarity: 'rare' },
  { id: 'tbm-crested', name: 'TBM Crested', base: 'trichocereus-bridgesii', desc: 'Crested mutation of bridgesii. Fan-shaped growth', valueMult: 6, rarity: 'grail' }
];

// Soil components
const SOIL_COMPONENTS = [
  { id: 'pumice', name: 'Pumice', drainage: 95, aeration: 90, waterRet: 5, organic: 0, desc: 'The gold standard. Porous, doesn\'t break down.' },
  { id: 'lava-rock', name: 'Lava Rock / Scoria', drainage: 90, aeration: 85, waterRet: 8, organic: 0, desc: 'Sharp, porous. Adds weight and minerals.' },
  { id: 'perlite', name: 'Perlite', drainage: 85, aeration: 80, waterRet: 10, organic: 0, desc: 'Cheap but floats. Breaks down over time.' },
  { id: 'crushed-granite', name: 'Crushed Granite', drainage: 80, aeration: 75, waterRet: 5, organic: 0, desc: 'Heavy. Adds trace minerals. Good for top dressing.' },
  { id: 'coir', name: 'Coir / Coco Fiber', drainage: 40, aeration: 30, waterRet: 70, organic: 80, desc: 'Sustainable peat alternative. Holds moisture.' },
  { id: 'worm-castings', name: 'Worm Castings', drainage: 30, aeration: 20, waterRet: 60, organic: 90, desc: 'Rich in nutrients. Use sparingly.' },
  { id: 'turface', name: 'Turface / Calcined Clay', drainage: 70, aeration: 70, waterRet: 25, organic: 0, desc: 'Bonsai staple. Holds water without staying wet.' },
  { id: 'zeolite', name: 'Zeolite', drainage: 85, aeration: 80, waterRet: 15, organic: 0, desc: 'Porous volcanic mineral. Excellent cation exchange.' },
  { id: 'sand', name: 'Coarse Sand', drainage: 75, aeration: 65, waterRet: 10, organic: 0, desc: 'Use coarse/gritty — never fine beach sand.' },
  { id: 'pine-bark', name: 'Pine Bark Fines', drainage: 30, aeration: 25, waterRet: 60, organic: 95, desc: 'Used in gritty mix. Decomposes slowly.' }
];

// Soil presets (pre-made recipes)
const SOIL_PRESETS = {
  trichocereus: { pumice: 50, 'lava-rock': 15, 'crushed-granite': 10, coir: 15, 'worm-castings': 10 },
  haworthia: { pumice: 35, 'lava-rock': 10, turface: 15, coir: 25, 'worm-castings': 10, 'pine-bark': 5 },
  seedling: { pumice: 30, perlite: 15, coir: 35, 'worm-castings': 15, sand: 5 },
  gritty: { turface: 33, 'crushed-granite': 33, 'pine-bark': 34 }
};

// Rootstocks for grafting
const ROOTSTOCKS = [
  { id: 'pereskiopsis', name: 'Pereskiopsis', desc: 'Fastest growth. Best for seedlings.', difficulty: 3, speedBonus: 3, temp: '22-30°C' },
  { id: 'trichocereus-pachanoi-root', name: 'Trichocereus pachanoi', desc: 'Standard columnar rootstock. Sturdy, compatible.', difficulty: 2, speedBonus: 2, temp: '15-35°C' },
  { id: 'myrtillocactus', name: 'Myrtillocactus geometrizans', desc: 'Good for globular cacti. Fast, hardy.', difficulty: 2, speedBonus: 2, temp: '15-35°C' },
  { id: 'hylocereus', name: 'Hylocereus undatus', desc: 'For epiphytic cacti. Dragonfruit rootstock.', difficulty: 1, speedBonus: 1, temp: '18-32°C' }
];

// Events
const EVENTS = [
  { id: 'spider-mites', type: 'bad', title: 'Spider Mites!', msg: 'Fine webbing on new growth. Treat with neem oil or miticide.', action: 'Treat with neem oil', icon: '🕷️' },
  { id: 'mealybugs', type: 'bad', title: 'Mealybugs!', msg: 'White cottony clusters on spines. Dab with alcohol swab.', action: 'Apply isopropyl alcohol', icon: '🐛' },
  { id: 'root-rot', type: 'bad', title: 'Root Rot Detected', msg: 'Mushy base, discoloration. Surgery needed.', action: 'Amputate above rot, sulfur powder', icon: '⚠️' },
  { id: 'corking', type: 'info', title: 'Corking at Base', msg: 'Natural aging. Brown tough skin at base. Normal — not rot!', action: 'No action needed', icon: '🌳' },
  { id: 'nectaries', type: 'good', title: 'Crying Cactus', msg: 'Amber droplets on areoles. Extrafloral nectaries — healthy sign!', action: 'Tephro Whisperer badge earned', icon: '💧' },
  { id: 'bloom', type: 'good', title: 'Bloom Time!', msg: 'A cactus is flowering! Pollinate for seeds.', action: 'Hand-pollinate flowers', icon: '🌸' },
  { id: 'offset', type: 'good', title: 'New Offset!', msg: 'A pup has appeared at the base. Propagate or let grow.', action: 'Remove and root the pup', icon: '🌱' },
  { id: 'sunburn', type: 'bad', title: 'Sunburn!', msg: 'Yellow/brown patches on sun-facing side. Move to shade.', action: 'Relocate to part shade', icon: '☀️' },
  { id: 'scale', type: 'bad', title: 'Scale Insects', msg: 'Brown waxy bumps on ribs. Scrape off with toothpick.', action: 'Scrape and apply neem oil', icon: '🟤' },
  { id: 'fungus-gnats', type: 'bad', title: 'Fungus Gnats', msg: 'Tiny flies near soil. Soil staying too wet.', action: 'Let soil dry out, yellow traps', icon: '🪰' },
  { id: 'fungal-rot', type: 'bad', title: 'Fungal Rot!', msg: 'Dark sunken spots spreading from a wet base. Cut to clean tissue and dry it out.', action: 'Sterile cut to clean tissue, dust with sulfur', icon: '🍄' }
];

// Treatment mini-game: the right fix + two wrong distractors per affliction.
// Correct choices mirror the Pests and Fungal Issues guides in the Codex.
const TREATMENTS = {
  'mealybugs':    { correct: 'alcohol', options: [
    { id: 'alcohol',   label: '🧴 Dab clusters with 70% isopropyl alcohol' },
    { id: 'water',     label: '💦 Blast them off with plain water' },
    { id: 'sun',       label: '☀️ Move it into full sun to dry them out' } ] },
  'scale':        { correct: 'scrape', options: [
    { id: 'scrape',    label: '🪥 Scrape the bumps off, then alcohol' },
    { id: 'water',     label: '💦 Rinse with water and hope' },
    { id: 'fertilize', label: '🌿 Fertilize so it outgrows them' } ] },
  'spider-mites': { correct: 'neem', options: [
    { id: 'neem',      label: '🛢️ Rinse, then miticide / neem (evening)' },
    { id: 'dry',       label: '🏜️ Let it dry out much further' },
    { id: 'sun',       label: '☀️ Bake it in hot full sun' } ] },
  'fungus-gnats': { correct: 'dry', options: [
    { id: 'dry',       label: '🏜️ Let the soil dry fully + sticky traps' },
    { id: 'water',     label: '💧 Water more to flush them out' },
    { id: 'alcohol',   label: '🧴 Swab the spines with alcohol' } ] },
  'root-rot':     { correct: 'cut', options: [
    { id: 'cut',       label: '🔪 Cut above the rot, dry, re-root' },
    { id: 'water',     label: '💧 Water it to revive the roots' },
    { id: 'fertilize', label: '🌿 Feed it to recover' } ] },
  'fungal-rot':   { correct: 'cut', options: [
    { id: 'cut',       label: '🔪 Sterile cut to clean tissue + sulfur' },
    { id: 'water',     label: '💧 Mist it to keep it hydrated' },
    { id: 'shade',     label: '🌑 Move it somewhere dark and humid' } ] },
  'sunburn':      { correct: 'shade', options: [
    { id: 'shade',     label: '⛅ Move it to part shade' },
    { id: 'water',     label: '💧 Soak it heavily to cool it' },
    { id: 'sun',       label: '☀️ Leave it in full sun to toughen up' } ] }
};

// Shop items for initial purchase
const SHOP_ITEMS = [
  { species: 'trichocereus-pachanoi', cost: 0, unlocked: true }, // Starter
  { species: 'trichocereus-bridgesii', cost: 20, unlocked: false },
  { species: 'trichocereus-peruvianus', cost: 30, unlocked: false },
  { species: 'echinocactus-grusonii', cost: 15, unlocked: false },
  { species: 'tephrocactus-articulatus', cost: 25, unlocked: false },
  { species: 'haworthia-truncata', cost: 35, unlocked: false },
  { species: 'trichocereus-scopulicola', cost: 60, unlocked: false },
  { species: 'echinocactus-horizonthalonius', cost: 80, unlocked: false },
  { species: 'astrophytum-asterias', cost: 50, unlocked: false },
  { species: 'lophophora-williamsii', cost: 120, unlocked: false },
  { species: 'ariocarpus-fissuratus', cost: 200, unlocked: false },
  { species: 'aztekium-ritteri', cost: 500, unlocked: false }
];

// Get species by ID
function getSpecies(id) {
  return SPECIES.find(s => s.id === id);
}

// Get active shop items
function getShopItems() {
  return SHOP_ITEMS.map(item => ({
    ...item,
    speciesData: getSpecies(item.species)
  }));
}
