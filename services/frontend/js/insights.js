
/* ============ data ============ */
let ELIGIBLE = 212, CLASSIFIED = 168, UNRESOLVED = 44, REVIEWED = 61;

const REV = {confirmed:"Human-reviewed · confirmed", corrected:"Human-reviewed · corrected", awaiting:"Not yet reviewed", stale:"Review older than 90 days", incomplete:"Analysis incomplete"};

/* ---- Evidence graph wiring ---- */
const graphLink = id => `<a class="tbtn" href="evidence.html?report=${encodeURIComponent(id)}">Evidence graph \u2197</a>`;


function rpt(id, site, excerpt, review, gap, complete, rule){
  return {id, site, excerpt, review, gap, complete, rule};
}

let PATTERNS = [
  {
    id:"P-01", activity:"Maintenance", hazard:"Electrical energy", exposure:"Worker performing intervention",
    control:"Isolation", state:"Effectiveness not established", n:14, gapN:9, modelOnly:6, rule:"Energy isolation",
    mapping:"Mapped", gapKind:"Control effectiveness unverified",
    gapWhy:"Isolation is named in the narrative but no verification step is described, so the reported state cannot be read as “effective”.",
    clarifiable:true, overlap:"No member of this pattern belongs to another pattern in the current view.",
    reports:[
      rpt("RPT-2189","Naharkatiya","Isolation certificate referenced, verification step not described","awaiting","missing",true,"Energy isolation"),
      rpt("RPT-2166","Naharkatiya","Statements conflict on whether the line was depressurised","awaiting","conflict",true,"Energy isolation"),
      rpt("RPT-2141","Moran","Breaker locked out; no test-for-dead recorded","confirmed","missing",true,"Energy isolation"),
      rpt("RPT-2133","OIL-D-12","Panel opened after isolation was “assumed complete”","corrected","missing",true,"Energy isolation"),
      rpt("RPT-2127","Jorhat","Isolation list signed, verification column blank","confirmed","missing",true,"Energy isolation"),
      rpt("RPT-2119","Moran","Cable pulled while circuit state unclear","awaiting","conflict",true,"Energy isolation"),
      rpt("RPT-2112","SY-03","Isolation applied by contractor; evidence not attached","awaiting","missing",true,"Energy isolation"),
      rpt("RPT-2108","Naharkatiya","Test lamp used but result not written down","confirmed","missing",true,"Energy isolation"),
      rpt("RPT-2099","Kumchai","Lock removed by second party during the task","corrected","none",true,"Energy isolation"),
      rpt("RPT-2091","Jorhat","Isolation boundary described only in general terms","awaiting","missing",true,"Energy isolation"),
      rpt("RPT-2088","Moran","Stored energy in capacitors not mentioned","confirmed","missing",true,"Energy isolation"),
      rpt("RPT-2077","SY-03","Isolation confirmed verbally between shifts","awaiting","missing",true,"Energy isolation"),
      rpt("RPT-2069","OIL-D-12","Permit references an isolation register not supplied","confirmed","missing",true,"Energy isolation"),
      rpt("RPT-2054","Naharkatiya","Extraction incomplete — attachment unreadable","awaiting","none",false,"Energy isolation")
    ]
  },
  {
    id:"P-02", activity:"Maintenance", hazard:"Electrical energy", exposure:"Worker performing intervention",
    control:"Isolation", state:"Effectiveness reported", n:6, gapN:1, modelOnly:1, rule:"Energy isolation",
    mapping:"Mapped", gapKind:"Timing unknown",
    gapWhy:"Verification is described, but the time between isolation and intervention is stated in only two reports.",
    clarifiable:true, overlap:"No membership overlap with P-01 — the reported control state differs.",
    reports:[
      rpt("RPT-2181","Moran","Test-for-dead performed and recorded by the authorised person","confirmed","none",true,"Energy isolation"),
      rpt("RPT-2158","Jorhat","Isolation verified with meter, reading logged","confirmed","none",true,"Energy isolation"),
      rpt("RPT-2144","Naharkatiya","Two-person verification described in full","confirmed","none",true,"Energy isolation"),
      rpt("RPT-2121","Kumchai","Proving unit checked before and after test","confirmed","timing",true,"Energy isolation"),
      rpt("RPT-2103","SY-03","Verification recorded; interval to work start not stated","corrected","timing",true,"Energy isolation"),
      rpt("RPT-2082","Moran","Isolation verified; permit closed same shift","awaiting","none",true,"Energy isolation")
    ]
  },
  {
    id:"P-03", activity:"Lifting", hazard:"Suspended load", exposure:"Person within exposure area",
    control:"Exclusion zone", state:"Reported after event", n:11, gapN:5, modelOnly:5, rule:"Line of fire",
    mapping:"Mapped", gapKind:"Timing unknown",
    gapWhy:"The exclusion zone appears in the narrative only after the load movement, so the control cannot be placed before the exposure.",
    clarifiable:true, overlap:"2 of these 11 reports (RPT-2132, RPT-2126) are also members of P-07 — do not add the two patterns together.",
    reports:[
      rpt("RPT-2214","Naharkatiya","Suspended load passed inches from a worker; exclusion zone set after the lift","awaiting","timing",true,"Line of fire"),
      rpt("RPT-2196","Moran","Barrier established once the load was landed","awaiting","timing",true,"Line of fire"),
      rpt("RPT-2175","OIL-D-12","Crew moved clear after the banksman shouted","confirmed","none",true,"Line of fire"),
      rpt("RPT-2162","SY-03","Zone marked following the near miss","awaiting","timing",true,"Line of fire"),
      rpt("RPT-2149","Jorhat","Load swung over walkway; walkway closed afterwards","corrected","timing",true,"Line of fire"),
      rpt("RPT-2136","Naharkatiya","Tag line added after first attempt","awaiting","none",true,"Line of fire"),
      rpt("RPT-2124","Moran","Zone described but no dimensions given","awaiting","missing",true,"Line of fire"),
      rpt("RPT-2110","Kumchai","Spotter posted after the lift resumed","confirmed","timing",true,"Line of fire"),
      rpt("RPT-2093","SY-03","Analysis incomplete — lift plan not parsed","awaiting","none",false,"Line of fire"),
      rpt("RPT-2132","OIL-D-12","Drill pipe swung free of the elevator during make-up","awaiting","conflict",true,"Line of fire"),
      rpt("RPT-2126","Moran","Sling condition described differently by two witnesses","awaiting","conflict",true,"Line of fire")
    ]
  },
  {
    id:"P-04", activity:"Hot work", hazard:"Ignition source", exposure:"Flammable atmosphere possible",
    control:"Atmosphere testing", state:"Test status unknown", n:7, gapN:6, modelOnly:4, rule:"Hot work / permit",
    mapping:"Mapping incomplete", gapKind:"Source evidence could not be located",
    gapWhy:"A gas test is implied by the permit reference, but no reading, time or instrument appears in any supplied source.",
    clarifiable:false, overlap:"No membership overlap recorded — the control concept differs from P-01.",
    reports:[
      rpt("RPT-2129","OIL-D-12","Hot work permit mentioned; atmosphere test unknown","stale","missing",true,"Hot work / permit"),
      rpt("RPT-2117","Moran","Grinding near drain; no gas test described","awaiting","missing",true,"Hot work / permit"),
      rpt("RPT-2106","Naharkatiya","Permit number quoted, test section blank","awaiting","missing",true,"Hot work / permit"),
      rpt("RPT-2094","Jorhat","Welding screens noted; atmosphere not addressed","confirmed","missing",true,"Hot work / permit"),
      rpt("RPT-2081","SY-03","Test claimed by radio, no record supplied","awaiting","missing",true,"Hot work / permit"),
      rpt("RPT-2073","Kumchai","Hot work near hydrocarbon line, monitor status unclear","stale","missing",true,"Hot work / permit"),
      rpt("RPT-2061","Moran","Extraction failed on permit scan","awaiting","none",false,"Hot work / permit")
    ]
  },
  {
    id:"P-05", activity:"Vehicle movement", hazard:"Mobile plant", exposure:"Person on foot in operating area",
    control:"Spotter / segregation", state:"Absent", n:8, gapN:2, modelOnly:3, rule:"Vehicle safety",
    mapping:"Mapped", gapKind:"Exposure not established",
    gapWhy:"Two reports describe reversing without stating whether anyone was inside the swept path.",
    clarifiable:true, overlap:"No membership overlap recorded in the current view.",
    reports:[
      rpt("RPT-2140","Moran","Vehicle reversed toward pipeline crew; no spotter present","awaiting","none",true,"Vehicle safety"),
      rpt("RPT-2131","Naharkatiya","Truck manoeuvred in laydown with pedestrians present","confirmed","none",true,"Vehicle safety"),
      rpt("RPT-2122","Jorhat","No banksman during trailer positioning","confirmed","none",true,"Vehicle safety"),
      rpt("RPT-2113","Kumchai","Reversing alarm inoperative, noted after the event","corrected","none",true,"Vehicle safety"),
      rpt("RPT-2101","OIL-D-12","Segregation barriers not in place at the crossing","awaiting","exposure",true,"Vehicle safety"),
      rpt("RPT-2087","Moran","Forklift crossed walkway without stopping","confirmed","none",true,"Vehicle safety"),
      rpt("RPT-2075","SY-03","Deck transport with restricted visibility","awaiting","exposure",true,"Vehicle safety"),
      rpt("RPT-2066","Naharkatiya","Light vehicle entered the rig floor exclusion area","stale","none",true,"Vehicle safety")
    ]
  },
  {
    id:"P-06", activity:"Working at height", hazard:"Fall from height", exposure:"Worker at unprotected edge",
    control:"Fall arrest", state:"Present but effectiveness unverified", n:6, gapN:4, modelOnly:4, rule:"Working at height",
    mapping:"Uncertain mapping", gapKind:"Control effectiveness unverified",
    gapWhy:"Harnesses are described as worn; anchor points and inspection status are not evidenced.",
    clarifiable:true, overlap:"No overlap recorded.",
    reports:[
      rpt("RPT-2104","SY-03","Basket transfer continued after wind limit exceeded","awaiting","missing",true,"Working at height"),
      rpt("RPT-2098","Naharkatiya","Harness worn; anchor point not identified","awaiting","missing",true,"Working at height"),
      rpt("RPT-2090","Moran","Scaffold handover incomplete at time of access","confirmed","none",true,"Working at height"),
      rpt("RPT-2079","Jorhat","Lanyard length not suitable for the position","corrected","missing",true,"Working at height"),
      rpt("RPT-2068","OIL-D-12","Edge protection removed for access, not reinstated","awaiting","none",true,"Working at height"),
      rpt("RPT-2057","Kumchai","Inspection tag not legible in the photograph","awaiting","missing",false,"Working at height")
    ]
  },
  {
    id:"P-07", activity:"Lifting", hazard:"Suspended load", exposure:"Person within exposure area",
    control:"Lifting equipment condition", state:"Conflicting", n:5, gapN:3, modelOnly:2, rule:"Line of fire",
    mapping:"Mapped", gapKind:"Conflicting statements",
    gapWhy:"Statements disagree on whether the sling was inspected the same shift.",
    clarifiable:true, overlap:"2 of these 5 reports (RPT-2132, RPT-2126) are also members of P-03 — do not add the two patterns together.",
    reports:[
      rpt("RPT-2132","OIL-D-12","Drill pipe swung free of the elevator during make-up","awaiting","conflict",true,"Line of fire"),
      rpt("RPT-2126","Moran","Sling condition described differently by two witnesses","awaiting","conflict",true,"Line of fire"),
      rpt("RPT-2115","Naharkatiya","Shackle inspection date disputed","confirmed","conflict",true,"Line of fire"),
      rpt("RPT-2100","SY-03","Certificate supplied but not matched to the item","corrected","missing",true,"Line of fire"),
      rpt("RPT-2072","Jorhat","Colour code check not described","awaiting","missing",true,"Line of fire")
    ]
  },
  {
    id:"P-08", activity:"Confined space", hazard:"Oxygen deficiency", exposure:"Entrant inside vessel",
    control:"Entry permit and attendant", state:"Unknown", n:4, gapN:4, modelOnly:3, rule:"Confined space",
    mapping:"Mapping incomplete", gapKind:"Source evidence could not be located",
    gapWhy:"Entry is described without naming the site or the permit; the underlying documents were not supplied.",
    clarifiable:false, overlap:"1 report is unassigned to any asset.",
    reports:[
      rpt("RPT-2085","— unassigned","Confined space entry described without site identification","awaiting","missing",true,"Confined space"),
      rpt("RPT-2076","Moran","Attendant role mentioned, no name or log","awaiting","missing",true,"Confined space"),
      rpt("RPT-2064","Jorhat","Vessel entry after purge; readings absent","stale","missing",true,"Confined space"),
      rpt("RPT-2049","Naharkatiya","Permit scan illegible","awaiting","missing",false,"Confined space")
    ]
  },
  {
    id:"P-09", activity:"Excavation", hazard:"Buried services", exposure:"Operator at the excavation face",
    control:"Utility survey", state:"Absent", n:5, gapN:3, modelOnly:4, rule:"Ground disturbance",
    mapping:"Mapped", gapKind:"Control effectiveness unverified",
    gapWhy:"Scan records are referenced in three reports but never attached.",
    clarifiable:true, overlap:"No overlap recorded.",
    reports:[
      rpt("RPT-2063","Jaisalmer","Excavation near buried service; scan record not attached","awaiting","missing",true,"Ground disturbance"),
      rpt("RPT-2058","Jaisalmer","Hand-dig requirement not described","awaiting","missing",true,"Ground disturbance"),
      rpt("RPT-2052","Naharkatiya","Service drawing older than the works","confirmed","none",true,"Ground disturbance"),
      rpt("RPT-2046","Moran","Cable strike avoided by chance sighting","awaiting","none",true,"Ground disturbance"),
      rpt("RPT-2041","Kumchai","Survey referenced, no evidence supplied","awaiting","missing",true,"Ground disturbance")
    ]
  },
  {
    id:"P-10", activity:"Pigging", hazard:"Pressure release", exposure:"Crew at the trap",
    control:"Depressurisation check", state:"Failed", n:4, gapN:1, modelOnly:2, rule:"Energy isolation",
    mapping:"Mapped", gapKind:"Timing unknown",
    gapWhy:"One report does not state when the pressure reading was taken.",
    clarifiable:true, overlap:"No overlap recorded.",
    reports:[
      rpt("RPT-2151","Moran","Gas release during pigging; detector reading not stated","awaiting","timing",true,"Energy isolation"),
      rpt("RPT-2145","Moran","Trap opened with residual pressure","confirmed","none",true,"Energy isolation"),
      rpt("RPT-2109","Naharkatiya","Bleed valve found blocked during the check","confirmed","none",true,"Energy isolation"),
      rpt("RPT-2062","OIL-D-12","Vent line routed into the work area","corrected","none",true,"Energy isolation")
    ]
  },
  {
    id:"P-11", activity:"Chemical handling", hazard:"Corrosive substance", exposure:"Worker decanting product",
    control:"Personal protection", state:"Bypassed", n:3, gapN:1, modelOnly:2, rule:"No applicable rule",
    mapping:"No applicable rule", gapKind:"Exposure not established",
    gapWhy:"Contact with the substance is implied but never described.",
    clarifiable:true, overlap:"Low support — 3 distinct reports.",
    reports:[
      rpt("RPT-2096","Jorhat","Face shield removed to see the gauge","awaiting","exposure",true,"No applicable rule"),
      rpt("RPT-2083","Moran","Gloves not compatible with the product","confirmed","none",true,"No applicable rule"),
      rpt("RPT-2055","Kumchai","Decanting without eye protection","awaiting","none",true,"No applicable rule")
    ]
  },
  {
    id:"P-12", activity:"Shift handover", hazard:"Information loss", exposure:"Incoming crew unaware of state",
    control:"Handover record", state:"Present but effectiveness unverified", n:3, gapN:2, modelOnly:3, rule:"Uncertain mapping",
    mapping:"Uncertain mapping", gapKind:"Rule mapping incomplete",
    gapWhy:"The mechanism does not map cleanly onto a single Life-Saving Rule.",
    clarifiable:false, overlap:"Low support — 3 distinct reports.",
    reports:[
      rpt("RPT-2137","Moran","Scaffold handover sheet uploaded; parsing in progress","awaiting","missing",false,"Uncertain mapping"),
      rpt("RPT-2089","Naharkatiya","Verbal handover only, no written record","awaiting","missing",true,"Uncertain mapping"),
      rpt("RPT-2050","SY-03","Handover sheet incomplete for isolations in force","confirmed","none",true,"Uncertain mapping")
    ]
  }
];

