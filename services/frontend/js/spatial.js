
/* ====================== data ====================== */
let ASSETS = [
  {id:"AST-01", name:"Naharkatiya Block", short:"Naharkatiya", type:"Onshore field", glyph:"◇", region:"Assam", lon:95.35, lat:27.28, review:9, gaps:4, total:14},
  {id:"AST-02", name:"Moran Gathering Stn.", short:"Moran", type:"Onshore installation", glyph:"◈", region:"Assam", lon:94.90, lat:27.05, review:10, gaps:6, total:16},
  {id:"AST-03", name:"Rig OIL-D-12", short:"OIL-D-12", type:"Drilling rig", glyph:"⌬", region:"Assam", lon:95.95, lat:27.62, review:8, gaps:3, total:11},
  {id:"AST-04", name:"Kumchai Field", short:"Kumchai", type:"Onshore field", glyph:"◇", region:"Assam", lon:96.35, lat:27.40, review:1, gaps:1, total:5},
  {id:"AST-05", name:"Jorhat Compressor", short:"Jorhat", type:"Onshore installation", glyph:"◈", region:"Assam", lon:94.20, lat:26.70, review:3, gaps:2, total:8},
  {id:"AST-06", name:"Block SY-03", short:"SY-03", type:"Offshore block", glyph:"⬡", region:"KG Offshore", lon:84.20, lat:16.30, review:7, gaps:5, total:12},
  {id:"AST-07", name:"Jaisalmer Prospect", short:"Jaisalmer", type:"Onshore exploration", glyph:"△", region:"Rajasthan", lon:71.30, lat:26.90, review:3, gaps:2, total:6}
];

let REPORTS = [
  {id:"RPT-2214", asset:"AST-01", excerpt:"Suspended load passed inches from a worker; exclusion zone set after the lift", reason:"Unreviewed 18 days", review:"Not reviewed", state:"Serious-risk candidate", proc:"Complete", s:"awaiting", exposure:"Person within swing radius — supported", control:"Exclusion-zone timing not established", gap:"Lift plan timestamp missing from narrative"},
  {id:"RPT-2189", asset:"AST-01", excerpt:"Isolation certificate referenced, verification step not described", reason:"Missing control fact", review:"Not reviewed", state:"Needs information", proc:"Complete", s:"gap", exposure:"Stored energy exposure — plausible", control:"Verification of isolation not described", gap:"No permit reference in source"},
  {id:"RPT-2170", asset:"AST-01", excerpt:"Trip hazard near walkway; barrier tape in place", reason:"Review older than 90 days", review:"Stale", state:"Low potential", proc:"Complete", s:"stale", exposure:"Slip/trip exposure — low", control:"Barrier in place at time of report", gap:"None"},
  {id:"RPT-2166", asset:"AST-01", excerpt:"Statements conflict on whether the line was depressurised", reason:"Conflicting evidence", review:"Not reviewed", state:"Unresolved", proc:"Complete", s:"gap", exposure:"Pressure release exposure — contested", control:"Two accounts disagree on depressurisation", gap:"Conflict unresolved between witnesses"},
  {id:"RPT-2151", asset:"AST-02", excerpt:"Gas release during pigging; detector reading not stated", reason:"Analysis failed", review:"Not reviewed", state:"Unprocessed", proc:"Failed", s:"failed", exposure:"—", control:"—", gap:"Extraction failed on attachment 2"},
  {id:"RPT-2140", asset:"AST-02", excerpt:"Vehicle reversed toward pipeline crew; no spotter present", reason:"Unreviewed 22 days", review:"Not reviewed", state:"Serious-risk candidate", proc:"Complete", s:"awaiting", exposure:"Vehicle–person exposure — supported", control:"Spotter control absent", gap:"Reversing distance not stated"},
  {id:"RPT-2137", asset:"AST-02", excerpt:"Scaffold handover sheet uploaded; parsing in progress", reason:"Processing", review:"Not reviewed", state:"Processing", proc:"Processing", s:"processing", exposure:"—", control:"—", gap:"Awaiting extraction"},
  {id:"RPT-2132", asset:"AST-03", excerpt:"Drill pipe swung free of the elevator during make-up", reason:"Unreviewed 11 days", review:"Not reviewed", state:"Serious-risk candidate", proc:"Complete", s:"awaiting", exposure:"Dropped/swinging object — supported", control:"Elevator latch check not evidenced", gap:"Latch inspection record not attached"},
  {id:"RPT-2129", asset:"AST-03", excerpt:"Hot work permit mentioned; atmosphere test unknown", reason:"Missing control fact", review:"Stale", state:"Needs information", proc:"Complete", s:"stale", exposure:"Ignition exposure — plausible", control:"Gas test result not recorded", gap:"Atmosphere reading absent"},
  {id:"RPT-2118", asset:"AST-06", excerpt:"Crane boom contacted railing during stores transfer", reason:"Processing failed", review:"Not reviewed", state:"Unprocessed", proc:"Failed", s:"failed", exposure:"—", control:"—", gap:"Model returned an error on retry 3"},
  {id:"RPT-2104", asset:"AST-06", excerpt:"Basket transfer continued after wind limit exceeded", reason:"Unreviewed 9 days", review:"Not reviewed", state:"Serious-risk candidate", proc:"Complete", s:"awaiting", exposure:"Fall from height — supported", control:"Wind-limit stop not applied", gap:"Recorded wind speed not in source"},
  {id:"RPT-2101", asset:"AST-06", excerpt:"Deck lighting outage logged and repaired same shift", reason:"Reviewed 4 days ago", review:"Current", state:"Controls reported", proc:"Complete", s:"reviewed", exposure:"Low-visibility exposure — minor", control:"Repair completed and verified", gap:"None"},
  {id:"RPT-2097", asset:"AST-05", excerpt:"Hydraulic weep on compressor skid; isolated and tagged", reason:"Review older than 90 days", review:"Stale", state:"Low potential", proc:"Complete", s:"stale", exposure:"Fluid release — low", control:"Isolated and tagged", gap:"None"},
  {id:"RPT-2071", asset:"AST-04", excerpt:"Ladder inspection overdue; task stopped before use", reason:"Reviewed 11 days ago", review:"Current", state:"Controls reported", proc:"Complete", s:"reviewed", exposure:"Fall exposure — avoided", control:"Task stopped before use", gap:"None"},
  {id:"RPT-2063", asset:"AST-07", excerpt:"Excavation near buried service; scan record not attached", reason:"Missing control fact", review:"Not reviewed", state:"Needs information", proc:"Complete", s:"gap", exposure:"Buried-service contact — plausible", control:"Scan record not attached", gap:"No utility survey reference"},
  {id:"RPT-2085", asset:null, excerpt:"Confined space entry described without site identification", reason:"Site unassigned", review:"Not reviewed", state:"Needs information", proc:"Complete", s:"gap", exposure:"Confined-space exposure — plausible", control:"Entry controls not described", gap:"No site named in the narrative"}
];

