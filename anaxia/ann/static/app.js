"use strict";

const $ = id => document.getElementById(id);
const canvas = $("graph");
const ctx = canvas.getContext("2d");
const colors = {running:"#008963", completed:"#6d53b1", failed:"#be4559",
  queued:"#c28321", dormant:"#a5bbb3", cancelled:"#818c89"};
const format = value => new Intl.NumberFormat().format(value);
const state = {catalog:null, current:null, snap:null, picked:null, offset:0, zoom:1, x:0, y:0,
  nodes:[], token:null, busy:false, filter:0};

function element(tag, value, className) {
  const node = document.createElement(tag);
  node.textContent = value;
  if (className) node.className = className;
  return node;
}

function notice(message) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}

async function request(path, payload) {
  const options = payload === undefined ? {} : {
    method:"POST", headers:{"Content-Type":"application/json","X-ANN-Token":state.token},
    body:JSON.stringify(payload)
  };
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request failed.");
  return data;
}

function definition(id) {
  return state.catalog?.strategies.find(route => route.id === id);
}

function renderLibrary() {
  const panel = $("library");
  panel.replaceChildren(element("h1","Methods and sources"));
  const sections = [
    ["Research routes", state.catalog.strategies.map(r => ({name:r.name, detail:r.method, badge:r.capability}))],
    ["Working engines", state.catalog.engines.map(r => ({name:r.name, detail:r.role, badge:r.status}))],
    ["Recent organization imports", state.catalog.integrations.map(r =>
      ({name:r.name, detail:r.role, badge:r.license + " · reference", url:r.url}))]
  ];
  for (const [name, rows] of sections) {
    panel.append(element("h2",name));
    const grid = element("div","","library-grid");
    for (const row of rows) {
      const card = element("article","","library-card");
      const title = element("strong",row.name);
      if (row.url) {
        const link = element("a",row.name);
        link.href = row.url;
        title.replaceChildren(link);
      }
      card.append(title, element("p",row.badge,"eyebrow"), element("p",row.detail));
      grid.append(card);
    }
    panel.append(grid);
  }
}

function showTab(library) {
  $("library").hidden = !library;
  $("workbench").hidden = library;
  $("library-tab").setAttribute("aria-pressed",String(library));
  $("graph-tab").setAttribute("aria-pressed",String(!library));
  if (!library) paint();
}

function listMissions(missions) {
  const container = $("missions");
  const signature = JSON.stringify(missions.map(m => [m.id,m.title,m.status,m.agent_count])) + state.current;
  if (container.dataset.signature === signature) return;
  container.dataset.signature = signature;
  container.replaceChildren();
  for (const m of missions) {
    const button = element("button", m.title,"mission-button");
    button.append(element("small", m.status + " · " + format(m.agent_count) + " profiles"));
    button.setAttribute("aria-current",String(m.id === state.current));
    button.addEventListener("click",() => selectMission(m.id));
    container.append(button);
  }
  if (!missions.length) container.append(element("p","Your research missions will appear here."));
}

function selectMission(id) {
  state.current = id;
  state.snap = null;
  state.offset = 0;
  state.picked = null;
  state.zoom = 1;
  state.x = 0;
  state.y = 0;
  $("downloads").replaceChildren();
  showTab(false);
  refresh();
}

function inspect() {
  const panel = $("selection");
  panel.replaceChildren();
  const node = state.nodes.find(item => item.id === state.picked);
  if (!node) return;
  if (node.agent) {
    const a = node.agent;
    panel.append(element("h3","Agent " + format(a.index + 1)),
      element("p", (definition(a.strategy)?.name || a.strategy) + " · " + a.status));
    if (a.result?.status) panel.append(element("strong",a.result.status.replaceAll("_"," ")));
    for (const key of ["summary","finding","scope","proposal","model_error"]) {
      if (a.result?.[key]) panel.append(element("p",a.result[key]));
    }
  } else if (node.route) {
    const route = definition(node.route);
    panel.append(element("h3",route.name),element("p",route.method),element("small",route.capability));
  } else {
    panel.append(element("h3","Research question"),element("p",state.snap.mission.statement));
  }
}

