/* Emerson Family Tree — interactive tree engine.
   No dependencies. Two modes: descendants (frontier → today) and ancestors (Jeanette's
   pedigree). Click any person for full details and every source link. */
(function(){
"use strict";
var T = window.RD_TREE, P = T.people;
var DESC_ROOT = "u-emerson-parents";
var CARD_W=170, CARD_H=88, GAP_X=24, GAP_Y=126, SP_GAP=14, PAD=46;
// Re-rootable: any person can be shown as the head of the descendant tree ("Show tree
// from here" in their panel), so every branch is reachable whichever side it sits on.
var treeRoot=DESC_ROOT;
// Multi-marriage units are clustered apart from simple couples: a dashed frame, one
// colour per marriage (spouse card bar + that marriage's child connectors), extra side spacing.
var CLUSTER_GAP=34, MCOLORS=["#7d9a72","#8a7d9a","#9a8a7d","#6f8f9a"];
function isClusterUnit(n){ return ((n.spids?n.spids.length:(n.spid?1:0))>=2); }

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

/* ---------- relationship to Jeanette (computed for every person) ---------- */
var REL={}, REL_SHORT={};
function computeRel(){
  var ME=T.me;
  function ancM(id){ var m={}, stack=[[id,0]];
    while(stack.length){ var it=stack.pop(), cur=it[0], d=it[1];
      if(m[cur]!==undefined && m[cur]<=d) continue; m[cur]=d;
      parentsOf(cur).forEach(function(pp){ stack.push([pp,d+1]); }); }
    delete m[id]; return m; }
  var meAnc=ancM(ME), desc={};
  (function walk(id,d){ allChildren(P[id]).forEach(function(c){ if(P[c]&&(desc[c]===undefined||desc[c]>d+1)){ desc[c]=d+1; walk(c,d+1); } }); })(ME,0);
  function ord(n){ var s=["","1st","2nd","3rd"]; return s[n]||(n+"th"); }
  function gp(g,s){ if(g===1) return s==="f"?"Mother":"Father"; if(g===2) return s==="f"?"Grandmother":"Grandfather";
    if(g===3) return s==="f"?"Great-grandmother":"Great-grandfather"; return (g-2)+"× great-"+(s==="f"?"grandmother":"grandfather"); }
  function kid(g,s){ if(g===1) return s==="f"?"Daughter":"Son"; if(g===2) return s==="f"?"Granddaughter":"Grandson";
    if(g===3) return s==="f"?"Great-granddaughter":"Great-grandson"; return (g-2)+"× great-"+(s==="f"?"granddaughter":"grandson"); }
  function aun(greats,s){ var t=s==="f"?"aunt":"uncle";
    if(greats===0) return t.charAt(0).toUpperCase()+t.slice(1);
    if(greats===1) return "Great-"+t; return greats+"× great-"+t; }
  function nib(greats,s){ var t=s==="f"?"niece":"nephew";
    if(greats===0) return t.charAt(0).toUpperCase()+t.slice(1);
    if(greats===1) return "Great-"+t; return greats+"× great-"+t; }
  var blood={}; blood[ME]=1;
  for(var id in P){
    var s=P[id].s==="f"?"f":"m";
    if(id===ME){ REL_SHORT[id]="Herself"; REL[id]="Jeanette herself — you are here"; continue; }
    if(id.indexOf("u-")===0){ REL_SHORT[id]="Unknown — end of the line"; REL[id]="Unknown — end of the line"; continue; }
    if(meAnc[id]!==undefined){ REL_SHORT[id]=gp(meAnc[id],s); blood[id]=1; continue; }
    if(desc[id]!==undefined){ REL_SHORT[id]=kid(desc[id],s); blood[id]=1; continue; }
    var pa=ancM(id), best=null, a;
    for(a in meAnc){ if(pa[a]!==undefined){ var tot=meAnc[a]+pa[a];
      if(!best||tot<best.tot||(tot===best.tot&&meAnc[a]<best.a)) best={a:meAnc[a],b:pa[a],tot:tot}; } }
    if(best){
      var A=best.a, B=best.b;
      if(A===1&&B===1) REL_SHORT[id]= s==="f"?"Sister":"Brother";
      else if(A>=2&&B===1) REL_SHORT[id]=aun(A-2,s);
      else if(A===1&&B>=2) REL_SHORT[id]=nib(B-2,s);
      else { var deg=Math.min(A,B)-1, rem=Math.abs(A-B); REL_SHORT[id]=ord(deg)+" cousin"+(rem?" "+rem+"× removed":""); }
      blood[id]=1;
    }
  }
  var rev={};
  function sps(p){ var o=[]; (p.sp||[]).forEach(function(x){ o.push(x.id); });
    (p.fam||[]).forEach(function(f){ if(f.sp) o.push(f.sp); }); return o.filter(function(x){return P[x];}); }
  for(var id2 in P) sps(P[id2]).forEach(function(x){ (rev[x]=rev[x]||[]).push(id2); });
  for(var cid in childIndex){ var ci=childIndex[cid]; if(ci[1]&&P[ci[1]]){ (rev[ci[1]]=rev[ci[1]]||[]); if(rev[ci[1]].indexOf(ci[0])<0) rev[ci[1]].push(ci[0]); } }
  for(var id3 in P){
    if(REL_SHORT[id3]) continue;
    var p3=P[id3], s3=p3.s==="f"?"f":"m";
    var cand=sps(p3).concat(rev[id3]||[]).filter(function(x){return blood[x];});
    if(cand.length){ REL_SHORT[id3]=(s3==="f"?"Wife":"Husband")+" of "+REL_SHORT[cand[0]].toLowerCase(); continue; }
    var kb=allChildren(p3).filter(function(x){return P[x]&&blood[x];});
    if(kb.length){ REL_SHORT[id3]=(s3==="f"?"Mother":"Father")+" of "+REL_SHORT[kb[0]].toLowerCase(); continue; }
    REL_SHORT[id3]="Married into the family";
  }
  for(var id4 in REL_SHORT){
    if(REL[id4]) continue;
    var t4=REL_SHORT[id4];
    REL[id4]= blood[id4] ? ("Jeanette's "+t4.toLowerCase()) : t4.replace(" of "," of Jeanette's ");
  }
}
computeRel();

/* ---------- instance building ---------- */
var expanded={}; // key mode:pid -> bool
function isExpanded(m,pid,depth,node){
  var k=m+":"+pid;
  if(k in expanded) return expanded[k];
  if(m==="descendants") return depth<=1 || !!P[pid].direct;
  return depth<=3;
}
var spouseCache={};
function spouseIdsOf(pid){
  if(spouseCache[pid]) return spouseCache[pid];
  var out=[], seen={}, p=P[pid]||{};
  (p.sp||[]).forEach(function(s){ if(s.id&&s.id!==pid&&P[s.id]&&!seen[s.id]){ seen[s.id]=1; out.push(s.id); } });
  (p.fam||[]).forEach(function(f){ var sid=f.sp; if(sid&&sid!==pid&&P[sid]&&!seen[sid]){ seen[sid]=1; out.push(sid); } });
  // Spouse links are one-sided in these datasets: anyone who lists this person as their
  // spouse is a spouse too, or a second marriage loses its card and its children hang
  // under the wrong couple.
  Object.keys(P).forEach(function(x){ if(x===pid||seen[x]) return;
    (P[x].sp||[]).forEach(function(s){ if(s.id===pid){ seen[x]=1; out.push(x); } });
    if(seen[x]) return;
    (P[x].fam||[]).forEach(function(f){ if(f.sp===pid){ seen[x]=1; out.push(x); } }); });
  return (spouseCache[pid]=out);
}
function mkUnit(m,pid,spid,depth){
  var node={pid:pid,spid:spid,depth:depth,ch:[],key:m+":"+pid};
  // Descendants view: a card for EVERY spouse, in marriage order, so each marriage's
  // children can hang under the right couple. Ancestors view: exactly the two parents.
  node.spids=(m==="descendants")?spouseIdsOf(pid).slice():(spid&&P[spid]?[spid]:[]);
  node.spid=node.spids.length?node.spids[0]:(spid||null);
  node.expanded=isExpanded(m,pid,depth,node);
  return node;
}
function parentsUnit(pid){ var pr=parentsOf(pid); if(!pr.length) return null; return {pid:pr[0],spid:pr[1]||null}; }
function expandChildren(m,node){
  var out=[];
  if(m==="descendants"){
    var seen={};
    var push=function(cid){ if(!P[cid]||cid===node.pid||seen[cid]) return;
      if((node.spids||[]).indexOf(cid)>=0) return; seen[cid]=1; out.push({pid:cid,spid:spouseOf(P[cid])}); };
    allChildren(P[node.pid]).forEach(push);
    // A marriage's children can live in EITHER parent's list: draw the spouse's children
    // too, or a child of a second marriage (Jennifer Ann Harmon) is never drawn at all.
    (node.spids||[]).forEach(function(sid){ allChildren(P[sid]).forEach(push); });
  }
  else{ var u1=parentsUnit(node.pid); if(u1&&P[u1.pid]) out.push(u1);
        if(node.spid){ var u2=parentsUnit(node.spid); if(u2&&P[u2.pid]) out.push(u2); } }
  return out;
}
function countBranch(m,node){
  var n=0; expandChildren(m,node).forEach(function(u){ var k=(m==="descendants")?spouseIdsOf(u.pid).length:(u.spid?1:0); n+=(1+k)+countBranch(m,u); }); return n;
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
function countPidInstances(node,map){ map[node.pid]=(map[node.pid]||0)+1; (node.spids||(node.spid?[node.spid]:[])).forEach(function(sid){ map[sid]=(map[sid]||0)+1; }); node.ch.forEach(function(c){countPidInstances(c,map);}); return map; }

/* ---------- layout ---------- */
function layout(root){
  var cards=[], links=[], pills=[], cursor=0;
  function widthOf(n){ var k=n.spids?n.spids.length:(n.spid?1:0); return CARD_W+k*(CARD_W+SP_GAP); }
  function childAnchorInfo(unit,cid){
    var par=parentsOf(cid), spids=unit.spids||[], i;
    var cardX=function(j){ return unit.x+(j+1)*(CARD_W+SP_GAP)+CARD_W/2; };
    for(i=0;i<spids.length;i++){ if(par.indexOf(spids[i])>=0){
      var other=par.filter(function(x){return x!==spids[i];})[0];
      var both=other&&(other===unit.pid||spids.indexOf(other)>=0);
      // pair centre only when BOTH parents are in this unit; a lone in-unit parent gets
      // the line under their own card (Jennifer under Carlene, not under Robert+Carlene).
      return {x:(i===0&&both)? (unit.x+(CARD_W+SP_GAP)/2+CARD_W/2) : cardX(i), mi:i}; } }
    if(par.indexOf(unit.pid)>=0) return {x:unit.x+CARD_W/2, mi:-1};
    return {x:unit.x+widthOf(unit)/2, mi:-1};
  }
  function place(node){
    var w=widthOf(node), kids=node.expanded?node.ch:[];
    node.y=node.depth*GAP_Y;
    if(!kids.length){ node.x=cursor; cursor+=w+GAP_X; cards.push(node); }
    else{
      var spans=[];
      kids.forEach(function(k,ki){ spans.push(place(k));
        var nk=kids[ki+1];
        if(nk && (isClusterUnit(k)||isClusterUnit(nk))) cursor+=CLUSTER_GAP; });
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
  var clusters=[];
  cards.forEach(function(c){ if(isClusterUnit(c)) clusters.push({x:c.x-12,y:c.y-10,w:widthOf(c)+24,h:CARD_H+20,n:c.spids.length,pid:c.pid}); });
  links.forEach(function(l){ var info=childAnchorInfo(l.from,l.to.pid); l.px=info.x; l.mi=info.mi; l.py=l.from.y+CARD_H; l.cx=l.to.x+CARD_W/2; l.cy=l.to.y; });
  return {cards:cards,links:links,pills:pills,clusters:clusters,W:maxX-minX+2*PAD,H:maxY-minY+2*PAD};
}

/* ---------- render ---------- */
var current=null, dupMap={};
function render(){
  canvas.innerHTML="";
  var root = mode==="descendants" ? buildDesc(treeRoot,null,0) : buildAnc(T.me,null,0);
  dupMap=countPidInstances(root,{});
  current=layout(root);
  var svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("class","ft-links"); svg.setAttribute("width",current.W); svg.setAttribute("height",current.H);
  current.links.forEach(function(l){
    var mid=(l.py+l.cy)/2;
    var path=document.createElementNS("http://www.w3.org/2000/svg","path");
    path.setAttribute("d","M"+l.px+" "+l.py+" V"+mid+" H"+l.cx+" V"+l.cy);
    if(l.direct) path.setAttribute("class","is-direct");
    // each marriage of a multi-marriage unit gets its own colour, matching the spouse card bar
    if(isClusterUnit(l.from)) path.setAttribute("stroke", MCOLORS[(l.mi>=0?l.mi:0)%MCOLORS.length]);
    svg.appendChild(path);
  });
  canvas.appendChild(svg);
  (current.clusters||[]).forEach(function(cl){
    var fr=document.createElement("div"); fr.className="ft-cluster";
    fr.style.left=cl.x+"px"; fr.style.top=cl.y+"px"; fr.style.width=cl.w+"px"; fr.style.height=cl.h+"px";
    var tg=document.createElement("span"); tg.className="ft-cluster-tag"; tg.textContent=cl.n+" marriages";
    fr.appendChild(tg); canvas.appendChild(fr);
  });
  current.cards.forEach(function(c){
    var clu=isClusterUnit(c);
    canvas.appendChild(makeCard(c, c.pid, c.x, c.y, clu?MCOLORS[0]:null));
    (c.spids||[]).forEach(function(sid,i){ if(P[sid]) canvas.appendChild(makeCard(c, sid, c.x+(i+1)*(CARD_W+SP_GAP), c.y, clu?MCOLORS[i%MCOLORS.length]:null)); });
  });
  current.pills.forEach(function(pl){ canvas.appendChild(makePill(pl)); });
  applyTransform();
}
function makeCard(node,pid,x,y,mcolor){
  var p=P[pid], el=document.createElement("div");
  el.className="ft-card"; el.dataset.pid=pid; el.style.left=x+"px"; el.style.top=y+"px";
  if(p.direct) el.classList.add("is-direct");
  if(p.living) el.classList.add("is-living");
  if(pid===T.me) el.classList.add("is-me");
  if(pid.indexOf("u-")===0) el.classList.add("is-unknown");
  if(dupMap[pid]>1) el.classList.add("is-dup");
  var html=(mcolor?'<span class="mbar" style="background:'+mcolor+'"></span>':"")+'<div class="nm">'+esc(p.n)+"</div><div class=\"dt\">"+esc(shortDates(p))+"</div><div class=\"rl\">"+esc(REL_SHORT[pid]||"")+"</div>";
  if(dupMap[pid]>1) html+='<span class="bdg dup" title="This ancestor appears more than once in the tree — the Wesley sisters!">2×</span>';
  if(p.src&&p.src.length) html+='<span class="dot" title="'+p.src.length+' source link'+(p.src.length>1?"s":"")+'"></span>';
  el.innerHTML=html;
  el.title=p.n+((p.b&&p.d&&!p.living)?(" ("+p.b+" – "+p.d+")"):"");
  el.addEventListener("click",function(){ if(!dragged && Date.now()-lastGestureEnd>150) select(pid,true); });
  return el;
}
function makePill(pl){
  var el=document.createElement("div"), node=pl.node;
  var k=(node.spids?node.spids.length:(node.spid?1:0)), uw=CARD_W+k*(CARD_W+SP_GAP);
  el.className="ft-pill"; el.style.top=(node.y+CARD_H+8)+"px";
  if(pl.collapsed){ el.style.left=(node.x+uw/2)+"px"; el.textContent="＋ "+pl.hidden+" more"; }
  else{ el.style.left=(node.x+uw+8)+"px"; el.textContent="− hide"; el.title="Collapse this branch"; }
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
  var want=(mode==="descendants")?(treeRoot===DESC_ROOT?"francis-emerson":treeRoot):T.me, focus=null;
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

/* ---------- pointer pan + pinch/wheel zoom ---------- */
var drag=null, pointers={}, pinch=null, lastTap={t:0,x:0,y:0}, lastGestureEnd=0;
function ptrCount(){ var n=0; for(var k in pointers) n++; return n; }
function ptrAt(i){ var a=[],k; for(k in pointers) a.push(pointers[k]); return a[i]; }
function ptrMid(){ var a=ptrAt(0), b=ptrAt(1); return {x:(a.x+b.x)/2, y:(a.y+b.y)/2}; }
function ptrDist(){ var a=ptrAt(0), b=ptrAt(1); var dx=a.x-b.x, dy=a.y-b.y; return Math.sqrt(dx*dx+dy*dy); }
viewport.addEventListener("pointerdown",function(e){
  if(e.target.closest(".ft-pill")||e.target.closest(".ft-rootbar")) return;
  pointers[e.pointerId]={x:e.clientX,y:e.clientY};
  if(ptrCount()===1){ drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y,moved:false,pid:e.pointerId}; dragged=false; }
  else if(ptrCount()===2){
    drag=null; dragged=true; viewport.classList.add("dragging");
    var r=viewport.getBoundingClientRect(), m=ptrMid();
    pinch={d0:Math.max(ptrDist(),1), s0:view.s, wx:(m.x-r.left-view.x)/view.s, wy:(m.y-r.top-view.y)/view.s};
  }
});
viewport.addEventListener("pointermove",function(e){
  if(!(e.pointerId in pointers)) return;
  pointers[e.pointerId]={x:e.clientX,y:e.clientY};
  if(pinch && ptrCount()>=2){
    var r=viewport.getBoundingClientRect(), m=ptrMid(), d=ptrDist();
    var ns=Math.min(Math.max(pinch.s0*d/pinch.d0,0.12),2.5);
    view.s=ns; view.x=(m.x-r.left)-pinch.wx*ns; view.y=(m.y-r.top)-pinch.wy*ns;
    applyTransform(); return;
  }
  if(!drag||e.pointerId!==drag.pid) return;
  var dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  if(!drag.moved && Math.abs(dx)+Math.abs(dy)>5){ drag.moved=true; dragged=true;
    viewport.classList.add("dragging"); try{ viewport.setPointerCapture(drag.pid); }catch(_e){} }
  if(!drag.moved) return;
  view.x=drag.vx+dx; view.y=drag.vy+dy; applyTransform();
});
function endPtr(e){
  if(e && (e.pointerId in pointers)){
    if(!pinch && !(drag&&drag.moved)){
      var t=Date.now(), r=viewport.getBoundingClientRect();
      if(t-lastTap.t<320 && Math.abs(e.clientX-lastTap.x)<40 && Math.abs(e.clientY-lastTap.y)<40){
        zoomAt(e.clientX-r.left,e.clientY-r.top,1.6);
        lastTap.t=0; dragged=true;
      } else { lastTap={t:t,x:e.clientX,y:e.clientY}; }
    }
    delete pointers[e.pointerId];
  }
  if(ptrCount()<2) pinch=null;
  if(!ptrCount()){ viewport.classList.remove("dragging");
    if(dragged){ lastGestureEnd=Date.now(); } dragged=false; drag=null; }
  else if(!drag && !pinch){ var k; for(k in pointers){} drag={x:pointers[k].x,y:pointers[k].y,vx:view.x,vy:view.y,moved:true,pid:+k}; }
  else if(drag && !(drag.pid in pointers)) drag=null;
}
viewport.addEventListener("pointerup",endPtr); viewport.addEventListener("pointercancel",endPtr);
window.addEventListener("pointerup",endPtr); window.addEventListener("pointercancel",endPtr);
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
  var p=P[pid]; if(!p) return;
  var frag=document.createDocumentFragment();
  var eyebrow=document.createElement("p"); eyebrow.className="eyebrow";
  eyebrow.textContent = p.direct? "Direct line" : (parentsOf(pid).length? "Family branch" : "Married into the family");
  frag.appendChild(eyebrow);
  var h=document.createElement("h2"); h.textContent=p.n; frag.appendChild(h);
  var relLine=document.createElement("p"); relLine.className="rel"; relLine.textContent=REL[pid]||""; frag.appendChild(relLine);
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
  if(p.photos&&p.photos.length){
    var phH=document.createElement("h3"); phH.textContent="Photos"; frag.appendChild(phH);
    var phWrap=document.createElement("div"); phWrap.className="ft-photos";
    p.photos.forEach(function(pho){
      var fig=document.createElement("figure"); fig.className="ft-photo";
      var pa=document.createElement("a"); pa.href=pho.link; pa.target="_blank"; pa.rel="noopener";
      var im=document.createElement("img"); im.src=pho.u; im.alt=p.n+" — "+(pho.t||"photo (Find A Grave)"); im.loading="lazy";
      pa.appendChild(im); fig.appendChild(pa);
      var cap=document.createElement("figcaption"); cap.textContent=(pho.t||"Find A Grave"); fig.appendChild(cap);
      phWrap.appendChild(fig);
    });
    frag.appendChild(phWrap);
  }
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
  var sibs=[];
  if(pr.length){ var seenSib={};
    pr.forEach(function(pn){ allChildren(P[pn]).forEach(function(id){ if(id!==pid&&P[id]&&!seenSib[id]){ seenSib[id]=1; sibs.push(id); } }); });
  }
    if(sibs.length){ var row4=document.createElement("div"); row4.innerHTML='<span class="lbl">Siblings ('+sibs.length+'): </span>';
      sibs.forEach(function(id,i){ if(i) row4.appendChild(document.createTextNode(" · ")); row4.appendChild(lb(id)); }); fam.appendChild(row4); }
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
  var bTree=document.createElement("button"); bTree.className="ft-btn";
  bTree.textContent=(mode==="descendants"&&treeRoot===pid)?"Showing this tree":"Show tree from here";
  bTree.title="Rebuild the tree with "+p.n+" as the head — see all of their descendants, spouses and in-laws";
  bTree.addEventListener("click",function(){ setTreeRoot(pid); });
  acts.appendChild(bTree);
  frag.appendChild(acts);
  panelBody.innerHTML=""; panelBody.appendChild(frag);
}
document.getElementById("ft-panel-close").addEventListener("click",function(){ panel.classList.remove("open"); });

/* ---------- re-root: show the tree from any person ---------- */
var rootBar=document.getElementById("ft-rootbar"), rootBarTxt=document.getElementById("ft-rootbar-txt"),
    rootBarReset=document.getElementById("ft-rootbar-reset");
function updateRootBar(){
  if(!rootBar) return;
  var showing=(mode==="descendants" && treeRoot!==DESC_ROOT);
  rootBar.hidden=!showing;
  if(showing) rootBarTxt.textContent="Showing the tree from "+nameOf(treeRoot);
}
function setTreeRoot(pid){
  if(!P[pid]) return;
  treeRoot=pid;
  setMode("descendants");
  updateRootBar();
  select(pid,false); centerOn(pid);
}
if(rootBarReset) rootBarReset.addEventListener("click",function(){ treeRoot=DESC_ROOT; setMode("descendants"); updateRootBar(); });
document.addEventListener("keydown",function(e){ if(e.key==="Escape") panel.classList.remove("open"); });

/* ---------- search ---------- */
searchInput.addEventListener("input",function(){
  var q=searchInput.value.trim().toLowerCase();
  results.innerHTML="";
  if(q.length<2){ results.classList.remove("open"); return; }
  var hits=Object.keys(P).filter(function(id){ return P[id].n.toLowerCase().indexOf(q)!==-1; }).slice(0,14);
  if(!hits.length){ results.classList.remove("open"); return; }
  hits.forEach(function(id){ var b=document.createElement("button");
    b.innerHTML=esc(P[id].n)+" <small>· "+esc(REL_SHORT[id]||shortDates(P[id]))+"</small>";
    b.addEventListener("mousedown",function(e){ e.preventDefault(); });
    b.addEventListener("click",function(){ results.classList.remove("open"); searchInput.value=P[id].n; select(id,true); centerOn(id); });
    results.appendChild(b); });
  results.classList.add("open");
});
document.addEventListener("click",function(e){ if(!e.target.closest(".ft-search")) results.classList.remove("open"); });

/* ---------- toolbar ---------- */
var btnDesc=document.getElementById("ft-mode-desc"), btnAnc=document.getElementById("ft-mode-anc");
function setMode(m){ mode=m; btnDesc.setAttribute("aria-pressed",m==="descendants"?"true":"false");
  btnAnc.setAttribute("aria-pressed",m==="ancestors"?"true":"false");
  allOn=false; var be=document.getElementById("ft-expand-all");
  if(be){ be.setAttribute("aria-pressed","false"); be.textContent="Expand all"; }
  render(); initialView(); updateRootBar(); }
btnDesc.addEventListener("click",function(){ setMode("descendants"); });
btnAnc.addEventListener("click",function(){ setMode("ancestors"); });
document.getElementById("ft-zoom-in").addEventListener("click",function(){ var r=viewport.getBoundingClientRect(); zoomAt(r.width/2,r.height/2,1.25); });
document.getElementById("ft-zoom-out").addEventListener("click",function(){ var r=viewport.getBoundingClientRect(); zoomAt(r.width/2,r.height/2,0.8); });
document.getElementById("ft-fit").addEventListener("click",fit);
/* ---------- expand all / collapse all ---------- */
var btnExpand=document.getElementById("ft-expand-all"), allOn=false;
function setAllExpanded(on){
  Object.keys(P).forEach(function(pid){ var k=mode+":"+pid; if(on){ expanded[k]=true; } else { delete expanded[k]; } });
  allOn=on;
  if(btnExpand){ btnExpand.setAttribute("aria-pressed",on?"true":"false"); btnExpand.textContent=on?"Collapse all":"Expand all"; }
  render(); if(on){ fit(); } else { initialView(); }
}
if(btnExpand) btnExpand.addEventListener("click",function(){ setAllExpanded(!allOn); });

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
    var nm=p.n, toks=nm.replace(/[“”‘’"']+[^“”‘’"']*[“”‘’"']/g,"").replace(/[“”‘’]/g,"").replace(/\s+/g," ").trim().split(" ");
    var sur=toks[toks.length-1]||"Other";
    if(/^\(/.test(sur)||/^(Jr\.?|Sr\.?|II|III|IV)$/.test(sur)) sur=toks[toks.length-2]||"Other"; if(!sur||!/[A-Za-z]/.test(sur)) sur="Other";
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
      var rs=document.createElement("span"); rs.className="rl"; rs.textContent=REL_SHORT[id]||""; b.appendChild(rs);
      b.title=P[id].living?"Living":((P[id].b&&P[id].b!=="—")?(P[id].b+(P[id].d&&P[id].d!=="—"?" – "+P[id].d:"")):"");
      b.addEventListener("click",function(){ select(id,true); centerOn(id);
        try{ viewport.scrollIntoView({behavior:"smooth",block:"center"}); }catch(_e){} });
      chips.appendChild(b);
    });
    g.appendChild(chips); azWrap.appendChild(g);
  });
}

/* ---------- init ---------- */
render(); initialView(); updateRootBar();
window.__ft={select:select,fit:fit,setMode:setMode,setAllExpanded:setAllExpanded,centerOn:centerOn,data:T,expanded:expanded,childIndex:childIndex,parentsOf:parentsOf,initialView:initialView,setTreeRoot:setTreeRoot,getRoot:function(){return treeRoot;},isClusterUnit:isClusterUnit};
})();