let UNMAPPED = [
  {id:"AST-08", name:"Dibrugarh Terminal", why:"No coordinates in register"},
  {id:"AST-09", name:"Barmer Gathering Line", why:"Geometry pending survey"}
];

const LENSES = [
  {key:"review", label:"Review attention"},
  {key:"gaps",   label:"Information gaps"},
  {key:"all",    label:"All assets"}
];

const STATE_LABEL = {awaiting:"Awaiting review", stale:"Stale review", reviewed:"Reviewed", gap:"Needs information", processing:"Processing", failed:"Analysis failed"};
const AI_VERBS = ["reading source","locating exposure phrase","checking control timing","mapping to rule set","forming candidate"];

/* ---- Evidence graph wiring ---- */
const graphLink = id => `<a class="tbtn" href="evidence.html?report=${encodeURIComponent(id)}">Evidence graph \u2197</a>`;


/* ====================== state ====================== */
const S = {
  lens:"review", sel:null, rep:null, hover:null, hoverRep:null,
  filter:null, unavailable:false, wb:false, ai:false, k:1
};
let projection, path, curT = d3.zoomIdentity, zoom, indiaFeature, W = 0, H = 0;

const $ = s => document.querySelector(s);
const el = (t,c,h) => { const e=document.createElement(t); if(c) e.className=c; if(h!=null) e.innerHTML=h; return e; };
const repsOf = id => REPORTS.filter(r => r.asset === id);
const lensCount = a => lensReports(a).length;
const lensReports = a => {
  const rs = repsOf(a.id);
  if (S.lens === "review") return rs.filter(r => r.s === "awaiting" || r.s === "stale");
  if (S.lens === "gaps") return rs.filter(r => r.s === "gap" || r.s === "failed" || r.s === "processing");
  return rs;
};
const visibleAssets = () => {
  if (S.filter === "none") return [];
  let list = ASSETS.slice();
  return list.filter(a => S.lens === "all" || lensReports(a).length > 0 || a.id === S.sel);
};

/* ====================== map ====================== */
const mapEl = $("#map");
const svg = d3.select(mapEl).append("svg");
const gRoot = svg.append("g");
const gGeo = gRoot.append("g");

function sizeMap(){
  const r = mapEl.getBoundingClientRect(); W = r.width; H = r.height;
  svg.attr("viewBox", `0 0 ${W} ${H}`);
}

let ro = null;
function remeasure(){
  sizeMap();
  if (!W || !H) return false;
  if (projection){ fitProjection(); redrawGeo(); render(); }
  return true;
}

async function boot(){
  sizeMap();
  ro = new ResizeObserver(() => remeasure());
  ro.observe(mapEl);
  try{
    const topo = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json").then(r=>r.json());
    const all = topojson.feature(topo, topo.objects.countries);
    indiaFeature = all.features.find(f => f.properties.name === "India");
    projection = d3.geoMercator();
    path = d3.geoPath(projection);
    fitToAssets(false);
    gGeo.selectAll("path.land").data(all.features.filter(f=>f.properties.name!=="India")).join("path").attr("class","land").attr("d",path);
    gGeo.append("path").attr("class","graticule").attr("d", path(d3.geoGraticule().step([5,5])()));
    gGeo.append("path").attr("class","india").attr("d", path(indiaFeature));
  }catch(e){
    console.warn("basemap failed", e);
    setUnavailable(true);
    projection = d3.geoMercator().center([82,22]).scale(900).translate([W/2,H/2]);
  }
  zoom = d3.zoom().scaleExtent([0.7, 14]).on("zoom", ev => {
    curT = ev.transform; S.k = ev.transform.k;
    gRoot.attr("transform", ev.transform);
    parallax(ev.transform);
    render();
  });
  svg.call(zoom).on("dblclick.zoom", null);
  mapEl.addEventListener("pointerdown", ()=>mapEl.classList.add("drag"));
  window.addEventListener("pointerup", ()=>mapEl.classList.remove("drag"));
  window.addEventListener("resize", remeasure);
  window.addEventListener("load", () => remeasure());
  document.addEventListener("visibilitychange", () => remeasure());
  mapEl.addEventListener("pointerdown", () => remeasure(), {once:false});
  mapEl.addEventListener("wheel", () => remeasure(), {passive:true});
  let tries = 0;
  const poll = setInterval(() => {
    tries++;
    if ((remeasure() && W > 0) || tries > 60) clearInterval(poll);
  }, 100);
  requestAnimationFrame(() => remeasure());
  renderLens(); renderRibbon(); render();
}