function drawSnapshot(snap) {
  const m = snap.mission, counts = snap.counts;
  $("title").textContent = m.title;
  $("statement").textContent = m.statement;
  $("registered").textContent = format(m.agent_count);
  $("active").textContent = format(counts.running || 0) + " / " + m.concurrency;
  $("completed").textContent = format((counts.completed || 0) + (counts.failed || 0)) + " / " + format(m.max_tasks);
  $("calls").textContent = format(m.model_calls_reserved) + " / " + format(m.max_model_calls);
  $("blank").hidden = true;
  $("graph-count").textContent = "Profiles " + format(snap.offset + 1) + "–" +
    format(snap.offset + snap.agents.length) + " of " + format(m.agent_count);
  $("prev").disabled = !snap.offset;
  $("next").disabled = snap.next_offset === null;
  $("state").textContent = m.status;
  $("inspect-title").textContent = m.exploration === "wide" ? "Wide exploration" : "Mission details";
  const canStart = m.status === "queued" || m.status === "paused" || m.status === "running";
  $("start").disabled = !canStart;
  $("start").textContent = m.status === "paused" ? "Resume" : m.status === "running" ? "Continue" : "Start";
  $("pause").disabled = m.status !== "running";
  $("cancel").disabled = !canStart;
  $("export").disabled = false;
  $("gaps").replaceChildren(...(m.gaps.length ? m.gaps : ["Review the exact statement and exported certificate."])
    .map(gap => element("li",gap)));
  const entries = snap.events.slice().reverse().map(event => {
    const item = document.createElement("li");
    const stamp = element("time",new Date(event.created_at*1000).toLocaleTimeString());
    item.append(stamp,element("strong",event.kind.replaceAll("_"," ")));
    if (event.payload.strategy) item.append(document.createTextNode(" · " + (definition(event.payload.strategy)?.name || event.payload.strategy)));
    if (Number.isInteger(event.payload.slot)) item.append(document.createTextNode(" · agent " + format(event.payload.slot+1)));
    if (event.payload.summary) item.append(document.createTextNode(" — " + event.payload.summary));
    return item;
  });
  $("activity").replaceChildren(...entries);
  paint();
  if (state.picked && !state.nodes.some(node => node.id === state.picked)) state.picked = null;
  const selected = state.nodes.find(node => node.id === state.picked);
  const key = JSON.stringify(selected?.agent || selected?.route || state.picked);
  if (key !== state.selectionKey) {
    state.selectionKey = key;
    inspect();
  }
}

async function refresh() {
  if (state.busy || !state.catalog) return;
  state.busy = true;
  try {
    const {missions} = await request("/api/missions");
    if (!state.current && missions.length) state.current = missions[0].id;
    listMissions(missions);
    if (state.current) {
      const current = state.current, offset = state.offset;
      const snap = await request("/api/missions/" + current + "?offset=" + offset + "&limit=512");
      if (current === state.current && offset === state.offset) {
        state.snap = snap;
        drawSnapshot(snap);
      }
    }
    $("connection").textContent = "Local service";
    $("connection").classList.add("ready");
  } catch (error) {
    $("connection").textContent = "Disconnected";
    $("connection").classList.remove("ready");
    notice(error.message);
  } finally {
    state.busy = false;
  }
}

