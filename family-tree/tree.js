/* Emerson Family Tree — interactive tree engine.
   No dependencies. Two modes: descendants (frontier → today) and ancestors (Jeanette's
   pedigree). Click any person for full details and every source link. */
(function(){
"use strict";
var T = window.RD_TREE, P = T.people;
var DESC_ROOT = "u-emerson-parents";
var CARD_W=170, CARD_H=74, GAP_X=24, GAP_Y=112, SP_GAP=14, PAD=46;

var viewport=document.getElementById("ft-viewport"), canvas=document.getElementById("ft-canvas");
var panel=document.getElementById("ft-panel"), panelBody=document.getElementById("ft-panel-body");
var results=document.getElementById("ft-results"), searchInput=document.getElementById("ft-search-input");
var mode="descendants", view={x:0,y:0,s:1}, dragged=false;

/* ---------- helpers ---------- */
function allChildren(p){ if(p.fam){ var out=[]; p.fam.forEach(function(f){ out=out.concat(f.ch||[]); }); return out; } return p.ch||[]; }
var childIndex={};
Object.keys(P).forEach(function(id){ allChildren(P[id]).forEach(function(cid){ if(!childIndex[cid]) childIndex[cid]=[id, (P[id].sp&&P[id].sp[0])?P[id].sp[0].id:null]; }); });
function parentsOf(pid){ var p=P[pid], out=[]; if(p.f) out.push(p.f); if(p.mo) out.push(p.mo); if(!out.length && childIndex[pid]) out=childIndex[pid].slice(); return out.filter(function(id){return P[id];}); }
function spouseOf(p){ return (p.sp&&p.sp.length)?p.sp[0].id:null; }
function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function shortDates(p){
  if(p.living) return "Living";
  var years=function(s){ var m=String(s||"").match(/\d{3,4}/g); return m||[]; };
  var by=years(p.b), dy=years(p.d);
  var b=by.length? by.join("/") : "?";
  var d=dy.length? dy[dy.length-1] : "";
  if(d && /after/i.test(String(p.d))) d="aft. "+d;
  else if(d && /before/i.test(String(p.d))) d="bef. "+d;
  return d? (b+" – "+d) : b;
}
function nameOf(id){ return P[id]?P[id].n:id; }

/* ---------- instance building ---------- */
var expanded={}; // key mode:pid -> bool
function isExpanded(m,pid,depth,node){
  var k=m+":"+pid;
  if(k in expanded) return expanded[k];
  if(m==="descendants") return depth<=1 || !!P[pid].direct;
  return depth<=3;
}
function mkUnit(m,pid,spid,depth){
  var node={pid:pid,spid:spid,depth:depth,ch:[],key:m+":"+pid};
  node.expanded=isExpanded(m,pid,depth,node);
  return node;
}
function parentsUnit(pid){ var pr=parentsOf(pid); if(!pr.length) return null; return {pid:pr[0],spid:pr[1]||null}; }
function expandChildren(m,node){
  var out=[];
  if(m==="descendants"){ allChildren(P[node.pid]).forEach(function(cid){ if(P[cid]) out.push({pid:cid,spid:spouseOf(P[cid])}); }); }
  else{ var u1=parentsUnit(node.pid); if(u1&&P[u1.pid]) out.push(u1);
        if(node.spid){ var u2=parentsUnit(node.spid); if(u2&&P[u2.pid]) out.push(u2); } }
  return out;
}
function countBranch(m,node){
  var n=0; expandChildren(m,node).forEach(function(u){ n+=(u.spid?2:1)+countBranch(m,u); }); return n;
}
function buildDesc(pid,spid,depth){
  var node=mkUnit("descendants",pid,spid,depth);
  if(node.expanded){ expandChildren("descendants",node).forEach(function(u){ node.ch.push(buildDesc(u.pid,u.spid,depth+1)); }); }
  return node;
}
function buildAnc(pid,spid,depth){
  var node=mkUnit("ancestors",pid,spid,depth);
  if(node.expanded){ expandChildren("ancestors",node).forEach(function(u){ node.ch.push(buildAnc(u.pid,u.spid,depth+1)); }); }
  return node;
}
function countPidInstances(node,map){ map[node.pid]=(map[node.pid]||0)+1; if(node.spid) map[node.spid]=(map[node.spid]||0)+1; node.ch.forEach(function(c){countPidInstances(c,map);}); return map; }

/* ---------- layout ---------- */
function layout(root){
  var cards=[], links=[], pills=[], cursor=0;
  function widthOf(n){ return n.spid? 2*CARD_W+SP_GAP : CARD_W; }
  function place(node){
    var w=widthOf(node), kids=node.expanded?node.ch:[];
    node.y=node.depth*GAP_Y;
    if(!kids.length){ node.x=cursor; cursor+=w+GAP_X; cards.push(node); }
    else{
      var spans=kids.map(place);
      var l=spans[0].l, r=spans[spans.length-1].r, center=(l+r)/2;
      node.x=Math.max(center-w/2, l);
      var right=Math.max(r, node.x+w);
      cursor=Math.max(cursor, right+GAP_X);
      cards.push(node);
      kids.forEach(function(c){ links.push({from:node,to:c,direct:!!P[c.pid].direct}); });
      pills.push({node:node,collapsed:false});
      return {l:Math.min(l,node.x), r:right};
    }
    var hidden=countBranch(mode,node); if(hidden) pills.push({node:node,collapsed:true,hidden:hidden});
    return {l:node.x, r:node.x+w};
  }
  place(root);
  // normalize
  var minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;
  cards.forEach(function(c){ var w=widthOf(c); minX=Math.min(minX,c.x); minY=Math.min(minY,c.y); maxX=Math.max(maxX,c.x+w); maxY=Math.max(maxY,c.y+CARD_H); });
  var dx=PAD-minX, dy=PAD-minY;
  cards.forEach(function(c){ c.x+=dx; c.y+=dy; }); // pill nodes are the same objects — shifted once, here
  links.forEach(function(l){ l.px=l.from.x+widthOf(l.from)/2; l.py=l.from.y+CARD_H; l.cx=l.to.x+CARD_W/2; l.cy=l.to.y; });
  return {cards:cards,links:links,pills:pills,W:maxX-minX+2*PAD,H:maxY-minY+2*PAD};
}

/* ---------- render ---------- */
var current=null, dupMap={};
function render(){
  canvas.innerHTML="";
  var root = mode==="descendants" ? buildDesc(DESC_ROOT,null,0) : buildAnc(T.me,null,0);
  dupMap=countPidInstances(root,{});
  current=layout(root);
  var svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("class","ft-links"); svg.setAttribute("width",current.W); svg.setAttribute("height",current.H);
  current.links.forEach(function(l){
    var mid=(l.py+l.cy)/2;
    var path=document.createElementNS("http://www.w3.org/2000/svg","path");
    path.setAttribute("d","M"+l.px+" "+l.py+" V"+mid+" H"+l.cx+" V"+l.cy);
    if(l.direct) path.setAttribute("class","is-direct");
    svg.appendChild(path);
  });
  canvas.appendChild(svg);
  current.cards.forEach(function(c){
    canvas.appendChild(makeCard(c, c.pid, c.x, c.y));
    if(c.spid) canvas.appendChild(makeCard(c, c.spid, c.x+CARD_W+SP_GAP, c.y));
  });
  current.pills.forEach(function(pl){ canvas.appendChild(makePill(pl)); });
  applyTransform();
}
function makeCard(node,pid,x,y){
  var p=P[pid], el=document.createElement("div");
  el.className="ft-card"; el.dataset.pid=pid; el.style.left=x+"px"; el.style.top=y+"px";
  if(p.direct) el.classList.add("is-direct");
  if(p.living) el.classList.add("is-living");
  if(pid===T.me) el.classList.add("is-me");
  if(pid.indexOf("u-")===0) el.classList.add("is-unknown");
  if(dupMap[pid]>1) el.classList.add("is-dup");
  var html='<div class="nm">'+esc(p.n)+"</div><div class=\"dt\">"+esc(shortDates(p))+"</div>";
  if(dupMap[pid]>1) html+='<span class="bdg dup" title="This ancestor appears more than once in the tree — the Wesley sisters!">2×</span>';
  if(p.src&&p.src.length) html+='<span class="dot" title="'+p.src.length+' source link'+(p.src.length>1?"s":"")+'"></span>';
  el.innerHTML=html;
  el.title=p.n+((p.b&&p.d&&!p.living)?(" ("+p.b+" – "+p.d+")"):"");
  el.addEventListener("click",function(){ if(!dragged) select(pid,true); });
  return el;
}
function makePill(pl){
  var el=document.createElement("div"), node=pl.node;
  el.className="ft-pill"; el.style.top=(node.y+CARD_H+8)+"px";
  if(pl.collapsed){ el.style.left=(node.x+((node.spid?(2*CARD_W+SP_GAP):CARD_W)/2))+"px"; el.textContent="＋ "+pl.hidden+" more"; }
  else{ el.style.left=(node.x+(node.spid?(2*CARD_W+SP_GAP):CARD_W)+8)+"px"; el.textContent="− hide"; el.title="Collapse this branch"; }
  el.addEventListener("click",function(e){ e.stopPropagation();
    expanded[node.key]=!node.expanded; render(); centerOn(node.pid); });
  return el;
}

/* ---------- viewport transform ---------- */
function applyTransform(){ canvas.style.transform="translate("+view.x+"px,"+view.y+"px) scale("+view.s+")"; }
function fit(){
  var vr=viewport.getBoundingClientRect();
  var s=Math.min(vr.width/current.W, vr.height/current.H, 1.1);
  view.s=s; view.x=(vr.width-current.W*s)/2; view.y=(vr.height-current.H*s)/2;
  applyTransform();
}
function initialView(){
  var vr=viewport.getBoundingClientRect();
  view.s=1;
  var want=(mode==="descendants")?"francis-emerson":T.me, focus=null;
  for(var i=0;i<current.cards.length;i++) if(current.cards[i].pid===want){ focus=current.cards[i]; break; }
  view.x=focus? (vr.width/2-(focus.x+CARD_W/2)) : (vr.width-current.W)/2;
  view.y=10;
  applyTransform();
}
function zoomAt(cx,cy,factor){
  var ns=Math.min(Math.max(view.s*factor,0.12),2.5);
  var wx=(cx-view.x)/view.s, wy=(cy-view.y)/view.s;
  view.x=cx-wx*ns; view.y=cy-wy*ns; view.s=ns; applyTransform();
}
function centerOn(pid){
  var node=null;
  for(var i=0;i<current.cards.length;i++) if(current.cards[i].pid===pid){ node=current.cards[i]; break; }
  if(!node) return;
  var vr=viewport.getBoundingClientRect();
  view.x=vr.width/2-(node.x+CARD_W/2)*view.s; view.y=vr.height/2-(node.y+CARD_H/2)*view.s;
  canvas.classList.add("anim"); applyTransform();
  setTimeout(function(){ canvas.classList.remove("anim"); },340);
}

/* ---------- pointer pan + wheel zoom ---------- */
var drag=null;
viewport.addEventListener("pointerdown",function(e){ if(e.target.closest(".ft-pill")||drag) return;
  drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y,moved:false,pid:e.pointerId}; dragged=false; });
viewport.addEventListener("pointermove",function(e){ if(!drag||e.pointerId!==drag.pid) return;
  var dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  if(!drag.moved && Math.abs(dx)+Math.abs(dy)>5){ drag.moved=true; dragged=true;
    viewport.classList.add("dragging"); try{ viewport.setPointerCapture(drag.pid); }catch(_e){} }
  if(!drag.moved) return;
  view.x=drag.vx+dx; view.y=drag.vy+dy; applyTransform(); });
function endDrag(e){ if(!drag||(e&&e.pointerId!==drag.pid)) return; viewport.classList.remove("dragging");
  if(drag.moved) setTimeout(function(){ dragged=false; },60); drag=null; }
viewport.addEventListener("pointerup",endDrag); viewport.addEventListener("pointercancel",endDrag);
window.addEventListener("pointerup",endDrag); window.addEventListener("pointercancel",endDrag);
viewport.addEventListener("wheel",function(e){ e.preventDefault();
  var r=viewport.getBoundingClientRect();
  zoomAt(e.clientX-r.left,e.clientY-r.top, e.deltaY<0?1.12:0.89); },{passive:false});

/* ---------- detail panel ---------- */
var selected=null;
function select(pid,openPanel){
  selected=pid;
  var all=canvas.querySelectorAll(".ft-card");
  for(var j=0;j<all.length;j++){ all[j].classList.toggle("is-focus", all[j].dataset.pid===pid); }
  if(openPanel){ buildPanel(pid); panel.classList.add("open"); }
}
function lb(pid,label){ var b=document.createElement("button"); b.className="lb"; b.textContent=label||nameOf(pid); b.addEventListener("click",function(){ select(pid,true); centerOn(pid); }); return b; }
function buildPanel(pid){
  var p=P[pid], frag=document.createDocumentFragment();
  var eyebrow=document.createElement("p"); eyebrow.className="eyebrow";
  eyebrow.textContent = p.direct? "Direct line" : (parentsOf(pid).length? "Family branch" : "Married into the family");
  frag.appendChild(eyebrow);
  var h=document.createElement("h2"); h.textContent=p.n; frag.appendChild(h);
  var life=document.createElement("div"); life.className="life";
  if(p.living){ life.innerHTML="<b>Living</b>"; }
  else{
    var r1=document.createElement("div"); r1.innerHTML="<b>Born</b> "+esc(p.b||"—"); life.appendChild(r1);
    if(p.bp){ var s1=document.createElement("span"); s1.textContent=p.bp; r1.appendChild(s1); }
    if(p.d&&p.d!=="—"){ var r2=document.createElement("div"); r2.style.marginTop="7px";
      r2.innerHTML="<b>Died</b> "+esc(p.d); life.appendChild(r2);
      if(p.dp){ var s2=document.createElement("span"); s2.textContent=p.dp; r2.appendChild(s2); } }
    if(p.bu){ var r3=document.createElement("div"); r3.style.marginTop="7px";
      r3.innerHTML="<b>Buried</b> "+esc(p.bu); life.appendChild(r3); }
  }
  frag.appendChild(life);
  if(p.note){ var n=document.createElement("div"); n.className="note"+(/flag|open|⚠/.test(p.note)?" flag":""); n.textContent=p.note; frag.appendChild(n); }
  // family
  var fam=document.createElement("div"); fam.className="ft-rel";
  var pr=parentsOf(pid);
  if(pr.length){ var row=document.createElement("div"); row.innerHTML='<span class="lbl">Parents: </span>';
    pr.forEach(function(id,i){ if(i) row.appendChild(document.createTextNode(" · ")); row.appendChild(lb(id)); }); fam.appendChild(row); }
  if(p.sp&&p.sp.length){ var row2=document.createElement("div"); row2.innerHTML='<span class="lbl">'+(p.sp.length>1?"Spouses":"Spouse")+': </span>';
    p.sp.forEach(function(s,i){ if(i) row2.appendChild(document.createTextNode(" · ")); row2.appendChild(lb(s.id));
      var dt=document.createElement("span"); dt.className="lbl"; dt.textContent=s.m&&s.m!=="—"?(" (m. "+s.m+")"):""; row2.appendChild(dt); }); fam.appendChild(row2); }
  var kids=allChildren(p);
  if(kids.length){ var row3=document.createElement("div"); row3.innerHTML='<span class="lbl">Children ('+kids.length+'): </span>';
    kids.forEach(function(id,i){ if(i) row3.appendChild(document.createTextNode(" · ")); row3.appendChild(lb(id)); }); fam.appendChild(row3); }
  if(pr.length){ var sibs=allChildren(P[pr[0]]).filter(function(id){return id!==pid&&P[id];});
    if(sibs.length){ var row4=document.createElement("div"); row4.innerHTML='<span class="lbl">Siblings ('+sibs.length+'): </span>';
      sibs.forEach(function(id,i){ if(i) row4.appendChild(document.createTextNode(" · ")); row4.appendChild(lb(id)); }); fam.appendChild(row4); } }
  if(fam.children.length){ var h3=document.createElement("h3"); h3.textContent="Family"; frag.appendChild(h3); frag.appendChild(fam); }
  // sources
  var h4=document.createElement("h3"); h4.textContent="Sources"; frag.appendChild(h4);
  var ul=document.createElement("ul"); ul.className="srcs";
  (p.src||[]).forEach(function(s){ var li=document.createElement("li"); var a=document.createElement("a");
    a.href=s.u; a.target="_blank"; a.rel="noopener"; a.textContent=s.t; li.appendChild(a);
    var ar=document.createElement("span"); ar.className="arrow"; ar.textContent="↗"; li.appendChild(ar); ul.appendChild(li); });
  var surname=p.m||p.n.split(" ").slice(-1)[0];
  var li2=document.createElement("li"); var a2=document.createElement("a");
  a2.href="https://www.findagrave.com/memorial/search?firstname=&lastname="+encodeURIComponent(surname);
  a2.target="_blank"; a2.rel="noopener"; a2.textContent="Find A Grave search — “"+surname+"”"; li2.appendChild(a2); ul.appendChild(li2);
  var li3=document.createElement("li"); var a3=document.createElement("a");
  a3.href="https://www.wikitree.com/genealogy/"+encodeURIComponent(surname.toUpperCase());
  a3.target="_blank"; a3.rel="noopener"; a3.textContent="WikiTree surname index — "+surname; li3.appendChild(a3); ul.appendChild(li3);
  frag.appendChild(ul);
  // actions
  var acts=document.createElement("div"); acts.className="actions";
  var bCenter=document.createElement("button"); bCenter.className="ft-btn"; bCenter.textContent="Center in tree";
  bCenter.addEventListener("click",function(){ centerOn(pid); }); acts.appendChild(bCenter);
  frag.appendChild(acts);
  panelBody.innerHTML=""; panelBody.appendChild(frag);
}
document.getElementById("ft-panel-close").addEventListener("click",function(){ panel.classList.remove("open"); });
document.addEventListener("keydown",function(e){ if(e.key==="Escape") panel.classList.remove("open"); });

/* ---------- search ---------- */
searchInput.addEventListener("input",function(){
  var q=searchInput.value.trim().toLowerCase();
  results.innerHTML="";
  if(q.length<2){ results.classList.remove("open"); return; }
  var hits=Object.keys(P).filter(function(id){ return P[id].n.toLowerCase().indexOf(q)!==-1; }).slice(0,14);
  if(!hits.length){ results.classList.remove("open"); return; }
  hits.forEach(function(id){ var b=document.createElement("button");
    b.innerHTML=esc(P[id].n)+" <small>· "+esc(shortDates(P[id]))+"</small>";
    b.addEventListener("mousedown",function(e){ e.preventDefault(); });
    b.addEventListener("click",function(){ results.classList.remove("open"); searchInput.value=P[id].n; select(id,true); centerOn(id); });
    results.appendChild(b); });
  results.classList.add("open");
});
document.addEventListener("click",function(e){ if(!e.target.closest(".ft-search")) results.classList.remove("open"); });

/* ---------- toolbar ---------- */
var btnDesc=document.getElementById("ft-mode-desc"), btnAnc=document.getElementById("ft-mode-anc");
function setMode(m){ mode=m; btnDesc.setAttribute("aria-pressed",m==="descendants"?"true":"false");
  btnAnc.setAttribute("aria-pressed",m==="ancestors"?"true":"false"); render(); initialView(); }
btnDesc.addEventListener("click",function(){ setMode("descendants"); });
btnAnc.addEventListener("click",function(){ setMode("ancestors"); });
document.getElementById("ft-zoom-in").addEventListener("click",function(){ var r=viewport.getBoundingClientRect(); zoomAt(r.width/2,r.height/2,1.25); });
document.getElementById("ft-zoom-out").addEventListener("click",function(){ var r=viewport.getBoundingClientRect(); zoomAt(r.width/2,r.height/2,0.8); });
document.getElementById("ft-fit").addEventListener("click",fit);

/* ---------- deep lines section ---------- */
var linesGrid=document.getElementById("ft-lines");
(T.lines||[]).forEach(function(l){
  var el=document.createElement("article"); el.className="ft-line";
  el.innerHTML='<h3>'+esc(l.t)+'</h3><p>'+esc(l.d)+'</p><span class="from'+(l.flag?' warn':'')+'">'+esc(l.from)+(l.flag?(" "+l.flag):"")+'</span>';
  linesGrid.appendChild(el);
});

/* ---------- everyone A–Z index ---------- */
var azWrap=document.getElementById("ft-az");
if(azWrap){
  var groups={}, azTotal=0;
  Object.keys(P).forEach(function(id){
    if(id.indexOf("u-")===0) return;
    var p=P[id]; azTotal++;
    var nm=p.n, toks=nm.replace(/["'][^"']*["']/g,"").replace(/\s+/g," ").trim().split(" ");
    var sur=toks[toks.length-1]||"Other";
    if(/^\(/.test(sur)||/^(Jr\.?|Sr\.?|II|III|IV)$/.test(sur)) sur=toks[toks.length-2]||"Other";
    if(/^Child/.test(nm)) sur="Emerson";
    (groups[sur]=groups[sur]||[]).push(id);
  });
  var countEl=document.getElementById("ft-az-count"); if(countEl) countEl.textContent=azTotal;
  Object.keys(groups).sort().forEach(function(sur){
    var g=document.createElement("div"); g.className="ft-az-group";
    var h=document.createElement("h3"); h.innerHTML=esc(sur)+" <span>"+groups[sur].length+"</span>"; g.appendChild(h);
    var chips=document.createElement("div"); chips.className="ft-az-chips";
    groups[sur].sort(function(a,b){ return P[a].n.localeCompare(P[b].n); }).forEach(function(id){
      var b=document.createElement("button"); b.className="ft-chip"+(P[id].direct?" is-direct":"");
      b.textContent=P[id].n;
      b.title=P[id].living?"Living":((P[id].b&&P[id].b!=="—")?(P[id].b+(P[id].d&&P[id].d!=="—"?" – "+P[id].d:"")):"");
      b.addEventListener("click",function(){ select(id,true); centerOn(id);
        try{ viewport.scrollIntoView({behavior:"smooth",block:"center"}); }catch(_e){} });
      chips.appendChild(b);
    });
    g.appendChild(chips); azWrap.appendChild(g);
  });
}

/* ---------- init ---------- */
render(); initialView();
window.__ft={select:select,fit:fit,setMode:setMode,centerOn:centerOn,data:T,expanded:expanded,childIndex:childIndex,parentsOf:parentsOf,initialView:initialView};
})();