function redrawGeo(){
  if (!path || !indiaFeature) return;
  gGeo.selectAll("path.land").attr("d", path);
  gGeo.select("path.graticule").attr("d", path(d3.geoGraticule().step([5,5])()));
  gGeo.select("path.india").attr("d", path(indiaFeature));
}

function fitProjection(){
  const pad = 44;
  const box = {type:"MultiPoint", coordinates: ASSETS.map(a=>[a.lon,a.lat])};
  projection.fitExtent([[pad+58,pad+30],[W-pad-40,H-pad-56]], indiaFeature || box);
}

function fitToAssets(animate){
  const pad = 44;
  const lons = ASSETS.map(a=>a.lon), lats = ASSETS.map(a=>a.lat);
  const box = {type:"MultiPoint", coordinates: ASSETS.map(a=>[a.lon,a.lat])};
  fitProjection();
  redrawGeo();
  if (zoom) { if (animate) animateTo(d3.zoomIdentity, 680); else svg.call(zoom.transform, d3.zoomIdentity); }
  else { curT = d3.zoomIdentity; render(); }
}

function xy(lon,lat){ const p = projection([lon,lat]); return p ? curT.apply(p) : [0,0]; }

let camTimer = null;
function animateTo(target, dur){
  if (!zoom) return;
  if (camTimer) clearInterval(camTimer);
  const from = curT, t0 = performance.now(), D = dur || 720;
  const iv = d3.interpolateZoom([from.x, from.y, from.k], [target.x, target.y, target.k]);
  camTimer = setInterval(() => {
    const u = Math.min(1, (performance.now() - t0) / D);
    const e = u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u+2, 3)/2;
    const a = from.x + (target.x - from.x) * e,
          b = from.y + (target.y - from.y) * e,
          k = from.k + (target.k - from.k) * e;
    svg.call(zoom.transform, d3.zoomIdentity.translate(a, b).scale(k));
    if (u >= 1){ clearInterval(camTimer); camTimer = null; }
  }, 16);
}
function flyTo(lon,lat,k,dur){
  if (!zoom) return;
  const p = projection([lon,lat]);
  animateTo(d3.zoomIdentity.translate(W/2 - p[0]*k, (H/2-30) - p[1]*k).scale(k), dur);
}

function parallax(t){
  const dx = (t.x)*0.04, dy = (t.y)*0.04;
  $("#b1").style.transform = `translate(${dx}px,${dy}px)`;
  $("#b2").style.transform = `translate(${-dx*0.7}px,${dy*0.5}px)`;
  $("#b3").style.transform = `translate(${dx*0.5}px,${-dy*0.6}px)`;
}

/* ====================== clustering ====================== */
function computeMarks(){
  const list = visibleAssets().map(a => ({a, p: xy(a.lon,a.lat)}));
  const GAP = 62, out = [];
  list.forEach(item => {
    if (S.sel === item.a.id) { out.push({kind:"asset", a:item.a, p:item.p}); return; }
    const hit = out.find(o => o.kind==="cluster" ? Math.hypot(o.p[0]-item.p[0], o.p[1]-item.p[1]) < GAP : (o.a.id!==S.sel && Math.hypot(o.p[0]-item.p[0], o.p[1]-item.p[1]) < GAP));
    if (hit && !S.sel){
      if (hit.kind === "asset"){ const first = hit.a; hit.kind="cluster"; hit.items=[first,item.a]; }
      else hit.items.push(item.a);
      const xs = hit.items.map(a=>xy(a.lon,a.lat));
      hit.p = [d3.mean(xs,d=>d[0]), d3.mean(xs,d=>d[1])];
    } else out.push({kind:"asset", a:item.a, p:item.p});
  });
  return out;
}

/* ====================== render ====================== */
function render(){
  renderCrumb();
  renderBeacons();
  renderConstellation();
  positionThread();
  const anyLens = visibleAssets().length;
  $("#empty").classList.toggle("on", anyLens === 0 && !S.unavailable);
  $("#idSub").textContent = `${ASSETS.length} assets · ${REPORTS.length} reports · lens ${LENSES.find(l=>l.key===S.lens).label.toLowerCase()}`;
}