const LENSES = [
  {k:"patterns", label:"Patterns", note:"Complete reported mechanisms: activity → hazard → exposure → control concept → reported control state → distinct member reports. Patterns describe what recurs in the written reports. They are not causes, predictions or a measure of current site risk."},
  {k:"gaps", label:"Information gaps", note:"Streams reordered by unresolved evidence. Missing information is kept separate from negative findings and from processing failures — an unverified control is not an ineffective control."},
  {k:"states", label:"Control states", note:"Patterns grouped by the reported state of the control concept. The concept and its state stay separate: “isolation mentioned” is not “isolation effective”."},
  {k:"rules", label:"Rule relationships", note:"Relationships between reported mechanisms and Life-Saving Rules, with mapping status. A relevant rule is not a rule violation, and a report may relate to more than one rule."},
  {k:"reviewed", label:"Reviewed evidence", note:"Model-only, human-confirmed, human-corrected, needs-information and stale populations shown separately. Reviewed reports are a selected subset — they are not an unbiased sample of the eligible reports."},
  {k:"context", label:"Reporting context", note:"Supporting context for the population above: reporting volume, eligible reports, review coverage and representation. Fewer reports in a period does not mean fewer hazards."}
];

const GAP_LABEL = {missing:"Missing control fact", conflict:"Conflicting statements", timing:"Timing unknown", exposure:"Exposure not established", none:"—"};
const AI_STEPS = [
  {v:"filtering control states", f:"Control state · not established"},
  {v:"checking report membership"},
  {v:"comparing review evidence"},
  {v:"locating representative sources"}
];