function paint() {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  if (!width || !height) return;
  const density = Math.min(devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(width*density) || canvas.height !== Math.round(height*density)) {
    canvas.width = Math.round(width*density);
    canvas.height = Math.round(height*density);
  }
  ctx.setTransform(density,0,0,density,0,0);
  ctx.clearRect(0,0,width,height);
  if (!state.snap) { state.nodes = []; return; }
  const {mission, agents} = state.snap;
  const root = {id:mission.id, x:width/2 + state.x, y:height/2 + state.y, radius:21, color:"#185c49"};
  const routes = mission.strategies;
  const byRoute = new Map(routes.map(id => [id,[]]));
  agents.forEach(agent => byRoute.get(agent.strategy)?.push(agent));
  const nodes = [root];
  const edge = (from,to, color) => {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.moveTo(from.x,from.y);
    ctx.lineTo(to.x,to.y);
    ctx.stroke();
  };
  const radial = Math.min(width,height) * .255 * state.zoom;
  routes.forEach((id,i) => {
    const angle = 2*Math.PI*i/routes.length - Math.PI/2;
    const parent = {id:"route:"+id, route:id, x:root.x + radial*Math.cos(angle),
      y:root.y + radial*Math.sin(angle), radius:9, color:"#5a718b"};
    nodes.push(parent);
    edge(root,parent,"#91b9a9");
    const children = byRoute.get(id);
    children.forEach((agent,j) => {
      const a = angle + (j*2.3999632297);
      const d = (14 + 5.7*Math.sqrt(j)) * Math.min(width/650,1) * state.zoom;
      const child = {id:agent.id, agent, x:parent.x+d*Math.cos(a), y:parent.y+d*Math.sin(a),
        radius:agent.status === "running" ? 4.6 : agents.length > 150 ? 2.6 : 3.6,
        color:colors[agent.status] || colors.dormant};
      nodes.push(child);
      edge(parent,child,agent.status === "running" ? "#69b9a0" : "#dbe6df");
    });
  });
  for (const node of [...nodes].reverse()) {
    ctx.beginPath();
    ctx.arc(node.x,node.y,node.radius,0,2*Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();
    if (state.picked === node.id || node.agent?.status === "running") {
      ctx.beginPath();
      ctx.arc(node.x,node.y,node.radius+3,0,2*Math.PI);
      ctx.strokeStyle = state.picked === node.id ? "#162b27" : "#6dd0ac";
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.lineWidth = 1;
    }
    if (node.route && routes.length <= 10) {
      ctx.font = "600 11px Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.strokeStyle = "#f7fbf7";
      ctx.lineWidth = 4;
      const label = definition(node.route)?.name || node.route;
      ctx.strokeText(label,node.x,node.y+23);
      ctx.fillStyle = "#243e39";
      ctx.fillText(label,node.x,node.y+23);
      ctx.lineWidth = 1;
    }
  }
  ctx.font = "700 19px Georgia, serif";
  ctx.textAlign = "center";
  ctx.fillStyle = "#fff";
  ctx.fillText("a",root.x,root.y+6);
  state.nodes = nodes;
}

const zoom = factor => { state.zoom = Math.min(3.4,Math.max(.45,state.zoom*factor)); paint(); };
function pick(node) {
  state.picked = node?.id || null;
  paint();
  inspect();
}
let drag = null;
canvas.addEventListener("pointerdown",event => {
  drag = {x:event.clientX,y:event.clientY,baseX:state.x,baseY:state.y};
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove",event => {
  if (!drag) return;
  state.x = drag.baseX + event.clientX - drag.x;
  state.y = drag.baseY + event.clientY - drag.y;
  paint();
});
canvas.addEventListener("pointercancel",() => { drag=null; });
canvas.addEventListener("pointerup",event => {
  if (drag && Math.hypot(event.clientX-drag.x,event.clientY-drag.y)<5) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX-rect.left, y = event.clientY-rect.top;
    pick(state.nodes.filter(node => Math.hypot(node.x-x,node.y-y) <= Math.max(9,node.radius+3))
      .sort((a,b)=>Math.hypot(a.x-x,a.y-y)-Math.hypot(b.x-x,b.y-y))[0]);
  }
  drag=null;
});
canvas.addEventListener("wheel",event => { event.preventDefault(); zoom(event.deltaY>0?.9:1.11); },{passive:false});
canvas.addEventListener("keydown",event => {
  const scale = 22;
  const moves = {ArrowLeft:[scale,0],ArrowRight:[-scale,0],ArrowUp:[0,scale],ArrowDown:[0,-scale]};
  if (event.key in moves) {
    event.preventDefault();
    state.x += moves[event.key][0];
    state.y += moves[event.key][1];
    paint();
  } else if (event.key === "+" || event.key === "=") zoom(1.12);
  else if (event.key === "-") zoom(.89);
  else if (event.key === "]" || event.key === "[") {
    const i = state.nodes.findIndex(node=>node.id===state.picked);
    if (state.nodes.length) pick(state.nodes[(i+state.nodes.length+(event.key==="]"?1:-1))%state.nodes.length]);
  }
});
new ResizeObserver(paint).observe(canvas);
$("zoom-in").onclick = () => zoom(1.18);
$("zoom-out").onclick = () => zoom(.85);
$("fit").onclick = () => { state.zoom=1; state.x=0; state.y=0; paint(); };
$("prev").onclick = () => { state.offset=Math.max(0,state.offset-512); refresh(); };
$("next").onclick = () => {
  if (state.snap?.next_offset != null) { state.offset=state.snap.next_offset; refresh(); }
};
$("graph-tab").onclick = () => showTab(false);
$("library-tab").onclick = () => showTab(true);