function renderBeacons(){
  const host = $("#beacons"); host.innerHTML = "";
  if (S.unavailable) return;
  computeMarks().forEach(m => {
    const b = el("div","beacon");
    b.dataset.l = S.lens;
    b.style.left = m.p[0]+"px"; b.style.top = m.p[1]+"px";
    if (m.kind === "cluster"){
      b.classList.add("cluster");
      const n = d3.sum(m.items, a=>lensCount(a));
      b.innerHTML = `<div class="bcore"><span class="glyph">${m.items.length}</span><span class="cnt">${n}</span></div>
        <div class="blab">${m.items.length} assets · ${m.items[0].region}<span class="sub">click to expand</span></div>`;
      b.onclick = () => {
        const lon = d3.mean(m.items,a=>a.lon), lat = d3.mean(m.items,a=>a.lat);
        flyTo(lon, lat, Math.max(4, S.k*2.4));
      };
    } else {
      const a = m.a, c = lensCount(a), rs = lensReports(a);
      if (S.sel && S.sel !== a.id) b.classList.add("recede");
      if (S.sel === a.id) b.classList.add("sel");
      if (c >= 7) b.classList.add("show-lab");
      b.innerHTML = `<div class="bcore"><span class="glyph">${a.glyph}</span>${c?`<span class="cnt">${c}</span>`:""}
          <svg class="arc" width="1" height="1" viewBox="-26 -26 52 52">${arcPaths(a)}</svg>
        </div>
        <div class="blab">${a.short}<span class="sub">${a.type.toUpperCase()}</span></div>`;
      b.onmouseenter = () => { S.hover = a.id; highlightRibbon(a.id, true); };
      b.onmouseleave = () => { S.hover = null; highlightRibbon(a.id, false); };
      b.onclick = () => selectAsset(a.id);
      b.tabIndex = 0;
      b.onkeydown = e => { if (e.key === "Enter") selectAsset(a.id); };
    }
    host.appendChild(b);
  });
}

function arcPaths(a){
  const rs = repsOf(a.id), counts = {};
  rs.forEach(r => counts[r.s] = (counts[r.s]||0)+1);
  const col = {awaiting:"#5b3df5", stale:"#b5730b", reviewed:"#0d8467", gap:"#5a5a6a", processing:"#8b8b9c", failed:"#c0392b"};
  const total = rs.length || 1; let a0 = -Math.PI/2, out = "";
  Object.keys(counts).forEach(k => {
    const a1 = a0 + (counts[k]/total) * Math.PI*2;
    const arc = d3.arc()({innerRadius:20, outerRadius:23.5, startAngle:a0+0.06, endAngle:a1-0.06});
    out += `<path d="${arc}" fill="${col[k]}" opacity=".85"></path>`;
    a0 = a1;
  });
  return out;
}

/* ---------- constellation ---------- */
function renderConstellation(){
  const host = $("#constel"), links = $("#links");
  host.innerHTML = ""; links.innerHTML = "";
  if (!S.sel || S.unavailable) return;
  const a = ASSETS.find(x=>x.id===S.sel);
  const rs = lensReports(a).length ? lensReports(a) : repsOf(a.id);
  const c = xy(a.lon,a.lat);
  const R = Math.min(150, Math.max(104, 40 + rs.length*15));
  rs.forEach((r,i) => {
    const ang = -Math.PI/2 + (i/rs.length)*Math.PI*2;
    const x = c[0] + Math.cos(ang)*R, y = c[1] + Math.sin(ang)*R;
    r._x = x; r._y = y;
    const ln = document.createElementNS("http://www.w3.org/2000/svg","line");
    ln.setAttribute("x1",c[0]); ln.setAttribute("y1",c[1]); ln.setAttribute("x2",x); ln.setAttribute("y2",y);
    ln.setAttribute("stroke", S.rep===r.id ? "rgba(91,61,245,.55)" : "rgba(20,20,32,.22)");
    ln.setAttribute("stroke-width", S.rep===r.id ? 1.6 : 1);
    ln.setAttribute("stroke-dasharray", r.s==="gap" ? "3 3" : "none");
    links.appendChild(ln);

    const n = el("button","rnode"+(S.rep===r.id?" act":""),"<i></i>");
    n.dataset.s = r.s; n.style.left = x+"px"; n.style.top = y+"px";
    n.style.animationDelay = (i*38)+"ms";
    n.onmouseenter = e => showTip(r, x, y);
    n.onmouseleave = hideTip;
    n.onclick = () => openReport(r.id);
    host.appendChild(n);

    const lab = el("div","rlab", `${r.id.replace("RPT-","")} · ${STATE_LABEL[r.s].toLowerCase()}`);
    const lx = c[0] + Math.cos(ang)*(R+34), ly = c[1] + Math.sin(ang)*(R+34);
    lab.style.left = lx+"px"; lab.style.top = ly+"px";
    host.appendChild(lab);
  });
  const core = el("div","rlab", a.name.toUpperCase());
  core.style.left = c[0]+"px"; core.style.top = (c[1]+34)+"px";
  core.style.fontSize = "10px"; core.style.letterSpacing = ".14em";
  host.appendChild(core);
}

function showTip(r,x,y){
  const t = $("#tip");
  t.innerHTML = `<div class="id">${r.id}</div>
    <div class="ex">“${r.excerpt}”</div>
    <div class="row"><span>Candidate state</span><b style="font-weight:500">${r.state}</b></div>
    <div class="row"><span>Needs attention</span><b style="font-weight:500">${r.reason}</b></div>`;
  t.classList.add("on");
  const w = 270, h = t.offsetHeight;
  t.style.left = Math.min(Math.max(10, x - w/2), W - w - 10) + "px";
  t.style.top = (y - h - 22 < 10 ? y + 24 : y - h - 22) + "px";
}
const hideTip = () => $("#tip").classList.remove("on");