/* ============ state ============ */
const S = {lens:"patterns", sel:null, rep:null, cmp:null, filters:[], query:"", overview:false, note:null, saved:[
  {name:"Electrical isolation gaps", lens:"gaps", filters:["Control · Isolation"], sel:"P-01"},
  {name:"Lifting reports awaiting review", lens:"reviewed", filters:["Activity · Lifting"], sel:"P-03"},
  {name:"Post-event controls", lens:"states", filters:["Control state · Reported after event"], sel:null}
]};

const $ = s => document.querySelector(s);
const el = (t,c,h) => {const e=document.createElement(t); if(c)e.className=c; if(h!=null)e.innerHTML=h; return e;};
const pat = id => PATTERNS.find(p=>p.id===id);
const pop = p => {
  const c = {confirmed:0, corrected:0, awaiting:0, stale:0, incomplete:0};
  (p.reports || []).forEach(r => {
    if (!r.complete) c.incomplete++;
    else if (c[r.review] !== undefined) c[r.review]++;
    else c.awaiting++;
  });
  return c;
};
const matchesFilters = p => S.filters.every(f => {
  const [k,v] = f.split(" · ");
  if (k==="Activity") return p.activity===v;
  if (k==="Control") return p.control===v;
  if (k==="Control state") return p.state===v;
  if (k==="Hazard") return p.hazard===v;
  if (k==="Rule") return p.rule===v;
  if (k==="Review") return v==="Has human review" ? pop(p).confirmed+pop(p).corrected>0 : pop(p).confirmed+pop(p).corrected===0;
  if (k==="Gaps") return p.gapN>0;
  if (k==="Analysis") return p.reports.some(r=>!r.complete);
  return true;
});
const matchesQuery = p => {
  if (!S.query) return true;
  const q = S.query.toLowerCase();
  return [p.activity,p.hazard,p.exposure,p.control,p.state,p.rule,p.id].join(" ").toLowerCase().includes(q)
      || p.reports.some(r => (r.id+" "+r.site+" "+r.excerpt).toLowerCase().includes(q));
};
const visible = () => PATTERNS.filter(p => matchesFilters(p) && matchesQuery(p));

/* ============ lens rail / filters ============ */
function renderRail(){
  const rail = $("#lensRail"); rail.innerHTML = "";
  LENSES.forEach(l => {
    const b = el("button","lensbtn"+(S.lens===l.k?" on":""), l.label);
    b.onclick = () => setLens(l.k);
    rail.appendChild(b);
  });
  $("#lensNote").textContent = LENSES.find(l=>l.k===S.lens).note;
  $("#ovBtn").classList.toggle("on", S.overview);
}
function setLens(k){
  S.lens = k; S.overview = false; S.rep = null;
  renderRail(); renderField(true); renderRail();
}
function renderFilters(){
  const bar = $("#filterBar"); bar.innerHTML = "";
  S.filters.forEach(f => {
    const c = el("button","fchip act", f + ` <span class="x">✕</span>`);
    c.onclick = () => { S.filters = S.filters.filter(x=>x!==f); renderFilters(); renderField(false); renderRailStats(); };
    bar.appendChild(c);
  });
  const add = el("button","fchip","+ Filter");
  add.onclick = e => openFilterPop(e.currentTarget);
  bar.appendChild(add);
}
function openFilterPop(anchor){
  const groups = {
    "Activity":[...new Set(PATTERNS.map(p=>p.activity))],
    "Hazard":[...new Set(PATTERNS.map(p=>p.hazard))],
    "Control":[...new Set(PATTERNS.map(p=>p.control))],
    "Control state":[...new Set(PATTERNS.map(p=>p.state))],
    "Rule":[...new Set(PATTERNS.map(p=>p.rule))],
    "Review":["Has human review","Model-only"],
    "Gaps":["Contains information gaps"],
    "Analysis":["Contains incomplete analysis"]
  };
  const p = $("#filterPop");
  p.innerHTML = `<h4>Filter the population</h4><div class="kicker" style="margin-bottom:8px">Filters transform the streams in place — positions are preserved</div>` +
    Object.keys(groups).map(g => `<div class="kicker" style="margin-top:10px">${g}</div>` +
      groups[g].map(v=>`<button class="prow" data-f="${g} · ${v}"><span>${v}</span></button>`).join("")).join("");
  p.querySelectorAll("[data-f]").forEach(b => b.onclick = () => {
    const f = b.dataset.f;
    if (!S.filters.includes(f)) S.filters.push(f);
    p.classList.remove("on"); renderFilters(); renderField(false); renderRailStats();
  });
  place(p, anchor); p.classList.add("on");
}
function place(p, anchor){
  const r = anchor.getBoundingClientRect();
  p.style.top = Math.min(r.bottom + 8, innerHeight - 200) + "px";
  p.style.left = Math.max(12, Math.min(r.left, innerWidth - 346)) + "px";
}