function composer() {
  if (!state.catalog) { notice("Wait for the local service to connect."); return; }
  $("form-error").textContent = "";
  $("composer").showModal();
}
$("new").onclick = composer;
$("new-empty").onclick = composer;
$("close").onclick = () => $("composer").close();
$("target").onchange = () => { $("custom").hidden=$("target").value!=="custom"; };
$("mode").onchange = () => { $("model-fields").hidden=$("mode").value!=="model"; };
$("mission-form").onsubmit = async event => {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button[type="submit"]');
  const f = new FormData(event.currentTarget);
  const body = {template_id:f.get("template_id"), exploration:f.get("exploration"), mode:f.get("mode")};
  for (const key of ["agent_count","concurrency","max_tasks"]) body[key]=Number(f.get(key));
  button.disabled=true;
  try {
    if (body.template_id==="custom") {
      body.title=f.get("title");
      body.statement=f.get("statement");
      if (f.get("task").trim()) body.task=JSON.parse(f.get("task"));
    }
    if (body.mode==="model") {
      body.max_model_calls=Number(f.get("max_model_calls"));
      body.modelconfig={provider:f.get("provider"), model:f.get("model"),
        base_url:f.get("base_url") || null, max_tokens:Number(f.get("max_tokens"))};
    }
    const {mission} = await request("/api/missions",body);
    $("composer").close();
    notice("");
    selectMission(mission.id);
  } catch (error) {
    $("form-error").textContent=error.message;
  } finally {
    button.disabled=false;
  }
};

async function control(action) {
  const id = state.current;
  if (!id) return;
  try {
    await request("/api/missions/" + id + "/control",{action});
    notice("");
    await refresh();
  } catch (error) { notice(error.message); }
}
$("start").onclick = () => control(state.snap?.mission.status==="paused" ? "resume" : "start");
$("pause").onclick = () => control("pause");
$("cancel").onclick = () => control("cancel");
$("export").onclick = async () => {
  const id = state.current;
  const downloads = $("downloads");
  downloads.replaceChildren(element("p","Assembling and rechecking evidence…"));
  try {
    const data = await request("/api/missions/" + id + "/export",{pdf:$("export-pdf").checked});
    if (id!==state.current) return;
    downloads.replaceChildren(element("p",data.status));
    for (const file of data.files) {
      const link=element("a",file.name==="mission.zip"?"Download complete bundle":file.name);
      link.href=file.url;
      if (file.name==="mission.zip") link.download="ann-mission.zip";
      downloads.append(link);
    }
  } catch (error) { if (id===state.current) downloads.replaceChildren(element("p",error.message)); }
};

async function initialize() {
  try {
    const [health,catalog] = await Promise.all([request("/api/health"),request("/api/strategies")]);
    state.token=health.csrf_token;
    state.catalog=catalog;
    const select = $("target");
    for (const target of [...catalog.targets,{id:"custom",title:"Custom conjecture"}]) {
      const option=element("option",target.title);
      option.value=target.id;
      select.append(option);
    }
    renderLibrary();
    await refresh();
    setInterval(refresh,1800);
  } catch (error) {
    notice(error.message);
    setTimeout(initialize,2500);
  }
}
initialize();