/* ---------- selection ---------- */
function renderCrumb(){
  const cr = $("#crumb");
  const a = ASSETS.find(x=>x.id===S.sel);
  if (!a){ cr.classList.remove("on"); cr.innerHTML = ""; return; }
  cr.classList.add("on");
  cr.innerHTML = `<span class="kicker">Selected</span><b style="font-weight:500">${a.name}</b>
    <span class="mono" style="font-size:10px;color:var(--ink-3)">${a.region} · ${lensReports(a).length} in lens</span>
    <button class="x" title="Clear selection">✕</button>`;
  cr.querySelector(".x").onclick = clearSelection;
}

function selectAsset(id, keepCam){
  S.sel = id; S.rep = null; closeThread();
  const a = ASSETS.find(x=>x.id===id);
  if (!keepCam) flyTo(a.lon, a.lat, Math.max(3.2, S.k));
  renderRibbon(); render();
}
function clearSelection(){ S.sel = null; S.rep = null; closeThread(); renderRibbon(); render(); }

/* ---------- evidence thread ---------- */
function openReport(id){
  S.rep = id; hideTip();
  const r = REPORTS.find(x=>x.id===id);
  const steps = threadSteps(r);
  const t = $("#thread");
  t.innerHTML = `<h4><span style="width:8px;height:8px;border-radius:50%;background:var(--violet);display:inline-block"></span>${r.id}
      <span class="mono" style="margin-left:auto;font-size:9.5px;color:var(--ink-3)">${STATE_LABEL[r.s].toUpperCase()}</span></h4>
    <div class="steps">${steps.map((s,i)=>`<button class="step" data-i="${i}">
        <span class="mk2"><b style="background:${s.c}"></b></span>
        <span class="tx"><span class="lb">${s.lb}</span>${s.tx}<span class="src"> ↗ ${s.src}</span></span></button>`).join("")}</div>
    <div id="oprec"><span>⌘</span><span>operation record · 5 steps · 1.2s · <a href="#" onclick="return false">inspect</a></span></div>
    <div id="aiverb"><span class="sp"></span><span class="v"></span></div>
    <div class="threadfoot">
      <button class="tbtn pri" id="openWb">Open Workbench</button>
      <button class="tbtn" id="aiBtn">AI inspection</button>
      <button class="tbtn" id="closeThread">Close</button>
      ${graphLink(r.id)}
    </div>`;
  t.classList.add("on");
  t.querySelectorAll(".step").forEach(b => b.onclick = () => {
    t.querySelectorAll(".step").forEach(x=>x.classList.remove("em"));
    b.classList.add("em");
  });
  $("#openWb").onclick = () => openWorkbench(r.id);
  $("#aiBtn").onclick = () => runAI(r.id);
  $("#closeThread").onclick = closeThread;
  positionThread();
  renderConstellation();
}
function closeThread(){ S.rep = null; $("#thread").classList.remove("on"); renderConstellation(); }

function positionThread(){
  const t = $("#thread");
  if (!S.rep || !t.classList.contains("on")) return;
  const r = REPORTS.find(x=>x.id===S.rep);
  if (r._x == null) return;
  const w = 296, h = t.offsetHeight || 320;
  let x = r._x + 26, y = r._y - h/2;
  if (x + w > W - 16) x = r._x - w - 26;
  y = Math.min(Math.max(56, y), Math.max(56, H - h - 76));
  t.style.left = x+"px"; t.style.top = y+"px";
}

function threadSteps(r){
  return [
    {lb:"Original narrative", tx:`“${r.excerpt}”`, src:"source doc p.1", c:"var(--ink)"},
    {lb:"Relevant exposure", tx:r.exposure, src:"phrase span 42–71", c:"var(--violet)"},
    {lb:"Control evidence", tx:r.control, src:"permit register", c:"var(--teal)"},
    {lb:"Information gap", tx:r.gap, src:"extraction log", c:"var(--amber)"},
    {lb:"Model candidate", tx:r.state, src:"rule SIF-04", c:"var(--violet)"},
    {lb:"Human review", tx:`${r.review} · ${r.reason}`, src:"review ledger", c:"var(--rose)"}
  ];
}

/* ---------- AI inspection ---------- */
function runAI(id){
  if (S.ai) return; S.ai = true;
  const t = $("#thread"), steps = [...t.querySelectorAll(".step")], verb = $("#aiverb");
  verb.classList.add("on"); $("#oprec").classList.remove("on");
  let i = 0;
  const tick = () => {
    steps.forEach(s=>s.classList.remove("em"));
    if (i >= AI_VERBS.length){
      verb.classList.remove("on"); S.ai = false;
      $("#oprec").classList.add("on");
      return;
    }
    steps[i].classList.add("em");
    verb.querySelector(".v").textContent = AI_VERBS[i];
    i++; setTimeout(tick, 780);
  };
  tick();
}