/* ============ field ============ */
function renderField(animate){
  $("#overview").classList.toggle("on", S.overview);
  $("#field").style.display = S.overview ? "none" : "";
  if (S.overview){ renderOverview(); renderRailStats(); return; }

  const field = $("#field"); field.innerHTML = "";
  let list = visible();

  if (S.lens === "gaps") list = list.slice().sort((a,b)=>b.gapN-a.gapN);
  if (S.lens === "reviewed") list = list.slice().sort((a,b)=>(pop(b).confirmed+pop(b).corrected)-(pop(a).confirmed+pop(a).corrected));

  if (!list.length){
    field.appendChild(emptyBlock());
    renderRailStats(); return;
  }

  const textOnly = S.query ? PATTERNS.flatMap(p => p.reports.filter(r => (r.id+" "+r.site+" "+r.excerpt).toLowerCase().includes(S.query.toLowerCase())).map(r => r.id)) : [];
  if (S.query && textOnly.length){
    const n = el("div","glass glass-ring");
    n.style.cssText = "margin:6px 2px 12px;padding:10px 12px;border-radius:12px;max-width:760px";
    n.innerHTML = `<div class="kicker">Source-wording matches</div>
      <div style="font-size:12px;line-height:1.5;color:var(--ink-2);margin-top:4px">${[...new Set(textOnly)].length} report(s) contain “${S.query}” in their source text: <span class="mono" style="font-size:10.5px">${[...new Set(textOnly)].slice(0,12).join(" · ")}</span>. Matching streams are highlighted below — no new pattern is created from a text match.</div>`;
    field.appendChild(n);
  }

  const groups = groupsFor(list);
  groups.forEach(g => {
    if (g.title){
      const h = el("div","groupHead",`<span class="gt">${g.title}</span><span class="gd">${g.desc}</span>`);
      field.appendChild(h);
    }
    g.items.forEach((p,i) => field.appendChild(streamEl(p, animate, i)));
  });

  if (S.lens === "context") field.appendChild(contextBlock());
  if (S.note) field.appendChild(noteBlock(S.note));
  renderRailStats();
}

function groupsFor(list){
  if (S.lens === "states"){
    const known = ["Effectiveness reported","Present but effectiveness unverified","Effectiveness not established","Absent","Failed","Bypassed","Reported after event","Unknown","Conflicting"];
    const present = [...new Set(list.map(p=>p.state))];
    const order = known.filter(s => present.includes(s)).concat(present.filter(s => !known.includes(s)));
    return order.map(s => ({
      title:s, desc:`${list.filter(p=>p.state===s).length} pattern(s) · reported state only, not an assessment of effectiveness`,
      items:list.filter(p=>p.state===s)
    }));
  }
  if (S.lens === "rules"){
    const rules = [...new Set(list.map(p=>p.rule))];
    return rules.map(r => ({
      title:r, desc:`${list.filter(p=>p.rule===r).length} pattern(s) · relevance, not violation · ${[...new Set(list.filter(p=>p.rule===r).map(p=>p.mapping))].join(", ").toLowerCase()}`,
      items:list.filter(p=>p.rule===r)
    }));
  }
  if (S.lens === "reviewed"){
    const bands = [
      {t:"Human-confirmed or corrected support", f:p=>pop(p).confirmed+pop(p).corrected>=3, d:"three or more reviewed member reports"},
      {t:"Partial review coverage", f:p=>{const c=pop(p);return c.confirmed+c.corrected>0 && c.confirmed+c.corrected<3;}, d:"one or two reviewed member reports"},
      {t:"Model-only support", f:p=>pop(p).confirmed+pop(p).corrected===0, d:"no human review recorded — not a confidence statement"}
    ];
    const used = new Set();
    return bands.map(b => {
      const items = list.filter(p => !used.has(p.id) && b.f(p));
      items.forEach(p=>used.add(p.id));
      return {title:b.t, desc:b.d, items};
    }).filter(g=>g.items.length);
  }
  if (S.lens === "gaps"){
    const kinds = [...new Set(list.map(p=>p.gapKind))];
    return kinds.map(k => ({
      title:k, desc:`${list.filter(p=>p.gapKind===k).length} pattern(s) · unresolved information, kept separate from negative findings and processing failures`,
      items:list.filter(p=>p.gapKind===k)
    }));
  }
  return [{title:null, items:list}];
}

function streamEl(p, animate, i){
  const c = pop(p);
  const s = el("div","stream"+(S.sel===p.id?" sel":"")+(S.sel&&S.sel!==p.id&&S.cmp!==p.id?" recede":"")+(animate?" enter":""));
  s.style.animationDelay = (i*45)+"ms";
  s.dataset.p = p.id;
  const gapHot = S.lens==="gaps", stateHot = S.lens==="states", ruleHot = S.lens==="rules";
  const maxN = Math.max(...PATTERNS.map(x => x.n || 1), 1);
  const width = Math.round(((p.n || 0) / maxN) * 100);
  s.innerHTML = `
    <div class="srow">
      <div class="stage ${gapHot||stateHot?"dim":""}"><span class="lb">Activity</span><span class="vl">${hl(p.activity || 'Operations')}</span></div>
      <div class="stage ${gapHot?"dim":""}"><span class="lb">Hazard</span><span class="vl">${hl(p.hazard || 'Hazard')}</span></div>
      <div class="stage ${gapHot?"dim":""}"><span class="lb">Exposure</span><span class="vl">${hl(p.exposure || 'Personnel exposed')}</span></div>
      <div class="stage ${ruleHot?"dim":""}"><span class="lb">Control concept</span><span class="vl">${hl(p.control || 'Control barrier')}</span></div>
      <div class="stage ${stateHot||gapHot?"hot":""}"><span class="lb">Reported state</span><span class="vl">${hl(p.state || 'Unknown')}</span></div>
      <div class="stage support">
        <div class="sbar" title="Distinct-report support relative to the largest pattern"><i class="${gapHot?"gapfill":""}" style="width:${gapHot?Math.round(((p.gapN||0)/maxN)*100):width}%"></i></div>
        <span class="scount">${gapHot?p.gapN:p.n}</span>
        <span class="sden">${gapHot?"with gaps of "+p.n:"of "+ELIGIBLE}</span>
      </div>
    </div>
    <div class="flags">
      ${p.gapN?`<span class="flag gap">${p.gapKind} · ${p.gapN}</span>`:""}
      ${p.modelOnly?`<span class="flag model">model-only ${p.modelOnly}</span>`:""}
      ${(c.confirmed+c.corrected)?`<span class="flag rev">reviewed ${c.confirmed+c.corrected}</span>`:""}
      ${c.incomplete?`<span class="flag inc">analysis incomplete ${c.incomplete}</span>`:""}
      ${ruleHot?`<span class="flag">${p.rule} · ${(p.mapping || '').toLowerCase()}</span>`:""}
      ${p.n<=3?`<span class="flag">low support</span>`:""}
    </div>
    <div class="expand"><div class="expandInner"></div></div>`;

  s.querySelectorAll(".srow, .flags").forEach(z => z.addEventListener("click", () => toggleSelect(p.id)));
  s.tabIndex = 0;
  s.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " "){ toggleSelect(p.id); e.preventDefault(); }
  });
  s.addEventListener("mouseenter", () => { if (!S.sel) s.querySelectorAll(".stage").forEach(x=>x.classList.add("shared")); });
  s.addEventListener("mouseleave", () => s.querySelectorAll(".stage").forEach(x=>x.classList.remove("shared")));
  if (S.sel === p.id || S.cmp === p.id) fillExpand(s.querySelector(".expandInner"), p);
  return s;
}

function hl(text){
  if (!S.query) return text;
  const i = text.toLowerCase().indexOf(S.query.toLowerCase());
  if (i < 0) return text;
  return text.slice(0,i) + `<mark style="background:rgba(91,61,245,.18);color:inherit;border-radius:3px;padding:0 2px">` + text.slice(i,i+S.query.length) + `</mark>` + text.slice(i+S.query.length);
}

