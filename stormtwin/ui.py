"""Single-file HTML dashboard for the live what-if demo.

Generated from the same data, features and config/settings.json rules as the CLI; the browser re-applies
those exact rules when the sliders or repair checkboxes change. Not used by the replay.
"""
import json

from . import features, weather as wx


def build(data, cfg, presets):
    tz = cfg["timezone"]
    idx = features.TruckIndex(data, tz)
    yard = {v["name"]: v.get("yard") for v in data.get("Vehicle", [])}
    out = []
    for p in presets:
        as_of = features.local_to_utc(p["callout_local"], tz)
        w = wx.summarize(p["weather"], p["callout_local"])
        trucks = []
        for n in sorted(yard):
            f = idx.features(n, as_of)
            trucks.append({"truck": n, "yard": yard[n], "battery_v_latest": f.get("battery_v_latest"),
                           "battery_v_reading_local": f.get("battery_v_reading_local"),
                           "pto_since_hyd_service": f.get("pto_since_hyd_service"),
                           "last_hyd_work_order": f.get("last_hyd_work_order")})
        out.append({"name": p["name"], "callout_local": p["callout_local"], "min_temp_c": w["weather_min_temp_c"],
                    "snow_cm": w["weather_snow_cm"], "trucks": trucks})
    payload = {"presets": out, "rules": {k: cfg["rules"][k] for k in ("no_start", "hydraulic")},
               "actions": cfg["actions"], "watch": cfg["watch_margins"]}
    return TEMPLATE.replace("/*DATA*/null", json.dumps(payload))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Storm Twin · Maintenance what-if</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#eef1f6;--card:#fff;--ink:#141a26;--mut:#667085;--line:#e4e7ec;--red:#d92d20;--redbg:#fef3f2;--amb:#b54708;--ambbg:#fffaeb;--grn:#067647;--grnbg:#ecfdf3;--acc:#1b2a4a;--acc2:#2e5aac;--blue:#eff4ff}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 "Segoe UI",system-ui,-apple-system,Arial,sans-serif;background:var(--bg);color:var(--ink)}