/* ====================== lens ====================== */
function renderLens(){
  const host = $("#lens"); host.innerHTML = "";
  LENSES.forEach(l => {
    const n = REPORTS.filter(r => l.key==="review" ? (r.s==="awaiting"||r.s==="stale") : l.key==="gaps" ? (r.s==="gap"||r.s==="failed"||r.s==="processing") : true).length;
    const b = el("button","lensbtn"+(S.lens===l.key?" on":""), `${l.label}<span class="n">${n}</span>`);
    b.onclick = () => setLens(l.key);
    host.appendChild(b);
  });
}
function setLens(k){
  if (S.lens === k) return;
  S.lens = k; S.rep = null; closeThread();
  const sw = $("#sweep");
  sw.classList.remove("run"); void sw.offsetWidth; sw.classList.add("run");
  $("#beacons").style.transition = "opacity .3s"; $("#beacons").style.opacity = ".25";
  setTimeout(()=>{ renderLens(); renderRibbon(); render(); $("#beacons").style.opacity = "1"; }, 420);
}

/* ====================== ribbon ====================== */
function ranked(){
  const WORD = {awaiting:"review", stale:"stale", gap:"gaps", failed:"failed", processing:"processing", reviewed:"reviewed"};
  return visibleAssets().map(a => {
    const rs = lensReports(a), by = {};
    rs.forEach(r => { const w = WORD[r.s]; by[w] = (by[w]||0)+1; });
    const parts = Object.keys(by).sort((x,y)=>by[y]-by[x]).map(w => by[w] + " " + w);
    return {a, n: rs.length, chip: parts.length ? parts.slice(0,2).join(" · ") : "0 in lens"};
  }).sort((x,y)=>y.n-x.n);
}
function renderRibbon(){
  const track = $("#track"); track.innerHTML = "";
  const rk = ranked();
  if (!rk.length){ track.appendChild(el("div","kicker","No assets in this lens")); return; }
  rk.forEach((r,i) => {
    const b = el("button","rit"+(S.sel===r.a.id?" on":""),
      `<span class="no">${String(i+1).padStart(2,"0")}</span><span class="nm">${r.a.short}</span><span class="ct">${r.chip}</span>`);
    b.dataset.asset = r.a.id;
    b.onmouseenter = () => { S.hover = r.a.id; renderBeacons(); pulseBeacon(r.a.id); };
    b.onmouseleave = () => { S.hover = null; renderBeacons(); };
    b.onclick = () => selectAsset(r.a.id);
    track.appendChild(b);
  });
  renderQueue();
}
function pulseBeacon(id){
  const a = ASSETS.find(x=>x.id===id); if (!a) return;
  [...document.querySelectorAll(".beacon")].forEach(b=>{});
  const marks = computeMarks();
  const m = marks.findIndex(m => m.kind==="asset" && m.a.id===id);
  const node = $("#beacons").children[m];
  if (node){ node.classList.add("show-lab"); node.querySelector(".bcore").style.transform = "scale(1.25)"; }
}
function highlightRibbon(id, on){
  const b = $(`#track .rit[data-asset="${id}"]`);
  if (b) b.classList.toggle("hl", on);
}
function renderQueue(){
  const q = $("#queue");
  const rows = REPORTS.filter(r => {
    if (S.lens === "review") return r.s==="awaiting" || r.s==="stale";
    if (S.lens === "gaps") return r.s==="gap" || r.s==="failed" || r.s==="processing";
    return true;
  });
  q.innerHTML = `<div class="qrow qhead"><span>Report</span><span>Excerpt</span><span>Site</span><span>State</span></div>` +
    rows.map(r => {
      const a = ASSETS.find(x=>x.id===r.asset);
      return `<button class="qrow" data-r="${r.id}"><span class="qi">${r.id}</span><span class="qe">${r.excerpt}</span>
        <span>${a?a.short:"— unassigned"}</span><span class="mono" style="font-size:10.5px;color:var(--ink-2)">${STATE_LABEL[r.s]}</span></button>`;
    }).join("");
  q.querySelectorAll(".qrow[data-r]").forEach(b => b.onclick = () => {
    const r = REPORTS.find(x=>x.id===b.dataset.r);
    if (!r.asset) { openPanel("#unassigned"); return; }
    $("#queue").classList.remove("on"); $("#queueBtn").classList.remove("on");
    selectAsset(r.asset);
    setTimeout(()=>openReport(r.id), 820);
  });
}