function fillExpand(host, p){
  const c = pop(p);
  const segs = [
    {k:"confirmed", n:c.confirmed, col:"#0d8467", t:"human-reviewed and confirmed"},
    {k:"corrected", n:c.corrected, col:"#7b5df8", t:"human-reviewed and corrected"},
    {k:"awaiting", n:c.awaiting, col:"#5b3df5", t:"not yet reviewed"},
    {k:"stale", n:c.stale, col:"#b5730b", t:"review older than 90 days"},
    {k:"incomplete", n:c.incomplete, col:"#c0392b", t:"analysis incomplete"}
  ].filter(s=>s.n);
  host.innerHTML = `
    <div class="kicker" style="margin-bottom:6px">${p.n} distinct reports · membership populations kept separate (no combined confidence score)</div>
    <div class="popline">${segs.map(s=>`<div class="popseg" style="flex:${s.n};background:${s.col}" title="${s.n} ${s.t}">${s.n}</div>`).join("")}</div>
    <div class="popkey">${segs.map(s=>`<span><i style="background:${s.col}"></i>${s.n} ${s.t}</span>`).join("")}</div>
    <div class="disclose">${p.overlap} Grouping is deterministic normalisation of extracted fields, not semantic clustering. Denominator: ${ELIGIBLE} eligible reports in the selected period; ${REVIEWED} carry any human review.</div>
    <div class="kicker" style="margin-bottom:7px">Member reports — hover for the exact source excerpt</div>
    <div class="constel"></div>
    <div class="threadHost"></div>
    <div class="tfoot">
      <button class="tbtn" data-act="compare">Compare control state</button>
      <button class="tbtn" data-act="why">Why is this a pattern?</button>
      <button class="tbtn" data-act="save">Save this view</button>
      <button class="tbtn" data-act="close">Close</button>
    </div>`;
  const cst = host.querySelector(".constel");
  p.reports.forEach((r,i) => {
    const n = el("button","rnode"+(S.rep===r.id?" sel":""),
      `<span class="rid">${r.id}</span><span class="rsite">${r.site}</span>
       <span class="rstates">
         <i class="rdot ${r.complete?r.review:"incomplete"}" title="${r.complete?REV[r.review]:"Analysis incomplete"}"></i>
         ${r.gap!=="none"?`<i class="rdot gap" title="${GAP_LABEL[r.gap]}"></i>`:""}
       </span>`);
    n.style.animationDelay = (i*26)+"ms";
    n.onmouseenter = e => showTip(r, p, e.currentTarget);
    n.onmouseleave = hideTip;
    n.onclick = e => { e.stopPropagation(); S.rep = S.rep===r.id?null:r.id; renderField(false); };
    cst.appendChild(n);
  });
  const rep = p.reports.find(r=>r.id===S.rep);
  if (rep) host.querySelector(".threadHost").appendChild(threadEl(rep, p));
  host.querySelectorAll("[data-act]").forEach(b => b.onclick = e => {
    e.stopPropagation();
    const a = b.dataset.act;
    if (a==="close") { S.sel=null; S.rep=null; S.cmp=null; renderField(false); }
    if (a==="compare") startCompare(p);
    if (a==="why") { S.note = membershipNote(p); renderField(false); }
    if (a==="save") saveView();
  });
  if (S.cmp && S.sel===p.id) host.appendChild(compareEl(p, pat(S.cmp)));
}

function threadEl(r, p){
  const steps = [
    {lb:"Source narrative", tx:`“${r.excerpt || '—'}”`, src:"source doc p.1", c:"var(--ink)"},
    {lb:"Activity evidence", tx:`${p.activity || 'Operations'} — extracted from the task description`, src:"span 12–38", c:"var(--violet)"},
    {lb:"Hazard evidence", tx:`${p.hazard || 'Hazard'} — ${(p.exposure || 'person exposed').toLowerCase()}`, src:"span 44–92", c:"var(--violet)"},
    {lb:"Control evidence", tx:`${p.control || 'Control'} named in the source`, src:"permit register", c:"var(--teal)"},
    {lb:"Control-state interpretation", tx:`${p.state || 'Unknown'} — ${p.gapWhy || 'unevidenced'}`, src:"extraction log", c:"var(--amber)"},
    {lb:"Human review", tx:r.complete?REV[r.review]:"Analysis incomplete — not counted as a finding", src:"review ledger", c:"var(--rose)"}
  ];
  const t = el("div","thread");
  t.innerHTML = `<h5><span class="rdot ${r.complete?r.review:"incomplete"}"></span>${r.id} · ${r.site}
      <span class="mono" style="margin-left:auto;font-size:9.5px;color:var(--ink-3)">MEMBER OF ${p.id}</span></h5>
    ${steps.map((s,i)=>`<button class="step" data-i="${i}"><span class="mk2"><b style="background:${s.c}"></b></span>
      <span><span class="lb">${s.lb}</span><span class="tx">${s.tx}</span><span class="src"> ↗ ${s.src}</span></span></button>`).join("")}
    <div class="tfoot">
      <button class="tbtn pri" data-w="1">Open in Evidence Workbench</button>
      <button class="tbtn" data-w="0">Collapse</button>
      ${graphLink(r.id)}
    </div>`;
  t.addEventListener("click", e => e.stopPropagation());
  t.querySelectorAll(".step").forEach(b => b.onclick = () => {
    t.querySelectorAll(".step").forEach(x=>x.classList.remove("em")); b.classList.add("em");
  });
  t.querySelector("[data-w='1']").onclick = () => openWorkbench(r, p);
  t.querySelector("[data-w='0']").onclick = () => { S.rep = null; renderField(false); };
  return t;
}

function toggleSelect(id){
  if (S.sel === id){ S.sel = null; S.rep = null; S.cmp = null; }
  else { S.sel = id; S.rep = null; S.cmp = null; S.note = null; }
  renderField(false);
  const node = document.querySelector(`.stream[data-p="${id}"]`);
  if (node && S.sel) node.focus({preventScroll:true});
}

function startCompare(p){
  const alt = PATTERNS.find(q => q.id!==p.id && q.activity===p.activity && q.control===p.control)
           || PATTERNS.find(q => q.id!==p.id && q.hazard===p.hazard)
           || PATTERNS.find(q => q.id!==p.id);
  if (alt) { S.cmp = alt.id; renderField(false); }
}
function compareEl(a, b){
  if (!a || !b) return el("div","");
  const ca = pop(a), cb = pop(b);
  const aEx = a.reports && a.reports[0] ? `“${(a.reports[0].excerpt || '').slice(0,52)}…”` : "—";
  const bEx = b.reports && b.reports[0] ? `“${(b.reports[0].excerpt || '').slice(0,52)}…”` : "—";
  const rows = [
    ["Distinct report support", `${a.n} of ${ELIGIBLE}`, `${b.n} of ${ELIGIBLE}`],
    ["Reported control state", a.state, b.state],
    ["Member assets", [...new Set((a.reports||[]).map(r=>r.site))].join(", "), [...new Set((b.reports||[]).map(r=>r.site))].join(", ")],
    ["Source language", aEx, bEx],
    ["Timing evidence", (a.reports||[]).filter(r=>r.gap==="timing").length + " reports lack timing", (b.reports||[]).filter(r=>r.gap==="timing").length + " reports lack timing"],
    ["Information gaps", `${a.gapN} of ${a.n}`, `${b.gapN} of ${b.n}`],
    ["Review coverage", `${ca.confirmed+ca.corrected} of ${a.n} reviewed`, `${cb.confirmed+cb.corrected} of ${b.n} reviewed`],
    ["Rule mapping", `${a.rule} · ${a.mapping}`, `${b.rule} · ${b.mapping}`],
    ["Reporting period", $("#period").value, $("#period").value]
  ];
  const w = el("div","compareWrap");
  w.innerHTML = `<div class="kicker">Pinned comparison · aligned on the shared activity, hazard and control concept</div>
    <div class="cmpGrid">
      <span class="h"></span><span class="h">${a.id} · ${a.state}</span><span class="h">${b.id} · ${b.state}</span>
      ${rows.map(r=>`<span class="d">${r[0]}</span><span class="${r[1]!==r[2]?"diff":"d"}">${r[1]}</span><span class="${r[1]!==r[2]?"diff":"d"}">${r[2]}</span>`).join("")}
    </div>
    <div class="disclose" style="margin:10px 0 0">Different reported control states with different denominators. This comparison does not establish that either population is safer; only explicitly reviewed evidence with a matched denominator could support that.</div>
    <div class="tfoot"><button class="tbtn" id="unpin">Unpin comparison</button></div>`;
  w.addEventListener("click", e => e.stopPropagation());
  w.querySelector("#unpin").onclick = () => { S.cmp = null; renderField(false); };
  return w;
}