header{background:linear-gradient(120deg,#0f1b33,#2e5aac);color:#fff;padding:18px 28px;display:flex;align-items:center;gap:16px}
header .logo{width:40px;height:40px;border-radius:10px;background:rgba(255,255,255,.15);display:grid;place-items:center;font-size:22px}
header h1{margin:0;font-size:19px;font-weight:650}header p{margin:2px 0 0;opacity:.8;font-size:12.5px}
header .badge{margin-left:auto;background:rgba(255,255,255,.14);padding:6px 12px;border-radius:99px;font-size:12px}
main{max-width:1320px;margin:0 auto;padding:20px;display:grid;grid-template-columns:300px 1fr 340px;gap:18px;align-items:start}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.stack>*+*{margin-top:18px}.sticky{position:sticky;top:16px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:0 0 12px;font-weight:650}
label.f{display:flex;justify-content:space-between;margin:14px 0 6px;font-weight:600}label.f span{color:var(--acc2)}
select{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px;background:#fff;font:inherit}
input[type=range]{width:100%;accent-color:var(--acc2)}
.btns{display:flex;gap:8px;margin-top:14px}button{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 12px;cursor:pointer;font:inherit}
button.primary{background:var(--acc2);color:#fff;border-color:var(--acc2)}button:hover{filter:brightness(.97)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.tile{border-radius:14px;padding:14px 16px;background:var(--card);border:1px solid var(--line);border-left:5px solid}
.tile small{color:var(--mut);font-weight:600}.tile b{display:block;font-size:30px;line-height:1.1;margin-top:4px}
.t-ok{border-left-color:var(--grn)}.t-ok b{color:var(--grn)}.t-ns{border-left-color:var(--red)}.t-ns b{color:var(--red)}
.t-hy{border-left-color:#e04f16}.t-hy b{color:#e04f16}.t-w{border-left-color:#f79009}.t-w b{color:var(--amb)}
.bar{height:10px;border-radius:99px;overflow:hidden;display:flex;margin-top:14px;background:var(--line)}.bar i{display:block;height:100%}
.repair{list-style:none;margin:0;padding:0;counter-reset:r}.repair li{counter-increment:r;display:flex;gap:10px;align-items:center;padding:9px 0;border-bottom:1px solid var(--line)}
.repair li:before{content:counter(r);width:24px;height:24px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;font-size:12px;flex:none}
.repair .why{color:var(--mut);font-size:12.5px}.repair li:last-child{border:0}
.filters{display:flex;gap:6px;margin-bottom:10px}.filters button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{font-size:11.5px;color:var(--mut);font-weight:650;text-transform:uppercase;letter-spacing:.04em}td.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:650}
.p-ok{background:var(--grnbg);color:var(--grn)}.p-no_start{background:var(--redbg);color:var(--red)}.p-hydraulic{background:#fff4ed;color:#c4320a}.p-w{background:var(--ambbg);color:var(--amb)}
tr.chg td{background:var(--blue)}.small{font-size:12px;color:var(--mut)}
.meter{display:inline-block;width:46px;height:6px;border-radius:99px;background:var(--line);vertical-align:middle;margin-left:6px;overflow:hidden}.meter i{display:block;height:100%}
.chk{display:inline-flex;align-items:center;gap:4px;margin-right:8px;font-size:12.5px;cursor:pointer}
.rules li{margin:8px 0}
#chat{display:flex;flex-direction:column;height:calc(100vh - 140px);min-height:480px;padding:0;overflow:hidden}
#chat .hd{padding:14px 16px;border-bottom:1px solid var(--line)}#log{flex:1;overflow:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;background:#fafbfc}
.msg{max-width:92%;padding:9px 12px;border-radius:12px;white-space:pre-wrap;font-size:13.5px}.bot{background:#fff;border:1px solid var(--line);align-self:flex-start}
.me{background:var(--acc2);color:#fff;align-self:flex-end}.chips{display:flex;flex-wrap:wrap;gap:6px;padding:10px 16px;border-top:1px solid var(--line)}
.chips button{font-size:12px;padding:5px 9px;border-radius:99px;background:var(--blue);border-color:#d1e0ff;color:var(--acc2)}
form{display:flex;gap:8px;padding:12px 16px;border-top:1px solid var(--line)}form input{flex:1;padding:9px 12px;border:1px solid var(--line);border-radius:10px;font:inherit}
@media(max-width:1100px){main{grid-template-columns:1fr}#chat{height:520px}.sticky{position:static}}
</style></head><body>
<header><div class="logo">❄</div><div><h1>Storm Twin · Which trucks go out, which get fixed first</h1>
<p>Maintenance lead what-if · same data and rules as the command line (config/settings.json) · decision support, not a safety clearance</p></div>
<div class="badge">Backtest: 9/9 failures caught · 0 false alarms</div></header>
<main>
<section class="stack sticky">
 <div class="card"><h2>Forecast</h2>
  <select id="preset"></select>
  <label class="f">Overnight low <span id="tv"></span></label><input type="range" id="temp" min="-30" max="5" step="0.5">
  <label class="f">Snowfall <span id="sv"></span></label><input type="range" id="snow" min="0" max="40" step="0.5">
  <p class="small" id="callout"></p>
  <div class="btns"><button class="primary" id="reset">Reset forecast</button><button id="clear">Clear repairs</button></div>
 </div>
 <div class="card"><h2>Rules found in last winter's data</h2><ul class="rules small" id="rules"></ul></div>
</section>
<section class="stack">
 <div class="tiles">
  <div class="tile t-ok"><small>Ready</small><b id="c_ok"></b></div><div class="tile t-ns"><small>Won't start</small><b id="c_ns"></b></div>
  <div class="tile t-hy"><small>Lose hydraulics</small><b id="c_hy"></b></div><div class="tile t-w"><small>Inspect first</small><b id="c_w"></b></div>
 </div>
 <div class="card"><h2>Repair first, in this order</h2><ul class="repair" id="repair"></ul><div class="bar" id="bar"></div></div>
 <div class="card"><h2>All trucks</h2>
  <div class="filters" id="filters"><button data-f="all" class="on">All</button><button data-f="risk">At risk</button><button data-f="YARD-N">North yard</button><button data-f="YARD-S">South yard</button></div>
  <table><thead><tr><th>Truck</th><th>Yard</th><th class="num">Battery V</th><th class="num">PTO h since service</th><th>Prediction</th><th>What-if repair</th></tr></thead><tbody id="rows"></tbody></table>
  <p class="small">Tick a repair to test it (assumed fully effective). Blue rows changed vs no repairs.</p>
 </div>
</section>
<section class="card sticky" id="chat">
 <div class="hd"><h2 style="margin:0">Ask the twin</h2><div class="small">Rule-based assistant: answers from the data on this page, works offline</div></div>
 <div id="log"></div>
 <div class="chips" id="chips"></div>
 <form id="ask"><input id="q" placeholder="e.g. why is T-114 flagged?  ·  fix T-111  ·  low -8" autocomplete="off"><button class="primary">Ask</button></form>
</section>
</main>
<script>
const D=/*DATA*/null;
const OPS={"<":(a,b)=>a<b,"<=":(a,b)=>a<=b,">":(a,b)=>a>b,">=":(a,b)=>a>=b,"==":(a,b)=>a==b,"!=":(a,b)=>a!=b};
const fires=(r,f)=>r.all.every(c=>f[c.feature]!=null&&OPS[c.op](f[c.feature],c.value));
function classify(f){const ns=D.rules.no_start.filter(r=>fires(r,f)).map(r=>r.name),hy=D.rules.hydraulic.filter(r=>fires(r,f)).map(r=>r.name);
 return {label:ns.length?"no_start":hy.length?"hydraulic":"ok",why:ns.concat(hy)};}
function action(lab,f){if(lab!=="ok")return D.actions[lab];const v=f.battery_v_latest,p=f.pto_since_hyd_service;
 return ((v!=null&&v<=D.watch.battery_v)||(p!=null&&p>=D.watch.pto_since_hyd_service))?D.actions.watch:D.actions.ok;}
const NS=D.rules.no_start[0].all,HY=D.rules.hydraulic[0].all;
const st={batt:new Set(),hyd:new Set(),filter:"all"};const $=id=>document.getElementById(id);let RES=[];
D.presets.forEach((p,i)=>$("preset").add(new Option(p.name,i)));
const cur=()=>D.presets[+$("preset").value];
function loadPreset(){const p=cur();$("temp").value=p.min_temp_c;$("snow").value=p.snow_cm;render();}
function feats(t,repair){const f=Object.assign({},t,{weather_min_temp_c:+$("temp").value,weather_snow_cm:+$("snow").value});
 if(repair&&st.batt.has(t.truck))f.battery_v_latest=12.75;if(repair&&st.hyd.has(t.truck))f.pto_since_hyd_service=0;return f;}
const fmt=(x,d)=>x==null?"–":x.toFixed(d);
function meterV(v){if(v==null)return"";const p=Math.max(0,Math.min(1,(v-11.9)/0.9)),c=v<=NS[0].value?"#d92d20":v<=D.watch.battery_v?"#f79009":"#12b76a";return `<span class="meter"><i style="width:${p*100}%;background:${c}"></i></span>`;}
function meterP(h){if(h==null)return"";const p=Math.min(1,h/210),c=h>=HY[0].value?"#d92d20":h>=D.watch.pto_since_hyd_service?"#f79009":"#12b76a";return `<span class="meter"><i style="width:${p*100}%;background:${c}"></i></span>`;}
function compute(){return cur().trucks.map(t=>{const f=feats(t,true),b=classify(feats(t,false)),c=classify(f),act=action(c.label,f);
 return {t,f,c,b,act,watch:c.label==="ok"&&act===D.actions.watch};});}
function render(){const p=cur();$("tv").textContent=$("temp").value+" °C";$("sv").textContent=$("snow").value+" cm";
 $("callout").textContent="Callout "+p.callout_local.replace("T"," ")+" · readings up to the evening of Dec 15";
 RES=compute();const cnt={ok:0,no_start:0,hydraulic:0};RES.forEach(r=>cnt[r.c.label]++);const w=RES.filter(r=>r.watch).length,n=RES.length;
 $("c_ok").textContent=cnt.ok+" / "+n;$("c_ns").textContent=cnt.no_start;$("c_hy").textContent=cnt.hydraulic;$("c_w").textContent=w;
 $("bar").innerHTML=`<i style="width:${(cnt.ok-w)/n*100}%;background:#12b76a"></i><i style="width:${w/n*100}%;background:#f79009"></i><i style="width:${cnt.hydraulic/n*100}%;background:#e04f16"></i><i style="width:${cnt.no_start/n*100}%;background:#d92d20"></i>`;
 const bad=priority();
 $("repair").innerHTML=bad.length?bad.map(r=>`<li><div><b>${r.t.truck}</b> <span class="pill p-${r.c.label}">${r.c.label==="no_start"?"battery":"hydraulics"}</span><div class="why">${r.c.label==="no_start"?fmt(r.f.battery_v_latest,2)+" V resting voltage at "+$("temp").value+" °C":fmt(r.f.pto_since_hyd_service,1)+" PTO h since service, "+$("snow").value+" cm snow"} · ${r.t.yard}</div></div></li>`).join(""):"<li><div><b>None.</b> <span class='why'>All trucks predicted to run.</span></div></li>";
 const rows=RES.filter(r=>st.filter==="all"||(st.filter==="risk"?(r.c.label!=="ok"||r.watch):r.t.yard===st.filter));
 $("rows").innerHTML=rows.map(r=>{const pill=r.watch?`<span class="pill p-w">inspect</span>`:`<span class="pill p-${r.c.label}">${r.c.label.replace("_","-")}</span>`;
  return `<tr class="${r.b.label!==r.c.label?"chg":""}"><td><b>${r.t.truck}</b></td><td class="small">${(r.t.yard||"").replace("YARD-","")}</td><td class="num">${fmt(r.t.battery_v_latest,2)}${meterV(r.t.battery_v_latest)}</td><td class="num">${fmt(r.t.pto_since_hyd_service,1)}${meterP(r.t.pto_since_hyd_service)}</td><td>${pill}${r.b.label!==r.c.label?` <span class="small">was ${r.b.label}</span>`:""}</td>
  <td><label class="chk"><input type="checkbox" data-k="batt" data-t="${r.t.truck}" ${st.batt.has(r.t.truck)?"checked":""}>battery</label><label class="chk"><input type="checkbox" data-k="hyd" data-t="${r.t.truck}" ${st.hyd.has(r.t.truck)?"checked":""}>hydraulics</label></td></tr>`;}).join("");
 $("rules").innerHTML=`<li><b>Won't start</b> if battery ${NS[0].op} ${NS[0].value} V and low ${NS[1].op} ${NS[1].value} °C</li><li><b>Loses hydraulics</b> if PTO h since service ${HY[0].op} ${HY[0].value} and snow ${HY[1].op} ${HY[1].value} cm</li>`;}
function priority(){return RES.filter(r=>r.c.label!=="ok").sort((a,b)=>a.c.label!==b.c.label?(a.c.label==="no_start"?-1:1):
 a.c.label==="no_start"?a.f.battery_v_latest-b.f.battery_v_latest:b.f.pto_since_hyd_service-a.f.pto_since_hyd_service);}
$("rows").addEventListener("change",e=>{const k=e.target.dataset.k,t=e.target.dataset.t;if(!k)return;e.target.checked?st[k].add(t):st[k].delete(t);render();});
$("filters").addEventListener("click",e=>{const f=e.target.dataset.f;if(!f)return;st.filter=f;[...$("filters").children].forEach(b=>b.classList.toggle("on",b.dataset.f===f));render();});
$("preset").onchange=loadPreset;$("temp").oninput=render;$("snow").oninput=render;$("reset").onclick=loadPreset;$("clear").onclick=()=>{st.batt.clear();st.hyd.clear();render();};

// ---- Ask the twin: deterministic, rule-based assistant over the data on this page ----
function say(t,who){const d=document.createElement("div");d.className="msg "+(who||"bot");d.textContent=t;$("log").appendChild(d);$("log").scrollTop=1e9;}
function counts(){const c={ok:0,no_start:0,hydraulic:0};RES.forEach(r=>c[r.c.label]++);return c;}
function summary(){const c=counts();return `${c.ok} of ${RES.length} ready · ${c.no_start} won't start · ${c.hydraulic} lose hydraulics · ${RES.filter(r=>r.watch).length} inspect first (low ${$("temp").value} °C, ${$("snow").value} cm).`;}
function explain(id){const r=RES.find(x=>x.t.truck===id);if(!r)return `I don't know ${id}. Trucks are T-101 to T-130.`;
 const f=r.f,v=f.battery_v_latest,p=f.pto_since_hyd_service,T=+$("temp").value,S=+$("snow").value;let s=`${id} (${r.t.yard}): ${r.watch?"OK but inspect first":r.c.label.toUpperCase()}.\n`;
 s+=`• Battery ${fmt(v,2)} V (reading ${r.t.battery_v_reading_local||"?"}). No-start needs ≤ ${NS[0].value} V and low ≤ ${NS[1].value} °C → ${v!=null&&v<=NS[0].value?"weak":"healthy"} battery, ${T<=NS[1].value?"cold enough":"not cold enough"} tonight.\n`;
 s+=`• ${fmt(p,1)} PTO h since hydraulic work (${r.t.last_hyd_work_order||"?"}). Hydraulic failure needs ≥ ${HY[0].value} h and ≥ ${HY[1].value} cm → ${p!=null&&p>=HY[0].value?"overdue":"within limit"}, ${S>=HY[1].value?"heavy":"light"} snow.\n`;
 s+=`• Action: ${r.act}`;if(st.batt.has(id)||st.hyd.has(id))s+=`\n• What-if repair applied: ${[st.batt.has(id)?"battery":"",st.hyd.has(id)?"hydraulics":""].filter(Boolean).join(" + ")} (assumed effective).`;return s;}
function answer(q){const s=q.toLowerCase().trim(),ids=[...new Set((q.toUpperCase().match(/T-?\d{3}/g)||[]).map(x=>x.replace(/^T-?/,"T-")))],num=s.match(/-?\d+(\.\d+)?/g);
 if(/^(help|\?|what can you do)/.test(s))return "Try:\n• summary / how many are ready?\n• what should I fix first?\n• why is T-114 flagged?\n• fix T-111 (or: replace battery T-109, service T-119)\n• undo T-111 / clear repairs\n• low -8 · snow 6 · reset\n• north yard / south yard\n• rules · how sure are you?";
 if(/reset/.test(s)){loadPreset();st.batt.clear();st.hyd.clear();render();return "Back to the forecast, repairs cleared.\n"+summary();}
 if(/clear|undo all/.test(s)&&!ids.length){st.batt.clear();st.hyd.clear();render();return "All what-if repairs cleared.\n"+summary();}
 if(ids.length&&/(fix|repair|replace|swap|service|charge)/.test(s)){const before=counts().ok;ids.forEach(id=>{const r=RES.find(x=>x.t.truck===id);if(!r)return;
   const wantB=/batt|charge|swap|replace/.test(s),wantH=/hyd|service/.test(s);if(wantB||(!wantH&&r.c.label==="no_start"))st.batt.add(id);if(wantH||(!wantB&&r.c.label==="hydraulic"))st.hyd.add(id);if(!wantB&&!wantH&&r.c.label==="ok"){st.batt.add(id);st.hyd.add(id);}});
   render();return `Applied what-if repair to ${ids.join(", ")} (assumed fully effective). Ready ${before} → ${counts().ok}.\n`+summary();}
 if(ids.length&&/(undo|remove|unfix|cancel)/.test(s)){ids.forEach(id=>{st.batt.delete(id);st.hyd.delete(id);});render();return `Removed repairs on ${ids.join(", ")}.\n`+summary();}
 if(ids.length)return ids.map(explain).join("\n\n");
 if(/(low|temp|cold|°c|degree)/.test(s)&&num){const v=Math.min(5,Math.max(-30,-Math.abs(+num[0])));$("temp").value=v;render();return `Overnight low set to ${v} °C.\n`+summary();}
 if(/snow|cm/.test(s)&&num){$("snow").value=Math.min(40,Math.max(0,+num[0]));render();return `Snowfall set to ${$("snow").value} cm.\n`+summary();}
 if(/(first|priority|fix|repair|what should|order)/.test(s)){const b=priority();return b.length?"Repair in this order:\n"+b.map((r,i)=>`${i+1}. ${r.t.truck}: ${r.c.label==="no_start"?"batteries ("+fmt(r.f.battery_v_latest,2)+" V)":"hydraulic service ("+fmt(r.f.pto_since_hyd_service,1)+" h)"}`).join("\n")+"\nAnything not fixed before the callout: hold it and tell dispatch.":"Nothing to repair: every truck is predicted to run.";}
 if(/north|south|yard/.test(s)){const y=/south/.test(s)?"YARD-S":"YARD-N",rs=RES.filter(r=>r.t.yard===y),bad=rs.filter(r=>r.c.label!=="ok");return `${y}: ${rs.length-bad.length} of ${rs.length} ready.`+(bad.length?" At risk: "+bad.map(r=>r.t.truck+" ("+r.c.label+")").join(", "):"");}
 if(/inspect|watch|close|near/.test(s)){const w=RES.filter(r=>r.watch);return w.length?"Deploy but inspect first (near a threshold): "+w.map(r=>`${r.t.truck} (${fmt(r.f.battery_v_latest,2)} V, ${fmt(r.f.pto_since_hyd_service,1)} h)`).join(", "):"No trucks near a threshold.";}
 if(/rule|why|how does|explain/.test(s))return `Two rules found in last winter's data:\n• Won't start: battery ≤ ${NS[0].value} V AND low ≤ ${NS[1].value} °C. All 11 no-starts matched; 12.25 V trucks started.\n• Loses hydraulics: ≥ ${HY[0].value} PTO h since service AND ≥ ${HY[1].value} cm snow. All 6 failures matched (181.8–191.4 h on 9.8–20.2 cm nights).\nBacktest on 11 callouts: 9/9 caught, 0 false alarms.`;
 if(/sure|confiden|uncertain|risk/.test(s))return "Weak spots:\n• Cold cut-off: Dec 31 (−10.8 °C) no failures vs Jan 18 (−10.7 °C) one. Daily lows hide the hour of the cold.\n• Snow cut-off sits between 4.8 and 9.8 cm (8 is a middle guess).\n• 27.5 cm is beyond last winter's biggest night (20.2 cm): T-127 and T-108 are a judgment call.\n• Repairs are assumed to work. Decision support, not a safety clearance.";
 if(/how many|ready|summary|status|count|overview/.test(s))return summary();
 return "I answer from this page's data. Type 'help' to see what I can do.";}
$("ask").onsubmit=e=>{e.preventDefault();const q=$("q").value.trim();if(!q)return;say(q,"me");say(answer(q));$("q").value="";};
["Summary","What should I fix first?","Why is T-114 flagged?","Fix T-111","Low -8","How sure are you?"].forEach(t=>{const b=document.createElement("button");b.type="button";b.textContent=t;b.onclick=()=>{say(t,"me");say(answer(t));};$("chips").appendChild(b);});
$("preset").value=D.presets.length-1;loadPreset();
say("Hi, I'm the Storm Twin assistant. I answer from the fleet data and rules on this page, offline.\n"+summary()+"\nType 'help' for examples.");
</script></body></html>
"""