/* ====================== panels ====================== */
function openPanel(sel){
  document.querySelectorAll(".floatpanel").forEach(p => { if (p !== $(sel)) p.classList.remove("on"); });
  $(sel).classList.toggle("on");
}
function buildPanels(){
  const un = REPORTS.filter(r => !r.asset);
  $("#unassigned").innerHTML = `<div class="fp-h"><div><div class="kicker">Floating action</div><b style="font-size:13px">Unassigned reports</b></div><span class="mono" style="font-size:10px;color:var(--ink-3)">${un.length}</span></div>
    <div class="kicker" style="margin-bottom:6px">Not placed on the map — no site in the source</div>
    ${un.map(r=>`<button class="fp-row"><span class="mono" style="color:var(--violet);font-size:11px">${r.id}</span><span>${r.excerpt}</span></button>`).join("")}`;
  $("#unmapped").innerHTML = `<div class="fp-h"><div><div class="kicker">Floating action</div><b style="font-size:13px">Unmapped assets</b></div><span class="mono" style="font-size:10px;color:var(--ink-3)">${UNMAPPED.length}</span></div>
    ${UNMAPPED.map(a=>`<button class="fp-row"><span class="mono" style="color:var(--violet);font-size:11px">${a.id}</span><span>${a.name}<br/><span style="color:var(--ink-3);font-size:11px">${a.why}</span></span></button>`).join("")}`;

  const states = [
    ["Map at rest", ()=>{ clearSelection(); fitToAssets(true); }],
    ["Hover a high-attention asset", ()=>{ clearSelection(); setTimeout(()=>{ const n = $("#beacons").children[0]; if(n){ n.classList.add("show-lab"); n.dispatchEvent(new MouseEvent("mouseenter")); } },300); }],
    ["Select an asset (constellation)", ()=>selectAsset("AST-02")],
    ["Select a report", ()=>{ selectAsset("AST-02"); setTimeout(()=>openReport("RPT-2140"), 820); }],
    ["Evidence thread + AI inspection", ()=>{ selectAsset("AST-02"); setTimeout(()=>{openReport("RPT-2140"); setTimeout(()=>runAI("RPT-2140"),400);}, 820); }],
    ["Lens sweep → Information gaps", ()=>setLens("gaps")],
    ["Priority ribbon → queue mode", ()=>{ $("#queue").classList.add("on"); $("#queueBtn").classList.add("on"); }],
    ["Unassigned reports", ()=>openPanel("#unassigned")],
    ["Open the Workbench", ()=>{ selectAsset("AST-01"); setTimeout(()=>{openReport("RPT-2214"); setTimeout(()=>openWorkbench("RPT-2214"),500);}, 820); }],
    ["Map unavailable", ()=>setUnavailable(true)],
    ["No matching reports", ()=>{ S.filter="none"; S.lens="review"; render(); $("#empty").classList.add("on"); }]
  ];
  $("#statesPanel").innerHTML = `<div class="fp-h"><div><div class="kicker">Prototype</div><b style="font-size:13px">Demonstration states</b></div></div>` +
    states.map((s,i)=>`<button class="fp-row" data-s="${i}"><span class="mono" style="color:var(--violet);font-size:11px">${String(i+1).padStart(2,"0")}</span><span>${s[0]}</span></button>`).join("");
  $("#statesPanel").querySelectorAll("[data-s]").forEach(b => b.onclick = () => {
    $("#statesPanel").classList.remove("on");
    if (S.unavailable && b.dataset.s !== "9") setUnavailable(false);
    if (S.filter) { S.filter = null; $("#empty").classList.remove("on"); }
    states[+b.dataset.s][1]();
  });
}
function setUnavailable(v){
  S.unavailable = v;
  $("#unavail").classList.toggle("on", v);
  $("#beacons").style.display = v ? "none" : "";
  if (v){ closeThread(); $("#constel").innerHTML=""; $("#links").innerHTML=""; }
}

/* ====================== workbench ====================== */
function openWorkbench(id){
  const r = REPORTS.find(x=>x.id===id), a = ASSETS.find(x=>x.id===r.asset);
  S.wb = true;
  $("#body").classList.add("receded");
  const steps = threadSteps(r);
  $("#wb").innerHTML = `
    <button id="wbback" class="pill">← Back to map · ${a?a.short:"unassigned"}</button>
    <div class="wbgrid">
      <div class="wbcard glass glass-ring">
        <div class="kicker">Evidence workbench</div>
        <h3>${r.id}</h3>
        <div class="mono" style="font-size:11px;color:var(--ink-3)">${a?a.name:"Unassigned"} · ${STATE_LABEL[r.s]}</div>
        <p class="narr">“${r.excerpt}”</p>
        <div class="chain">${steps.slice(1).map(s=>`<button class="chainrow">
            <span style="width:7px;height:7px;border-radius:50%;background:${s.c};margin-top:6px;flex:none"></span>
            <span><span class="lb kicker">${s.lb}</span><span style="font-size:13.5px;line-height:1.5">${s.tx}</span>
            <span class="mono" style="display:block;font-size:10px;color:var(--violet);margin-top:3px">↗ ${s.src}</span></span></button>`).join("")}</div>
      </div>
      <div class="wbcard glass glass-ring wbside">
        <div class="kicker">Entry context</div>
        <div class="kv"><span>Arrived from</span><b>${a?a.name:"Unassigned queue"}</b></div>
        <div class="kv"><span>Lens</span><b>${LENSES.find(l=>l.key===S.lens).label}</b></div>
        <div class="kv"><span>Candidate</span><b>${r.state}</b></div>
        <div class="kv"><span>Review</span><b>${r.review}</b></div>
        <div class="kv"><span>Processing</span><b>${r.proc}</b></div>
        <div style="display:flex;gap:8px;margin-top:14px">
          <button class="tbtn pri">Record review</button><button class="tbtn">Request information</button>
        </div>
        <div class="kicker" style="margin-top:16px">Sibling reports at this asset</div>
        <div style="margin-top:6px">${(a?repsOf(a.id):[]).filter(x=>x.id!==r.id).map(x=>`<button class="fp-row" data-sib="${x.id}"><span class="mono" style="color:var(--violet);font-size:11px">${x.id}</span><span>${x.excerpt}</span></button>`).join("")}</div>
      </div>
    </div>`;
  $("#wb").classList.add("on");
  $("#wbback").onclick = closeWorkbench;
  $("#wb").querySelectorAll("[data-sib]").forEach(b => b.onclick = () => openWorkbench(b.dataset.sib));
  document.querySelectorAll("#dock .nav").forEach(n=>n.classList.remove("on"));
}
function closeWorkbench(){
  S.wb = false;
  $("#wb").classList.remove("on");
  $("#body").classList.remove("receded");
  document.querySelectorAll("#dock .nav")[0].classList.add("on");
  setTimeout(()=>{ positionThread(); }, 60);
}