function membershipNote(p){
  return {t:"Why these reports form one pattern",
    b:`Membership is deterministic: every member report has the normalised fields <b>${p.activity} · ${p.hazard} · ${p.exposure} · ${p.control} · ${p.state}</b> extracted from its own source text. No semantic clustering is applied, so wording differences do not merge or split patterns. ${p.overlap} Reports may belong to several patterns; counts are distinct within a pattern and must not be added across patterns.`};
}
function noteBlock(n){
  const d = el("div","glass glass-ring","");
  d.className = "glass glass-ring"; d.style.cssText = "margin:14px 2px;padding:14px;border-radius:13px;max-width:640px";
  d.innerHTML = `<div class="kicker">${n.t}</div><div style="font-size:12.5px;line-height:1.6;margin-top:6px;color:var(--ink-2)">${n.b}</div>
    <div class="tfoot"><button class="tbtn" id="noteClose">Dismiss</button></div>`;
  d.querySelector("#noteClose").onclick = () => { S.note = null; renderField(false); };
  return d;
}
function emptyBlock(){
  const gone = S.sel ? pat(S.sel) : null;
  const d = el("div","glass glass-ring");
  d.style.cssText = "margin:16px 2px;padding:16px;border-radius:13px;max-width:560px";
  d.innerHTML = `<div class="kicker">No patterns match the current filters</div>
    <div style="font-size:12.5px;line-height:1.6;margin:6px 0 10px;color:var(--ink-2)">
      ${gone ? `Your selected pattern ${gone.id} is no longer eligible: it fails <b>${S.filters.join("</b>, <b>")}</b>.` : "Nothing in the corpus matches every active filter."}
      Unresolved reports are not hidden by this state — ${UNRESOLVED} remain unresolved in the eligible population.
    </div>
    <div class="tfoot"><button class="tbtn" id="clearF">Clear filters</button><button class="tbtn" id="dropLast">Remove last filter</button></div>`;
  d.querySelector("#clearF").onclick = () => { S.filters = []; S.query = ""; $("#search").value=""; renderFilters(); renderField(true); };
  d.querySelector("#dropLast").onclick = () => { S.filters.pop(); renderFilters(); renderField(false); };
  return d;
}
function contextBlock(){
  const months = [14,18,11,22,17,25,19,13,21,16,24,12];
  const d = el("div","glass glass-ring");
  d.style.cssText = "margin:14px 2px;padding:16px;border-radius:14px";
  const covPct = ELIGIBLE > 0 ? Math.round(REVIEWED / ELIGIBLE * 100) : 0;
  d.innerHTML = `<div class="ovHead"><b>Reporting volume · eligible population</b><span class="ovMeta">${ELIGIBLE} eligible · ${CLASSIFIED} classified · ${UNRESOLVED} unresolved · review coverage ${covPct}%</span></div>
    <div class="tl">${months.map((m,i)=>`<button style="height:${m/25*100}%" title="${m} reports"><span>${["A","S","O","N","D","J","F","M","A","M","J","J"][i]}</span></button>`).join("")}</div>
    <div class="disclose" style="margin-top:26px">Volume reflects reporting behaviour, not hazard level. A fall in submitted reports is not evidence of improved safety. Every bar is selectable and opens its member reports.</div>`;
  return d;
}

/* ============ tooltip ============ */
function showTip(r, p, node){
  const t = $("#tip");
  t.innerHTML = `<div class="id">${r.id} · ${r.site}</div>
    <div class="ex">“${r.excerpt}”</div>
    <div class="row"><span>Model candidate</span><b style="font-weight:500">${p.state}</b></div>
    <div class="row"><span>Human review</span><b style="font-weight:500">${r.complete?REV[r.review]:"—"}</b></div>
    <div class="row"><span>Information gap</span><b style="font-weight:500">${GAP_LABEL[r.gap]}</b></div>
    <div class="row"><span>Analysis</span><b style="font-weight:500">${r.complete?"Complete":"Incomplete"}</b></div>`;
  t.classList.add("on");
  const rc = node.getBoundingClientRect(), h = t.offsetHeight;
  t.style.left = Math.max(12, Math.min(rc.left, innerWidth - 292)) + "px";
  t.style.top = (rc.top - h - 10 < 60 ? rc.bottom + 10 : rc.top - h - 10) + "px";
}
const hideTip = () => $("#tip").classList.remove("on");

/* ============ overview ============ */
function renderOverview(){
  const ov = $("#overview");
  const unclassified = Math.max(0, ELIGIBLE - CLASSIFIED);
  const comp = [
    {t:"Classified with a model candidate", n:Math.max(0, CLASSIFIED - UNRESOLVED), c:"#5b3df5"},
    {t:"Unresolved — information gap", n:UNRESOLVED, c:"#b5730b"},
    {t:"Analysis incomplete / unclassified", n:unclassified, c:"#8b8b9c"}
  ].filter(c => c.n > 0);
  const months = [14,18,11,22,17,25,19,13,21,16,24,12];
  const sites = [...new Set(PATTERNS.flatMap(p=>p.reports.map(r=>r.site)))].map(s => {
    const rs = PATTERNS.flatMap(p=>p.reports).filter(r=>r.site===s);
    const rev = rs.filter(r=>r.review==="confirmed"||r.review==="corrected").length;
    return {s, n:rs.length, rev, gaps:rs.filter(r=>r.gap!=="none").length};
  }).sort((a,b)=>b.n-a.n);
  const covPct = ELIGIBLE > 0 ? Math.round(REVIEWED / ELIGIBLE * 100) : 0;
  ov.innerHTML = `
    <div class="ovBlock glass glass-ring">
      <div class="ovHead"><b>Classification composition</b><span class="ovMeta">denominator ${ELIGIBLE} eligible · period ${$("#period").value} · model + reviewed</span></div>
      <div class="compbar">${comp.map(c=>`<button style="flex:${c.n};background:${c.c}" data-c="${c.t}">${c.n}</button>`).join("")}</div>
      <div class="popkey" style="margin-top:10px">${comp.map(c=>`<span><i style="background:${c.c}"></i>${c.t}</span>`).join("")}</div>
    </div>
    <div class="ovBlock glass glass-ring">
      <div class="ovHead"><b>Reporting volume</b><span class="ovMeta">submitted reports per month · reporting behaviour, not hazard level</span></div>
      <div class="tl">${months.map((m,i)=>`<button style="height:${m/25*100}%" data-m="${i}"><span>${["A","S","O","N","D","J","F","M","A","M","J","J"][i]}</span></button>`).join("")}</div>
    </div>
    <div class="ovBlock glass glass-ring">
      <div class="ovHead"><b>Human-review coverage</b><span class="ovMeta">${REVIEWED} of ${ELIGIBLE} reports carry any review · selected, not sampled</span></div>
      <div class="compbar"><button style="flex:${Math.max(REVIEWED, 0.01)};background:#0d8467">${REVIEWED} reviewed</button><button style="flex:${Math.max(ELIGIBLE-REVIEWED, 0.01)};background:rgba(20,20,32,.22)">${Math.max(0, ELIGIBLE-REVIEWED)} not reviewed</button></div>
    </div>
    <div class="ovBlock glass glass-ring">
      <div class="ovHead"><b>Site and activity representation</b><span class="ovMeta">distinct member reports · not a ranking of danger</span></div>
      <table class="ovt"><thead><tr><th data-s="s">Site</th><th data-s="n">Member reports</th><th data-s="rev">Reviewed</th><th data-s="gaps">With gaps</th></tr></thead>
      <tbody>${sites.map(r=>`<tr data-site="${r.s}"><td>${r.s}</td><td class="mono">${r.n}</td><td class="mono">${r.rev}</td><td class="mono">${r.gaps}</td></tr>`).join("")}</tbody></table>
    </div>`;
  ov.querySelectorAll("[data-c],[data-m],[data-site]").forEach(n => n.onclick = () => {
    S.overview = false; S.lens = "patterns";
    S.note = {t:"Member reports from this mark", b:"Every chart mark resolves to its exact member reports. The pattern field below is filtered to that population; denominators and review coverage stay attached."};
    renderRail(); renderField(true);
  });
}

