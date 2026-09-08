// Dependency-free regression tests for the cultivation game and persistent graft lifecycle.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
let assertions = 0;
function equal(a,b,message) { assert.equal(a,b,message); assertions++; }
const elements = new Map();
function element(id) {
  if(!elements.has(id)) elements.set(id,{value:'',textContent:'',innerHTML:'',style:{},classList:{add(){},remove(){},contains(){return false;}},appendChild(){},before(){},options:[],setAttribute(){},querySelector(){return null;}});
  return elements.get(id);
}
const context = vm.createContext({
  console, Math:Object.create(Math), Date, performance:{now:()=>1000},
  btoa:s=>Buffer.from(s,'binary').toString('base64'), atob:s=>Buffer.from(s,'base64').toString('binary'),
  encodeURIComponent,decodeURIComponent,escape,unescape,
  document:{getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener(){},createElement:()=>element(Math.random())},
  confirm:()=>true,alert(){},setTimeout(){},requestAnimationFrame(){},cancelAnimationFrame(){},
});
for(const [file,name] of [['data','SPECIES'],['save','SAVE'],['soil','SOIL'],['collection','COLLECTION'],['events','EVENT_ENGINE'],['breeding','BREED'],['market','MARKET'],['game','G'],['bench','BENCH']]) {
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../gritty-mix/js/'+file+'.js'),'utf8')+`;globalThis.${name}=${name};`,context);
}
vm.runInContext(`globalThis.ROOTSTOCKS=ROOTSTOCKS;globalThis.SOIL_COMPONENTS=SOIL_COMPONENTS;globalThis.STUDIO={toast(){},sync(){},save(){},progress(){return G.state.progress||(G.state.progress={xp:0,grafts:0});},plantArt(){return '';}};`,context);
const {G,BENCH,COLLECTION,SAVE,SOIL,BREED,MARKET}=context;
BENCH.render=()=>{};BENCH.draw=()=>{};BENCH.animate=()=>{};G.renderNursery=()=>{};G.renderEvents=()=>{};G.refreshAll=()=>{};
function fresh(){G.state=G.defaultState();G.state.graft=BENCH.fresh();BREED.activeFruit=null;COLLECTION.nextId=1;}
function plant(){return COLLECTION.add('astrophytum-asterias',{health:85,water:10,growth:20});}
function choose(root){const c=plant();element('rootstock-select').value=root; element('scion-select').value=String(c.instanceId);BENCH.choose();return c;}
for(const root of context.ROOTSTOCKS){
  fresh();const c=choose(root.id);equal(BENCH.job.stage,1,'pair starts cutting');
  BENCH.secure();BENCH.heal();BENCH.lockAlignment();equal(BENCH.job.stage,1,'out-of-order actions do nothing');
  BENCH.set('cut',20);BENCH.lockCut();equal(BENCH.job.stage,1,'bad cut cannot be committed');
  BENCH.set('cut',0);BENCH.lockCut();equal(BENCH.job.stage,2,'level cut advances');
  BENCH.lockAlignment();equal(BENCH.job.stage,2,'concentric unequal rings are not connected');
  BENCH.set('position',50+(BENCH.alignment().rootRadius-32)/2.4);equal(BENCH.alignment().score,0,'nested rings never earn contact credit');
  const target=BENCH.alignment().rootRadius-31+18;
  BENCH.set('position',50+target/2.4);BENCH.lockAlignment();equal(BENCH.job.stage,3,'intersecting rings advance');
  BENCH.secure();equal(BENCH.job.stage,3,'loose wrap cannot be committed');
  BENCH.set('tension',55);element('wrap-method').value='bands';BENCH.secure();BENCH.heal();
  BENCH.heal();BENCH.heal();equal(BENCH.job.days,0,'repeated heal does not advance the clock');
  G.state=SAVE.decode(SAVE.encode(G.state));equal(BENCH.job.stage,5,'graft survives portable save');
  BENCH.init();equal(BENCH.job.stage,5,'reopening bench preserves recovery');
  for(let day=0;day<6;day++)BENCH.tick();equal(BENCH.job.stage,5,'six days cannot complete seven-day recovery');
  BENCH.tick();equal(BENCH.job.stage,6,'seventh day completes union');equal(BENCH.job.quality,100,'perfect technique earns 100');
  const completed=COLLECTION.get(c.instanceId);equal(completed.grafted,true,'result changes actual nursery plant');equal(completed.rootstock,root.id,'selected stock is retained');
  const coins=G.state.coins;BENCH.tick();BENCH.heal();equal(G.state.coins,coins,'reward granted exactly once');
  BENCH.reset();element('rootstock-select').value=root.id;element('scion-select').value=String(c.instanceId);BENCH.choose();equal(BENCH.job.stage,0,'cannot graft the same specimen again');
}
fresh();let c=choose('pereskiopsis');COLLECTION.remove(c.instanceId);BENCH.init();equal(BENCH.job.stage,0,'missing specimen resets safely');
fresh();c=plant();c.affliction='mealybugs';element('rootstock-select').value='pereskiopsis';element('scion-select').value=String(c.instanceId);BENCH.choose();equal(BENCH.job.stage,0,'sick specimens must be treated first');
fresh();c=COLLECTION.add('trichocereus-pachanoi',{health:0,water:0,growth:0,value:0});equal(c.health,0,'zero health is preserved');equal(c.water,0,'zero water is preserved');equal(c.value,0,'zero value is preserved');
fresh();c=plant();equal(c.water,10,'starter hydration is respected');
// Old portable saves stay valid, and IDs are reseeded above loaded plants.
const v1=context.btoa(JSON.stringify({v:1,d:42,c:20,p:[{i:19,s:c.speciesId,h:90,g:20,w:4}],s:[],h:[]}));
G.state=SAVE.decode(v1);equal(G.state.day,42,'v1 game day preserved');equal(plant().instanceId,20,'new IDs do not collide with loaded IDs');
G.state.activeFruit={parentA:c.speciesId,parentB:c.speciesId,progress:12,maxDays:30};equal(SAVE.decode(SAVE.encode(G.state)).activeFruit.progress,12,'fruit growth survives save');
// Only ready fruit and chambers pay out; small starter packets are usable.
fresh();BREED.activeFruit={parentA:'trichocereus-pachanoi',parentB:'trichocereus-peruvianus',progress:2,maxDays:30};BREED.harvest();equal(G.state.seeds.length,0,'unripe fruit cannot be harvested');
BREED.renderSeedInventory=()=>{};BREED.renderSowSelect=()=>{};BREED.renderGermChambers=()=>{};G.floatingText=()=>{};
G.state.seeds=[{name:'Starter',parentA:'trichocereus-pachanoi',parentB:'trichocereus-pachanoi',count:2,quality:90}];element('sow-select').value='0';BREED.sow();equal(G.state.chambers[0].seedsUsed,2,'two-seed packet can be sown');equal(G.state.seeds.length,0,'sowing consumes exactly the packet');
const chamber=G.state.chambers[0];BREED.potUp(chamber.id);equal(G.state.collection.length,0,'unready chambers cannot pay out');chamber.stage='ready';BREED.potUp(chamber.id);equal(G.state.collection.length,2,'seedlings never exceed seeds sown');BREED.potUp(chamber.id);equal(G.state.collection.length,2,'chambers only pay once');
// Normalize precisely, including recovering from a single 100% component.
SOIL.sliders=Object.fromEntries(context.SOIL_COMPONENTS.map(c=>[c.id,0]));const component=context.SOIL_COMPONENTS[0].id;
for(const value of [100,50,0,37,99,1]){SOIL.sliders[component]=value;SOIL.normalize(component);equal(Object.values(SOIL.sliders).reduce((a,b)=>a+b,0),100,'recipe always sums to exactly 100');}
// Supplies have actual effects and consume inventory once; no use at full vitality.
MARKET.renderMarket=()=>{};fresh();c=plant();G.state.marketInv={'pots':1,'fert':1,'graft-kit':1};element('supply-target').value=String(c.instanceId);
MARKET.use('pots');equal(c.health,100,'repot restores vitality');equal(G.state.marketInv.pots,0,'repot consumes one pot');MARKET.use('pots');equal(c.health,100,'empty inventory cannot apply again');
const growth=c.growth;MARKET.use('fert');equal(c.growth,growth+10,'feed produces growth');MARKET.use('graft-kit');equal(G.state.marketInv['graft-kit'],1,'invalid aftercare leaves item intact');
console.log(`Gritty Mix: ${assertions} regression checks passed.`);