/* ====================== search ====================== */
const searchEl = $("#search"), resEl = $("#results");
searchEl.addEventListener("input", () => {
  const q = searchEl.value.trim().toLowerCase();
  if (!q){ resEl.classList.remove("on"); return; }
  const hits = [];
  ASSETS.filter(a => (a.name+a.id+a.region).toLowerCase().includes(q)).forEach(a => hits.push({id:a.id, tx:a.name+" · "+a.region, go:()=>selectAsset(a.id)}));
  REPORTS.filter(r => (r.id+r.excerpt).toLowerCase().includes(q)).forEach(r => hits.push({id:r.id, tx:r.excerpt, go:()=>{ if(!r.asset){openPanel("#unassigned");return;} selectAsset(r.asset); setTimeout(()=>openReport(r.id), 820); }}));
  resEl.innerHTML = hits.length ? "" : `<div class="res"><span class="rtx">No matches</span></div>`;
  hits.slice(0,8).forEach(h => {
    const b = el("button","res",`<span class="rid">${h.id}</span><span class="rtx">${h.tx}</span>`);
    b.onclick = () => { resEl.classList.remove("on"); searchEl.value = ""; h.go(); };
    resEl.appendChild(b);
  });
  resEl.classList.add("on");
});
searchEl.addEventListener("keydown", e => {
  if (e.key === "Enter"){ const f = resEl.querySelector(".res"); if (f && f.onclick) f.click(); }
  if (e.key === "Escape"){ resEl.classList.remove("on"); searchEl.blur(); }
});
document.addEventListener("click", e => { if (!e.target.closest("#searchWrap")) resEl.classList.remove("on"); });

/* ====================== wiring ====================== */
$("#fitBtn").onclick = () => { clearSelection(); fitToAssets(true); };
const scaleAround = f => { const c = [W/2, H/2]; const k = Math.max(.7, Math.min(14, curT.k*f));
  const x = c[0] - (c[0] - curT.x) * (k/curT.k), y = c[1] - (c[1] - curT.y) * (k/curT.k);
  animateTo(d3.zoomIdentity.translate(x,y).scale(k), 300); };
$("#zIn").onclick = () => scaleAround(1.6);
$("#zOut").onclick = () => scaleAround(1/1.6);
$("#zHome").onclick = () => { const a = ASSETS.find(x=>x.id===S.sel); a ? flyTo(a.lon,a.lat,Math.max(3.2,S.k)) : fitToAssets(true); };
$("#unassignedBtn").onclick = () => { positionFloat("#unassigned"); openPanel("#unassigned"); };
$("#unmappedBtn").onclick = () => { positionFloat("#unmapped"); openPanel("#unmapped"); };
$("#statesBtn").onclick = () => { positionFloat("#statesPanel"); openPanel("#statesPanel"); };
function positionFloat(sel){ const p = $(sel); p.style.right = "16px"; p.style.top = "112px"; p.style.left = "auto"; }
$("#queueBtn").onclick = () => { const on = $("#queue").classList.toggle("on"); $("#queueBtn").classList.toggle("on", on); };
$("#unavailQueue").onclick = () => { $("#queue").classList.add("on"); $("#queueBtn").classList.add("on"); };
$("#unavailRetry").onclick = () => setUnavailable(false);
$("#emptyReset").onclick = () => { S.filter = null; render(); };
document.querySelectorAll("#dock .nav").forEach(n => n.onclick = () => {
  document.querySelectorAll("#dock .nav").forEach(x=>x.classList.remove("on"));
  n.classList.add("on");
  if (S.wb && n.dataset.dest === "Command Centre") closeWorkbench();
});
$("#track").addEventListener("wheel", e => { if (Math.abs(e.deltaY) > Math.abs(e.deltaX)){ $("#track").scrollLeft += e.deltaY; e.preventDefault(); } }, {passive:false});

document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "Escape"){ if (S.wb) closeWorkbench(); else if (S.rep) closeThread(); else clearSelection(); }
  if (e.key === "ArrowRight" || e.key === "ArrowLeft"){
    const list = ranked().map(r=>r.a.id); if (!list.length) return;
    const i = list.indexOf(S.sel);
    const nx = e.key === "ArrowRight" ? (i+1) % list.length : (i<=0 ? list.length-1 : i-1);
    selectAsset(list[nx]); e.preventDefault();
  }
});

buildPanels();

async function loadData() {
    try {
        const data = await API.getSpatialOverview();
        if (data && data.assets && data.assets.length > 0) {
            ASSETS = data.assets;
            UNMAPPED = data.unmapped || [];
            if (data.reports && data.reports.length > 0) {
                REPORTS = data.reports;
            }
        }
    } catch (e) {
        console.error("Failed to load live data, falling back to hardcoded", e);
    }
    boot();
}
loadData();