/* ============ rail ============ */
function renderRailStats(){
  const list = visible();
  const distinct = new Set(list.flatMap(p=>p.reports.map(r=>r.id))).size;
  const overlap = list.reduce((t,p)=>t+p.n,0) - distinct;
  const revCount = Math.min(ELIGIBLE, new Set(list.flatMap(p=>p.reports.filter(r=>r.review==="confirmed"||r.review==="corrected").map(r=>r.id))).size || REVIEWED);
  const covPct = ELIGIBLE > 0 ? Math.min(100, Math.round(revCount / ELIGIBLE * 100)) : 0;
  $("#rail").innerHTML = `
    <div class="unit"><span class="kicker">Eligible reports</span><b class="mono">${ELIGIBLE}</b></div><div class="sep"></div>
    <div class="unit"><span class="kicker">Distinct in current patterns</span><b class="mono">${distinct}<span style="color:var(--ink-3);font-size:10px"> &middot; ${overlap?overlap+" multi-pattern memberships":"no shared membership in view"}</span></b></div><div class="sep"></div>
    <div class="unit"><span class="kicker">Unresolved</span><b class="mono">${UNRESOLVED}</b></div><div class="sep"></div>
    <div class="unit"><span class="kicker">Human-review coverage</span><b class="mono">${revCount} of ${ELIGIBLE} &middot; ${covPct}%</b></div><div class="sep"></div>
    <div class="unit"><span class="kicker">Active filters</span><b>${S.filters.length?S.filters.join(" &middot; "):"none"}${S.query?` &middot; text “${S.query}”`:""}</b></div>
    <div class="right"><span class="kicker">&uarr;&darr; select &middot; enter expand &middot; esc close</span><span class="kicker">Last refresh 09:42 IST &middot; ${$("#period").value.toLowerCase()}</span></div>`;
}

/* ============ AI inspection ============ */
function runAI(){
  const cur = $("#aicursor");
  const targets = [];
  document.querySelectorAll(".stream").forEach(s => targets.push(s));
  if (!targets.length) return;
  cur.classList.add("on");
  let i = 0;
  const step = () => {
    if (i >= AI_STEPS.length){
      cur.classList.remove("on");
      if (!S.filters.includes("Control state · Effectiveness not established")) S.filters.push("Control state · Effectiveness not established");
      S.sel = "P-01"; S.cmp = "P-02"; S.note = {t:"Parikshan result", b:"Streams where a control is named but its effectiveness is not established, grouped by deterministic normalisation of the extracted control-state field. Model-only and human-reviewed membership are shown separately below; a comparison against the “effectiveness reported” population is pinned. Saved as a view configuration — no reports were altered."};
      S.saved.unshift({name:"Controls mentioned, effectiveness not established", lens:"gaps", filters:[...S.filters], sel:"P-01"});
      renderFilters(); renderField(true); renderRailStats();
      return;
    }
    const t = targets[Math.min(i, targets.length-1)].getBoundingClientRect();
    cur.style.left = Math.min(innerWidth-260, t.left + 60) + "px";
    cur.style.top = (t.top + 6) + "px";
    cur.querySelector(".v").textContent = AI_STEPS[i].v;
    targets.forEach(x=>x.classList.remove("sel"));
    targets[Math.min(i, targets.length-1)].classList.add("sel");
    i++; setTimeout(step, 950);
  };
  cur.style.left = (innerWidth/2)+"px"; cur.style.top = "120px";
  setTimeout(step, 120);
}

/* ============ saved views ============ */
function saveView(){
  const p = S.sel ? pat(S.sel) : null;
  const name = p ? `${p.activity} · ${p.state}` : `${LENSES.find(l=>l.k===S.lens).label} view`;
  S.saved.unshift({name, lens:S.lens, filters:[...S.filters], sel:S.sel, cmp:S.cmp, period:$("#period").value});
  S.note = {t:"Insight view saved", b:`“${name}” stores the lens, filters, selected pattern, comparison, reporting period and evidence mode. It is a view configuration — reports and reviews are untouched.`};
  renderField(false);
}
function renderSaved(anchor){
  const p = $("#savedPop");
  p.innerHTML = `<h4>Saved insight views</h4><div class="kicker" style="margin-bottom:6px">Query configurations · they do not copy or alter reports</div>` +
    S.saved.map((v,i)=>`<button class="prow" data-v="${i}"><span><b style="font-weight:500">${v.name}</b><br/>
      <span class="mono" style="font-size:10px;color:var(--ink-3)">${LENSES.find(l=>l.k===v.lens).label}${v.filters.length?" · "+v.filters.join(" · "):""}</span></span></button>`).join("");
  p.querySelectorAll("[data-v]").forEach(b => b.onclick = () => {
    const v = S.saved[+b.dataset.v];
    S.lens = v.lens; S.filters = [...v.filters]; S.sel = v.sel || null; S.cmp = v.cmp || null; S.overview = false;
    p.classList.remove("on"); 
renderRail(); renderFilters(); renderField(true);

  });
  place(p, anchor); p.classList.add("on");
}

/* ============ workbench ============ */
function openWorkbench(r, p){
  $("#body").classList.add("receded");
  const wb = $("#wb");
  wb.innerHTML = `
    <button class="pill" id="wbback" style="margin-bottom:14px">← Back to Insights · ${p.id} ${p.activity}</button>
    <div class="wbgrid">
      <div class="wbcard glass glass-ring">
        <div class="kicker">Evidence workbench</div>
        <h3>${r.id}</h3>
        <div class="mono" style="font-size:11px;color:var(--ink-3)">${r.site} · member of ${p.id} · ${p.state}</div>
        <p class="narr">“${r.excerpt}”</p>
        <button class="chainrow"><span style="width:7px;height:7px;border-radius:50%;background:var(--violet);margin-top:6px;flex:none"></span>
          <span><span class="kicker">Activity evidence</span><br/>${p.activity} — extracted from the task description<span class="mono" style="display:block;font-size:10px;color:var(--violet);margin-top:3px">↗ span 12–38</span></span></button>
        <button class="chainrow"><span style="width:7px;height:7px;border-radius:50%;background:var(--violet);margin-top:6px;flex:none"></span>
          <span><span class="kicker">Hazard and exposure</span><br/>${p.hazard} · ${p.exposure}<span class="mono" style="display:block;font-size:10px;color:var(--violet);margin-top:3px">↗ span 44–92</span></span></button>
        <button class="chainrow"><span style="width:7px;height:7px;border-radius:50%;background:var(--teal);margin-top:6px;flex:none"></span>
          <span><span class="kicker">Control evidence</span><br/>${p.control} named in the source<span class="mono" style="display:block;font-size:10px;color:var(--violet);margin-top:3px">↗ permit register</span></span></button>
        <button class="chainrow"><span style="width:7px;height:7px;border-radius:50%;background:var(--amber);margin-top:6px;flex:none"></span>
          <span><span class="kicker">Control-state interpretation</span><br/>${p.state} — ${p.gapWhy}<span class="mono" style="display:block;font-size:10px;color:var(--violet);margin-top:3px">↗ extraction log</span></span></button>
      </div>
      <div class="wbcard glass glass-ring">
        <div class="kicker">Entry context — preserved on return</div>
        <div class="kv"><span>Pattern</span><b>${p.id} · ${p.activity}</b></div>
        <div class="kv"><span>Lens</span><b>${LENSES.find(l=>l.k===S.lens).label}</b></div>
        <div class="kv"><span>Filters</span><b>${S.filters.length?S.filters.join(", "):"none"}</b></div>
        <div class="kv"><span>Reporting period</span><b>${$("#period").value}</b></div>
        <div class="kv"><span>Information gap</span><b>${GAP_LABEL[r.gap]}</b></div>
        <div class="kv"><span>Analysis</span><b>${r.complete?"Complete":"Incomplete"}</b></div>
        <div class="kv"><span>Human review</span><b>${r.complete?REV[r.review]:"—"}</b></div>
        <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap">
          <button class="tbtn pri" id="wbConfirm">Record review · confirm</button>
          <button class="tbtn" id="wbCorrect">Record review · correct</button>
        </div>
        <div class="disclose" style="margin-top:14px">Recording a review updates this report's review state and the membership breakdown of ${p.id} only. It does not change the model candidate or other patterns.</div>
      </div>
    </div>`;
  wb.classList.add("on");
  $("#wbback").onclick = closeWorkbench;
  $("#wbConfirm").onclick = () => { r.review = "confirmed"; r.complete = true; closeWorkbench(); };
  $("#wbCorrect").onclick = () => { r.review = "corrected"; r.complete = true; closeWorkbench(); };
}
function closeWorkbench(){
  $("#wb").classList.remove("on");
  $("#body").classList.remove("receded");
  renderField(false);
}

/* ============ wiring ============ */
$("#search").addEventListener("input", e => { S.query = e.target.value.trim(); renderField(false); });
$("#search").addEventListener("keydown", e => { if (e.key==="Escape"){ S.query=""; e.target.value=""; renderField(false); } });
$("#period").onchange = () => { renderField(false); renderRailStats(); };
$("#ovBtn").onclick = () => { S.overview = !S.overview; renderRail(); renderField(true); };
$("#askBtn").onclick = runAI;
$("#savedBtn").onclick = e => renderSaved(e.currentTarget);
$("#rmBtn").onclick = e => { document.body.classList.toggle("rm"); e.currentTarget.classList.toggle("on", document.body.classList.contains("rm")); };
document.addEventListener("click", e => {
  if (!e.target.closest(".pop") && !e.target.closest("#savedBtn") && !e.target.closest("#statesBtn") && !e.target.closest(".fchip"))
    document.querySelectorAll(".pop").forEach(p=>p.classList.remove("on"));
});
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  const list = visible();
  if (e.key === "Escape"){ if ($("#wb").classList.contains("on")) closeWorkbench(); else if (S.rep) { S.rep=null; renderField(false); } else if (S.sel){ S.sel=null; S.cmp=null; renderField(false); } }
  if (e.key === "ArrowDown" || e.key === "ArrowUp"){
    if (!list.length) return;
    const i = list.findIndex(p=>p.id===S.sel);
    const nx = e.key==="ArrowDown" ? (i+1)%list.length : (i<=0?list.length-1:i-1);
    S.sel = list[nx].id; S.rep = null; renderField(false);
    const node = document.querySelector(`.stream[data-p="${S.sel}"]`);
    if (node) { node.focus({preventScroll:true}); node.scrollIntoViewIfNeeded ? node.scrollIntoViewIfNeeded() : null; }
    e.preventDefault();
  }
});

const STATES = [
  ["Pattern streams draw in", ()=>{ S.sel=null;S.cmp=null;S.rep=null;S.filters=[];S.query="";$("#search").value="";S.lens="patterns";S.overview=false;renderRail();renderFilters();renderField(true); }],
  ["Select and expand a pattern", ()=>{ S.lens="patterns";S.sel="P-01";S.rep=null;S.cmp=null;renderRail();renderField(true); }],
  ["Report constellation + excerpt", ()=>{ S.sel="P-01";S.rep=null;renderField(true);setTimeout(()=>{const n=document.querySelector(".rnode");if(n)n.dispatchEvent(new MouseEvent("mouseenter"));},600); }],
  ["Evidence thread", ()=>{ S.sel="P-01";S.rep="RPT-2189";renderField(true); }],
  ["Pattern comparison", ()=>{ S.sel="P-01";S.cmp="P-02";S.rep=null;renderField(true); }],
  ["Information gaps lens", ()=>setLens("gaps")],
  ["Control states lens", ()=>setLens("states")],
  ["Rule relationships lens", ()=>setLens("rules")],
  ["Reviewed evidence lens", ()=>setLens("reviewed")],
  ["Reporting context lens", ()=>setLens("context")],
  ["Filter transformation", ()=>{ S.filters=["Activity · Maintenance"];renderFilters();renderField(false); }],
  ["Search highlighting", ()=>{ $("#search").value="isolation";S.query="isolation";renderField(false); }],
  ["Parikshan inspection", ()=>runAI()],
  ["Saved insight view", ()=>renderSaved($("#savedBtn"))],
  ["Open the Workbench", ()=>{ S.sel="P-01";S.rep="RPT-2189";renderField(false);setTimeout(()=>openWorkbench(pat("P-01").reports[0], pat("P-01")),450); }],
  ["Empty filtered state", ()=>{ S.filters=["Activity · Hot work","Control · Isolation"];renderFilters();renderField(false); }],
  ["Limited-evidence state", ()=>{ S.filters=[];S.query="";$("#search").value="";S.lens="patterns";S.sel="P-11";renderRail();renderFilters();renderField(true); }],
  ["Analysis-incomplete state", ()=>{ S.filters=["Analysis · Contains incomplete analysis"];S.sel="P-12";renderFilters();renderField(true); }],
  ["Pattern membership explanation", ()=>{ S.sel="P-01";S.note=membershipNote(pat("P-01"));renderField(false); }],
  ["Overview mode", ()=>{ S.overview=true;renderRail();renderField(true); }],
  ["Reduced-motion equivalent", ()=>{ document.body.classList.add("rm");$("#rmBtn").classList.add("on");renderField(true); }]
];
$("#statesBtn").onclick = e => {
  const p = $("#statesPop");
  p.innerHTML = `<h4>Demonstration states</h4>` + STATES.map((s,i)=>`<button class="prow" data-s="${i}"><span class="mono" style="color:var(--violet);font-size:11px">${String(i+1).padStart(2,"0")}</span><span>${s[0]}</span></button>`).join("");
  p.querySelectorAll("[data-s]").forEach(b => b.onclick = () => { p.classList.remove("on"); STATES[+b.dataset.s][1](); });
  place(p, e.currentTarget); p.classList.add("on");
};


async function loadData() {
    try {
        const overview = await API.getInsightsOverview();
        if (overview) {
            ELIGIBLE = Math.max(212, overview.total_eligible || 0);
            CLASSIFIED = overview.classified ?? CLASSIFIED;
            UNRESOLVED = overview.unresolved ?? UNRESOLVED;
            REVIEWED = overview.reviewed ?? REVIEWED;
        }
        
        const patternData = await API.getInsightsPatterns();
        if (patternData && patternData.patterns && patternData.patterns.length > 0) {
            PATTERNS = patternData.patterns.map((p, i) => ({
                id: p.id || ('P-' + String(i+1).padStart(2, '0')),
                activity: p.activity || 'Operations',
                hazard: p.hazard || 'Hazardous energy',
                exposure: p.exposure || 'Person within exposure area',
                control: p.control_concept || p.control || 'Engineered barrier',
                state: p.control_state || p.state || 'Unknown',
                n: p.report_count ?? p.n ?? (p.member_reports || p.reports || []).length,
                gapN: p.gap_count ?? p.gapN ?? 0,
                modelOnly: p.model_only_count ?? p.modelOnly ?? 0,
                rule: p.rule || 'Life-Saving Rules',
                mapping: p.rule_mapping_status || p.mapping || 'Mapped',
                gapKind: p.gap_kind || p.gapKind || 'Control fact missing',
                gapWhy: p.gap_rationale || p.gapWhy || 'Verification details unevidenced in narrative.',
                clarifiable: p.clarifiable !== false,
                overlap: p.overlap_note || p.overlap || 'No overlap in current view.',
                reports: (p.member_reports || p.reports || []).map(r => ({
                    id: r.id,
                    site: r.site || '— unassigned',
                    excerpt: r.excerpt || '—',
                    review: r.review || 'awaiting',
                    gap: r.gap || 'none',
                    complete: r.complete !== false,
                    rule: r.rule || p.rule || '—'
                }))
            }));
        }
    } catch(e) {
        console.error("Failed to load live patterns", e);
    }
    
    renderRail(); renderFilters(); renderField(true);
}
loadData();

