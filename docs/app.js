"use strict";
// SparRadar – Anzeige der täglich abgerufenen Angebote (docs/data/offers.json)

const STORES = {
  lidl:   {n:"Lidl",          m:"Li", c:"#2F6FE4", app:"Lidl Plus",  link:"https://www.lidl.de/", dom:"lidl.de"},
  aldi:   {n:"Aldi Süd",      m:"AS", c:"#1590B5",                   link:"https://www.aldi-sued.de/de/angebote.html", dom:"aldi-sued.de"},
  rewe:   {n:"Rewe",          m:"Re", c:"#D9363E", app:"Rewe Bonus", link:"https://www.kaufda.de/Woerth-am-Rhein/REWE/p-r101", dom:"rewe.de"},
  netto:  {n:"Netto",         m:"Ne", c:"#C99400", app:"Netto App",  link:"https://www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9", dom:"netto-online.de"},
  edeka:  {n:"Edeka Jockgrim",m:"Ed", c:"#1F5FAF", app:"Payback",    link:"https://www.kaufda.de/Jockgrim/EDEKA/p-r107", dom:"edeka.de"},
  dm:     {n:"dm",            m:"dm", c:"#B8327F", app:"dm App",     link:"https://www.dm.de/", dom:"dm.de"}
};
const CATS = {obst:"Obst & Gemüse",fleisch:"Fleisch & Fisch",kuehl:"Milch, Käse & Eier",brot:"Brot & Backwaren",vorrat:"Vorrat",tk:"Tiefkühl",suess:"Süßes & Snacks",kaffee:"Kaffee & Tee",getraenke:"Getränke",katze:"Katzenfutter",drogerie:"Drogerie & Pflege",
  haushalt:"Haushalt & Putzen",tier:"Tierbedarf",baby:"Baby & Kind",technik:"Technik & Elektro",mode:"Mode & Schuhe",wohnen:"Wohnen & Küche",garten:"Garten & Heimwerken",freizeit:"Freizeit, Spiel & Reisen",sonstiges:"Sonstiges"};
const NONFOOD_CATS = ["haushalt","tier","baby","technik","mode","wohnen","garten","freizeit","sonstiges"];
const CC = {obst:"#E5484D",fleisch:"#C2453A",kuehl:"#F2B705",brot:"#C98A4B",vorrat:"#3B6FD9",tk:"#3BA5DC",suess:"#8B4A2B",kaffee:"#7A4A2A",getraenke:"#2E9E5B",katze:"#E8893A",drogerie:"#B8327F",
  haushalt:"#14A3A3",tier:"#9A6B3F",baby:"#E77FB0",technik:"#4B5563",mode:"#2B3034",wohnen:"#D97A12",garten:"#3F8F3A",freizeit:"#E5484D",sonstiges:"#6B7280"};
// Ersatzbilder, falls ein Angebot kein Foto hat oder das Foto nicht lädt
const ILL = {
obst:'<svg class="ill" viewBox="0 0 120 90"><circle cx="74" cy="58" r="20" fill="#F59E0B"/><circle cx="50" cy="52" r="27" fill="#E5484D"/><path d="M50 26l5 7 8-3-5 7 7 4-9 1-1 8-5-7-5 7-1-8-9-1 7-4-5-7 8 3z" fill="#2E9E5B"/></svg>',
fleisch:'<svg class="ill" viewBox="0 0 120 90"><path d="M22 44c0-16 20-26 44-24 22 2 34 14 32 30-2 18-22 24-44 22C32 70 22 60 22 44z" fill="#F4D3C4"/><path d="M28 45c0-12 17-20 38-18 19 2 28 11 26 23-2 13-19 18-38 16-17-2-26-9-26-21z" fill="#C2453A"/><circle cx="72" cy="45" r="8" fill="#F4D3C4"/></svg>',
kuehl:'<svg class="ill" viewBox="0 0 120 90"><rect x="74" y="16" width="26" height="58" rx="8" fill="#fff"/><rect x="74" y="34" width="26" height="18" fill="#3B6FD9"/><path d="M14 66l52-34 4 34z" fill="#F7C948"/><circle cx="44" cy="58" r="4" fill="#E0A82E"/></svg>',
brot:'<svg class="ill" viewBox="0 0 120 90"><path d="M18 56c0-20 18-34 42-34s42 14 42 34c0 8-6 12-14 12H32c-8 0-14-4-14-12z" fill="#C98A4B"/><path d="M40 36l8 16M56 32l6 18M72 34l4 17" stroke="#F1C995" stroke-width="4" stroke-linecap="round"/></svg>',
vorrat:'<svg class="ill" viewBox="0 0 120 90"><rect x="22" y="22" width="38" height="52" rx="6" fill="#3B6FD9"/><rect x="22" y="38" width="38" height="18" fill="#fff"/><rect x="66" y="30" width="34" height="44" rx="4" fill="#F2B705"/></svg>',
tk:'<svg class="ill" viewBox="0 0 120 90"><rect x="28" y="18" width="64" height="54" rx="8" fill="#3BA5DC"/><g stroke="#fff" stroke-width="3.5" stroke-linecap="round"><path d="M60 32v30M47 40l26 14M73 40L47 54"/></g></svg>',
suess:'<svg class="ill" viewBox="0 0 120 90"><g transform="rotate(-12 60 45)"><rect x="20" y="28" width="80" height="34" rx="5" fill="#6B3E26"/><rect x="62" y="26" width="40" height="38" rx="4" fill="#E5484D"/></g></svg>',
kaffee:'<svg class="ill" viewBox="0 0 120 90"><path d="M30 36h50v18c0 14-11 22-25 22S30 68 30 54z" fill="#fff"/><path d="M80 42h6c6 0 9 4 9 8s-3 8-9 8h-7" stroke="#fff" stroke-width="5" fill="none"/><ellipse cx="55" cy="37" rx="24" ry="5" fill="#7A4A2A"/></svg>',
getraenke:'<svg class="ill" viewBox="0 0 120 90"><path d="M48 8h12v12c8 4 12 10 12 18v42c0 3-2 5-5 5H41c-3 0-5-2-5-5V38c0-8 4-14 12-18z" fill="#2E9E5B"/><rect x="36" y="46" width="36" height="20" fill="#fff"/><rect x="78" y="38" width="22" height="46" rx="5" fill="#E5484D"/></svg>',
drogerie:'<svg class="ill" viewBox="0 0 120 90"><rect x="26" y="22" width="30" height="58" rx="8" fill="#B8327F"/><rect x="33" y="10" width="16" height="14" rx="3" fill="#7A1F55"/><rect x="26" y="42" width="30" height="16" fill="#fff" opacity=".85"/><rect x="64" y="40" width="34" height="40" rx="6" fill="#fff"/><circle cx="81" cy="40" r="10" fill="#fff"/><circle cx="81" cy="40" r="4" fill="#DCE1EE"/></svg>',
katze:'<svg class="ill" viewBox="0 0 120 90"><path d="M20 66h80l-6 16H26z" fill="#3B6FD9"/><path d="M36 36l-4-24 16 12M84 36l4-24-16 12" fill="#E8893A"/><ellipse cx="60" cy="38" rx="26" ry="20" fill="#E8893A"/><circle cx="50" cy="36" r="3.5" fill="#141726"/><circle cx="70" cy="36" r="3.5" fill="#141726"/></svg>',
haushalt:'<svg class="ill" viewBox="0 0 120 90"><path d="M44 30h28v8l8 6v36c0 3-2 5-5 5H41c-3 0-5-2-5-5V44l8-6z" fill="#14A3A3"/><rect x="50" y="14" width="16" height="16" rx="2" fill="#0E7C7C"/><path d="M66 18h16l4 6H66z" fill="#0E7C7C"/><rect x="36" y="52" width="44" height="16" fill="#fff" opacity=".85"/><circle cx="92" cy="30" r="3" fill="#fff"/><circle cx="98" cy="22" r="2.5" fill="#fff"/><circle cx="96" cy="38" r="2" fill="#fff"/></svg>',
tier:'<svg class="ill" viewBox="0 0 120 90"><ellipse cx="60" cy="58" rx="18" ry="15" fill="#9A6B3F"/><ellipse cx="38" cy="38" rx="7" ry="9" fill="#9A6B3F"/><ellipse cx="52" cy="26" rx="7" ry="9" fill="#9A6B3F"/><ellipse cx="68" cy="26" rx="7" ry="9" fill="#9A6B3F"/><ellipse cx="82" cy="38" rx="7" ry="9" fill="#9A6B3F"/></svg>',
baby:'<svg class="ill" viewBox="0 0 120 90"><rect x="46" y="10" width="28" height="10" rx="5" fill="#E77FB0"/><path d="M50 20h20l4 10v44c0 4-3 7-7 7H53c-4 0-7-3-7-7V30z" fill="#fff"/><path d="M46 46h28v28c0 4-3 7-7 7H53c-4 0-7-3-7-7z" fill="#F7C6DD"/><path d="M52 36h8M52 46h8M52 56h8" stroke="#E77FB0" stroke-width="2.5" stroke-linecap="round"/></svg>',
technik:'<svg class="ill" viewBox="0 0 120 90"><rect x="20" y="16" width="80" height="50" rx="6" fill="#4B5563"/><rect x="26" y="22" width="68" height="38" rx="3" fill="#7DD3FC"/><path d="M50 66h20l4 10H46z" fill="#4B5563"/><path d="M34 52l14-14 10 10 18-18" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
mode:'<svg class="ill" viewBox="0 0 120 90"><path d="M44 14l-24 14 8 16 10-5v41h44V39l10 5 8-16-24-14c-2 6-8 10-16 10s-14-4-16-10z" fill="#2B3034"/><path d="M44 14c2 6 8 10 16 10s14-4 16-10" stroke="#fff" stroke-width="3" fill="none" opacity=".7"/></svg>',
wohnen:'<svg class="ill" viewBox="0 0 120 90"><path d="M20 44 60 14l40 30v36H20z" fill="#D97A12"/><rect x="50" y="54" width="20" height="26" rx="2" fill="#fff"/><rect x="28" y="50" width="14" height="12" rx="2" fill="#FFE7C2"/><rect x="78" y="50" width="14" height="12" rx="2" fill="#FFE7C2"/></svg>',
garten:'<svg class="ill" viewBox="0 0 120 90"><path d="M40 56h40l-6 26H46z" fill="#C2410C"/><rect x="36" y="50" width="48" height="8" rx="3" fill="#9A3412"/><path d="M60 50V26" stroke="#3F8F3A" stroke-width="4" stroke-linecap="round"/><path d="M60 34c-14 0-20-10-20-18 12 0 20 6 20 18zM60 30c0-12 8-20 22-20 0 10-8 20-22 20z" fill="#3F8F3A"/></svg>',
freizeit:'<svg class="ill" viewBox="0 0 120 90"><circle cx="60" cy="46" r="30" fill="#E5484D"/><path d="M30 46h60M60 16c-12 10-12 50 0 60M60 16c12 10 12 50 0 60" stroke="#fff" stroke-width="3.5" fill="none"/></svg>',
sonstiges:'<svg class="ill" viewBox="0 0 120 90"><rect x="28" y="36" width="64" height="44" rx="5" fill="#6B7280"/><rect x="24" y="26" width="72" height="14" rx="4" fill="#9CA3AF"/><rect x="55" y="26" width="10" height="54" fill="#FFD60A"/><path d="M60 26c-8-14-24-12-18-2 4 6 18 2 18 2zm0 0c8-14 24-12 18-2-4 6-18 2-18 2z" fill="#FFD60A"/></svg>'
};
const IC = {
 star:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9Z"/></svg>',
 plus:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
 check:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg>',
 x:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
 layers:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/></svg>',
 bell:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/></svg>',
 flame:'<svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c.6 3.6 4.5 5.4 5.6 9.2A6 6 0 1 1 6.1 13c.3-1.9 1.4-3 2.4-3.8 0 1.8.9 3 2.1 3.4C9.9 9.3 10.6 5.4 12 2Z"/></svg>',
 cal:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
 chart:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>',
 scale:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 3v18M5 7h14M5 7l-3 7h6zM19 7l-3 7h6z"/></svg>',
 box:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="m3 7 9-4 9 4v10l-9 4-9-4z"/><path d="m3 7 9 4 9-4M12 11v10"/></svg>',
 gear:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>',
 bag:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M5 8h14l-1 13H6z"/><path d="M9 8a3 3 0 0 1 6 0"/></svg>'
};

// ---------- Zustand ----------
const store = {get(k,d){try{const v=localStorage.getItem("sr_"+k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem("sr_"+k,JSON.stringify(v))}catch(e){}}};
const S = {tab:"offers",week:0,q:"",stores:new Set(),cats:new Set(),sort:"off",flt:Object.assign({min:0,max:0,bio:0,vegan:0,real:0,app:0,noapp:0,low:0},store.get("flt",{})),useApp:store.get("useApp",true),
  watch:store.get("watch2",[{k:"Katzenfutter",max:6},{k:"Butter"},{k:"Kaffee"}]),list:store.get("list",[]),
  coupons:store.get("coupons",[]),extra:store.get("extra",[]),checked:store.get("checked",[]),saved:store.get("saved",[]),trips:store.get("trips",[]),qty:store.get("qty",{}),budget:store.get("budget",0),sheet:null,limit:60};
let OFFERS = [], RAW = [], HIST = {}, META = {}, NAMES = [], APPV = {}, OLD = new Map();
// lokales Datum (nicht UTC), sonst gilt nach Mitternacht noch der Vortag
const TODAY = (d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`)(new Date());
// Einkaufstag: Samstag ab 22 Uhr und sonntags hat kein Markt mehr offen -> die Hauptseite zeigt schon die
// Angebote ab Montag (Kevins Wunsch). Alles, was Samstag endet, fällt dann weg.
const shopFrom = (now=new Date()) => {const d=new Date(now);const wd=d.getDay();
  if(wd===0||(wd===6&&d.getHours()>=22)){d.setDate(d.getDate()+(wd===0?1:2))}
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`};
const SHOP = shopFrom();
const WEEKEND = SHOP>TODAY;

// ---------- Helfer ----------
const eur = v => (v<0?"−":"")+Math.abs(v).toFixed(2).replace(".",",")+" €";
const norm = s => (s||"").toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss").replace(/[^a-z0-9]/g,"");
// nur echte https-Links zulassen (Schutz, falls eine Quelle einmal kaputte oder manipulierte Daten liefert)
const safeUrl = u => /^https:\/\//i.test(u||"") ? u : "";
const esc = s => String(s??"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const parseNum = s => {const v=parseFloat(String(s||"").replace(",","."));return isFinite(v)&&v>0?v:null};
// Prospekte „ab Sonntag“ starten im Laden erst am Montag (sonntags geschlossen)
const shopDay = d => {if(!d)return d;const x=new Date(d+"T12:00:00");if(x.getDay()!==0)return d;x.setDate(x.getDate()+1);return x.toISOString().slice(0,10)};
const fmtDate = d => d ? new Date(d+"T12:00:00").toLocaleDateString("de-DE",{weekday:"short",day:"2-digit",month:"2-digit"}) : "";
// Markt-Logo: das Website-Symbol des Markts (wird beim Öffnen geladen, liegt nicht im Repo).
// Lädt es nicht, bleibt das farbige Kürzel darunter sichtbar.
const logoUrl = s => STORES[s]?.dom ? `https://www.google.com/s2/favicons?domain=${STORES[s].dom}&sz=64` : "";
const sb = (s,lg) => `<span class="sb${lg?" lg":""}" style="--c:${(STORES[s]||{}).c||"#888"}" aria-hidden="true">${(STORES[s]||{}).m||"?"}${logoUrl(s)?`<img src="${logoUrl(s)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-logo="1">`:""}</span>`;
const sname = s => (STORES[s]||{}).n || s;
let tt; function toast(m){const t=document.getElementById("toast");t.textContent=m;t.hidden=false;clearTimeout(tt);tt=setTimeout(()=>t.hidden=true,2600)}
// Scheck-In/Serpa und „Angebot eintragen“ wurden entfernt: alte Einträge vom Gerät löschen
try{localStorage.removeItem("sr_manual")}catch(e){}
S.coupons=S.coupons.filter(c=>c.s==="all"||STORES[c.s]);
const save = () => {store.set("watch2",S.watch);store.set("list",S.list);store.set("useApp",S.useApp);store.set("coupons",S.coupons);store.set("extra",S.extra);store.set("checked",S.checked);store.set("saved",S.saved);store.set("trips",S.trips);store.set("qty",S.qty);store.set("budget",S.budget);Sync.changed()};

// ---------- Geräte verbinden (Handy <-> PC) ----------
// Merkliste, Einkaufszettel und Coupons liegen zusätzlich in einem geheimen Gist im
// GitHub-Konto des Nutzers. Der Schlüssel (nur Recht "gist") bleibt auf dem Gerät, nie im Repo.
const Sync = {
  API:"https://api.github.com", FILE:"sparradar-sync.json", DESC:"SparRadar-Sync (Merkliste, Einkaufszettel, Coupons)",
  cfg(){return store.get("sync",null)}, timer:null, busy:false, status:"", devices:store.get("syncDevs",{}),
  // Jedes Gerät trägt sich mit Name + „zuletzt aktiv“ ein -> Liste „Verbundene Geräte“ (beliebig viele Geräte mit demselben Code)
  devId(){let id=store.get("devId","");if(!id){id=Math.random().toString(36).slice(2,10);store.set("devId",id)}return id},
  devType(){const u=navigator.userAgent;return /iPad|Tablet|SM-T|Tab\b/i.test(u)||(/Android/i.test(u)&&!/Mobile/i.test(u))?"tablet":/Android|iPhone|Mobile/i.test(u)?"phone":"pc"},
  devName(){return store.get("devName","")||({phone:/iPhone/.test(navigator.userAgent)?"iPhone":"Android-Handy",tablet:"Tablet",pc:/Mac/.test(navigator.userAgent)?"Mac":"Windows-PC"})[this.devType()]},
  devs(){const me={n:this.devName(),t:this.devType(),at:Date.now(),sh:this.on()},old=Date.now()-90*864e5;
    const d=Object.fromEntries(Object.entries(this.devices||{}).filter(([k,v])=>v&&v.at>old&&k!==this.devId()));d[this.devId()]=me;return d},
  // Bereiche: jedes Gerät wählt selbst, was es mit den anderen teilt (Kevins Wunsch: Familie teilt den Einkaufszettel,
  // die Merkliste nur, wer sie teilen will). Jeder Bereich hat einen eigenen Zeitstempel -> nichts wird überschrieben.
  PARTS:{list:{n:"Einkaufszettel",keys:["list","extra","checked","qty","trips","saved"]},watch:{n:"Merkliste",keys:["watch"]},coupons:{n:"Coupons",keys:["coupons"]}},
  SKEY:{watch:"watch2"},
  share(){const d=store.get("syncParts",null);return d||(this.cfg()?.gist?{list:true,watch:true,coupons:true}:{list:true,watch:false,coupons:false})},
  on(){const sh=this.share();return Object.keys(this.PARTS).filter(p=>sh[p])},
  get(p){return Object.fromEntries(this.PARTS[p].keys.map(k=>[k,S[k]]))},
  set(p,d){this.PARTS[p].keys.forEach(k=>{S[k]=d[k]??(k==="qty"?{}:[]);store.set(this.SKEY[k]||k,S[k])})},
  pick(d,p){return Object.fromEntries(this.PARTS[p].keys.filter(k=>d&&d[k]!=null).map(k=>[k,d[k]]))},
  snap(p){return JSON.stringify(this.get(p))},
  // alte Datei {updatedAt,data} (vor Version 67) in Bereiche umrechnen; ist „data“ neuer, gewinnt es
  norm(r){const parts={...(r.parts||{})};if(r.data)Object.keys(this.PARTS).forEach(p=>{if(!parts[p]||(r.updatedAt||0)>(parts[p].at||0))parts[p]={at:r.updatedAt||1,d:this.pick(r.data,p)}});return parts},
  // Zwei Speicher: Familien-Code (SR-…, eigener Cloudflare-Speicher, Adresse in docs/sync.json) oder GitHub-Gist (ghp_…)
  ready(){const c=this.cfg();return !!(c&&(c.gist||c.srv))},
  _srv:undefined,
  async srv(){if(this._srv!==undefined)return this._srv;try{const r=await fetch("sync.json",{cache:"no-store"});this._srv=r.ok?((await r.json()).url||null):null}catch(e){this._srv=null}return this._srv},
  async sreq(path,opt={}){const u=await this.srv();if(!u)throw new Error("Sync-Speicher nicht erreichbar");
    let r;try{r=await fetch(u+path,{...opt,cache:"no-store",headers:opt.body?{"Content-Type":"application/json"}:{}})}catch(e){throw new Error("keine Verbindung")}
    if(r.status===404)throw new Error("Code unbekannt");if(!r.ok)throw new Error("Speicher antwortet nicht ("+r.status+")");return r.json()},
  code(){const c=this.cfg();return c?.srv?"SR-"+c.srv:c?.token||""},
  async write(obj){const c=this.cfg();if(c.srv)return this.sreq("/s/"+c.srv,{method:"PUT",body:JSON.stringify(obj)});
    return this.req("/gists/"+c.gist,{method:"PATCH",body:JSON.stringify({files:{[this.FILE]:{content:JSON.stringify(obj)}}})})},
  // Umzug GitHub-Gist -> Familien-Code: alles mitnehmen (Listen + Geräte), danach braucht dieses Gerät keinen GitHub-Schlüssel mehr
  async migrate(){const c=this.cfg();if(!c?.gist)return;const r=await this.load(),sh=this.share();
    store.set("syncParts",sh);store.set("syncGive",sh); // eigene Geräte: gleiche Auswahl behalten (meist alles)
    const {id}=await this.sreq("/new",{method:"POST"});
    await this.sreq("/s/"+id,{method:"PUT",body:JSON.stringify({v:2,updatedAt:Date.now(),parts:r.parts,devices:r.devices})});
    store.set("sync",{srv:id,from:"gist"});await this.pull();return id},
  async create(parts){const {id}=await this.sreq("/new",{method:"POST"});store.set("sync",{srv:id});if(parts)store.set("syncParts",parts);store.set("syncAt",{});store.set("syncSnaps",{});await this.push();return id},
  async req(path,opt={}){const c=this.cfg();const r=await fetch(this.API+path,{...opt,cache:"no-store",headers:{Authorization:"Bearer "+c.token,Accept:"application/vnd.github+json",...(opt.body?{"Content-Type":"application/json"}:{})}});
    if(r.status===401)throw new Error("Schlüssel ungültig oder abgelaufen");if(!r.ok)throw new Error("GitHub antwortet nicht ("+r.status+")");return r.json()},
  async load(){const c=this.cfg();let r;
    if(c.srv)r=await this.sreq("/s/"+c.srv);
    else{const g=await this.req("/gists/"+c.gist),f=g.files[this.FILE];
      const raw=f?(f.truncated?await (await fetch(f.raw_url,{cache:"no-store"})).text():f.content):"{}";r=JSON.parse(raw||"{}")}
    if(r.devices&&typeof r.devices==="object"){this.devices=r.devices;store.set("syncDevs",r.devices)}
    return {parts:this.norm(r),devices:r.devices||{}}},
  // beide Seiten geändert: nichts verlieren, alles zusammenführen
  merge(a,b){const u=(x,y,k)=>{const m=new Map();[...x,...y].forEach(e=>m.set(k(e),e));return [...m.values()]};
    return {watch:u(a.watch||[],b.watch||[],w=>norm(w.k)),list:[...new Set([...(a.list||[]),...(b.list||[])])],
      coupons:u(a.coupons||[],b.coupons||[],c=>[c.id||"",c.s,c.k,c.t,c.v,c.to].join("|")),
      extra:u(a.extra||[],b.extra||[],x=>x.id),checked:[...new Set([...(a.checked||[]),...(b.checked||[])])],saved:(()=>{const m=new Map();[...(a.saved||[]),...(b.saved||[])].forEach(e=>{const k=e.id+"|"+e.d,o=m.get(k);m.set(k,o&&(o.off||e.off)?{...e,off:1}:e)});return [...m.values()]})(), // gelöscht (off) bleibt gelöscht
      trips:u(a.trips||[],b.trips||[],x=>x.id).sort((x,y)=>(y.at||"").localeCompare(x.at||"")),qty:{...(a.qty||{}),...(b.qty||{})}}},
  mergeP(p,remote,local){return this.pick({...this.merge(remote,local)},p)},
  async connect(token,parts){
    if(/^SR-/.test(token)){const id=token.slice(3);store.set("sync",{srv:id});
      try{await this.load();if(parts)store.set("syncParts",parts);store.set("syncAt",{});store.set("syncSnaps",{});await this.pull(true);return true}
      catch(e){store.set("sync",null);throw e}}
    store.set("sync",{token});
    try{const gs=await this.req("/gists?per_page=100");let g=gs.find(x=>x.description===this.DESC&&x.files[this.FILE]);
      if(!g)g=await this.req("/gists",{method:"POST",body:JSON.stringify({description:this.DESC,public:false,files:{[this.FILE]:{content:JSON.stringify({v:2,updatedAt:Date.now(),parts:{},devices:{}})}}})});
      store.set("sync",{token,gist:g.id});if(parts)store.set("syncParts",parts);store.set("syncAt",{});store.set("syncSnaps",{});await this.pull(true);return true}
    catch(e){store.set("sync",null);throw e}},
  disconnect(){store.set("sync",null);store.set("syncAt",{});store.set("syncSnaps",{});store.set("syncParts",null);this.status=""},
  // neu geteilten Bereich beim nächsten Abgleich zusammenführen statt überschreiben
  setShare(sh){const old=this.share();store.set("syncParts",sh);const sn=store.get("syncSnaps",{}),at=store.get("syncAt",{});
    Object.keys(this.PARTS).forEach(p=>{if(sh[p]&&!old[p]){delete sn[p];at[p]=-1}});store.set("syncSnaps",sn);store.set("syncAt",at)},
  async pull(){if(!this.ready()||this.busy)return;this.busy=true;
    try{const {parts}=await this.load(),at=store.get("syncAt",{}),sn=store.get("syncSnaps",{});let push=false,changed=false;
      for(const p of this.on()){const rp=parts[p],localNew=this.snap(p)!==sn[p],fresh=at[p]==null||at[p]<0;
        if(rp&&(rp.at||0)>(at[p]||0)){
          if(localNew||fresh){this.set(p,this.mergeP(p,rp.d,this.get(p)));push=true}else this.set(p,{...this.get(p),...rp.d});
          at[p]=rp.at;if(!push)sn[p]=this.snap(p);changed=true}
        else if(localNew||!rp)push=true}
      store.set("syncAt",at);store.set("syncSnaps",sn);
      const mine=(this.devices||{})[this.devId()];
      if(!mine||mine.n!==this.devName()||Date.now()-mine.at>6*36e5||JSON.stringify(mine.sh||[])!==JSON.stringify(this.on()))push=true;
      if(changed)render();
      if(push){this.busy=false;return this.push()}
      this.ok()}
    catch(e){this.fail(e)}finally{this.busy=false}},
  // lesen – zusammenführen – schreiben: so gehen Änderungen anderer Geräte/Personen nie verloren
  async push(){if(!this.ready())return;if(this.busy){this.changed();return}this.busy=true;
    try{const {parts}=await this.load(),at=store.get("syncAt",{}),sn=store.get("syncSnaps",{}),now=Date.now();let changed=false;
      for(const p of this.on()){const rp=parts[p];
        if(rp&&(rp.at||0)>(at[p]||0)){this.set(p,this.mergeP(p,rp.d,this.get(p)));changed=true}
        if(!rp||this.snap(p)!==sn[p]||(rp.at||0)>(at[p]||0)){parts[p]={at:now,d:this.get(p)};at[p]=now}
        sn[p]=this.snap(p)}
      const devs=this.devs();
      await this.write({v:2,updatedAt:now,parts,devices:devs});
      this.devices=devs;store.set("syncDevs",devs);store.set("syncAt",at);store.set("syncSnaps",sn);this.ok();if(changed)render()}
    catch(e){this.fail(e)}finally{this.busy=false}},
  changed(){if(!this.ready())return;clearTimeout(this.timer);this.timer=setTimeout(()=>this.push(),1500)},
  ok(){this.status="Verbunden · abgeglichen "+new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})+" Uhr";const el=document.getElementById("syncState");if(el)el.textContent=this.status},
  fail(e){this.status="Abgleich fehlgeschlagen: "+e.message;const el=document.getElementById("syncState");if(el)el.textContent=this.status}
};

function histOf(o){const rows=HIST[o.s+"|"+norm(o.n).slice(0,40)]||[];return rows.filter(r=>r[0]<(o.from||TODAY)).map(r=>r[1])}
// Referenzpreis für "Ersparnis": statt-Preis, sonst Durchschnitt aus dem Verlauf, sonst Angebotspreis
function ref(o){if(o.o)return o.o;const h=histOf(o);return h.length>=3?Math.max(o.p,h.reduce((a,b)=>a+b,0)/h.length):o.p}
function steps(o){if(!o.p)return [{l:"Bonus-Aktion",v:0,t:"base"}]; // Rewe-Bonus ohne Preis im Prospekt
  const st=[{l:o.o?"Normalpreis":"Angebotspreis",v:o.o||o.p,t:"base"}];
  if(o.o)st.push({l:"Angebot",v:o.p-o.o,t:"of"});
  if(S.useApp){if(o.ap)st.push({l:o.s==="lidl"?"Lidl Plus App-Preis":(STORES[o.s]?STORES[o.s].n.split(" ")[0]+" App-Preis":"App-Preis"),v:o.ap-o.p,t:"app"});(o.x||[]).forEach(([t,l,v])=>st.push({l,v:-v,t}))
    // eigene Coupons: werden in der eingetragenen Reihenfolge auf den jeweils aktuellen Preis angewendet
    couponsFor(o).forEach(c=>{const cur=st.reduce((a,s)=>a+s.v,0),d=cpValue(c,cur);if(d>0.004)st.push({l:cpLabel(c),v:-d,t:c.t==="punkte"||c.prog==="Cashback-App"||c.prog==="Geld zurück"?"cb":"coupon"})})}
  return st}

// ---------- Meine Coupons ----------
const PROGS = ["Lidl Plus","Rewe Bonus","Payback","Netto App","Edeka App","dm App","Cashback-App","Geld zurück","Hersteller-Coupon","Sonstiges"];
const CP_TYPES = {euro:"€ Rabatt / Guthaben",pct:"% Rabatt",preis:"Coupon-Preis (zahlst nur …)",punkte:"Payback-Extrapunkte"};
const defaultProg = s => ({lidl:"Lidl Plus",rewe:"Rewe Bonus",netto:"Payback",edeka:"Payback",dm:"dm App",all:"Cashback-App"})[s]||"Sonstiges";
const cpActive = c => !c.to || c.to>=TODAY;
const couponsFor = o => S.coupons.filter(c=>cpActive(c)&&c.k&&(c.s==="all"||c.s===o.s)&&c.k.split(/\s+/).every(w=>matches(o,w)));
function cpValue(c,cur){
  if(c.t==="euro")return c.v;
  if(c.t==="pct"){const d=Math.round(cur*c.v)/100;return c.mx?Math.min(d,c.mx):d}
  if(c.t==="preis")return Math.max(0,cur-c.v);
  if(c.t==="punkte")return c.v/100; // 1 Payback-Punkt = 1 Cent
  return 0} // t:"app" (vom Coupon-Sucher) = App-Preis/Bonus steht schon im Angebot -> nicht doppelt abziehen
function cpValueTxt(c){return !c.v?"Coupon":c.t==="app"?"−"+eur(c.v)+" mit App":c.t==="euro"?"−"+eur(c.v):c.t==="pct"?`−${String(c.v).replace(".",",")} %`:c.t==="preis"?"für "+eur(c.v):`${c.v} Extra-°P`}
const cpLabel = c => `${c.prog} ${cpValueTxt(c)}`;
const fin = o => Math.round(steps(o).reduce((a,s)=>a+s.v,0)*100)/100;
const offPct = o => {const r=ref(o);return r>0?Math.max(0,Math.round((1-fin(o)/r)*100)):0};
const unit = o => o.gp ? o.gp.v*(fin(o)/o.p) : null;
const unitTxt = o => o.gp ? `1 ${o.gp.u} = ${eur(unit(o))}` : "";
// Suche: Artikelname, Marke und Markt. Die Beschreibung nur als Notlösung, der Kategoriename nie
// (sonst findet „Milch“ alles aus „Milch, Käse & Eier“).
const hay = o => o._hay ??= [o.n,o.b,sname(o.s)].map(norm).join(" "); // Felder getrennt: „Prodomo“ + „Rewe“ ergibt nicht „…more…“
const hayD = o => o._hayD ??= norm(o.d);
// genauer Kategoriename (z. B. „Katzenfutter“, „Getränke“) findet die ganze Kategorie
const matches = (o,k) => hay(o).includes(norm(k)) || norm(CATS[o.c]||"")===norm(k);
const matchesAll = (o,t) => t.every(x=>matches(o,x));
// Treffer im Namen als ganzes Wort zuerst, dann im Namen, dann Marke/Markt
const relevance = (o,t) => {const n=(o.n||"").toLowerCase();return t.reduce((a,x)=>{const w=x.toLowerCase();
  return a+(new RegExp("(^|[^a-zäöüß])"+w.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"([^a-zäöüß]|$)").test(n)?0:norm(o.n).includes(norm(x))?1:2)},0)};
function searchOffers(list,q){const t=q.trim().split(/\s+/).filter(Boolean);if(!t.length)return list;
  let r=list.filter(o=>matchesAll(o,t));
  if(!r.length)r=list.filter(o=>t.every(x=>matches(o,x)||hayD(o).includes(norm(x))));
  return r}
// Merkliste: passt ein Angebot zum gemerkten Artikel?
// 1) alle wichtigen Wörter kommen im Angebot vor (Name, Marke, Beschreibung), Reihenfolge egal
// 2) Prospekt bietet „versch. Sorten“ an: dann reicht die Marke/Produktlinie (erstes Wort),
//    z. B. gemerkt „Tassimo Morning Café XL“, Angebot „Jacobs Tassimo, versch. Sorten“
const WATCH_FILL=/^(\d.*|g|kg|ml|l|cl|x|xl|xxl|st|stk|stueck|pack|packung|bigpack|big|cups?|portionen|kapseln|und|mit|fuer|der|die|das|von)$/;
const WATCH_WEAK=new Set(["bio","gut","ja","mini","frisch","frische","original","classic","klassik","deluxe","premium","neu","extra"]);
const wTokens = k => (k.toLowerCase().match(/[a-zäöüß0-9]+/g)||[]).map(norm).filter(t=>t.length>1&&!WATCH_FILL.test(t));
// Wörter einzeln vergleichen (nie über Wortgrenzen hinweg: „Prodomo Rewe“ enthält sonst „more“)
const oWords = o => [...new Set(`${o.b||""} ${o.n} ${o.d||""} ${sname(o.s)}`.toLowerCase().match(/[a-zäöüß0-9]+/g)||[])].map(norm).filter(Boolean);
function watchMatch(o,k){
  if(norm(CATS[o.c]||"")===norm(k))return true;
  const t=wTokens(k);if(!t.length)return false;
  const w=oWords(o),inW=x=>w.some(v=>{const i=v.indexOf(x);if(i<0)return false;const r=v.slice(i+x.length);return /^(|e|n|en|s|es|er|ern|ns)$/.test(r)||r.length>=4}); // zusammengesetzte Wörter und Mehrzahl zählen (Bohnenkaffee, Kaffeebohnen, Weißbiere), Milkana ist aber nicht Milka
  if(t.every(inW))return true;
  // „versch. Sorten“: Marke/Produktlinie reicht – aber nur als ganzes Wort oder Wortanfang, mind. 4 Buchstaben
  return t.length>1&&t[0].length>=4&&!WATCH_WEAK.has(t[0])&&w.some(v=>v===t[0]||(v.startsWith(t[0])&&t[0].length>=5))&&/versch|sorten|oderweitere/.test(norm(o.d)+norm(o.n))}
const hitW = (o,w) => watchMatch(o,w.k) && (!w.max || (unit(o)!=null && unit(o)<=w.max+1e-9));
const TOMORROW=(d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`)(new Date(Date.now()+864e5));
const validTxt = o => o.from && o.from>SHOP ? "ab "+fmtDate(shopDay(o.from)) : o.to===TODAY ? "nur noch heute" : o.to===TOMORROW ? "nur noch bis morgen" : o.to ? "bis "+fmtDate(o.to) : "";
const tagHTML = v => {v=Math.round(Math.max(v,0)*100);const e=Math.floor(v/100),c=v%100;return `<span class="eu">${e}</span><span class="ct">.${String(c).padStart(2,"0")}</span>`};
const comboLabels = o => steps(o).filter(s=>s.t!=="base"&&s.t!=="of").map(s=>s.l);
function verdict(o){const h=histOf(o);
  if(h.length<3)return{t:"ok",l:"Preisvergleich startet: SparRadar merkt sich ab jetzt jeden Tag den Preis. Nach ein paar Tagen siehst du hier, ob es ein echter Tiefpreis ist oder ein Schein-Rabatt.",s:"Preis wird beobachtet",fresh:true};
  const avg=h.reduce((a,b)=>a+b,0)/h.length,min=Math.min(...h);
  if(o.o&&avg<=o.p*1.05)return{t:"fake",l:`Rabatt fraglich: kostete zuletzt meist ${eur(avg)}`,s:"Rabatt fraglich"};
  if(o.p<min-.001)return{t:"low",l:`Tiefstpreis seit ${h.length} Abrufen`,s:"Tiefstpreis"};
  return{t:"ok",l:`Gab es zuletzt schon für ${eur(min)}`,s:"Übliches Angebot"}}
function spark(o,w=64,h=20){const pts=[...histOf(o).slice(-10),o.p];if(pts.length<2)return"";
  const mx=Math.max(...pts),mn=Math.min(...pts)*0.95,sx=w/(pts.length-1),y=v=>h-2-(v-mn)/(mx-mn||1)*(h-4);
  return `<svg width="${w}" height="${h}" viewBox="-3 -3 ${w+6} ${h+6}" aria-hidden="true"><polyline points="${pts.map((v,i)=>`${(i*sx).toFixed(1)},${y(v).toFixed(1)}`).join(" ")}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" opacity=".55"/><circle cx="${w}" cy="${y(o.p).toFixed(1)}" r="3" fill="currentColor"/></svg>`}
// Scharfe Bilder: kaufDA liefert unter derselben Adresse ohne „?impolicy=…“ die volle Auflösung,
// Aldi in größerer Breite. Gilt auch für schon gespeicherte Angebote.
const sharp = u => !u ? u : u.replace(/\?impolicy=SEO-offer-(?:normal|thumbnails)$/,"").replace(/\/scaleWidth\/500\//,"/scaleWidth/1000/");
// Winzige Prospekt-Ausschnitte (kaufDA, z. B. 150 px) nicht auf Kartengröße aufblasen – das macht sie pixelig.
// Größe kommt vom Abruf (o.iw) oder wird beim Laden gemessen (lowres()).
const LOWPX=320;
const imgTag = (o,cls="") => safeUrl(o.img) ? `<img src="${esc(sharp(o.img))}" alt="${esc(o.n)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" class="${cls}${o.iw&&Math.max(...o.iw)<LOWPX?" lowres":""}" data-cat="${o.c}">` : (ILL[o.c]||ILL.sonstiges);
// Beschriftung für kommende Angebote: „Nächste Woche“, oder „Ab Donnerstag“, wenn etwas noch diese Woche startet
function nextLabel(){const nx=OFFERS.filter(o=>o.from&&o.from>SHOP).map(o=>shopDay(o.from)).sort()[0];
  if(!nx)return "Nächste Woche";
  const d=new Date(SHOP+"T12:00:00"),mon=new Date(d);mon.setDate(d.getDate()+((8-d.getDay())%7||7));
  const nextMon=`${mon.getFullYear()}-${String(mon.getMonth()+1).padStart(2,"0")}-${String(mon.getDate()).padStart(2,"0")}`;
  return nx>=nextMon?"Nächste Woche":"Ab "+new Date(nx+"T12:00:00").toLocaleDateString("de-DE",{weekday:"long"})}
const nextShort = () => {const l=nextLabel();return l==="Nächste Woche"?"nächste Woche":l.replace("Ab","ab")};
// ---------- Vorteil ohne „statt“-Preis ----------
// Steht im Prospekt kein „statt“-Preis, zeigt SparRadar den Vorteil aus eigenen Daten – klar gekennzeichnet (blau):
// 1) günstiger als zuletzt im selben Markt  2) Großpackung günstiger pro kg/l  3) günstigster aller Märkte
const PERK=new Map();
const fmtQty = q => !q?"":q.v<1?`${Math.round(q.v*1000)} ${q.u==="kg"?"g":"ml"}`:`${String(Math.round(q.v*100)/100).replace(".",",")} ${q.u}`;
const coreKey = o => [...new Set(((o.b||"")+" "+o.n).toLowerCase().match(/[a-zäöüß0-9]+/g)||[])].map(norm)
  .filter(t=>t&&!/^(xxl|xl|maxi|mega|jumbo|grosspackung|vorratspackung|familienpackung|sparpack|xxxl)$/.test(t)).map(t=>t.replace(/(en|e|n)$/,"").replace(/([^s])s$/,"$1")).sort().join(" ");
function perk(o){
  if(!o||o.o||o.bo||!o.p||offPct(o))return null;
  if(PERK.has(o.id))return PERK.get(o.id);
  let r=null;const k=coreKey(o),q=packQty(o.d);
  const same=[...OFFERS,...OLD.values()].filter(x=>x!==o&&x.s===o.s&&x.p>o.p+.009&&(x.from||"")<(o.from||"")&&coreKey(x)===k&&((q&&packQty(x.d)&&Math.abs(packQty(x.d).v-q.v)/q.v<.05)||(!q&&x.d===o.d))).sort((a,b)=>(b.from||"").localeCompare(a.from||""))[0];
  if(same){const pct=Math.round((1-o.p/same.p)*100);
    if(pct>=3)r={pct,w:same.p,b:`−${pct} % ggü. bisher`,s:`bisher ${eur(same.p)}`,l:`Bei ${sname(o.s)} kostet dieselbe Packung bis ${same.to?fmtDate(same.to):"jetzt"} ${eur(same.p)}, ab ${fmtDate(shopDay(o.from))} nur ${eur(o.p)}. Das sind ${pct} % weniger.`}}
  const h=histOf(o),last=h.length?h[h.length-1]:0;
  if(!r&&last>o.p+.009){const pct=Math.round((1-o.p/last)*100);
    if(pct>=3)r={pct,w:last,b:`−${pct} % ggü. zuletzt`,s:`zuletzt ${eur(last)}`,l:`Bei ${sname(o.s)} kostete dieser Artikel zuletzt ${eur(last)}, jetzt ${eur(o.p)}. Das sind ${pct} % weniger (aus dem SparRadar-Preisverlauf, kein „statt“-Preis des Händlers).`}}
  if(!r&&o.gp&&o.gp.v>0){
    const sm=OFFERS.filter(x=>x!==o&&x.s===o.s&&x.p>0&&x.p<o.p&&x.gp&&x.gp.u===o.gp.u&&x.gp.v>o.gp.v*1.03&&coreKey(x)===k).sort((a,b)=>a.gp.v-b.gp.v)[0];
    if(sm){const pct=Math.round((1-o.gp.v/sm.gp.v)*100);
      r={pct,b:`Großpackung −${pct} %/${o.gp.u}`,s:`pro ${o.gp.u} ${pct} % günstiger als ${packQty(sm.d)?"die "+fmtQty(packQty(sm.d))+"-Packung":"die kleine Packung"}`,
        l:`Großpackung: ${eur(o.gp.v)} pro ${o.gp.u} statt ${eur(sm.gp.v)} pro ${o.gp.u} bei der kleineren Packung (${sm.d||sm.n}, ${eur(sm.p)}). Pro ${o.gp.u==="l"?"Liter":"Kilo"} sparst du ${pct} %.`}}}
  if(!r){const c=sameElsewhere(o,weekOffers()).filter(x=>Math.abs(x.f-1)<.05).map(x=>({x:x.x,v:fin(x.x)})).sort((a,b)=>a.v-b.v);
    if(c.length&&c[0].v>=fin(o)*1.05){const pct=Math.round((1-fin(o)/c[0].v)*100);
      r={pct,b:"günstigster Markt",s:`bei ${sname(c[0].x.s)} ${eur(c[0].v)}`,l:`Derselbe Artikel kostet beim nächstgünstigen Markt (${sname(c[0].x.s)}) ${eur(c[0].v)}. Hier sparst du ${pct} %.`}}}
  PERK.set(o.id,r);return r}
function thumb(o,big){return `<div class="thumb" style="--cc:${CC[o.c]||CC.sonstiges}">${imgTag(o)}${big?"":sb(o.s)}${appName(o)?`<span class="apptag" title="App-Angebot: ${esc(o.ao?"Preis gilt nur mit "+o.ao:"günstiger mit "+appName(o))}">📱 ${esc(appName(o))}</span>`:""}${offPct(o)?`<span class="off${dealWarn(o)?" q":""}"${dealWarn(o)?' title="Rabatt widerlegt – Details antippen"':""}>−${offPct(o)} %${dealWarn(o)?" ?":""}</span>`:perk(o)?`<span class="off pk" title="Vorteil ohne „statt“-Preis – Details antippen">${perk(o).b}</span>`:""}</div>`}

document.addEventListener("load",e=>{const i=e.target;if(i.tagName==="IMG"&&i.closest(".thumb")&&i.naturalWidth&&Math.max(i.naturalWidth,i.naturalHeight)<LOWPX)i.classList.add("lowres")},true);
// ---------- Daten ----------
// ---------- Automatische Rabatt-Prüfung ----------
// Jeder Rabatt wird beim Laden geprüft. Falsche „statt“-Preise fliegen raus; Rabatte ab 40 %
// werden zusätzlich gegengecheckt. Zweifelhafte bekommen ein „?“ und rutschen in Sortierung und Kracher nach hinten.
function packQty(t){ // Menge aus „6 x 1,5 Liter“, „200-g-Pckg.“, „750 g“ -> {v,u} in kg/l; Spannen/mehrere Größen -> null
  t=String(t||"");const m=[...t.matchAll(/(?:(\d+)\s*[x×]\s*)?(?:(\d+)\s*[x×]\s*)?(\d+(?:[.,]\d+)?)\s*-?\s*(kg|g|ml|l|liter)\b/gi)];
  if(m.length!==1||/\d\s*[\/–-]\s*\d/.test(t))return null;
  const [,n,n2,v,u0]=m[0],u=u0.toLowerCase(),x=parseFloat(v.replace(",","."))*(+n||1)*(+n2||1);
  return u==="g"?{v:x/1000,u:"kg"}:u==="ml"?{v:x/1000,u:"l"}:{v:x,u:u==="kg"?"kg":"l"}}
function sizes(t){ // alle Größen im Text in kg/l: „250 – 750 ml“ -> [0.25, 0.75]
  return [...String(t||"").matchAll(/(\d+(?:[.,]\d+)?)\s*(?=(?:(?:-|–|\/|bis)\s*\d+(?:[.,]\d+)?\s*)*(kg|g|ml|l|liter)\b)/gi)].map(m=>{const v=parseFloat(m[1].replace(",","."));return /^(g|ml)$/i.test(m[2])?v/1000:v})}
// Gleicher Artikel bei anderen Märkten. Schlüssel = Wörter aus Marke + Name (Reihenfolge egal),
// Preis umgerechnet auf dieselbe Menge (über den Grundpreis oder bei gleicher Packungsgröße).
const tokKey = o => [...new Set(((o.b||"")+" "+o.n).toLowerCase().match(/[a-zäöüß0-9]+/g)||[])].map(norm).filter(Boolean).sort().join(" ");
function sameElsewhere(o,pool){const k=tokKey(o),uf=x=>x.gp&&x.gp.v>0&&x.p>0?{v:x.gp.v/x.p,u:x.gp.u}:null,mine=uf(o),a=packQty(o.d);
  return pool.filter(x=>x!==o&&x.id!==o.id&&x.s!==o.s&&x.p>0&&tokKey(x)===k).map(x=>{const u=uf(x);
    if(mine&&u&&u.u===mine.u)return {x,f:u.v/mine.v};  // Preis von x × f = Preis für die Menge von o
    const b=packQty(x.d);return a&&b&&a.u===b.u&&Math.abs(a.v-b.v)/a.v<.05?{x,f:1}:null}).filter(Boolean)}
function checkDeal(o){
  if(!o.p)return o;
  const txt=`${o.n} ${o.d||""}`;
  // 1) „statt“ = Kilo-/Literpreis  2) „statt“ = Preis der ganzen Packung (10 x 0,75 € = 7,50 €)
  if(o.o){const kilo=o.gp&&Math.abs(o.gp.v-o.o)<.006,pack=[...txt.matchAll(/(\d+)\s*[x×]\s*\d/g)].find(m=>+m[1]>1&&+m[1]<=48&&Math.abs(o.p*m[1]-o.o)<.02);
    const big=!kilo&&!pack&&o.gp&&sizes(txt).some(v=>v>0&&Math.abs(o.gp.v*v-o.o)<.02)&&sizes(txt).some(v=>v>0&&Math.abs(o.gp.v*v-o.p)<.02);
    if(big)return {...o,o:null,rk:{t:"fix",l:[`Der Prospekt nannte „statt ${eur(o.o)}“ – das ist aber der Preis der größeren Packung (gleicher Grundpreis ${eur(o.gp.v)}/${o.gp.u}), kein früherer Preis. Kein echter Rabatt, SparRadar hat ihn entfernt.`]}};
    if(kilo||pack)return {...o,o:null,rk:{t:"fix",l:[kilo?`Der Prospekt nannte „statt ${eur(o.o)}“ – das ist aber der Preis pro ${o.gp.u==="l"?"Liter":"Kilo"}, kein früherer Preis. Kein echter Rabatt, SparRadar hat ihn entfernt.`:`Der Prospekt nannte „statt ${eur(o.o)}“ – das ist der Preis für alle ${pack[1]} Stück zusammen (${pack[1]} × ${eur(o.p)}), kein früherer Preis. Kein echter Rabatt, SparRadar hat ihn entfernt.`]}};}
  const e=o.ap&&o.ap<o.p?o.ap:o.p,base=o.o||o.p,pct=Math.round((1-e/base)*100);if(pct<40)return o;
  const ok=[],bad=[],q=packQty(o.d);let real=null,ext=0; // ext = Bestätigungen von außen (Händlerangabe, anderer Markt, Preisverlauf)
  // 0) Händlerangabe: „statt“ = eigener früherer Preis -> laut Preisangabenverordnung (§ 11) der niedrigste Preis
  //    der letzten 30 Tage in diesem Markt. Das ist der stärkste Beleg. „statt“ = UVP -> nur Preisempfehlung.
  const own=o.o&&o.ou===0,uvp=o.o&&o.ou===1;
  if(own){ok.push(`${sname(o.s)} gibt ${eur(o.o)} als eigenen früheren Preis an. Das muss laut Preisangabenverordnung der niedrigste Preis der letzten 30 Tage sein – der Rabatt ist echt.`);ext+=2}
  if(uvp)ok.push(`„statt“-Preis ${eur(o.o)} ist die unverbindliche Preisempfehlung (UVP) des Herstellers, nicht der bisherige Preis im Laden.`);
  // 3) Passt der Grundpreis zum Preis (Angebot oder App-Preis)?
  if(o.gp&&q&&q.u===o.gp.u&&q.v>0){const near=v=>Math.abs(v/q.v-o.gp.v)/o.gp.v<.12;
    if(near(o.p)||near(e))ok.push("Grundpreis passt zum Angebotspreis");
    else if(o.o&&near(o.o))bad.push("Der Grundpreis gehört zum „statt“-Preis, nicht zum Angebot – die Preisangabe im Prospekt wirkt fehlerhaft");
    else bad.push("Grundpreis und Preis passen nicht zusammen");}
  // 4) Gleicher Artikel bei anderen Märkten: wie teuer ist er dort regulär? Verglichen wird pro kg/l
  //    (Grundpreis) oder bei gleicher Packungsgröße – nie 100 g gegen 1 kg.
  const cmp=sameElsewhere(o,RAW).map(({x,f})=>({s:x.s,n:(x.o||x.p)*f}));
  if(cmp.length){const best=cmp.reduce((a,b)=>a.n<=b.n?a:b),n=Math.round(best.n*100)/100;
    if(n<base*.7&&own)ok.push(`Hinweis: bei ${sname(best.s)} kostet derselbe Artikel (gleiche Menge) regulär nur ${eur(n)}`);
    else if(n<base*.7){real=Math.max(0,Math.round((1-e/n)*100));bad.push(`„statt“-Preis ${eur(base)} ist zu hoch angesetzt: bei ${sname(best.s)} kostet derselbe Artikel (gleiche Menge) regulär ${eur(n)}. Realistische Ersparnis: ${real} %`)}
    else {ok.push(`Normalpreis passt zu anderen Märkten (${sname(best.s)}: ${eur(n)})`);ext++}}
  // 5) Preisverlauf: war er schon öfter so günstig?
  const h=histOf(o);if(h.length>=3){const avg=h.reduce((a,b)=>a+b,0)/h.length;
    if(avg<=e*1.1)bad.push(`Kostete zuletzt meist ${eur(avg)} – der Rabatt besteht nur auf dem Papier`);else {ok.push(`Vorher meist ${eur(avg)} – echter Preissturz`);ext++}}
  // 6) „statt“ genau 3-, 4-, 5- … faches des Angebots: meist eine Mehrfachpackung
  const mult=o.o?Math.round(o.o/o.p):0;if(mult>=3&&Math.abs(o.p*mult-o.o)<.015)bad.push(`„statt“-Preis ist genau ${mult} × der Angebotspreis – vermutlich der Preis einer Mehrfach- oder Großpackung`);
  // 7) Ungewöhnlich hoch. Lebensmittel haben immer einen Grundpreis; teure Artikel ohne Grundpreis = Non-Food
  const nonfood=NONFOOD_CATS.includes(o.c)||(!o.gp&&base>=15);
  // Lebensmittel: 82 % aller Rabatte liegen unter 40 %, nur gut 1 % bei 60 % und mehr -> ab 60 % nur mit Bestätigung von außen
  const open=[]; // nichts spricht dagegen, aber auch noch keine Bestätigung von außen
  if(pct>=60&&!ext&&(!nonfood||uvp))open.push(`Sehr hoher Rabatt (${pct} %) – kein Gegenbeweis gefunden, aber noch nicht durch Händlerangabe, anderen Markt oder Preisverlauf bestätigt. Der Preisverlauf bestätigt ihn automatisch in den nächsten Tagen.`);
  if(nonfood&&o.o&&pct>=60&&!ext&&!uvp)open.push("„statt“-Preis ist bei Non-Food meist die Preisempfehlung des Herstellers (UVP) – so teuer war es im Laden oft nie");
  if(o.ap&&e<o.p)ok.push(`Der stärkste Preis gilt nur mit ${o.s==="lidl"?"Lidl Plus":"der App"} – ohne App ${eur(o.p)}`);
  return {...o,rk:bad.length?{t:"warn",l:bad,real}:open.length?{t:"open",l:[...open,...ok]}:{t:"ok",l:ok.length?ok:["Keine Auffälligkeiten (Packung, Grundpreis und Kilopreis geprüft)"]}}}
const wasLbl = o => o.o&&o.ou===1&&ref(o)===o.o?"UVP":"statt";
const dealWarn = o => !!(o.rk&&o.rk.t==="warn");
// Sortierung: zweifelhafte Rabatte zählen nur mit der realistischen Ersparnis (sonst höchstens 45 %)
const sortPct = o => dealWarn(o)?(o.rk.real!=null?Math.min(o.rk.real,offPct(o)):Math.min(offPct(o),45)):offPct(o);
const weekOffers = () => OFFERS.filter(o => S.week ? (o.from && o.from>SHOP) : (!o.from || o.from<=SHOP));
function filtered(){
  let r=weekOffers();
  if(S.stores.size)r=r.filter(o=>S.stores.has(o.s));
  const qt=S.q.trim().split(/\s+/).filter(Boolean);S._catOff=false;
  if(qt.length){r=searchOffers(r,S.q);
    // Suche findet in der gewählten Kategorie nichts? Dann in allen Kategorien suchen statt „nicht im Angebot“
    if(S.cats.size){const rc=r.filter(o=>S.cats.has(o.c));if(rc.length||!r.length)r=rc;else S._catOff=true}}
  else if(S.cats.size)r=r.filter(o=>S.cats.has(o.c));
  r=r.filter(fltOk);
  // Sortierung „Ersparnis“ (Kevins Wunsch 01.11.): erst Lebensmittel, dann Getränke, Drogerie & Pflege, Tier, dann der Rest – innerhalb jeder Gruppe nach % Rabatt
  const f0={off:(a,b)=>catGrp(a)-catGrp(b)||sortPct(b)-sortPct(a)||fin(a)-fin(b),gp:(a,b)=>((unit(a)??1e9)-(unit(b)??1e9)),p:(a,b)=>((a.p>0?fin(a):1e9)-(b.p>0?fin(b):1e9))}[S.sort];
  // immer zuerst nach der gewählten Sortierung (Standard: stärkster Rabatt), bei Gleichstand der passendere Name
  const f=qt.length?(a,b)=>f0(a,b)||relevance(a,qt)-relevance(b,qt):f0;
  return r.sort(f)}
const CAT_GRP={getraenke:1,drogerie:2,katze:3,tier:3};
const catGrp=o=>NONFOOD_CATS.includes(o.c)&&!CAT_GRP[o.c]?4:(CAT_GRP[o.c]??(o.c==="sonstiges"?4:0));
// Zusatz-Filter (Fenster „Kategorien & Filter“), pro Gerät gespeichert
const FLT_TXT=o=>`${o.b||""} ${o.n} ${o.d||""}`;
const fltOk=o=>{const F=S.flt;
  if(F.min&&offPct(o)<F.min)return false;
  if(F.max&&!(o.p>0&&fin(o)<=F.max))return false;
  if(F.bio&&!/\bbio\b|\bbio-|naturland|demeter|bioland/i.test(FLT_TXT(o)))return false;
  if(F.vegan&&!/vegan|pflanzlich/i.test(FLT_TXT(o)))return false;
  if(F.real&&(!(o.o>0)||dealWarn(o)||offPct(o)<=0))return false;
  if(F.noapp&&(o.ap||o.ao||(o.x||[]).length))return false;
  if(F.app&&!appName(o))return false;
  if(F.low&&verdict(o).t!=="low")return false;
  return true};
const fltCount=()=>Object.values(S.flt).filter(Boolean).length;
const FLT_LABEL={bio:"Nur Bio",vegan:"Vegan",real:"Nur echte Rabatte",app:"Nur App-Angebote",noapp:"Ohne App & Karte",low:"Tiefstpreis"};
// App-Angebot? (Preis nur mit App = ao, oder extra App-Preis = ap) -> Name der App fürs Abzeichen
const appName = o => (o.ao||"").replace(/-App$/," App")||(o.ap&&o.ap<o.p?(o.s==="lidl"?"Lidl Plus":(STORES[o.s]?STORES[o.s].n.split(" ")[0]+" App":"App")):"");
const fltSummary=()=>[].concat(S.flt.min?[`ab ${S.flt.min} %`]:[],S.flt.max?[`bis ${eur(S.flt.max)}`]:[],Object.keys(FLT_LABEL).filter(k=>S.flt[k]).map(k=>FLT_LABEL[k]));
const score = o => {const v=verdict(o).t;return sortPct(o)-(dealWarn(o)?25:0)+(o.rk&&o.rk.t==="ok"?3:0)-(o.rk&&o.rk.t==="open"&&o.ou===1?20:0)+(v==="low"?8:0)-(v==="fake"?40:0)+(S.useApp?((o.x||[]).length+couponsFor(o).length)*3+(o.ap?3:0):0)};
// Kracher (Kevins Wunsch 01.11.): nur Lebensmittel & Drogerie – keine Non-Food-Aktionen wie Edekas Topf-Serie mit 70 %.
// Und Abwechslung: höchstens 2 Artikel derselben Warengruppe pro Markt vorne, der Rest rutscht nach hinten.
const ranked = () => {const all=weekOffers().filter(o=>o.p>0&&!NONFOOD_CATS.includes(o.c)).sort((a,b)=>score(b)-score(a)),n={},head=[],tail=[];
  all.forEach(o=>{const k=o.s+"|"+o.c;n[k]=(n[k]||0)+1;(n[k]<=2?head:tail).push(o)});const r=head.concat(tail);
  // jeder Markt mit belegtem Vorteil (Rabatt oder „Dein Vorteil“) bekommt einen Platz unter den ersten 8 (Kevin: Rewe soll auch dabei sein)
  [...new Set(r.map(o=>o.s))].forEach(st=>{if(r.slice(0,8).some(o=>o.s===st))return;
    const b=r.find(o=>o.s===st&&(score(o)>0||perk(o)));if(b){r.splice(r.indexOf(b),1);r.splice(7,0,b)}});
  return r};
// Märkte mit Angeboten, aber ohne belegbaren Rabatt (Rewe druckt fast nie „statt“) -> kurzer Hinweis im Kracher
const noProof=()=>{const r=ranked(),ws=weekOffers();return [...new Set(ws.map(o=>o.s))].filter(st=>!r.slice(0,8).some(o=>o.s===st))}
const watchHits = wk => S.watch.map(w=>({w,hits:OFFERS.filter(o=>(wk==null||(wk?o.from>SHOP:!o.from||o.from<=SHOP))&&hitW(o,w))}));

async function load(){
  try{
    const [o,h,nm]=await Promise.all([fetch("data/offers.json",{cache:"no-store"}).then(r=>r.json()),fetch("data/history.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({})),fetch("data/names.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({}))]);
    NAMES=Object.keys(nm||{});
    fetch("app-version.json",{cache:"no-store"}).then(r=>r.json()).then(v=>{APPV=v||{};render()}).catch(()=>{});
    META=o;HIST=h;
    RAW=o.offers.filter(x=>!x.to||x.to>=SHOP);OLD=new Map(o.offers.filter(x=>x.to&&x.to<SHOP).map(x=>[x.id,x]));OFFERS=RAW.map(checkDeal);PERK.clear();
    const g=new Date(o.generated);
    const pr=flyerInfo();
    document.getElementById("stand").innerHTML=`Wörth am Rhein · Stand ${g.toLocaleDateString("de-DE",{weekday:"short",day:"2-digit",month:"2-digit"})}, ${g.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})} Uhr · ${OFFERS.length} Angebote${pr.sum?`<br><button class="flyer" id="flyerBtn" aria-expanded="false">${pr.sum}</button>`:""}`;
    document.getElementById("flyerInfo").innerHTML=pr.rows;
  }catch(e){
    OFFERS=[];
    document.getElementById("stand").textContent="Wörth am Rhein · Angebote konnten nicht geladen werden";
    toast("Angebote konnten nicht geladen werden. Bitte später neu öffnen.");
  }
  OFFERS.forEach(o=>{if(!o.id)o.id="m-"+norm(o.n)+"-"+o.p});
  const before=S.coupons.length;S.coupons=S.coupons.filter(cpActive);if(S.coupons.length!==before)save(); // abgelaufene Coupons aufräumen
  render();  if(OFFERS.length)checkNews();
  checkWhatsNew(); // nur wenn kein anderes Fenster offen ist, sonst beim nächsten Öffnen
  Sync.pull(); // Listen vom anderen Gerät holen (nur wenn verbunden)
  Sync.srv().then(u=>{if(u&&S.sheet==="settings"&&!Sync.ready())render()}); // „Familien-Code erstellen“ nur zeigen, wenn der Speicher eingerichtet ist
}
// Wie aktuell sind die Prospekte? Häufigster Zeitraum je Markt, dazu wann die nächsten starten
function flyerInfo(){
  const mode=a=>{const c={};a.forEach(x=>{if(x)c[x]=(c[x]||0)+1});return Object.entries(c).sort((x,y)=>y[1]-x[1])[0]?.[0]};
  const d=x=>new Date(x+"T12:00:00").toLocaleDateString("de-DE",{day:"2-digit",month:"2-digit"});
  const wd=x=>new Date(x+"T12:00:00").toLocaleDateString("de-DE",{weekday:"short"}).replace(".","")+" "+d(x);
  // Wochenprospekt = Enddatum in den nächsten 8 Tagen (Dauerangebote bis Jahresende zählen nicht)
  const soon=new Date(Date.now()+8*864e5).toISOString().slice(0,10),week=a=>{const w=a.filter(o=>o.to&&o.to<=soon);return w.length?w:a};
  const auto=OFFERS,now=auto.filter(o=>!o.from||o.from<=SHOP),next=auto.filter(o=>o.from&&o.from>SHOP);
  const to=mode(week(now).map(o=>o.to)),nf=next.map(o=>o.from).sort()[0];
  const sum=[to?"Prospekte bis "+wd(to):"",nf?"neue ab "+wd(shopDay(nf)):""].filter(Boolean).join(" · ");
  const rows=Object.keys(STORES).filter(s=>auto.some(o=>o.s===s)).map(s=>{
    const n=week(now.filter(o=>o.s===s)),f=mode(n.map(o=>o.from)),t=mode(n.map(o=>o.to)),nx=next.filter(o=>o.s===s).map(o=>o.from).sort()[0];
    return `<span>${sb(s)}${esc(sname(s))}: ${f&&t?d(shopDay(f))+"–"+d(t):t?"bis "+d(t):"laufend"}${nx?` · neu ab ${d(shopDay(nx))}`:""}</span>`}).join("");
  return {sum,rows}}
const byId = id => OFFERS.find(o=>o.id===id);

// ---------- Vorschläge beim Tippen (Suche und Merkliste) ----------
// Gängige Artikel und Marken, damit es auch Vorschläge gibt, wenn gerade nichts davon im Angebot ist
const BASE_WORDS=("Butter,Milch,H-Milch,Hafermilch,Käse,Gouda,Mozzarella,Feta,Joghurt,Skyr,Quark,Sahne,Schmand,Eier,Margarine,"+
 "Hackfleisch,Hähnchenbrust,Hähnchenschenkel,Putenbrust,Schweinefilet,Schnitzel,Rindersteak,Bratwurst,Wiener Würstchen,Salami,Schinken,Aufschnitt,Lachs,Thunfisch,Garnelen,Fischstäbchen,"+
 "Brot,Toastbrot,Brötchen,Croissant,Nudeln,Spaghetti,Reis,Mehl,Zucker,Olivenöl,Sonnenblumenöl,Haferflocken,Müsli,Cornflakes,Marmelade,Honig,Nutella,Ketchup,Mayonnaise,Senf,Tomatensoße,"+
 "Tomaten,Kartoffeln,Äpfel,Bananen,Gurken,Paprika,Zwiebeln,Knoblauch,Salat,Möhren,Brokkoli,Erdbeeren,Trauben,Mandarinen,Avocado,Zitronen,Pilze,"+
 "Pizza,Tiefkühlpizza,Pommes,Eis,Tiefkühlgemüse,Schokolade,Chips,Kekse,Gummibärchen,Pralinen,Nüsse,"+
 "Kaffee,Kaffeebohnen,Kaffeepads,Kaffeekapseln,Tassimo,Tassimo Morning Café Strong & Intense XL,Dolce Gusto,Senseo,Nespresso,Jacobs,Tchibo,Dallmayr,Lavazza,Melitta,Eduscho,Tee,Kakao,"+
 "Coca-Cola,Pepsi,Fanta,Sprite,Spezi,Red Bull,Monster,Energy Drink,Mineralwasser,Apfelsaft,Orangensaft,Eistee,Bier,Pils,Radler,Weißwein,Rotwein,Sekt,Prosecco,"+
 "Milka,Lindt,Ritter Sport,Kinder,Ferrero,Haribo,Lorenz,Pringles,Leibniz,Oreo,Bahlsen,Dr. Oetker,Wagner,Iglo,Frosta,Barilla,Knorr,Maggi,Ehrmann,Müller,Weihenstephan,Landliebe,Kerrygold,Philadelphia,Bärenmarke,Alpro,"+
 "Katzenfutter,Nassfutter,Trockenfutter,Felix,Sheba,Whiskas,Gourmet,Kitekat,Animonda,Katzensnacks,Katzenstreu,Hundefutter,"+
 "Duschgel,Shampoo,Spülung,Deo,Zahnpasta,Zahnbürste,Rasierer,Rasierklingen,Gillette,Nivea,Dove,Balea,Toilettenpapier,Küchenrolle,Taschentücher,Feuchttücher,Windeln,Pampers,"+
 "Waschmittel,Persil,Ariel,Weichspüler,Spülmittel,Spülmaschinentabs,Finish,Putzmittel,Müllbeutel,Batterien").split(",");
// Großer Artikelstamm (Open Food Facts / Open Beauty Facts), wird erst beim ersten Tippen geladen
let CATALOG=null,CATALOG_N=null,catLoading=false;
function loadCatalog(then){if(CATALOG||catLoading)return;catLoading=true;
  fetch("data/catalog.json").then(r=>r.json()).then(a=>{CATALOG=Array.isArray(a)?a:[];CATALOG_N=CATALOG.map(norm);CAT_IDX=null;then&&then()}).catch(()=>{CATALOG=[];CATALOG_N=[]})}
// Kleine Bilder in der Vorschlagsliste: aus den Angeboten, aus names-img.json (z. B. Lidl-Sortiment)
// und aus catalog-img.json (Open Food Facts / Open Beauty Facts). Wird erst beim ersten Vorschlag geladen.
let SIMG=null,simgLoading=false,CAT_IDX=null;
function loadSugImgs(then){if(SIMG||simgLoading)return;simgLoading=true;
  Promise.all([fetch("data/names-img.json").then(r=>r.json()).catch(()=>({})),fetch("data/catalog-img.json").then(r=>r.json()).catch(()=>[])])
    .then(([n,c])=>{SIMG={names:n&&typeof n==="object"?n:{},cat:Array.isArray(c)?c:[]};then&&then()})}
// Kein Bild für genau diesen Namen? Ähnlichster Artikel im Artikelstamm (gleiche Marke = erstes Wort, mind. 3 gleiche Wörter)
function simImg(t){if(!SIMG||!CATALOG||!SIMG.cat.length)return "";const w=wTokens(t);if(w.length<3)return "";
  let best=-1,bi=-1;for(let i=0;i<CATALOG.length;i++){const c=CATALOG_N[i];if(!SIMG.cat[i]||!c.startsWith(w[0]))continue;
    const ct=wTokens(CATALOG[i]),n=w.filter(x=>ct.includes(x)).length;if(n>=3&&n>=w.length*.6&&n-ct.length*.1>best){best=n-ct.length*.1;bi=i}}
  if(bi<0)return "";const c=SIMG.cat[bi];return (c[0]==="b"?"https://images.openbeautyfacts.org":"https://images.openfoodfacts.org")+"/images/products/"+c.slice(2)+".jpg"}
function sugImg(t){
  const k=norm(t),o=OFFERS.find(x=>x.img&&(norm(x.n)===k||norm((x.b||"")+x.n)===k));if(o)return sharp(o.img);
  if(!SIMG)return "";
  const n=SIMG.names[t];if(n)return n;
  if(CATALOG_N&&SIMG.cat.length){if(!CAT_IDX){CAT_IDX=new Map();CATALOG_N.forEach((x,i)=>{if(!CAT_IDX.has(x))CAT_IDX.set(x,i)})}
    const c=SIMG.cat[CAT_IDX.get(k)];if(c)return (c[0]==="b"?"https://images.openbeautyfacts.org":"https://images.openfoodfacts.org")+"/images/products/"+c.slice(2)+".jpg"}
  return ""}
function suggest(q){
  const k=norm(q),tk=(q.toLowerCase().match(/[a-zäöüß0-9]+/g)||[]).map(norm).filter(Boolean);if(k.length<2)return [];
  const out=[],seen=new Set(),add=t=>{const n=norm(t);if(!n||seen.has(n))return;seen.add(n);out.push(t)};
  const hasAll=n=>tk.every(x=>n.includes(x));
  const starts=a=>a.filter(t=>norm(t).startsWith(k)),inside=a=>a.filter(t=>{const n=norm(t);return !n.startsWith(k)&&hasAll(n)});
  const live=weekOffers().map(o=>o.b&&!norm(o.n).includes(norm(o.b))?o.b+" "+o.n:o.n);
  const brands=[...new Set(OFFERS.map(o=>o.b).filter(Boolean))];
  [starts(BASE_WORDS),starts(brands),starts(live),inside(BASE_WORDS),inside(live),starts(NAMES),inside(NAMES)].forEach(a=>a.forEach(add));
  if(CATALOG_N){const a=[],b=[];for(let i=0;i<CATALOG_N.length&&a.length+b.length<400;i++){const n=CATALOG_N[i];if(n.startsWith(k))a.push(CATALOG[i]);else if(hasAll(n))b.push(CATALOG[i])}
    a.sort((x,y)=>x.length-y.length);b.sort((x,y)=>x.length-y.length);[...a,...b].forEach(add)}
  const wo=weekOffers();return out.slice(0,30).map(t=>({t,n:wo.filter(o=>watchMatch(o,t)).length}))}
function suggHTML(q,kind){const list=suggest(q);if(!list.length)return "";
  if(!SIMG)loadSugImgs(()=>{const box=document.getElementById(kind==="q"?"qSugg":"kwSugg");if(box&&box.innerHTML)showSugg(box.id,kind==="q"?S.q:(document.getElementById("kwIn")?.value||""),kind)});
  return `<div class="sugg" role="listbox" aria-label="Vorschläge">${list.map(x=>{const im=sugImg(x.t);return `<button type="button" role="option" data-sugg="${kind}" data-v="${esc(x.t)}"><i class="simg">${im?`<img src="${esc(im)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">`:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'}</i><span class="st">${esc(x.t)}</span>${x.n?`<em class="on">${x.n} im Angebot</em>`:`<em>nicht im Angebot</em>`}</button>`}).join("")}</div>`}
function showSugg(id,q,kind){const el=document.getElementById(id);if(!el)return;el.innerHTML=suggHTML(q,kind);
  if(!CATALOG)loadCatalog(()=>{const inp=document.getElementById(kind==="q"?"q":"kwIn");if(inp&&document.activeElement===inp)showSugg(id,inp.value,kind)})}
const hideSugg=()=>["qSugg","kwSugg"].forEach(id=>{const el=document.getElementById(id);if(el)el.innerHTML=""});

// ---------- Teilen ----------
const APP_URL="https://tiry38.github.io/sparradar/",APK_URL="https://github.com/Tiry38/sparradar/releases/download/apps/SparRadar-App.apk";
// wa.me öffnet WhatsApp (Handy-App bzw. WhatsApp Web am PC), dort nur noch den Kontakt antippen
const waLink = t => "https://wa.me/?text="+encodeURIComponent(t);
const SHARE_TXT = `Schau mal: SparRadar zeigt alle Angebote rund um Wörth am Rhein (Lidl, Aldi, Rewe, Netto, Edeka, dm) 🛒\n${APP_URL}\n\nAls Android-App zum Installieren:\n${APK_URL}`;
function listText(){const items=S.list.map(byId).filter(Boolean),g={};items.forEach(o=>(g[o.s]=g[o.s]||[]).push(o));
  const ex=S.extra.length?"\n\nSONSTIGES\n"+S.extra.map(x=>"- "+(qty(x.id)>1?qty(x.id)+"× ":"")+x.n+(x.p?" "+eur(x.p*qty(x.id)):"")).join("\n"):"";
  return "🛒 Einkaufszettel\n\n"+Object.entries(g).map(([s,os])=>sname(s).toUpperCase()+"\n"+os.map(o=>`- ${qty(o.id)>1?qty(o.id)+"× ":""}${o.n}${o.d?" ("+o.d+")":""} ${eur(fin(o)*qty(o.id))}${comboLabels(o).length?" mit "+comboLabels(o).join(" + "):""}`).join("\n")).join("\n\n")+ex}
const WA_ICON='<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></svg>';

// ---------- Ansichten ----------
function card(o,bestIds){
  const fav=S.watch.some(w=>norm(w.k)===norm(o.n)),inL=S.list.includes(o.id),vd=verdict(o),cl=comboLabels(o);
  // App-Preis direkt beim Preis: „Lidl Plus App-Preis 1,49 €“; mehrere Vorteile zusammen = „Mit Kombi“
  const combo=cl.length?`<div class="combo"><div class="top">${IC.layers} ${cl.length===1?esc(cl[0]):"Mit Kombi"}<b>${eur(fin(o))}</b></div>${cl.length>1?`<div class="src">${cl.map(esc).join(" + ")}</div>`:""}</div>`:"";
  return `<article class="card" data-detail="${esc(o.id)}" tabindex="0" aria-label="${esc(o.n)}: Details anzeigen">${thumb(o)}
   <div class="body">
   <span class="store">${esc(sname(o.s))}${o.b?" · "+esc(o.b):""}${o.pv?' <em class="pvtag" title="Vorschau – der Prospekt deines Markts ist noch nicht online">Vorschau</em>':""}</span>
   <div class="name">${esc(o.n)}<small>${esc(o.d||"")}</small></div>
   ${o.ao?`<span class="aonly">${IC.bag}Preis nur mit ${esc(o.ao)}</span>`:""}
   <div class="pricerow">${o.bo?`<div class="bonustag"><b>${eur(o.bo)}</b><small>Bonus-Guthaben</small></div>`:`<div class="tag" aria-label="${eur(o.p)}">${tagHTML(o.p)}</div>`}
     <div class="was">${o.o?`<s>${wasLbl(o)} ${eur(o.o)}</s>`:perk(o)&&perk(o).w?`<s>${perk(o).s}</s>`:perk(o)?`<span class="perk">▼ ${perk(o).s}</span>`:""}<span class="gp">${unitTxt(o)}</span>${bestIds.has(o.id)?'<br><span class="best">Bester Grundpreis</span>':""}</div></div>
   <div class="hist ${vd.t}" title="${esc(vd.l)}">${spark(o)}${vd.s}</div>
   ${combo}
   <div class="card-foot"><span class="valid${o.to===TODAY||o.to===TOMORROW?" last":""}">${validTxt(o)}</span>
     <button class="ibtn" data-fav="${esc(o.id)}" aria-pressed="${fav}" aria-label="${fav?"Von Merkliste entfernen":"Auf Merkliste setzen"}" title="Merken">${IC.star}</button>
     ${inL?qStep(o.id):""}<button class="ibtn add" data-add="${esc(o.id)}" aria-pressed="${inL}" aria-label="${inL?"Vom Einkaufszettel nehmen":"Auf den Einkaufszettel"}" title="Einkaufszettel">${inL?IC.check:IC.plus}</button></div>
   </div></article>`}

function kracherBtn(){const k=ranked()[0];if(!k)return"";
  return `<button class="kracher" id="openK" aria-label="Kracher öffnen">
   <span class="boom">${IC.flame}</span>
   <span><span class="eyebrow">Kracher ${S.week?nextShort():"der Woche"}</span><span class="what" style="display:block">${esc(k.n)} bei ${esc(sname(k.s))}</span><span class="how" style="display:block">${comboLabels(k).length?"Kombi: "+comboLabels(k).join(" + "):verdict(k).fresh?[ref(k)>fin(k)?"statt "+eur(ref(k)):"",validTxt(k)].filter(Boolean).join(" · "):verdict(k).l} · antippen für Details</span></span>
   <span class="big"><b>${eur(fin(k))}</b>${offPct(k)?`<span>−${offPct(k)} %</span>`:""}</span></button>`}

// Märkte ohne Angebote in der gewählten Woche (z. B. Prospekt für nächste Woche noch nicht veröffentlicht)
// mehrere Kategorien gleichzeitig (Kevins Wunsch)
const catNames=()=>[...S.cats].filter(k=>CATS[k]).map(k=>CATS[k]);
const catTitle=()=>{const n=catNames();return n.length>3?`${n.length} Kategorien`:n.join(" · ")};
function missingHTML(){if(S.q.trim()||S.cats.size)return "";
  const have=new Set((S.week||WEEKEND?weekOffers():OFFERS.filter(o=>!o.from||o.from<=SHOP)).map(o=>o.s)),miss=Object.keys(STORES).filter(s=>!have.has(s));
  if(!miss.length)return "";
  const dm=miss.includes("dm")?` <span class="dmnote">dm veröffentlicht seine Aktionen nicht vorab und hat sonst Dauerpreise (mind. 4 Monate garantiert) – ohne Aktion lohnt kein Warten.</span>`:"";
  return `<p class="catoff miss">Noch kein Prospekt ${S.week?"dafür":WEEKEND?"für nächste Woche":"für heute"} online: <b>${miss.map(s=>esc(sname(s))).join(", ")}</b>. Sobald er veröffentlicht ist, holt SparRadar ihn automatisch.${dm}</p>`}
function renderOffers(){
  if(!OFFERS.length)return `<div class="empty"><b>Noch keine Angebote</b>Sobald der tägliche Abruf gelaufen ist, erscheinen hier die Angebote.</div>`;
  const r=filtered(),bestIds=new Set();
  if((S.q.trim()||S.cats.size)&&r.length>1){const by={};r.forEach(o=>{if(unit(o)==null)return;const k=o.gp.u;if(!by[k]||unit(o)<unit(by[k]))by[k]=o});Object.values(by).forEach(o=>bestIds.add(o.id))}
  const hitCount=new Set(watchHits(S.week).flatMap(x=>x.hits.map(o=>o.id))).size;
  const title=S.q.trim()?`„${esc(S.q.trim())}“ im Angebot`:S.cats.size?catTitle():(S.week?"Angebote "+(nextShort()==="nächste Woche"?"der nächsten Woche":nextShort()):WEEKEND?"Angebote ab Montag":"Angebote, die jetzt gelten");
  const shown=r.slice(0,S.limit);
  return `${kracherBtn()}
   ${hitCount?`<button class="alertbar" id="goWatch">${IC.bell}${hitCount} Angebote passen zu deiner Merkliste</button>`:""}
   <div class="meta"><h2>${title}</h2><span>${r.length} von ${weekOffers().length} Angeboten</span></div>
   ${missingHTML()}
   ${fltCount()?`<p class="catoff fact">Filter aktiv: <b>${fltSummary().map(esc).join(" · ")}</b> <button class="linkbtn" data-fclear="1">Filter aus</button></p>`:""}
   ${S._catOff?`<p class="catoff">In „${esc(catNames().join(", "))}“ nichts gefunden – hier die Treffer aus allen Kategorien.</p>`:""}
   ${r.length?`<div class="grid">${shown.map(o=>card(o,bestIds)).join("")}</div>${r.length>shown.length?`<button class="btn ghost more" id="more">${r.length-shown.length} weitere anzeigen</button>`:""}`:
    `<div class="empty"><b>Gerade nicht im Angebot</b>Setz den Begriff auf deine Merkliste. Sobald ein Markt ihn reduziert, siehst du es dort.<br><br><button class="btn" id="watchFromSearch">${IC.bell} „${esc(S.q.trim()||"Suche")}“ beobachten</button></div>`}
   ${S.q.trim()?moreArticles(r):""}
   <div class="demo">${IC.bag}<span><b>Quellen:</b> Lidl und Aldi Süd direkt von deren Websites, Rewe, Netto, Edeka Jockgrim und dm aus den Prospekten bei kaufDA. Ist der Prospekt deines Markts für nächste Woche noch nicht online, zeigt SparRadar eine „Vorschau“ (Edeka aus dem regionalen Prospekt bei kaufDA, Rewe aus dem allgemeinen Prospekt bei prospektewoche.de). Gezeigt werden alle Angebote: Lebensmittel, Getränke, Drogerie und auch Haushalt, Technik, Mode, Garten und mehr. Persönliche App-Coupons kann SparRadar nicht sehen. Prüfe sie vor dem Einkauf in der jeweiligen App.</span></div>`}

// Suche: auch Artikel zeigen, die gerade nicht im Angebot sind, damit man sie auf die Merkliste setzen kann
function moreArticles(shown){
  const t=S.q.trim().split(/\s+/).map(norm).filter(Boolean);if(!t.length)return "";
  const have=new Set(shown.map(o=>norm(o.n)));
  const cand=[...new Set([...BASE_WORDS,...NAMES,...(CATALOG||[])])].filter(n=>{const k=norm(n);return t.every(x=>k.includes(x))&&![...have].some(h=>k.includes(h)||h.includes(k))});
  cand.sort((a,b)=>(norm(b).startsWith(t[0])-norm(a).startsWith(t[0]))||a.length-b.length);
  if(!CATALOG)loadCatalog(()=>{if(S.tab==="offers"&&S.q.trim())render()});
  if(!cand.length)return "";
  return `<section class="panel"><h3>Gerade nicht im Angebot</h3><p>Auf die Merkliste setzen: Sobald einer dieser Artikel im Angebot ist, zeigt SparRadar es dir beim Öffnen.</p>
   <div class="rows">${cand.slice(0,15).map(n=>{const on=S.watch.some(w=>norm(w.k)===norm(n));
    return `<div class="mrow"><span>${esc(n)}</span>${on?`<em>✓ auf der Merkliste</em>`:`<button class="btn ghost sm" data-watchname="${esc(n)}">${IC.star}Merken</button>`}</div>`}).join("")}</div></section>`}

// ---------- Preisvergleich: derselbe Artikel bei anderen Märkten ----------
function compareHTML(o){
  const rows=sameElsewhere(o,OFFERS).map(({x,f})=>({x,v:fin(x)*f,same:Math.abs(f-1)<.02}));
  if(!rows.length)return "";
  const top=rows.sort((a,b)=>a.v-b.v).slice(0,6),all=[{x:o,v:fin(o),same:true,me:true},...top].sort((a,b)=>a.v-b.v),best=all[0].v;
  return `<div class="cmp"><h4>Preisvergleich</h4><p class="cmp-sub">Derselbe Artikel bei anderen Märkten, umgerechnet auf die gleiche Menge.</p>
   ${all.map(r=>`<button class="cmprow${r.me?" me":""}" ${r.me?"disabled":`data-detail="${esc(r.x.id)}"`}>${sb(r.x.s)}<span class="cn">${esc(sname(r.x.s))}${r.me?" <em>(dieses Angebot)</em>":""}<small>${esc(r.x.d||"")}${r.x.from&&r.x.from>TODAY?" · ab "+esc(fmtDate(shopDay(r.x.from))):""}</small></span>
     <span class="cp"><b>${eur(r.v)}</b>${r.same?"":`<small>${eur(fin(r.x))} pro Packung</small>`}${r.v<=best+.004?'<em class="cbest">günstigster</em>':""}</span></button>`).join("")}</div>`}

// ---------- Barcode-Scanner ----------
// Kamera -> Strichcode (EAN) -> Artikelname über Open Food Facts / Open Beauty Facts (offene Datenbanken)
// -> passende Angebote. Erkennung: eingebauter BarcodeDetector (Chrome auf Android), sonst ZXing (docs/vendor).
const Scan={stream:null,timer:null,busy:false,last:"",res:"",
  msg(t){const e=document.getElementById("scanMsg");if(e)e.textContent=t},
  stop(){clearTimeout(this.timer);this.timer=null;if(this.stream){this.stream.getTracks().forEach(t=>t.stop());this.stream=null}},
  sync(){if(S.sheet!=="scan"){this.stop();return}const v=document.getElementById("scanVideo");if(v&&!this.stream&&!this.busy)this.start(v)},
  async start(v){
    if(!navigator.mediaDevices?.getUserMedia){this.msg("Die Kamera ist hier nicht verfügbar. Tippe die Nummer unter dem Strichcode unten ein.");return}
    this.busy=true;
    try{this.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"},audio:false})}
    catch(e){this.busy=false;this.msg(/SparRadarAndroid/.test(navigator.userAgent)?"Die alte Android-App darf die Kamera nicht nutzen. Installiere SparRadar über Chrome (Einladungslink) oder tippe die Nummer unten ein.":"Kein Zugriff auf die Kamera. Erlaube den Zugriff oder tippe die Nummer unter dem Strichcode unten ein.");return}
    this.busy=false;if(S.sheet!=="scan"){this.stop();return}
    v.srcObject=this.stream;try{await v.play()}catch(e){}
    this.msg("Strichcode in das Feld halten …");
    let det=null;
    if("BarcodeDetector" in window){try{const f=await BarcodeDetector.getSupportedFormats();if(f.includes("ean_13"))det=new BarcodeDetector({formats:["ean_13","ean_8","upc_a","upc_e"]})}catch(e){}}
    if(!det){try{await loadZXing()}catch(e){this.msg("Scanner konnte nicht geladen werden. Tippe die Nummer unten ein.");return}}
    const c=document.createElement("canvas"),ctx=c.getContext("2d",{willReadFrequently:true});
    const zx=det?null:(()=>{const h=new Map();h.set(ZXing.DecodeHintType.POSSIBLE_FORMATS,[ZXing.BarcodeFormat.EAN_13,ZXing.BarcodeFormat.EAN_8,ZXing.BarcodeFormat.UPC_A,ZXing.BarcodeFormat.UPC_E]);h.set(ZXing.DecodeHintType.TRY_HARDER,true);const r=new ZXing.MultiFormatReader();r.setHints(h);return r})();
    const tick=async()=>{if(!this.stream||S.sheet!=="scan")return;let code="";
      try{if(det){const r=await det.detect(v);code=r[0]?.rawValue||""}
        else if(v.videoWidth){c.width=v.videoWidth;c.height=v.videoHeight;ctx.drawImage(v,0,0);
          code=zx.decodeWithState(new ZXing.BinaryBitmap(new ZXing.HybridBinarizer(new ZXing.HTMLCanvasElementLuminanceSource(c)))).getText()}}catch(e){}
      if(code&&code!==this.last){this.last=code;try{navigator.vibrate?.(80)}catch(e){}this.lookup(code)}
      this.timer=setTimeout(tick,det?250:400)};
    tick()},
  async lookup(code){
    code=String(code).replace(/\D/g,"");if(code.length<8){this.msg("Bitte die ganze Nummer unter dem Strichcode eingeben (8 oder 13 Ziffern).");return}
    this.msg(`Strichcode ${code} erkannt – suche Artikel …`);
    let p=null;
    for(const host of ["world.openfoodfacts.org","world.openbeautyfacts.org"]){
      try{const r=await fetch(`https://${host}/api/v2/product/${code}.json?fields=product_name,product_name_de,brands,quantity`);
        const j=await r.json();if(j.status===1&&j.product){p=j.product;break}}catch(e){}}
    const box=document.getElementById("scanRes");if(!box)return;
    if(!p){this.msg(`Strichcode ${code}: Artikel nicht in der offenen Produktdatenbank gefunden.`);box.innerHTML=`<p class="cmp-sub">Tipp: Gib den Namen oben in die Suche ein.</p>`;return}
    const brand=(p.brands||"").split(",")[0].trim(),name=(p.product_name_de||p.product_name||"").trim(),full=[brand&&!norm(name).includes(norm(brand))?brand:"",name].filter(Boolean).join(" ");
    this.msg(`Erkannt: ${full}${p.quantity?" ("+p.quantity+")":""}`);
    box.innerHTML=scanResultHTML(full,brand,name);this.res=box.innerHTML},
};
function loadZXing(){return window.ZXing?Promise.resolve():new Promise((ok,err)=>{const s=document.createElement("script");s.src="vendor/zxing.min.js";s.onload=ok;s.onerror=err;document.head.appendChild(s)})}
function scanResultHTML(full,brand,name){
  const wo=weekOffers(),words=name.split(/\s+/).filter(w=>w.length>2).slice(0,3).join(" ");
  let hits=full?searchOffers(wo,full):[],how="Genau dieser Artikel";
  if(!hits.length&&brand&&words){hits=searchOffers(wo,brand+" "+words);how="Ähnliche Artikel der Marke"}
  if(!hits.length&&brand){hits=searchOffers(wo,brand);how="Andere Angebote der Marke "+brand}
  hits=hits.sort((a,b)=>fin(a)-fin(b)).slice(0,12);
  const on=S.watch.some(w=>norm(w.k)===norm(full));
  return `${hits.length?`<h4>${esc(how)} im Angebot</h4>${hits.map(o=>`<button class="cmprow" data-detail="${esc(o.id)}">${sb(o.s)}<span class="cn">${esc(o.n)}<small>${esc(sname(o.s))}${o.d?" · "+esc(o.d):""}</small></span><span class="cp"><b>${eur(fin(o))}</b>${offPct(o)?`<small>−${offPct(o)} %</small>`:""}</span></button>`).join("")}`
    :`<p><b>Gerade nicht im Angebot.</b> Setz ihn auf die Merkliste, dann siehst du es, sobald ein Markt ihn reduziert.</p>`}
   ${full?(on?`<p class="cmp-sub">✓ „${esc(full)}“ ist auf deiner Merkliste.</p>`:`<button class="btn" data-watchname="${esc(full)}">${IC.star}„${esc(full)}“ merken</button>`):""}`}
function renderScan(){
  return `<div class="sheet scan" role="dialog" aria-modal="true" aria-label="Barcode scannen">
   <div class="sheet-h"><h2>Artikel scannen</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <div class="scanbox"><video id="scanVideo" playsinline muted></video><i class="scanframe"></i></div>
   <p id="scanMsg" class="scanmsg">Kamera wird gestartet …</p>
   <form class="addrow" id="eanForm"><input id="eanIn" inputmode="numeric" pattern="[0-9 ]*" placeholder="oder Nummer unter dem Strichcode eintippen" autocomplete="off"><button class="btn" type="submit">Suchen</button></form>
   <div id="scanRes" class="cmp scanres">${Scan.res}</div>
   <p class="cmp-sub">Artikeldaten: Open Food Facts / Open Beauty Facts (offene Datenbanken). Das Kamerabild bleibt auf deinem Gerät.</p></div>`}

// ---------- Detailansicht eines Artikels ----------
const dImages = o => [...new Set([o.il||o.img,o.img,...(o.ims||[])].filter(u=>safeUrl(u)).map(sharp))];
function renderDetail(){
  const o=byId(S.detail);if(!o)return `<div class="sheet"><div class="sheet-h"><h2>Artikel</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div><div class="empty"><b>Nicht mehr im Angebot</b></div></div>`;
  const ims=dImages(o),cur=ims[Math.min(S.dImg||0,ims.length-1)],inL=S.list.includes(o.id),fav=S.watch.some(w=>norm(w.k)===norm(o.n)),vd=verdict(o),st=steps(o);
  const hist=(HIST[o.s+"|"+norm(o.n).slice(0,40)]||[]).slice(-8).reverse();
  const share=`${o.n}${o.b?" ("+o.b+")":""} bei ${sname(o.s)}: ${o.bo?eur(o.bo)+" Bonus":eur(fin(o))}${offPct(o)?` (−${offPct(o)} %)`:""}${validTxt(o)?", "+validTxt(o):""}\n\nGefunden mit SparRadar: ${APP_URL}`;
  return `<div class="sheet detail" role="dialog" aria-modal="true" aria-label="${esc(o.n)}">
   <div class="sheet-h">${sb(o.s,true)}<h2>${esc(sname(o.s))}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <div class="dpic" style="--cc:${CC[o.c]||CC.sonstiges}">${cur?`<button class="dzoom" data-zoom="${esc(cur)}" aria-label="Bild groß anzeigen"><img src="${esc(cur)}" alt="${esc(o.n)}" referrerpolicy="no-referrer" data-cat="${o.c}"></button>`:(ILL[o.c]||ILL.sonstiges)}${offPct(o)?`<span class="off${dealWarn(o)?" q":""}"${dealWarn(o)?' title="Rabatt widerlegt – Details antippen"':""}>−${offPct(o)} %${dealWarn(o)?" ?":""}</span>`:""}${cur?`<span class="zhint">Antippen zum Vergrößern</span>`:""}</div>
   ${ims.length>1?`<div class="dthumbs">${ims.map((u,i)=>`<button data-dimg="${i}" aria-pressed="${u===cur}" aria-label="Bild ${i+1}"><img src="${esc(u)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-thumb="1"></button>`).join("")}</div>`:""}
   <div class="dinfo">
    ${o.b?`<span class="store">${esc(o.b)}</span>`:""}
    <h3 class="dtitle">${esc(o.n)}</h3>
    ${o.d?`<p class="dsub">${esc(o.d)}</p>`:""}
    ${o.ao?`<span class="aonly">${IC.bag}Preis nur mit ${esc(o.ao)}</span>`:""}
    <div class="dprice">${o.bo?`<div class="bonustag"><b>${eur(o.bo)}</b><small>Bonus-Guthaben</small></div>`:`<div class="tag xl">${tagHTML(fin(o))}</div>`}
     <div>${ref(o)>fin(o)&&!o.bo?`<s>${wasLbl(o)} ${eur(ref(o))}</s><br><b style="color:var(--save)">Du sparst ${eur(ref(o)-fin(o))}</b>`:perk(o)&&perk(o).w?`<s>${perk(o).s}</s>`:""}${unitTxt(o)?`<div class="gp">${esc(unitTxt(o))}</div>`:""}</div></div>
    ${st.length>1?`<div class="stack">${st.map((x,i)=>i===0?`<div><span>${esc(x.l)}</span><span>${eur(x.v)}</span></div>`:`<div class="neg"><span>− ${esc(x.l)}</span><span>${eur(x.v)}</span></div>`).join("")}<div class="res"><span>Du zahlst effektiv</span><span>${eur(fin(o))}</span></div></div>`:""}
    ${cpQuick(o)}
    ${o.rk?`<div class="rk ${o.rk.t}"><h4>${o.rk.t==="warn"?"⚠️ Rabatt widerlegt":o.rk.t==="fix"?"🔧 Rabatt korrigiert":o.rk.t==="open"?"🔍 Rabatt noch nicht bestätigt":"✅ Rabatt bestätigt"}</h4><ul>${o.rk.l.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>`:""}
    ${o.ous&&o.o?`<div class="rk perkbox"><h4>🏷️ Kostet eigentlich ${eur(o.o)}</h4><p>Das ist die UVP (Preisempfehlung des Herstellers). ${esc(sname(o.s))} nennt im Prospekt keinen „statt“-Preis – die UVP stammt von ${esc(sname(o.ous))} für denselben Markenartikel in gleicher Menge.</p></div>`:""}
    ${perk(o)?`<div class="rk perkbox"><h4>💡 Dein Vorteil</h4><p>${esc(perk(o).l)}</p></div>`:""}
    ${compareHTML(o)}
    <dl class="dfacts">
     <dt>Gültig</dt><dd>${o.from&&o.to?fmtDate(shopDay(o.from))+" – "+fmtDate(o.to):validTxt(o)||"laufend"}${o.to===TODAY?' <b class="last">nur noch heute</b>':""}</dd>
     <dt>Markt</dt><dd>${esc(sname(o.s))}</dd>
     ${o.pv?`<dt>Vorschau</dt><dd>Aus dem ${o.src==="prospektewoche.de"?"allgemeinen "+esc(sname(o.s).split(" ")[0])+"-Prospekt (prospektewoche.de)":esc(sname(o.s).split(" ")[0])+"-Prospekt der Region"} für nächste Woche. Der Prospekt deines Markts ist noch nicht online – sobald er da ist, gleicht SparRadar automatisch ab. Einzelne Preise können abweichen.</dd>`:""}
     ${o.pg?`<dt>Prospekt</dt><dd>Seite ${esc(o.pg)}</dd>`:""}
     ${o.cat?.length?`<dt>Kategorie</dt><dd>${o.cat.map(esc).join(" › ")}</dd>`:`<dt>Kategorie</dt><dd>${esc(CATS[o.c]||"")}</dd>`}
     <dt>Quelle</dt><dd>${esc(o.src||"")}</dd>
    </dl>
    ${o.inf?`<div class="dtext"><h4>Beschreibung</h4><p>${esc(o.inf)}</p></div>`:""}
    <div class="verdict ${vd.t}">${spark(o,90,24)}<span>${esc(vd.l)}</span></div>
    ${hist.length?`<div class="dtext"><h4>Preisverlauf</h4><ul class="dhist">${hist.map(([d,p])=>`<li><span>${fmtDate(d)}</span><b>${eur(p)}</b></li>`).join("")}</ul></div>`:""}
    <div class="dactions">
     <button class="btn" data-add="${esc(o.id)}">${inL?IC.check+"Auf dem Zettel":IC.plus+"Auf den Einkaufszettel"}</button>${inL?qStep(o.id,true):""}
     <button class="btn ghost" data-fav="${esc(o.id)}">${IC.star}${fav?"Gemerkt":"Merken"}</button>
     <a class="btn wa" href="${waLink(share)}" target="_blank" rel="noopener">${WA_ICON}Teilen</a>
    </div>
   </div>
  </div>`}
function renderLightbox(){const u=S.lightbox,pg=/zoomlarge_page_/.test(u||"");return u?`<div class="lightbox${pg?" pg":""}" id="lightbox" role="dialog" aria-label="Bild groß"><img src="${esc(u)}" alt="" referrerpolicy="no-referrer"${pg?' class="page"':""}><button class="ibtn lbclose" id="lbClose" aria-label="Schließen">${IC.x}</button></div>`:""}

// ---------- „Was ist neu“ nach einem Update ----------
// Bei jeder neuen Version hier oben einen Eintrag ergänzen (Schlüssel = Nummer aus app.js?v= in index.html)
const CHANGES={
  88:["Die Coupon-Suche heißt jetzt „Coupon-Finder“."],
  87:["Neu: der Coupon-Finder findet jetzt geheime Geld-zurück-Aktionen der Hersteller (oft 100 % zurück), die in keiner Markt-App stehen. App-Preise siehst du weiter direkt bei den Angeboten.","Nach dem Einkauf erinnert SparRadar dich, den Kassenbon hochzuladen."],
  86:["Coupon-Bericht: oben nach Markt filtern – z. B. nur Lidl-Coupons ansehen."],
  85:["Coupons nur noch digital und ganz einfach: suchen, einfügen, in der Markt-App aktivieren – an der Kasse reicht ein Scan der Kundenkarte."],
  84:["Kasse noch einfacher: großer Zähler und klare Tipps."],
  83:["Einstellungen und Willkommens-Infos neu erklärt – Schritt für Schritt, für jeden verständlich.","Am PC bleibt die obere Leiste auch mit großer Schrift (A+) im Bild."],
  82:["Nach dem letzten Haken auf dem Zettel öffnet sich die App des Markts – Kundenkarte zeigen, fertig."],
  81:["Neu im Tab „Coupons“: Knopf „🔍 Coupon suchen“. Zeigt alle App- und Bonus-Vorteile der Woche (Lidl Plus, Edeka-/Netto-App, Rewe Bonus), die größten zuerst – einfach „Einfügen“ oder „Nein“."],
  80:["Kracher: höchstens 2 Angebote pro Markt je Abschnitt – nicht mehr fast nur Edeka mit App-Preis."],
  79:["Angebote nach Ersparnis: erst Lebensmittel, dann Getränke, Drogerie & Pflege, Tierbedarf und zum Schluss Technik, Kleidung & Co. – innerhalb jeder Gruppe weiter nach dem höchsten Rabatt."],
  78:["Kracher: Jeder Markt mit einem belegten Rabatt bekommt einen Platz. Fehlt ein Markt (oft Rewe, der selten „statt“-Preise druckt), steht kurz dabei, warum."],
  77:["Am PC bleibt die ganze obere Leiste (Logo, Schriftgröße, Woche und Reiter) beim Scrollen stehen."],
  76:["Kracher der Woche: nur noch Lebensmittel & Drogerie – keine Töpfe, Leitern & Co. mehr. Und mehr Abwechslung statt zehnmal dasselbe."],
  75:["Am PC bleibt die Leiste mit Angebote, Merkliste, Einkaufszettel und Coupons beim Runterscrollen oben stehen."],
  74:["Den Knopf zur Markt-App gibt es jetzt auch für Aldi Süd, Netto und dm."],
  73:["Geräte verbinden: Wer noch mit GitHub-Schlüssel verbunden ist, kann mit einem Tipp auf einen Familien-Code umziehen – sicherer, alles wird mitgenommen."],
  72:["Geräte verbinden ohne GitHub: „Neuen Familien-Code erstellen“ antippen, Code kopieren, an die Familie schicken – fertig."],
  71:["Gespart-Zähler antippen: Einträge einzeln löschen oder alles auf 0 setzen (z. B. nach einem Test)."],
  70:["Im Willkommens-Fenster steht jetzt: Fehler entdeckt? Einfach Kevin schreiben."],
  69:["Auf dem Einkaufszettel steht neben Lidl, Rewe und Edeka ein Knopf „📱 Lidl Plus“ usw. – ein Tipp öffnet die App des Markts, z. B. für deinen Code an der Kasse."],
  68:["Einkauf fertig im Lidl, Rewe oder Edeka? Nach dem letzten Haken öffnet SparRadar am Handy direkt die App des Markts – Code an der Kasse zeigen. Abschaltbar in den Einstellungen."],
  67:["Geräte verbinden: Jedes Gerät wählt jetzt selbst, was es teilt – Einkaufszettel, Merkliste, Coupons. So teilt die Familie den Einkaufszettel, während deine Merkliste nur auf deinem Handy und PC gleich ist.","Beim „Code kopieren“ wählst du gleich mit aus, was das neue Gerät teilen soll – auf dem anderen Gerät nur noch einfügen.","Neue Nutzer sehen beim ersten Öffnen ein Willkommens-Fenster mit allen wichtigen Funktionen (auch in den Einstellungen unter „Erste Schritte“)."],
  66:["App-Angebote sind jetzt auf einen Blick erkennbar: Abzeichen „📱 Lidl Plus“ direkt auf dem Bild.","Neuer Filter „Nur App-Angebote“. „Ohne App & Karte“ blendet jetzt auch Preise aus, die nur mit der App gelten."],
  65:["Einkaufszettel: Neben jedem Artikel gibt es jetzt 🎟️. Im Laden antippen, Coupon-Wert wählen – fertig, Preis und Summe sind sofort angepasst."],
  64:["Coupon mit einem Tipp: Im Angebot auf „🎟️ Ich habe einen Coupon dafür“ tippen und den Wert wählen (z. B. −1 € oder −20 %). Markt, Artikel und Gültigkeit übernimmt SparRadar selbst und rechnet den Coupon sofort ein.","Merkliste: Gemerkte Artikel zeigen jetzt ihr Produktbild (aus dem Artikelstamm), auch wenn sie gerade nicht im Angebot sind."],
  63:["Geräte verbinden: Beliebig viele Geräte mit demselben Code verbinden (z. B. Handys von Mama und Stefan, Tablet, PC) – alle haben denselben Einkaufszettel und dieselbe Merkliste.","In den Einstellungen siehst du jetzt, welche Geräte verbunden sind und wann sie zuletzt aktiv waren. Jedem Gerät kannst du einen Namen geben, z. B. „Mamas Handy“."],
  62:["Merkliste: Falsche Treffer behoben (z. B. „More Barista“ fand „Dallmayr Prodomo“, weil Wörter über Wortgrenzen verglichen wurden).","Gemerkte Artikel jetzt übersichtlich mit Bild und „x Treffer im Angebot“ bzw. „gerade nicht im Angebot“. Antippen zeigt nur die Treffer dieses Artikels."],
  61:["Bilder: Hohe Fotos (z. B. Flaschen) wurden in der Kachel abgeschnitten, sodass oft nur der Deckel zu sehen war. Jetzt ist immer das ganze Bild sichtbar.","Schärfere Bilder: Winzige Prospekt-Ausschnitte werden nicht mehr künstlich vergrößert (das machte sie pixelig). Wo es denselben Markenartikel bei einem anderen Markt mit gutem Foto gibt, zeigt SparRadar dieses Foto."],
  60:["Menge gleich beim Hinzufügen: Sobald ein Artikel auf dem Einkaufszettel ist, kannst du direkt auf der Karte (und im Detail) mit − und + die Anzahl einstellen.","Kaffeemaschinen, Pizzaöfen, Fritteusen & Co. stehen jetzt unter Technik."],
  59:["Durchgestrichener Preis „kostet eigentlich“ jetzt auch bei Rewe und Edeka: Nennt der Prospekt keinen „statt“-Preis, zeigt SparRadar die echte UVP desselben Markenartikels (gleiche Menge) von einem anderen Markt – oder den bisherigen Preis im selben Markt.","Kaffeemaschinen, Wasserkocher & Co. stehen jetzt unter Technik statt unter Kaffee & Tee."],
  58:["Kategorien: Du kannst jetzt mehrere gleichzeitig auswählen, z. B. Obst & Gemüse und Fleisch & Fisch. Nochmal antippen nimmt eine Kategorie wieder raus, „Alle Kategorien“ setzt alles zurück.","Prospekte, die erst am Montag erscheinen, werden jetzt auch sofort geholt."],
  57:["Einkaufszettel als Einkaufswagen: Im Laden antippen, was im Wagen liegt. Am Handy schließt der letzte Artikel den Einkauf ab – mit kurzem Bericht und „Zurückholen“.","Neu unter dem Zettel: „Meine Einkäufe“ mit Monatsbericht (ausgegeben, gespart, nach Markt) und allen Einkäufen zum Nachlesen.","Mengen (2×, 3×), eigene Einträge mit Preis („Brot 1,99“), Budget, „Wieder kaufen“ aus deinen letzten Einkäufen. Beim Einkaufen bleibt der Bildschirm an."],
  56:["Neue Filter unter „Kategorien & Filter“: Mindest-Ersparnis (z. B. ab 30 %), Preis bis (z. B. bis 2 €), nur Bio, vegan, nur echte Rabatte, ohne App & Karte und Tiefstpreis. Die Auswahl bleibt gespeichert, „Filter aus“ setzt sie mit einem Tipp zurück."],
  55:["Neue Angebote kommen jetzt viel schneller in die App: Sobald ein Markt seinen neuen Prospekt veröffentlicht, ist er nach wenigen Minuten drin, statt erst nach dem kompletten Abruf. Die App schaut alle 5 Minuten nach neuen Daten."],
  54:["dm: Fehlt der neue dm-Prospekt, sagt die App das jetzt klar dazu. dm veröffentlicht nichts vorab, dafür schaut der Prospekt-Wächter jetzt jeden Tag nach, damit die neuen dm-Aktionen sofort drin sind."],
  53:["Rewe: Angebote der nächsten Woche als „Vorschau“ aus dem Rewe-Prospekt, sobald er veröffentlicht ist. Kommt der Prospekt deines Markts, ersetzt er die Vorschau sofort.","Einkaufszettel: abgelaufene Angebote verschwinden nicht mehr still, sondern stehen unter „Abgelaufen“ – mit Tausch-Knopf, wenn es den Artikel wieder gibt.","Fehlt ein Markt in der nächsten Woche, steht oben, dass sein Prospekt noch nicht online ist."],
  52:["Samstag ab 22 Uhr und sonntags zeigt die ganze App automatisch schon die Angebote ab Montag – dann hat eh kein Markt mehr offen."],
  51:["Nächste Woche früher: Aldi-Angebote der kommenden Woche kommen jetzt direkt von den Aldi-Tagesseiten, Edeka als „Vorschau“ aus dem regionalen Prospekt, sobald es ihn gibt.","Ein Prospekt-Wächter schaut Do–So alle 2 Stunden nach neuen Prospekten aller Märkte."],
  50:["Vorschläge beim Tippen (Suche und Merkliste) zeigen jetzt kleine Produktbilder."],
  49:["Der Knopf „Demnächst“ heißt jetzt „Nächste Woche“ (bzw. „Ab Donnerstag“, wenn noch diese Woche etwas startet).","Neu: Angebote ohne „statt“-Preis zeigen jetzt ihren Vorteil – blau markiert: günstiger als zuletzt, Großpackung günstiger pro Kilo oder günstigster Markt.","Filter überarbeitet: Kategorien richten sich nur noch nach Artikelname, Marke und Warengruppe, nicht mehr nach der Beschreibung."],
  48:["Neu: Barcode-Scanner. Im Laden auf das Strichcode-Symbol im Suchfeld tippen, Artikel scannen und sehen, ob er gerade irgendwo im Angebot ist.","Neu: Preisvergleich in der Artikelansicht – derselbe Artikel bei den anderen Märkten.","Einkaufszettel: Summe pro Markt und Tipp, wenn es einen Artikel woanders günstiger gibt (mit „Tauschen“).","Neu: Gespart-Zähler. Was du auf dem Zettel abhakst, zählt als gekauft: diese Woche, diesen Monat, insgesamt."],
  47:["Kracher der Woche: zählt jetzt nur belegte Rabatte. Rabatte gegenüber der UVP (Preisempfehlung des Herstellers) stehen in der Liste mit vollem Prozentwert, werden aber nicht mehr zum Kracher.","Bei UVP steht jetzt „UVP“ statt „statt“ am Preis."],
  46:["Scheck-In und Serpa sind entfernt, ebenso „Angebot eintragen“.","Genaue Rabatt-Prüfung: Ab 40 % wird jeder Rabatt geprüft. Echte Rabatte (Händler nennt eigenen 30-Tage-Preis, anderer Markt oder Preisverlauf bestätigt) bleiben oben. Grau wird nur, was nachweislich falsch ist. UVP wird als „UVP“ angezeigt."],
  45:["Automatische Rabatt-Prüfung: Jeder hohe Rabatt wird gegengecheckt (Packung, Grundpreis, andere Märkte, Preisverlauf). Zweifelhafte zeigen ein „?“ und stehen nicht mehr ganz oben.","Falsche Riesen-Rabatte aussortiert (z. B. Kilopreis oder Packungspreis als „statt“-Preis).","Suche findet jetzt immer etwas, auch wenn gerade eine andere Kategorie gewählt ist.","Preise unter 1 € stehen jetzt richtig da (z. B. 0.88 statt -.88).","Neue Prospekte zeigen den echten ersten Einkaufstag (Montag statt Sonntag).","App-Preise sauber benannt, z. B. „Netto App-Preis“.","Lange Artikelbeschreibungen machen die Karten nicht mehr riesig – alles Weitere in der Detailansicht."],
  44:["Kein Knopf führt mehr unnötig aus der App heraus – alle Infos stehen direkt in SparRadar."],
  43:["Update-Fenster sieht sauber aus."],
  40:["Alle Produktbilder jetzt in voller Auflösung – scharf statt verpixelt.","Grüne Umrandung der Markt-Kacheln nicht mehr abgeschnitten."],
  38:["Neues Logo in Anthrazit und Grün – mit Prozentzeichen."],
  37:["Zurück-Taste: geht immer nur einen Schritt zurück, ganz am Ende fragt SparRadar, ob du die App schließen willst."],
  36:["SparRadar verschenken: schöne Einladung mit Logo per WhatsApp, Installation ohne Warnungen."],
  35:["Jeden Artikel antippen: Detailansicht mit großem Bild, Beschreibung, Preisrechnung und Preisverlauf. Bild antippen zum Vergrößern."],
  34:["Angebote stehen immer nach dem stärksten Rabatt sortiert, auch bei der Suche.","Die Einstellungen findest du jetzt ganz unten im Tab „Coupons“."],
  32:["Viel mehr Angebote: Vorher fehlten bei jedem Markt viele Angebote (z. B. bei Lidl), jetzt kommen alle aus den Prospekten.","Lidl-Plus-Preise, App-Preise und Rewe-Bonus stehen direkt beim Angebot."],
  31:["Suche und Merkliste kennen jetzt zehntausende Artikel (z. B. alle Tassimo-Sorten) zum gezielten Merken.","Merkliste erkennt auch Prospekt-Angebote wie „Tassimo, versch. Sorten“."],
  30:["Keine Update-Hinweise für die Android-App mehr: Neuigkeiten kommen ab jetzt immer automatisch, ohne Installieren."],
  29:["Nach jedem Update erscheint dieses Fenster mit den Neuigkeiten."],
  27:["Die Zurück-Taste bzw. Wischgeste schließt zuerst offene Fenster statt der App."],
  26:["Neue Farben: Anthrazit und Grün."],
  24:["Märkte oben als Kacheln mit Logo und Anzahl der Angebote.","Die Suche ist genauer, beim Tippen gibt es Vorschläge."],
  20:["Einkaufszettel: Artikel antippen zum Abhaken, eigene Einträge wie „Brot“.","Rot markiert: Angebote, die nur noch heute oder bis morgen gelten."]};
// beim Start festhalten, ob SparRadar auf diesem Gerät schon benutzt wurde (vor diesem Öffnen)
const WAS_USER=(()=>{try{return localStorage.getItem("sr_seenHits")!=null}catch(e){return false}})();
function checkWhatsNew(){
  if(!MYV)return;
  const last=store.get("seenVersion",null);
  // Erstinstallation: nichts zeigen. Wer SparRadar schon vorher benutzt hat, sieht die letzten Neuigkeiten.
  if(last==null&&!WAS_USER){store.set("seenVersion",MYV);if(!S.sheet||S.sheet==="news"){S.sheet="welcome";render()}return}
  if(S.sheet)return;
  if(String(last)===String(MYV))return;
  const vs=Object.keys(CHANGES).map(Number).sort((a,b)=>b-a);
  let pick=vs.filter(v=>v>(+last||0)&&v<=+MYV);
  if(!pick.length)pick=vs.filter(v=>v<=+MYV).slice(0,1);
  S.whatsNew=pick.flatMap(v=>CHANGES[v]).slice(0,7);
  store.set("seenVersion",MYV);S.sheet="whatsnew";render()}
// Erstes Öffnen nach der Installation: kurz erklären, was SparRadar kann (auch später über Einstellungen erreichbar)
function renderWelcome(){const it=[
  ["🏷️","Alle Angebote rund um Wörth","Lidl, Aldi, Rewe, Netto, Edeka und dm – jeden Tag neu. Samstagabend siehst du schon die Angebote ab Montag."],
  ["🔎","Suchen & filtern","Oben suchen oder nach Markt und Kategorie filtern. Mehrere Kategorien gleichzeitig gehen auch."],
  ["📱","App-Angebote erkennen","Das Abzeichen „📱 Lidl Plus“ usw. zeigt: Dieser Preis gilt nur mit der App des Markts."],
  ["🔔","Merkliste","Artikel merken – SparRadar zeigt dir, sobald sie im Angebot sind."],
  ["🛒","Einkaufszettel","Mit ＋ auf den Zettel. Im Laden antippen, was im Wagen liegt. Mit 🎟️ trägst du einen Coupon mit einem Tipp ein."],
  ["👨‍👩‍👦","Geräte verbinden","Mehrere Handys, Tablets oder PCs teilen denselben Einkaufszettel. Ob auch die Merkliste gleich sein soll, wählt jedes Gerät selbst – z. B. eigene Geräte alles, andere Menschen nur den Zettel."],
  ["🎟️","Coupons","Tab „Coupons“: Der Coupon-Finder zeigt Aktionen, bei denen dir der Hersteller den Kaufpreis zurückzahlt – oft komplett. Einfügen, einkaufen, Kassenbon hochladen."],
  ["⚙️","Einstellungen","Ganz unten im Tab „Coupons“: Geräte verbinden, SparRadar teilen. Schrift größer: „A+“ oben rechts."],
  ["💬","Fehler entdeckt?","Stimmt ein Preis nicht oder klemmt etwas? Sag gern der Person Bescheid, von der du SparRadar bekommen hast. Jeder Hinweis hilft!"]];
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Willkommen bei SparRadar">
   <div class="sheet-h"><span class="newsico">👋</span><h2>Willkommen bei SparRadar</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <p style="margin:-6px 0 4px;color:var(--muted)">Deine Spar-App für alle Angebote in der Nähe. Das Wichtigste in 30 Sekunden:</p>
   <ul class="welc">${it.map(([i,t,d])=>`<li><span class="wi">${i}</span><span><b>${t}</b><small>${d}</small></span></li>`).join("")}</ul>
   <div class="factions"><button class="btn ghost" data-welcome="sync">Geräte verbinden</button><button class="btn" data-welcome="ok">Los geht's</button></div>
  </div>`}
function renderWhatsNew(){const n=S.whatsNew||[];
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="SparRadar wurde aktualisiert">
   <div class="sheet-h"><span class="newsico">✨</span><h2>SparRadar wurde aktualisiert</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <p style="margin:-6px 0 0;color:var(--muted)">Du hast jetzt <b>Version ${esc(MYV)}</b>.${n.length?" Das ist neu:":""}</p>
   ${n.length?`<ul class="wn">${n.map(t=>`<li>${esc(t)}</li>`).join("")}</ul>`:"<p>Kleine Verbesserungen und Fehlerkorrekturen.</p>"}
   <div class="factions" style="grid-template-columns:1fr"><button class="btn" data-newsdone="ok">Super, danke</button></div>
  </div>`}

// Beim Öffnen: was von der Merkliste ist neu im Angebot? (nur Neues seit dem letzten Hinweis)
function checkNews(){
  if(S.sheet)return;
  const hits=[...new Map(watchHits(0).flatMap(x=>x.hits).map(o=>[o.id,o])).values()];
  const sh0=store.get("seenHits",[]),seen=new Set(Array.isArray(sh0)?sh0:[]),fresh=hits.filter(o=>!seen.has(o.id));
  store.set("seenHits",hits.map(o=>o.id));
  if(!fresh.length||!WAS_USER)return; // Erstinstallation: zuerst Willkommen, kein Treffer-Fenster
  S.news=fresh.sort((a,b)=>offPct(b)-offPct(a));S.sheet="news";render()}
function renderNews(){
  const n=S.news||[];
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Neu im Angebot">
   <div class="sheet-h"><span class="newsico">${IC.bell}</span><h2>Von deiner Merkliste im Angebot</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <p style="margin:-6px 0 0;color:var(--muted)">${n.length===1?"Ein Artikel":n.length+" Artikel"} von deiner Merkliste ${n.length===1?"ist":"sind"} neu im Angebot:</p>
   <div class="rows">${n.slice(0,12).map(o=>{const inL=S.list.includes(o.id);return `<div class="drow"><div class="mini" style="--cc:${CC[o.c]||CC.sonstiges}">${imgTag(o)}</div>
     <div class="t">${esc(o.n)}<small>${esc(sname(o.s))}${o.b?" · "+esc(o.b):""} · ${validTxt(o)}</small></div>
     <div class="pr"><b>${eur(fin(o))}</b>${offPct(o)?`<span class="off" style="font-size:.8rem">−${offPct(o)} %</span>`:""}<div style="margin-top:4px"><button class="ibtn add" data-add="${esc(o.id)}" aria-pressed="${inL}" aria-label="${inL?"Vom Einkaufszettel nehmen":"Auf den Einkaufszettel"}">${inL?IC.check:IC.plus}</button></div></div></div>`}).join("")}</div>
   ${n.length>12?`<p style="margin:0;color:var(--muted)">… und ${n.length-12} weitere</p>`:""}
   <div class="factions"><button class="btn ghost" data-newsdone="watch">Alle Treffer</button><button class="btn" data-newsdone="ok">Alles klar</button></div>
  </div>`}

function weekPlan(){const by={};S.watch.forEach(w=>{const h=weekOffers().filter(o=>hitW(o,w)).sort((a,b)=>(unit(a)??fin(a))-(unit(b)??fin(b)))[0];if(h){(by[h.s]=by[h.s]||{items:[],save:0});if(!by[h.s].items.includes(h)){by[h.s].items.push(h);by[h.s].save+=ref(h)-fin(h)}}});
  return Object.entries(by).sort((a,b)=>b[1].items.length-a[1].items.length)}

function renderKracher(){
  const r=ranked(),k=r[0];if(!k)return"";
  const vd=verdict(k),st=steps(k),inL=S.list.includes(k.id);
  // Abwechslung (Kevin: zu viel Edeka mit App): höchstens 2 je Markt pro Abschnitt, Rest füllt nur auf, wenn sonst zu wenig da ist
  const pickDiv=(list,n,cap)=>{const c={},out=[];list.forEach(o=>{if(out.length<n&&(c[o.s]||0)<cap){c[o.s]=(c[o.s]||0)+1;out.push(o)}});
    list.forEach(o=>{if(out.length<n&&!out.includes(o))out.push(o)});return out};
  const top=S.useApp?pickDiv(r.filter(o=>o!==k&&((o.x||[]).length||o.ap||couponsFor(o).length)),5,2):[];
  const rest=pickDiv(r.filter(o=>o!==k&&!top.includes(o)),8-top.length,2);
  const lows=r.filter(o=>verdict(o).t==="low").slice(0,5),fakes=weekOffers().filter(o=>verdict(o).t==="fake").slice(0,5);
  const plan=weekPlan();
  const drow=o=>`<div class="drow" data-detail="${esc(o.id)}"><div class="mini" style="--cc:${CC[o.c]||CC.sonstiges}">${imgTag(o)}</div>
    <div class="t">${esc(o.n)}<small>${esc(sname(o.s))}${o.b?" · "+esc(o.b):""} · ${esc(o.d||"")}</small><div class="pills">${offPct(o)?`<span class="pill of">−${offPct(o)} %</span>`:""}${steps(o).filter(s=>!["base","of"].includes(s.t)).map(s=>`<span class="pill ${s.t==="cb"?"cb":""}">${esc(s.l)}</span>`).join("")}</div></div>
    <div class="pr"><b>${eur(fin(o))}</b>${ref(o)>fin(o)?`<s>${eur(ref(o))}</s>`:""}</div></div>`;
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Kracher">
   <div class="sheet-h"><span style="width:38px;height:38px;border-radius:11px;background:#E5332A;color:#FFE27A;display:grid;place-items:center;transform:rotate(-8deg)">${IC.flame}</span><h2>Kracher ${S.week?nextShort():"der Woche"}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <section class="hero">${thumb(k,true)}
    <div class="info">
     <div class="store" style="gap:9px">${sb(k.s,true)}${esc(sname(k.s))} · ${validTxt(k)}</div>
     <h3>${esc(k.n)}<small>${esc([k.b,k.d,unitTxt(k)].filter(Boolean).join(" · "))}</small></h3>
     <div style="display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap"><div class="tag xl">${tagHTML(fin(k))}</div>${ref(k)>fin(k)?`<div class="was" style="text-align:left"><s>${wasLbl(k)} ${eur(ref(k))}</s><b style="color:var(--save);font-size:1rem">Du sparst ${eur(ref(k)-fin(k))} (${offPct(k)} %)</b></div>`:""}</div>
     <div class="stack">${st.map((s,i)=>i===0?`<div><span>${esc(s.l)}</span><span>${eur(s.v)}</span></div>`:`<div class="neg"><span>− ${esc(s.l)}</span><span>${eur(s.v)}</span></div>`).join("")}<div class="res"><span>Du zahlst effektiv</span><span>${eur(fin(k))}</span></div></div>
     <div class="verdict ${vd.t}">${spark(k,90,24)}<span>${esc(vd.l)}</span></div>
     <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" data-add="${esc(k.id)}">${inL?IC.check+"Auf dem Zettel":IC.plus+"Auf den Einkaufszettel"}</button>${inL?qStep(k.id,true):""}<button class="btn ghost" data-fav="${esc(k.id)}">${IC.star}Merken</button><a class="btn wa" href="${waLink(`🔥 ${k.n}${k.b?" ("+k.b+")":""} bei ${sname(k.s)} für ${eur(fin(k))}${offPct(k)?` (−${offPct(k)} %)`:""}${validTxt(k)?", "+validTxt(k):""}\n\nGefunden mit SparRadar: ${APP_URL}`)}" target="_blank" rel="noopener">${WA_ICON}Teilen</a></div>
    </div></section>
   ${top.length?`<h3 class="sec-h">Beste Kombi-Deals</h3><p style="margin:-8px 0 0;color:var(--muted);font-size:.88rem">Angebot + App-Preis, Bonus-Guthaben und deine Coupons zusammengerechnet.</p><div class="rows">${top.map(drow).join("")}</div>`:""}
   <h3 class="sec-h">Weitere Top-Angebote</h3><div class="rows">${rest.map(drow).join("")}</div>
   ${noProof().length?`<p class="kr-note">ℹ️ ${noProof().map(sname).join(", ")}: im Prospekt stehen diesmal keine Vergleichspreise („statt“), daher kein belegbarer Kracher. Sobald es welche gibt, ist ${noProof().length>1?"jeder Markt":sname(noProof()[0])} automatisch dabei.</p>`:""}
   <h3 class="sec-h">Dein Wochenplan</h3>
   ${plan.length?`<p style="margin:-8px 0 0;color:var(--muted);font-size:.88rem">Für deine Merkliste lohnen sich ${plan.length} ${plan.length===1?"Markt":"Märkte"}:</p>
    <div class="plan">${plan.map(([s,g])=>`<div class="stop"><h4>${sb(s)}${esc(sname(s))}${g.save>0.005?`<em>spart ${eur(g.save)}</em>`:""}</h4><ul>${g.items.map(o=>`<li>${esc(o.n)}: ${eur(fin(o))}${unitTxt(o)?" ("+unitTxt(o)+")":""}</li>`).join("")}</ul></div>`).join("")}</div>
    <div><button class="btn" id="planToList">${IC.plus}Wochenplan auf den Einkaufszettel</button></div>`
    :'<div class="empty"><b>Noch kein Plan</b>Gerade ist nichts von deiner Merkliste im Angebot.</div>'}
   <div class="two">
    <section class="panel"><h3 style="color:var(--save)">Echte Tiefpreise</h3>${lows.length?`<div class="rows">${lows.map(o=>`<div style="display:flex;justify-content:space-between;gap:10px;font-size:.9rem"><span>${esc(o.n)} <span style="color:var(--muted)">${esc(sname(o.s))}</span></span><b style="font-variant-numeric:tabular-nums">${eur(fin(o))}</b></div>`).join("")}</div>`:"<p>Der Preisverlauf baut sich noch auf. Nach ein paar Tagen erscheinen hier die echten Tiefpreise.</p>"}</section>
    <section class="panel"><h3 style="color:var(--alert)">Vorsicht, Fake-Rabatt</h3>${fakes.length?`<div class="rows">${fakes.map(o=>`<div style="font-size:.9rem"><b>${esc(o.n)}</b> <span style="color:var(--muted)">${esc(sname(o.s))}</span><br><span style="color:var(--muted)">${esc(verdict(o).l)}</span></div>`).join("")}</div>`:"<p>Keine verdächtigen Rabatte gefunden.</p>"}</section>
   </div></div>`}

function renderWatch(){
  const wh=watchHits(null);
  if(S.wsel!=null&&!wh[S.wsel])S.wsel=null;
  // Bilder der gemerkten Artikel: brauchen Bilder-Liste UND Artikelstamm (catalog.json) – beide erst hier laden
  if(S.watch.length&&(!SIMG||!CATALOG_N)){const again=()=>{if(S.tab==="watch"&&SIMG&&CATALOG_N)render()};if(!SIMG)loadSugImgs(again);if(!CATALOG_N)loadCatalog(again)}
  const sel=S.wsel!=null?[wh[S.wsel]]:wh;
  const hits=[...new Map(sel.flatMap(x=>x.hits).map(o=>[o.id,o])).values()].sort((a,b)=>offPct(b)-offPct(a));
  return `<section class="panel"><h3>Was soll ich für dich beobachten?</h3>
    <p>Begriff oder Marke eingeben. Mit Wunschpreis wird daraus ein <b>Vorrats-Alarm</b>: Treffer zählen nur, wenn der Grundpreis darunter liegt. Die Zahl am Tab „Merkliste“ zeigt dir beim Öffnen, wie viele Treffer gerade im Angebot sind.</p>
    <form class="addrow" id="kwForm"><input id="kwIn" placeholder="z. B. Mozzarella, Felix, Cola" autocomplete="off"><input id="kwMax" class="sm" inputmode="decimal" placeholder="max. €/kg (optional)" autocomplete="off"><button class="btn" type="submit">${IC.plus}Merken</button></form>
    <div id="kwSugg"></div>
    <div class="wlist">${S.watch.map((w,i)=>{const n=wh[i].hits.length,im=sugImg(w.k)||(wh[i].hits.find(o=>o.img)||{}).img||simImg(w.k)||"",on=S.wsel===i;
      return `<div class="witem${n?" hit":""}${on?" on":""}"><button class="wmain" data-wsel="${i}" aria-pressed="${on}" title="${esc(w.k)}">${safeUrl(im)?`<img src="${esc(sharp(im))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility='hidden'">`:`<span class="wph">${IC.bell}</span>`}<span class="wtx"><b>${esc(w.k)}</b><small>${n?`${n} ${n===1?"Treffer":"Treffer"} im Angebot`:"gerade nicht im Angebot"}${w.max?` · bis ${eur(w.max)}/kg`:""}</small></span></button><button class="wdel" data-delkw="${i}" aria-label="${esc(w.k)} entfernen">${IC.x}</button></div>`}).join("")||'<span style="color:var(--muted)">Noch nichts gemerkt.</span>'}</div>
   </section>
   <div class="meta"><h2>${S.wsel!=null?`Treffer für „${esc(S.watch[S.wsel].k)}“`:"Deine Treffer"}</h2><span>${S.wsel!=null?`<button class="linkbtn" data-wsel="${S.wsel}">Alle zeigen</button> · `:""}${hits.length} Angebote</span></div>
   ${hits.length?`<div class="grid">${hits.slice(0,60).map(o=>card(o,new Set())).join("")}</div>`:'<div class="empty"><b>Keine Treffer</b>${S.wsel!=null?"Dieser Artikel ist gerade nicht im Angebot. SparRadar schaut bei jedem Abruf nach.":"Gerade ist nichts von deiner Merkliste reduziert oder unter deinem Wunschpreis."}</div>'}`}

// Ersparnis-Zähler: was auf dem Zettel abgehakt wird, zählt als gekauft
const savedOn=()=>S.saved.filter(x=>!x.off);
function savedHTML(){const sv=savedOn();if(!sv.length)return "";
  const sum=a=>a.reduce((t,x)=>t+x.v,0),mon=TODAY.slice(0,7),wk=new Date(Date.now()-6*864e5).toISOString().slice(0,10);
  const m=sum(sv.filter(x=>x.d.startsWith(mon))),w=sum(sv.filter(x=>x.d>=wk)),all=sum(sv);
  return `<button class="savedc" data-savedopen="1" title="Antippen zum Ansehen oder Löschen"><div><span>Diese Woche</span><b>${eur(w)}</b></div><div><span>Diesen Monat</span><b>${eur(m)}</b></div><div><span>Insgesamt</span><b>${eur(all)}</b></div><p>Gespart mit SparRadar · antippen zum Ansehen oder Löschen</p></button>`}
// Fenster „Gespart“: jeden Eintrag einzeln löschen (z. B. Test-Abhaken) oder alles auf 0
function renderSaved(){const sv=savedOn().slice().sort((a,b)=>b.d.localeCompare(a.d)),days=[...new Set(sv.map(x=>x.d))];
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Gespart">
   <div class="sheet-h"><span class="newsico">💰</span><h2>Gespart: ${eur(sv.reduce((t,x)=>t+x.v,0))}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <p style="margin:-6px 0 4px;color:var(--muted)">Stimmt etwas nicht (z. B. nur zum Testen abgehakt)? Mit ✕ rausnehmen.</p>
   ${sv.length?days.map(d=>`<h4 class="svd">${fmtDate(d)}</h4>${sv.map((x,i)=>[x,S.saved.indexOf(x)]).filter(([x])=>x.d===d).map(([x,i])=>`<div class="svrow"><span>${sb(x.s)}${esc(x.n)}</span><b class="sv">${eur(x.v)}</b><button class="ibtn" data-saveddel="${i}" aria-label="${esc(x.n)} löschen">${IC.x}</button></div>`).join("")}`).join(""):`<p>Nichts mehr drin.</p>`}
   ${sv.length?`<div class="factions" style="grid-template-columns:1fr"><button class="btn ghost" data-savedreset="1">Alles auf 0 setzen</button></div>`:""}
  </div>`}
// Gleicher Artikel woanders günstiger (gleiche Menge)? -> Tausch vorschlagen
function swapTips(items){
  const t=items.filter(o=>!S.checked.includes(o.id)).map(o=>{const c=sameElsewhere(o,weekOffers()).filter(r=>Math.abs(r.f-1)<.05&&!S.list.includes(r.x.id)).sort((a,b)=>fin(a.x)-fin(b.x))[0];
    return c&&fin(c.x)<fin(o)-.04?{o,x:c.x}:null}).filter(Boolean);
  if(!t.length)return "";
  return `<section class="panel swaps"><h3>Woanders günstiger</h3><p>Derselbe Artikel in gleicher Menge kostet bei einem anderen Markt weniger.</p>
   <div class="rows">${t.map(({o,x})=>`<div class="swap"><span><b>${esc(o.n)}</b><small>${esc(sname(o.s))} ${eur(fin(o))} → ${esc(sname(x.s))} ${eur(fin(x))} · ${eur(fin(o)-fin(x))} weniger</small></span><button class="btn ghost sm" data-swap="${esc(o.id)}|${esc(x.id)}">Tauschen</button></div>`).join("")}</div></section>`}
// Zettel-Einträge, deren Angebot abgelaufen ist: nicht still verschwinden lassen, sondern zeigen + neues Angebot vorschlagen
function goneHTML(){const g=S.list.filter(id=>!byId(id)&&OLD.has(id)).map(id=>OLD.get(id));if(!g.length)return "";
  const wo=weekOffers().filter(x=>!S.list.includes(x.id));
  const alt=o=>{const k=tokKey(o),nn=norm(o.n),same=wo.filter(x=>tokKey(x)===k||(x.s===o.s&&norm(x.n)===nn)).sort((a,b)=>fin(a)-fin(b));
    if(same.length)return same.find(x=>x.s===o.s)||same[0];const c=sameElsewhere(o,wo).sort((a,b)=>fin(a.x)-fin(b.x))[0];return c?c.x:null};
  return `<section class="panel swaps gone"><h3>Abgelaufen</h3><p>Diese Angebote gelten nicht mehr.${g.some(alt)?" Wo es denselben Artikel wieder im Angebot gibt, kannst du ihn tauschen.":""}</p>
   <div class="rows">${g.map(o=>{const x=alt(o);return `<div class="swap"><span><b>${esc(o.n)}</b><small>${esc(sname(o.s))} ${eur(fin(o))} · abgelaufen am ${fmtDate(o.to)}${x?` → jetzt ${esc(sname(x.s))} ${eur(fin(x))}`:" · gerade nirgends im Angebot"}</small></span>${x?`<button class="btn ghost sm" data-swap="${esc(o.id)}|${esc(x.id)}">Tauschen</button>`:""}<button class="ibtn" data-add="${esc(o.id)}" aria-label="${esc(o.n)} entfernen">${IC.x}</button></div>`}).join("")}</div></section>`}
// ---------- Einkaufszettel = Einkaufswagen (Kevins Wunsch) ----------
// Antippen = liegt im Wagen. Am Handy schließt der letzte Artikel den Einkauf ab: Zettel leer, Einkauf mit Bericht in „Meine Einkäufe“.
const TOUCH=()=>matchMedia("(hover:none) and (pointer:coarse)").matches;
const qty=id=>Math.max(1,S.qty[id]||1);
// Menge direkt beim Hinzufügen: auf Karte und im Detail erscheint „− 1 +“, sobald der Artikel auf dem Zettel ist
function qStep(id,big){return `<span class="qstep cq${big?" big":""}" title="Menge auf dem Einkaufszettel"><button data-qm="${esc(id)}" aria-label="weniger">−</button><b>${qty(id)}<small>×</small></b><button data-qp="${esc(id)}" aria-label="mehr">+</button></span>`}
const r2=v=>Math.round(v*100)/100;
const lineP=o=>r2(fin(o)*qty(o.id)),lineR=o=>r2(Math.max(ref(o),fin(o))*qty(o.id)),extraP=x=>x.p?r2(x.p*qty(x.id)):0;
// „3x Joghurt“, „Brot 1,99“, „Kaffee 4,49 €“ -> Menge, Name, Preis
function parseExtra(v){let q=1,n=v.trim(),p=0,m=n.match(/^(\d{1,2})\s*[x×*]\s*(.+)$/i)||n.match(/^(\d{1,2})\s+(.+)$/);
  if(m&&+m[1]>0&&+m[1]<50){q=+m[1];n=m[2]}
  m=n.match(/^(.*?)\s+(\d{1,3}[,.]\d{1,2})\s*€?$/)||n.match(/^(.*?)\s+(\d{1,3})\s*€$/);if(m){n=m[1];p=parseFloat(m[2].replace(",","."))}
  return {n:n.trim()||v.trim(),p,q}}
let WL=null;  // Bildschirm bleibt beim Einkaufen an
async function wakeOn(){try{if(!WL&&navigator.wakeLock&&TOUCH()&&!document.hidden)WL=await navigator.wakeLock.request("screen");WL?.addEventListener?.("release",()=>{WL=null})}catch(e){WL=null}}
function wakeOff(){try{WL?.release()}catch(e){}WL=null}
function finishTrip(ids,auto){
  const items=S.list.filter(id=>ids.includes(id)).map(byId).filter(Boolean),ex=S.extra.filter(x=>ids.includes(x.id));
  if(!items.length&&!ex.length)return;
  const t={id:"t"+Date.now(),d:TODAY,at:new Date().toISOString(),
    items:items.map(o=>({id:o.id,n:o.n,b:o.b||"",s:o.s,q:qty(o.id),p:lineP(o),r:lineR(o)})),
    extra:ex.map(x=>({id:x.id,n:x.n,q:qty(x.id),p:extraP(x)}))};
  t.paid=r2(t.items.reduce((a,x)=>a+x.p,0)+t.extra.reduce((a,x)=>a+x.p,0));t.saved=r2(t.items.reduce((a,x)=>a+Math.max(0,x.r-x.p),0));
  S.trips.unshift(t);S.trips=S.trips.slice(0,400);
  S.list=S.list.filter(id=>!ids.includes(id));S.extra=S.extra.filter(x=>!ids.includes(x.id));S.checked=S.checked.filter(id=>!ids.includes(id));
  ids.forEach(id=>delete S.qty[id]);
  if(!S.list.length&&!S.extra.length)wakeOff();
  save();render();tripPop(t,auto)}
// Einkauf zurück auf den Zettel holen (zum Nachlesen oder weil noch etwas fehlt) – alles bleibt abgehakt
function restoreTrip(id){const t=S.trips.find(x=>x.id===id);if(!t)return;
  t.items.forEach(it=>{let k=it.id;if(!byId(k)&&!OLD.has(k)){k="x-r"+it.id;if(!S.extra.some(x=>x.id===k))S.extra.push({id:k,n:it.n,p:it.q?r2(it.p/it.q):it.p})}else if(!S.list.includes(k))S.list.push(k);
    S.qty[k]=it.q||1;if(!S.checked.includes(k))S.checked.push(k)});
  t.extra.forEach(x=>{if(!S.extra.some(e=>e.id===x.id))S.extra.push({id:x.id,n:x.n,p:x.q&&x.p?r2(x.p/x.q):0});S.qty[x.id]=x.q||1;if(!S.checked.includes(x.id))S.checked.push(x.id)});
  S.trips=S.trips.filter(x=>x.id!==id);S.tab="list";S.sheet=null;hideTripPop();save();render();scrollTo({top:0});
  toast("Einkauf ist wieder auf dem Zettel")}
// Nach dem Einkauf die Kunden-App des Markts öffnen (Kundenkarte/Code an der Kasse zeigen). Nur Android, nur geprüfte Paketnamen.
const MKT_APP={lidl:{n:"Lidl Plus",pkg:"com.lidl.eci.lidlplus"},rewe:{n:"REWE",pkg:"de.rewe.app.mobile"},edeka:{n:"EDEKA",pkg:"de.edeka.genuss"},
  aldi:{n:"ALDI SÜD",pkg:"de.apptiv.business.android.aldi_de"},netto:{n:"Netto",pkg:"com.valuephone.vpnetto"},dm:{n:"Mein dm",pkg:"de.dm.meindm.android"}}; // Aldi/Netto/dm: Kennungen aus Kevins Play-Store-Links
const ANDROID=/Android/i.test(navigator.userAgent),IN_APK=/SparRadarAndroid|; wv\)/.test(navigator.userAgent);
function tripStore(t){const c={};t.items.forEach(x=>c[x.s]=(c[x.s]||0)+1);const s=Object.keys(c).sort((a,b)=>c[b]-c[a])[0];return s&&MKT_APP[s]?s:null}
function openMktApp(s){const a=MKT_APP[s];if(!a)return;const play=`https://play.google.com/store/apps/details?id=${a.pkg}`;
  // Chrome/Web-App: intent-Link öffnet die App, fehlt sie, kommt der Play Store. Alte APK-Hülle kennt nur normale Links -> Play Store mit „Öffnen“.
  location.href=IN_APK?play:`intent://#Intent;package=${a.pkg};action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;S.browser_fallback_url=${encodeURIComponent(play)};end`}
let tpT;
function tripPop(t,auto){
  let el=document.getElementById("tripPop");
  if(!el){el=document.createElement("div");el.id="tripPop";el.className="trippop";el.setAttribute("role","status");document.body.appendChild(el)}
  const n=t.items.length+t.extra.length,ms=ANDROID?tripStore(t):null;
  el.innerHTML=`<div class="tp-h"><span class="tp-ok">✓</span><b>Einkauf abgeschlossen</b><button class="ibtn" data-tpclose="1" aria-label="Schließen">${IC.x}</button></div>
   <div class="tp-n">${n} Artikel · bezahlt <b>${eur(t.paid)}</b>${t.saved>0?` · gespart <b class="sv">${eur(t.saved)}</b>`:""}</div>
   <div class="tp-a"><button class="btn ghost sm" data-triprestore="${t.id}">Zurückholen</button><button class="btn sm" data-tripopen="${t.id}">Bericht ansehen</button></div>
   ${tripCb(t).map(c=>`<a class="btn ghost sm tp-cb" href="${esc(c.url)}" target="_blank" rel="noopener nofollow">💸 Geld zurück: ${esc(c.n||c.k)} – Bon hochladen ↗</a>`).join("")}
   ${ms?`<button class="btn tp-app" data-mktapp="${ms}">📱 ${auto&&store.get("openMktApp",true)?`${esc(MKT_APP[ms].n)} öffnet sich – Kundenkarte an der Kasse zeigen`:`${esc(MKT_APP[ms].n)}-App öffnen`}</button>`:""}`;
  el.hidden=false;clearTimeout(tpT);tpT=setTimeout(hideTripPop,ms||tripCb(t).length?15000:auto?9000:6000);
  if(ms&&auto&&store.get("openMktApp",true))setTimeout(()=>openMktApp(ms),350);
  try{if(TOUCH())navigator.vibrate?.([30,60,30])}catch(e){}}
// Geld-zurück-Coupons, die zu einem Artikel des Einkaufs passen -> Link „Bon hochladen“
function tripCb(t){return S.coupons.filter(c=>c.cb&&c.url&&cpActive(c)&&t.items.some(x=>(c.s==="all"||c.s===x.s)&&c.k.split(/\s+/).every(w=>norm((x.b+" "+x.n)).includes(norm(w))))).slice(0,3)}
function hideTripPop(){const el=document.getElementById("tripPop");if(el)el.hidden=true}
const monKey=d=>d.slice(0,7),monName=k=>new Date(k+"-15").toLocaleDateString("de-DE",{month:"long",year:"numeric"});
function storeSplit(ts){const m={};ts.forEach(t=>t.items.forEach(x=>m[x.s]=(m[x.s]||0)+x.p));const ex=ts.reduce((a,t)=>a+t.extra.reduce((b,x)=>b+x.p,0),0);if(ex>0)m._=ex;return Object.entries(m).sort((a,b)=>b[1]-a[1])}
// Monatsbericht + Liste aller Einkäufe
function tripsHTML(){if(!S.trips.length)return "";
  const mk=monKey(TODAY),cur=S.trips.filter(t=>monKey(t.d)===mk);
  const sum=(ts,f)=>r2(ts.reduce((a,t)=>a+t[f],0));
  const months=[...new Set(S.trips.map(t=>monKey(t.d)))].sort().reverse().slice(0,6);
  const sp=storeSplit(cur),maxS=Math.max(1,...sp.map(x=>x[1]));
  const paid=sum(cur,"paid"),sav=sum(cur,"saved");
  return `<section class="panel trips"><h3>Meine Einkäufe</h3>
   <div class="mrep"><div class="mrep-h">${esc(monName(mk))}</div>
    <div class="mrep-g"><div><span>Ausgegeben</span><b>${eur(paid)}</b></div><div><span>Gespart</span><b class="sv">${eur(sav)}</b></div><div><span>Einkäufe</span><b>${cur.length}</b></div><div><span>Ø pro Einkauf</span><b>${cur.length?eur(paid/cur.length):"–"}</b></div></div>
    ${paid+sav>0&&sav>0?`<p class="mrep-q">Ohne Angebote hättest du <b>${eur(paid+sav)}</b> bezahlt – du hast <b>${Math.round(sav/(paid+sav)*100)} %</b> gespart.</p>`:""}
    ${sp.length?`<div class="mbars">${sp.map(([k,v])=>`<div class="mbar"><span>${k==="_"?"Eigene Einträge":esc(sname(k))}</span><i style="--w:${Math.max(4,Math.round(v/maxS*100))}%;--c:${k==="_"?"#6B7280":(STORES[k]||{}).c||"#2B3034"}"></i><b>${eur(v)}</b></div>`).join("")}</div>`:""}
   </div>
   ${months.length>1?`<div class="mhist">${months.map(k=>{const ts=S.trips.filter(t=>monKey(t.d)===k);return `<div><span>${esc(monName(k))}</span><span>${ts.length} ×</span><span>${eur(sum(ts,"paid"))}</span><span class="sv">−${eur(sum(ts,"saved")).replace("−","")}</span></div>`}).join("")}</div>`:""}
   <div class="tlist">${S.trips.slice(0,S.tripLimit||10).map(t=>{const st=[...new Set(t.items.map(x=>x.s))];
     return `<button class="trow" data-tripopen="${t.id}"><span class="td">${fmtDate(t.d)}<small>${new Date(t.at).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})} Uhr</small></span><span class="tm">${st.map(x=>sb(x)).join("")}${t.extra.length?`<em>+${t.extra.length}</em>`:""}<small>${t.items.length+t.extra.length} Artikel</small></span><span class="tp">${eur(t.paid)}${t.saved>0?`<small class="sv">−${eur(t.saved).replace("−","")}</small>`:""}</span></button>`}).join("")}</div>
   ${S.trips.length>(S.tripLimit||10)?`<button class="btn ghost more" data-tripmore="1">Ältere Einkäufe zeigen</button>`:""}
  </section>`}
function renderTrip(){const t=S.trips.find(x=>x.id===S.tripId);if(!t)return renderKracher();
  const g={};t.items.forEach(x=>(g[x.s]=g[x.s]||[]).push(x));
  const row=x=>`<div class="rline"><span>${x.q>1?x.q+"× ":""}${esc(x.n)}</span><span>${x.p?eur(x.p):""}${x.r>x.p+.004?`<small class="sv"> −${eur(x.r-x.p).replace("−","")}</small>`:""}</span></div>`;
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Einkauf vom ${fmtDate(t.d)}">
   <div class="sheet-h"><span class="newsico">🧾</span><h2>Einkauf vom ${fmtDate(t.d)}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <div class="mrep-g"><div><span>Bezahlt</span><b>${eur(t.paid)}</b></div><div><span>Gespart</span><b class="sv">${eur(t.saved)}</b></div><div><span>Artikel</span><b>${t.items.length+t.extra.length}</b></div></div>
   <div class="receipt">${Object.entries(g).map(([s,xs])=>`<div class="rgroup"><div class="rs">${sb(s)}${esc(sname(s))}</div>${xs.map(row).join("")}</div>`).join("")}
    ${t.extra.length?`<div class="rgroup"><div class="rs">${IC.bag}Eigene Einträge</div>${t.extra.map(row).join("")}</div>`:""}
    <div class="rtot"><div class="big"><span>BEZAHLT</span><span>${eur(t.paid)}</span></div>${t.saved>0?`<div class="sv"><span>GESPART</span><span>${eur(t.saved)}</span></div>`:""}</div></div>
   <p class="fhint">Preise laut Angebot (mit eingerechneten Apps &amp; Coupons, wenn eingeschaltet). Eigene Einträge zählen nur, wenn du einen Preis dazugeschrieben hast, z. B. „Brot 1,99“.</p>
   <div class="factions"><button class="btn ghost" data-tripdel="${t.id}">Löschen</button><button class="btn" data-triprestore="${t.id}">Zurück auf den Zettel</button></div>
  </div>`}
// Häufig gekauft: aus dem Verlauf mit einem Tipp wieder auf den Zettel (wenn möglich als aktuelles Angebot)
function freqHTML(){if(!S.trips.length)return "";
  const have=new Set([...S.list.map(byId).filter(Boolean).map(o=>norm(o.n)),...S.extra.map(x=>norm(x.n))]),c={};
  S.trips.slice(0,60).forEach(t=>[...t.items,...t.extra].forEach(x=>{const k=norm(x.n);if(!k||have.has(k))return;(c[k]=c[k]||{n:x.n,c:0}).c++}));
  const top=Object.values(c).sort((a,b)=>b.c-a.c||a.n.length-b.n.length).slice(0,12);
  if(!top.length)return "";
  return `<div class="freq"><span>Wieder kaufen:</span>${top.map(x=>`<button class="chip plain" data-readd="${esc(x.n)}">${IC.plus}${esc(x.n.length>28?x.n.slice(0,27)+"…":x.n)}</button>`).join("")}</div>`}
function readd(n){const k=norm(n),wo=weekOffers().filter(o=>norm(o.n)===k).sort((a,b)=>fin(a)-fin(b));
  if(wo.length&&!S.list.includes(wo[0].id)){S.list.push(wo[0].id);toast(`${n}: im Angebot bei ${sname(wo[0].s)} für ${eur(fin(wo[0]))}`)}
  else{S.extra.push({id:"x-"+Date.now(),n});toast(`${n} auf den Zettel gesetzt`)}save();render()}
function cartHTML(items,extra){const all=[...items.map(o=>o.id),...extra.map(x=>x.id)],inCart=all.filter(id=>S.checked.includes(id)).length;
  const tot=r2(items.reduce((a,o)=>a+lineP(o),0)+extra.reduce((a,x)=>a+extraP(x),0));
  const cart=r2(items.filter(o=>S.checked.includes(o.id)).reduce((a,o)=>a+lineP(o),0)+extra.filter(x=>S.checked.includes(x.id)).reduce((a,x)=>a+extraP(x),0));
  const pct=all.length?Math.round(inCart/all.length*100):0,b=S.budget,left=b?r2(b-tot):0;
  return `<div class="cart${inCart?" on":""}"><div class="cart-h"><span class="cart-i">🛒</span><b>${inCart?`Im Wagen: ${inCart} von ${all.length}`:`${all.length} Artikel auf dem Zettel`}</b><span class="cart-s">${inCart?`${eur(cart)} von ${eur(tot)}`:eur(tot)}</span></div>
   <div class="cart-bar"><i style="width:${pct}%"></i></div>
   <div class="cart-f">${b?`<span class="${left<0?"over":""}">Budget ${eur(b)} · ${left<0?`${eur(-left)} drüber`:`noch ${eur(left)} frei`}</span>`:`<span>${TOUCH()?"Im Laden: Artikel antippen, wenn er im Wagen liegt.":"Am Handy beim Einkaufen abhaken – der letzte Artikel schließt den Einkauf ab."}</span>`}<button class="linkbtn" data-budget="1">${b?"Budget ändern":"Budget festlegen"}</button></div>
   ${TOUCH()&&inCart&&inCart<all.length?`<button class="btn ghost sm cart-done" data-tripfinish="1">Einkauf jetzt abschließen (Rest bleibt auf dem Zettel)</button>`:""}</div>`}
function renderList(){
  const items=S.list.map(byId).filter(Boolean),extra=S.extra;
  const addRow=`<form class="addrow" id="extraForm"><input id="extraIn" placeholder="Eigener Eintrag, z. B. Brot 1,99 oder 3x Joghurt" autocomplete="off"><button class="btn" type="submit">${IC.plus}Dazu</button></form>`;
  if(!items.length&&!extra.length)return `${addRow}${freqHTML()}${savedHTML()}${goneHTML()}${goneHTML()?"":`<div class="empty"><b>Dein Einkaufszettel ist leer</b>Tippe bei einem Angebot auf Plus, übernimm im Kracher-Fenster deinen Wochenplan oder schreib oben selbst etwas dazu. SparRadar sortiert alles nach Markt.</div>`}${tripsHTML()}`;
  const groups={};items.forEach(o=>(groups[o.s]=groups[o.s]||[]).push(o));
  const done=id=>S.checked.includes(id);
  const sortDone=a=>[...a.filter(x=>!done(x.id)),...a.filter(x=>done(x.id))];  // was im Wagen liegt, rutscht nach unten
  const sum=items.reduce((a,o)=>a+lineP(o),0)+extra.reduce((a,x)=>a+extraP(x),0),reg=items.reduce((a,o)=>a+lineR(o),0)+extra.reduce((a,x)=>a+extraP(x),0);
  const rest=items.filter(o=>!done(o.id)).reduce((a,o)=>a+lineP(o),0)+extra.filter(x=>!done(x.id)).reduce((a,x)=>a+extraP(x),0);
  const todo=[...new Set(items.flatMap(comboLabels))];
  // 🎟️ je Artikel: im Laden Coupon mit einem Tipp nachtragen (öffnet den Artikel mit den Coupon-Knöpfen)
  const cpBtn=id=>{if(id.startsWith("x-")||done(id))return "";const o=byId(id);if(!o||!o.p)return "";const c=couponsFor(o)[0];
    return `<button class="cpbtn${c?" on":""}" data-cpqlist="${esc(id)}" aria-label="${c?"Coupon "+esc(cpValueTxt(c)):"Coupon eintragen"}" title="${c?"Coupon eingerechnet":"Ich habe einen Coupon dafür"}">🎟️${c?`<small>${esc(cpValueTxt(c))}</small>`:""}</button>`};
  const stepper=id=>done(id)?"":`<span class="qstep"><button data-qm="${esc(id)}" aria-label="weniger">−</button><b>${qty(id)}</b><button data-qp="${esc(id)}" aria-label="mehr">+</button></span>`;
  const line=(id,name,price,label)=>`<div class="rline${done(id)?" done":""}"><button class="rcheck" data-check="${esc(id)}" aria-pressed="${done(id)}" aria-label="${esc(name)} ${done(id)?"aus dem Wagen nehmen":"in den Wagen"}"><i></i><span>${qty(id)>1?`<em class="qx">${qty(id)}×</em> `:""}${esc(name)}${label||""}</span></button>${cpBtn(id)}${stepper(id)}<span>${price}</span><button data-${id.startsWith("x-")?"delextra":"add"}="${esc(id)}" aria-label="${esc(name)} entfernen">${IC.x}</button></div>`;
  const nDone=[...items.map(o=>o.id),...extra.map(x=>x.id)].filter(done).length;
  const grpTot=os=>{const t=os.reduce((a,o)=>a+lineP(o),0),r=os.reduce((a,o)=>a+lineR(o),0);return `<div class="rsub"><span>Summe ${os.length} Artikel${r>t+.004?` · gespart ${eur(r-t)}`:""}</span><span>${eur(t)}</span></div>`};
  return `${addRow}${freqHTML()}${cartHTML(items,extra)}${savedHTML()}${goneHTML()}${swapTips(items)}<div class="receipt"><h3>EINKAUFSZETTEL</h3><div class="sub">${Object.keys(groups).length+(extra.length?1:0)} ${Object.keys(groups).length+(extra.length?1:0)===1?"Abschnitt":"Abschnitte"} · ${items.length+extra.length} Artikel${nDone?` · ${nDone} im Wagen`:""}</div>
   ${Object.entries(groups).map(([s,os])=>`<div class="rgroup"><div class="rs">${sb(s)}${esc(sname(s))}${ANDROID&&MKT_APP[s]?`<button class="mktbtn" data-mktapp="${s}" title="${esc(MKT_APP[s].n)}-App öffnen, z. B. für deinen Code an der Kasse">📱 ${esc(MKT_APP[s].n)}</button>`:""}</div>
     ${sortDone(os).map(o=>line(o.id,o.n,eur(lineP(o)),comboLabels(o).length?" *":"")).join("")}${Object.keys(groups).length>1?grpTot(os):""}</div>`).join("")}
   ${extra.length?`<div class="rgroup"><div class="rs">${IC.bag}Sonstiges</div>${sortDone(extra).map(x=>line(x.id,x.n,x.p?eur(extraP(x)):"")).join("")}</div>`:""}
   <div class="rtot"><div class="big"><span>SUMME</span><span>${eur(sum)}</span></div>${nDone&&rest<sum-.004?`<div><span>Noch offen</span><span>${eur(rest)}</span></div>`:""}${reg>sum+.004?`<div><span>Normalpreis</span><span>${eur(reg)}</span></div><div class="sv"><span>GESPART</span><span>${eur(reg-sum)}</span></div>`:""}</div>
   ${todo.length?`<div style="margin-top:12px;font-size:.78rem;color:var(--muted)">* Vor dem Einkauf in der App aktivieren:<br>${todo.map(esc).join(" · ")}</div>`:""}</div>
   <div class="ractions"><a class="btn wa" href="${waLink(listText())}" target="_blank" rel="noopener">${WA_ICON}Per WhatsApp schicken</a><button class="btn ghost" id="copyList">Als Text kopieren</button>${nDone?'<button class="btn ghost" id="clearDone">Erledigte entfernen</button>':""}<button class="btn ghost" id="clearList">Zettel leeren</button></div>
   ${tripsHTML()}`}

// ---------- Coupon mit einem Tipp (direkt am Angebot) ----------
// Kevins Wunsch: so einfach, dass es jeder schafft. Markt, Artikel und Gültigkeit kommen vom Angebot, man wählt nur den Wert.
const CPQ=[["euro",.5],["euro",1],["euro",2],["pct",10],["pct",20],["pct",30]];
function cpQuick(o){if(!o.p)return "";
  const mine=S.coupons.map((c,i)=>({c,i})).filter(x=>cpActive(x.c)&&couponsFor(o).includes(x.c));
  if(mine.length)return `<div class="cpq has"><div class="cpq-h">🎟️ Dein Coupon ist eingerechnet</div>${mine.map(({c,i})=>`<div class="cpq-row"><b>${esc(cpValueTxt(c))}</b><span>${esc(c.k)} · ${esc(c.prog)}${c.to?" · bis "+fmtDate(c.to):""}</span><button class="btn ghost sm" data-delcp="${i}">Entfernen</button></div>`).join("")}</div>`;
  if(S.cpq!==o.id)return `<button class="btn cpq-open" data-cpq="${esc(o.id)}">🎟️ Ich habe einen Coupon dafür</button>`;
  return `<div class="cpq"><div class="cpq-h">🎟️ Wie viel bringt dein Coupon?</div><p>Einfach antippen – SparRadar rechnet ihn sofort ein (gilt bei ${esc(sname(o.s))}${o.to?" bis "+fmtDate(o.to):""}).</p>
    <div class="cpq-grid">${CPQ.map(([t,v])=>`<button class="cpq-b" data-cpqset="${esc(o.id)}|${t}|${v}">${t==="euro"?"−"+eur(v):`−${v} %`}</button>`).join("")}</div>
    <form class="cpq-own" id="cpqForm" data-id="${esc(o.id)}"><input id="cpqVal" inputmode="decimal" placeholder="anderer Wert, z. B. 1,50" autocomplete="off"><select id="cpqType"><option value="euro">€ weniger</option><option value="pct">% weniger</option><option value="preis">€ Endpreis</option></select><button class="btn" type="submit">OK</button></form>
    <button class="linkbtn" data-cpq="">Abbrechen</button></div>`}
function cpqSave(id,t,v){const o=byId(id);if(!o||!v)return;
  if(t==="pct"&&v>=100){toast("Ein Rabatt muss unter 100 % liegen.");return}
  if(t==="preis"&&v>=o.p){toast("Der Coupon-Preis muss unter dem Angebotspreis liegen.");return}
  const k=(o.b&&!norm(o.n).includes(norm(o.b))?o.b+" ":"")+o.n;
  S.coupons.push({s:o.s,prog:defaultProg(o.s),k:k.replace(/\s+/g," ").trim(),t,v,to:o.to||null});S.cpq=null;save();
  toast(S.useApp?`Coupon gespeichert – du zahlst jetzt ${eur(fin(o))}`:"Coupon gespeichert. „Apps & Coupons einrechnen“ ist ausgeschaltet – in den Einstellungen einschalten.");render()}

// ---------- Coupon-Finder (Kevins Wunsch 01.11.) ----------
// Zeigt NUR Vorteile, die nicht schon in den Angeboten stehen: Geld-zurück-Aktionen der Hersteller („Gratis testen“).
// Daten: docs/data/cashback.json (täglicher Abruf einer öffentlichen Übersicht, nur Fakten + Link zur Hersteller-Aktion).
// App-Preise der Märkte stehen schon bei den Angeboten (📱-Abzeichen) und kommen hier bewusst nicht vor.
let CASHBACK=null;
function loadCashback(){if(CASHBACK)return Promise.resolve(CASHBACK);
  return fetch("data/cashback.json?"+(META.generated||Date.now())).then(r=>r.ok?r.json():{items:[]}).catch(()=>({items:[]})).then(j=>(CASHBACK=j))}
const CB_FILL=/^(gratis|testen|probieren|produkt|produkte|und|oder|mit|der|die|das|von|für|neu|aktion|sorten?)$/i;
const cbWords=a=>(a.n||"").split(/[\s\-–\/&+]+/).map(w=>w.replace(/[^\wäöüßÄÖÜ]/g,"")).filter(w=>w.length>2&&!CB_FILL.test(w));
const cbHit=(o,w)=>new RegExp("(^|[^a-z0-9äöüß])"+norm(w).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).test(hay(o));
const cbLive=a=>(!a.ab||a.ab<=SHOP_END())&&(!a.kauf||a.kauf>=TODAY)&&(!a.ende||a.ende>=TODAY);
function SHOP_END(){const o=weekOffers().map(o=>o.to).filter(Boolean).sort();return o.at(-1)||TODAY}
// Passende Angebote: Marke + (wenn vorhanden) ein weiteres Wort aus dem Aktionsnamen, nur in den genannten Märkten
function cbOffers(a){const w=cbWords(a);if(!w.length)return [];const [br,...rest]=w;
  return weekOffers().filter(o=>o.p>0&&cbHit(o,br)&&rest.slice(0,2).every(x=>cbHit(o,x))&&(!a.shops?.length||a.shops.includes(o.s))).sort((x,y)=>fin(x)-fin(y))}
const cbBack=(a,price)=>{const p=a.pct??100;let d=price*p/100;if(a.max)d=Math.min(d,a.max);return Math.round(d*100)/100};
function cbFinds(){const no=store.get("cpNo",[]),have=new Set(S.coupons.map(c=>c.cb).filter(Boolean));
  return (CASHBACK?.items||[]).filter(a=>cbLive(a)&&!no.includes("cb:"+a.id)&&!have.has(a.id)).map(a=>{const os=cbOffers(a),o=os[0]||null;
    return {a,o,val:o?cbBack(a,fin(o)):(a.max||a.w||0)}}).sort((x,y)=>(!!y.o-!!x.o)||y.val-x.val||String(x.a.kauf||x.a.ende).localeCompare(String(y.a.kauf||y.a.ende)))}
const cbShopTxt=a=>a.shops?.length?"bei "+a.shops.map(sname).join(", "):"in vielen Märkten";
const CB_ICO={drogerie:"🧴",lebensmittel:"🍽️",tiernahrung:"🐾"};
function cpHowHTML(){return `<section class="panel cphow"><h3>Geheime Coupons: Geld zurück vom Hersteller</h3>
  <p>Viele Hersteller zahlen dir den Kaufpreis zurück („Gratis testen“). Das steht in keiner Markt-App und in keinem Prospekt – SparRadar sucht es jeden Tag für dich.</p>
  <ol><li><b>🔍 Coupon-Finder</b> antippen und bei allem, was du willst, <b>„Einfügen“</b> drücken. Der Artikel landet auf deinem Einkaufszettel.</li>
   <li><b>Ganz normal einkaufen</b> und den <b>Kassenbon aufheben</b>.</li>
   <li><b>💸 Geld holen:</b> Nach dem Einkauf auf „Bon hochladen“ tippen, Kassenbon fotografieren, Kontonummer eingeben – fertig. Das Geld kommt in ein paar Wochen aufs Konto.</li></ol>
  <p class="cpf-n">Rabatte, die nur mit der Markt-App gelten, siehst du direkt bei den Angeboten am 📱-Abzeichen. In der Markt-App aktivieren und an der Kasse die Kundenkarte zeigen – ein Scan.</p></section>`}
function cpFindHTML(){if(!S.cpFind)return `${cpHowHTML()}<button class="btn cpfind" id="cpFind">🔍 Coupon-Finder starten</button>`;
  if(!CASHBACK)return `<section class="panel cpf"><p>Coupon-Finder sucht …</p></section>`;
  const all=cbFinds(),cnt={};all.forEach(x=>(x.a.shops?.length?x.a.shops:["_"]).forEach(s=>cnt[s]=(cnt[s]||0)+1));
  if(S.cpfS&&!cnt[S.cpfS])S.cpfS=null;
  const f=S.cpfS?all.filter(x=>!x.a.shops?.length||x.a.shops.includes(S.cpfS)):all,tot=f.reduce((a,x)=>a+x.val,0);
  const ks=Object.keys(STORES).filter(k=>cnt[k]);
  const chips=ks.length?`<div class="cpf-ch">${[["","Alle",all.length],...ks.map(k=>[k,STORES[k].n,cnt[k]+(cnt._||0)])].map(([k,n,c])=>`<button class="chip${(S.cpfS||"")===k?" on":""}" data-cpfs="${k}" aria-pressed="${(S.cpfS||"")===k}">${k?sb(k)+" ":""}${esc(n)} <small>${c}</small></button>`).join("")}</div>`:"";
  return `<section class="panel cpf"><div class="cpf-h"><h3>🔍 Coupon-Finder</h3><button class="ibtn" id="cpFindX" aria-label="Coupon-Finder schließen">${IC.x}</button></div>
    ${chips}${f.length?`<p><b>${f.length} Geld-zurück-Aktion${f.length===1?"":"en"} gefunden – zusammen bis zu ${eur(tot)} zurück.</b> Ganz oben: was es gerade auch im Angebot gibt – doppelt gespart.</p>
    <div class="rows">${f.map(({a,o,val})=>`<div class="drow cpf-r">${o?`<button class="mini" style="--cc:${CC[o.c]||CC.sonstiges}" data-detail="${esc(o.id)}" aria-label="Details">${imgTag(o)}</button>`:`<span class="mini cbico" aria-hidden="true">${CB_ICO[a.cat]||"💸"}</span>`}
      <div class="t">${esc(a.n)}<small>${a.pct??100} % Geld zurück${a.max?" (max. "+eur(a.max)+")":""} · ${esc(cbShopTxt(a))}${a.kauf?" · kaufen bis "+fmtDate(a.kauf):""}${a.ab&&a.ab>TODAY?" · ab "+fmtDate(a.ab):""}</small>
       ${o?`<small class="cbhit">🔥 Gerade im Angebot: ${esc(sname(o.s))} ${eur(fin(o))}${cbBack(a,fin(o))>=fin(o)-.005?" → mit Geld zurück <b>gratis</b>":" → danach nur "+eur(fin(o)-cbBack(a,fin(o)))}</small>`:""}</div>
      <div class="pr"><b>−${eur(val)}</b><small>${a.pct??100} %</small></div>
      <div class="cpf-b"><button class="btn sm" data-cbadd="${esc(a.id)}">Einfügen</button><button class="btn ghost sm" data-cpfno="cb:${esc(a.id)}">Nein</button><a class="btn ghost sm" href="${esc(a.url)}" target="_blank" rel="noopener nofollow">Aktion ↗</a></div></div>`).join("")}</div>
    ${f.length>1?`<button class="btn ghost" id="cpFindAll">Alle ${f.length} einfügen</button>`:""}`
    :`<div class="empty" style="padding:16px"><b>Gerade nichts Neues</b>Alle aktuellen Geld-zurück-Aktionen hast du schon eingefügt oder abgelehnt. SparRadar sucht jeden Tag neu.</div>`}
    <p class="cpf-n">Gefunden in einer öffentlichen Übersicht von Hersteller-Aktionen, täglich neu. „Aktion ↗“ öffnet die Seite des Herstellers mit allen Bedingungen. Oft gilt: nur eine Teilnahme pro Person, begrenzte Teilnehmerzahl.</p></section>`}
function cbAdd(id,quiet){const a=(CASHBACK?.items||[]).find(x=>x.id===id);if(!a)return 0;const o=cbOffers(a)[0],w=cbWords(a);
  const k=o?[w[0],...w.slice(1).filter(x=>cbHit(o,x)).slice(0,1)].join(" "):w.slice(0,2).join(" ");
  S.coupons.push({id:"cb-"+a.id,s:o?o.s:(a.shops?.length===1?a.shops[0]:"all"),prog:"Geld zurück",k,t:"pct",v:a.pct??100,mx:a.max||null,to:a.ende||a.kauf||null,cb:a.id,url:a.url,n:a.n});
  if(o&&!S.list.includes(o.id))S.list.push(o.id);
  if(!quiet){save();toast(o?`Eingefügt und auf dem Zettel: ${a.n}. Kassenbon aufheben!`:`Eingefügt: ${a.n}. Beim Kauf Kassenbon aufheben!`)}return 1}

function renderCoupons(){
  const act=S.coupons.map((c,i)=>({c,i})).filter(x=>cpActive(x.c));
  const wo=weekOffers();
  const sopts=`<option value="all">Alle Märkte (z. B. Cashback-App)</option>`+Object.entries(STORES).map(([k,s])=>`<option value="${k}" ${k==="rewe"?"selected":""}>${esc(s.n)}</option>`).join("");
  const popts=PROGS.map(p=>`<option ${p==="Rewe Bonus"?"selected":""}>${p}</option>`).join("");
  const topts=Object.entries(CP_TYPES).map(([k,n])=>`<option value="${k}">${n}</option>`).join("");
  const plus=7;const d=new Date(Date.now()+plus*864e5).toISOString().slice(0,10);
  return `${cpFindHTML()}<section class="panel"><h3>Meine Coupons</h3>
    <p>Coupon in Lidl Plus, der Rewe-App, bei Payback oder in einer Cashback-App aktiviert? Kurz hier eintragen. SparRadar rechnet ihn dann in alle passenden Angebote, den Kracher und den Einkaufszettel ein. Abgelaufene Coupons verschwinden von selbst.</p>
    <form class="form" id="cpForm">
     <div class="row"><label>Markt<select id="cpStore">${sopts}</select></label><label>Programm<select id="cpProg">${popts}</select></label></div>
     <label>Gilt für (Artikel oder Marke)<input id="cpKw" required placeholder="z. B. Kaffee, Jacobs, Katzenfutter" autocomplete="off"></label>
     <div class="row"><label>Art<select id="cpType">${topts}</select></label><label>Wert<input id="cpVal" required inputmode="decimal" placeholder="z. B. 1,00 oder 20"></label></div>
     <div class="row"><label>Gültig bis<input id="cpTo" type="date" value="${d}"></label><label style="align-self:end"><button class="btn" type="submit">${IC.plus}Coupon speichern</button></label></div>
    </form>
    ${act.length?`<div class="rows">${act.map(({c,i})=>{const n=wo.filter(o=>couponsFor(o).includes(c)).length;
      return `<div class="drow"><div class="mini" style="--cc:${(STORES[c.s]||{}).c||"#2B3034"};display:grid;place-items:center">${c.s==="all"?`<span class="sb lg" style="--c:#2B3034">%</span>`:sb(c.s,true)}</div>
       <div class="t">${esc(c.cb&&c.n?c.n:c.k)}<small>${esc(c.s==="all"?"Alle Märkte":sname(c.s))} · ${esc(c.prog)} · ${c.to?(c.cb?"Bon einsenden bis ":"bis ")+fmtDate(c.to):"ohne Ende"}</small>
        ${c.cb&&c.url?`<a class="btn sm cblink" href="${esc(c.url)}" target="_blank" rel="noopener nofollow">🧾 Bon hochladen ↗</a>`:""}
        <div class="pills"><span class="pill ${n?"cb":""}">${n?`passt zu ${n} Angebot${n===1?"":"en"}`:"gerade kein passendes Angebot"}</span></div></div>
       <div class="pr"><b>${esc(cpValueTxt(c))}</b><div style="display:flex;gap:6px;justify-content:flex-end;margin-top:4px">${n?`<button class="btn ghost sm" data-cpshow="${i}">Zeigen</button>`:""}<button class="ibtn" data-delcp="${i}" aria-label="Coupon ${esc(c.k)} löschen">${IC.x}</button></div></div></div>`}).join("")}</div>`
      :'<div class="empty" style="padding:16px"><b>Noch keine Coupons</b>Trag oben deinen ersten aktivierten Coupon ein.</div>'}
    ${S.useApp?"":`<p style="color:var(--alert)">„Apps &amp; Coupons einrechnen“ ist ausgeschaltet. Coupons werden gerade nicht berücksichtigt.</p>`}
   </section>`}

// Code mit Auswahl: "ghp_…#sr:list,watch" -> das andere Gerät übernimmt die Auswahl beim Einfügen
const DEF_PICK={list:true,watch:false,coupons:false};
function codeParse(v){const m=String(v||"").trim().match(/^(\S+?)(?:#sr:([a-z,]*))?$/);if(!m)return{t:"",p:null};
  return{t:m[1],p:m[2]==null?null:Object.fromEntries(Object.keys(Sync.PARTS).map(k=>[k,m[2].split(",").includes(k)]))}}
function shareChecks(sh,attr){return `<div class="shchk">${Object.entries(Sync.PARTS).map(([p,v])=>`<button class="chip${sh[p]?" on":""}" ${attr}="${p}" aria-pressed="${!!sh[p]}">${sh[p]?"✓ ":""}${esc(v.n)}</button>`).join("")}</div>`}
function renderSync(){
  const c=Sync.cfg();
  return `<section class="panel" id="syncPanel"><h3>📱 ↔ 💻 Geräte verbinden</h3>
   ${Sync.ready()?(()=>{const ds=Object.entries(Sync.devs()).sort((a,b)=>(b[0]===Sync.devId())-(a[0]===Sync.devId())||b[1].at-a[1].at),ic={phone:"📱",tablet:"📱",pc:"💻"};
     const ago=t=>{const m=Math.round((Date.now()-t)/6e4);return m<2?"gerade aktiv":m<60?`vor ${m} Min.`:m<1440?`vor ${Math.round(m/60)} Std.`:`vor ${Math.round(m/1440)} Tag${Math.round(m/1440)===1?"":"en"}`};
     const pn=a=>(a||[]).map(p=>Sync.PARTS[p]?.n).filter(Boolean).join(", ")||"nichts";
     return `<p><b>${ds.length} ${ds.length===1?"Gerät":"Geräte"} verbunden.</b> Jedes Gerät wählt selbst, was es mit den anderen teilt. Änderungen kommen automatisch überall an.</p>
     <div class="shbox"><b>Dieses Gerät teilt:</b>${shareChecks(Sync.share(),"data-share")}<small>Antippen = an oder aus. Was hier aus ist, bleibt nur auf diesem Gerät. Was an ist, ist auf allen Geräten gleich, die es ebenfalls teilen.</small></div>
     <div class="devlist">${ds.map(([k,v])=>`<div class="dev${k===Sync.devId()?" me":""}"><span class="di">${ic[v.t]||"📱"}</span><span class="dt"><b>${esc(v.n||"Gerät")}</b><small>${k===Sync.devId()?"dieses Gerät":ago(v.at)}</small><small class="dsh">teilt: ${esc(pn(k===Sync.devId()?Sync.on():v.sh))}</small></span></div>`).join("")}</div>
     <form class="addrow" id="devForm"><input id="devName" value="${esc(Sync.devName())}" maxlength="30" placeholder="Name dieses Geräts, z. B. Handy oder Laptop" autocomplete="off"><button class="btn ghost" type="submit">Name speichern</button></form>
     <p id="syncState">${esc(Sync.status||"Verbunden")}</p>
     <p><b>Weiteres Gerät verbinden</b> (beliebig viele: eigenes Tablet oder PC, oder das Handy von jemandem, mit dem du zusammen einkaufst):</p>
     <ol class="steps"><li>Unten auswählen, was das neue Gerät teilen soll.</li><li>„Code kopieren“ drücken und den Code z. B. per WhatsApp schicken.</li><li>Auf dem neuen Gerät: SparRadar öffnen → Tab „Coupons“ → ganz unten „Einstellungen“ → „Geräte verbinden“ → Code einfügen → „Verbinden“.</li></ol>
     <p style="font-size:.8rem">🔒 Wer den Code hat, sieht und ändert die geteilten Listen. Gib ihn nur Menschen, denen du vertraust.</p>`})()+`
     <div class="shbox"><b>Was soll das neue Gerät teilen?</b>${shareChecks(store.get("syncGive",null)||DEF_PICK,"data-give")}<small>Die Auswahl steckt im Code, auf dem neuen Gerät ist nichts mehr einzustellen. Tipp: Ein eigenes zweites Gerät teilt meist alles. Bei einem anderen Menschen reicht oft der Einkaufszettel – dann bleiben Merkliste und Coupons privat.</small></div>
     ${Sync.cfg()?.gist&&Sync._srv?`<div class="shbox"><b>🔒 Sicherer: auf einen SparRadar-Code umziehen</b><small>Dieses Gerät ist noch mit einem GitHub-Schlüssel verbunden. Ein SparRadar-Code ist sicherer, weil er nur die SparRadar-Listen öffnet. Alles wird mitgenommen. Danach den neuen Code auf den anderen Geräten einfügen.</small><button class="btn sm" id="syncMigrate" style="margin-top:6px">Jetzt umziehen</button></div>`:""}
     ${Sync.cfg()?.from==="gist"?`<div class="shbox"><b>✅ Umgezogen auf SparRadar-Code</b><small>1. Unten „Code kopieren“ und auf den anderen Geräten unter „Verbindung trennen“ → Code einfügen. 2. Wenn alle Geräte umgezogen sind, den alten Schlüssel löschen: <a href="https://github.com/settings/tokens" target="_blank" rel="noopener">github.com/settings/tokens</a> → „SparRadar“ → Delete.</small><button class="btn ghost sm" id="syncMigDone" style="margin-top:6px">Erledigt, Hinweis ausblenden</button></div>`:""}
     <div class="links"><button class="btn sm" id="syncCopy">Code kopieren</button><button class="btn ghost sm" id="syncNow">Jetzt abgleichen</button><button class="btn ghost sm" id="syncOff">Verbindung trennen</button></div>`
   :`<p>Damit mehrere Geräte denselben Einkaufszettel haben – z. B. Handy und PC oder du und die Menschen, mit denen du einkaufst. Hakt einer etwas ab, sehen es alle sofort. Kostenlos, ohne Anmeldung.</p>
     <div class="shbox"><b>Was soll dieses Gerät teilen?</b>${shareChecks(store.get("syncPick",null)||DEF_PICK,"data-pick")}<small>Antippen = an oder aus. Hast du einen Code bekommen, ist die Auswahl meist schon drin und wird beim Einfügen übernommen. Später jederzeit änderbar.</small></div>
     ${Sync._srv?`<p><b>Du fängst an?</b> Code erstellen, danach erscheint „Code kopieren“ zum Weitergeben:</p><button class="btn" id="syncCreate" style="width:100%">✨ Neuen Code erstellen</button>
     <p style="margin-top:14px"><b>Du hast einen Code bekommen?</b> Hier einfügen und „Verbinden“ drücken:</p>`:`<p><b>Schon ein Gerät verbunden?</b> Dort „Code kopieren“ drücken, dir schicken und hier einfügen. Fertig.</p>`}
     <form class="addrow" id="syncForm"><input id="syncToken" type="password" placeholder="Code einfügen (beginnt mit SR-)" autocomplete="off" spellcheck="false"><button class="btn${Sync._srv?" ghost":""}" type="submit">Verbinden</button></form>
     <details class="steps-d"><summary>${Sync._srv?"Andere Möglichkeit: mit eigenem GitHub-Konto verbinden":"Noch kein Gerät verbunden? So bekommst du den Code (einmalig, am besten am PC)"}</summary>
     <ol class="steps"><li><a href="https://github.com/settings/tokens/new?scopes=gist&description=SparRadar" target="_blank" rel="noopener">Hier tippen</a> und bei GitHub anmelden.</li><li>Bei „Expiration“ <b>No expiration</b> auswählen. Der Haken bei <b>gist</b> ist schon gesetzt, sonst nichts anhaken.</li><li>Ganz unten auf den grünen Knopf <b>Generate token</b>.</li><li>Den langen Code, der mit <code>ghp_</code> anfängt, kopieren und oben einfügen.</li></ol><p style="font-size:.8rem">Der Schlüssel bleibt nur auf diesem Gerät und darf nur deinen geheimen SparRadar-Notizzettel bei GitHub lesen und schreiben.</p></details>
     <p style="font-size:.8rem">🔒 Wer den Code hat, sieht und ändert die geteilten Listen. Gib ihn nur Menschen, denen du vertraust.</p>`}
  </section>`}

// Einladung: schöne Landingpage (einladung.html) mit Logo-Vorschau in WhatsApp; Name steht nur im Link
const inviteUrl = () => { const n=(store.get("inviteName","")||"").trim(); return APP_URL+"einladung.html"+(n?"?von="+encodeURIComponent(n):""); };
const inviteText = () => { const n=(store.get("inviteName","")||"").trim();
  return `🎁 Persönliche Einladung${n?" von "+n:""}\n\nIch habe dich für SparRadar ausgewählt – meine Spar-App mit allen Angeboten von Lidl, Aldi, Rewe, Netto, Edeka und dm rund um Wörth.\n\n👉 So einfach geht's:\n1. Link antippen\n2. „SparRadar installieren“ drücken\n3. Mit „Installieren“ bestätigen – fertig!\n\nKeine Warnung, nichts zu deaktivieren.\n${inviteUrl()}`; };
function renderShare(){
  const n=store.get("inviteName","");
  return `<section class="panel invite" id="sharePanel">
   <div class="inv-head"><span class="inv-logo" aria-hidden="true"><img src="logo-tag.svg" alt="" width="36" height="36"></span>
    <div><span class="inv-badge">🎁 PERSÖNLICHE EINLADUNG</span><h3>SparRadar verschenken</h3></div></div>
   <p>Lade Freunde, Familie oder Bekannte ein. Sie bekommen eine Einladung mit Logo, tippen auf <b>„SparRadar installieren“</b> und haben die App auf dem Startbildschirm – ohne Warnungen, mit automatischen Updates.</p>
   <label class="inv-name">Dein Name auf der Einladung<input id="inviteName" value="${esc(n)}" placeholder="z. B. dein Vorname" maxlength="30" autocomplete="off"></label>
   <div class="links"><a class="btn wa inv-btn" id="inviteWa" href="${waLink(inviteText())}" target="_blank" rel="noopener">${WA_ICON}Einladung per WhatsApp senden</a>${navigator.share?'<button class="btn ghost" id="shareOther">Anders teilen …</button>':""}</div>
  </section>`}

function renderSettings(){
  const g=META.generated?new Date(META.generated):null;
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Einstellungen">
   <div class="sheet-h"><span class="newsico">${IC.gear}</span><h2>Einstellungen</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   ${renderShare()}
   ${renderSync()}
   ${ANDROID?`<section class="panel"><h3>📱 Nach dem Einkauf</h3><p>Hakst du am Handy den letzten Artikel ab, gilt der Einkauf als erledigt. Hast du für den Markt Coupons fotografiert, kommen sie zuerst groß nacheinander zum Scannen. Danach öffnet SparRadar die App des Markts (Lidl Plus, REWE, EDEKA, ALDI SÜD, Netto, Mein dm), damit du an der Kasse gleich deine Kundenkarte zeigen kannst.</p><button class="chip${store.get("openMktApp",true)?" on":""}" data-mktauto="1" aria-pressed="${store.get("openMktApp",true)}">${store.get("openMktApp",true)?"✓ Markt-App automatisch öffnen":"Markt-App automatisch öffnen"}</button></section>`:""}
   <section class="panel"><h3>👋 Erste Schritte</h3><p>Kurz erklärt, was SparRadar alles kann.</p><button class="btn ghost sm" data-showwelcome="1">Willkommens-Infos ansehen</button></section>
   <section class="panel"><h3>SparRadar als App</h3><p><b>Am einfachsten:</b> SparRadar in Chrome öffnen → Menü ⋮ → „App installieren“ bzw. „Zum Startbildschirm hinzufügen“. Ohne Warnungen, aktualisiert sich selbst.</p><p>Alternativ als Datei: Android-App (APK, Android fragt dabei nach Erlaubnis) oder Windows-Setup. Beide aktualisieren sich danach ebenfalls selbst.</p>
    <div class="links"><a class="btn ghost sm" href="${APK_URL}">Android-App (APK)</a><a class="btn ghost sm" href="https://github.com/Tiry38/sparradar/releases/download/apps/SparRadar-Setup.exe">Windows-Setup</a></div></section>
   <section class="panel"><h3>Über SparRadar</h3><p>Angebote werden jeden Morgen gegen 5:15 Uhr neu abgerufen${g?`, zuletzt am ${g.toLocaleDateString("de-DE",{weekday:"long",day:"2-digit",month:"2-digit"})} um ${g.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})} Uhr`:""}. ${OFFERS.length} Angebote, ${NAMES.length} bekannte Artikel für Vorschläge.</p>
    <div class="links"><button class="btn ghost sm" id="reloadApp">App neu laden</button>${window.SparRadarApp?'<button class="btn ghost sm" id="appUpdNow">Nach App-Update suchen</button>':""}</div></section>
   <div class="verline">${versionText()} · <span id="verState">wird geprüft …</span></div>
  </div>`}
// ---------- App-Update-Hinweis (Android-App / Windows-Programm) ----------
const UA=navigator.userAgent, AND_V=+(UA.match(/SparRadarAndroid\/(\d+)/)||[])[1]||0;
const IN_ANDROID_APP = !!AND_V || (/Android/.test(UA) && /; wv\)/.test(UA));   // auch alte App-Versionen ohne Versionsnummer
const verCmp=(a,b)=>{const x=String(a).split(".").map(Number),y=String(b).split(".").map(Number);for(let i=0;i<3;i++){if((x[i]||0)!==(y[i]||0))return (x[i]||0)-(y[i]||0)}return 0};
function appUpdateHTML(){
  // Android-App: kein Balken mehr. Updates der App-Hülle sind selten nötig und Android verlangt dafür
  // jedes Mal Bestätigungen und Warnungen. Wer will, sucht in den Einstellungen selbst nach Updates.
  if(false&&IN_ANDROID_APP&&APPV.code&&(!AND_V||AND_V<APPV.code))
    return `<div class="appupd">${IC.bell}<span><b>Neue App-Version da.</b> Kurz aktualisieren, dann ist alles auf dem neuesten Stand.</span>${window.SparRadarApp?'<button class="btn sm" id="appUpdNow">Aktualisieren</button>':`<a class="btn sm" href="${APK_URL}">Aktualisieren</a>`}</div>`;
  const w=window.__SR_DESKTOP__;
  if(w&&APPV.desktop&&verCmp(w,APPV.desktop)<0)
    return `<div class="appupd">${IC.bell}<span><b>Neue Programm-Version da.</b> SparRadar einmal schließen und wieder öffnen, dann aktualisiert es sich von selbst.</span></div>`;
  return ""}

// Versionsnummern: Web-App (app.js?v=) und, falls vorhanden, Android-App bzw. Windows-Programm
function versionText(){
  const w=window.__SR_DESKTOP__;
  return `SparRadar Version ${MYV||"?"}${AND_V?` · Android-App 1.${AND_V}`:IN_ANDROID_APP?" · Android-App (ältere Version)":""}${w?` · Windows-Programm ${esc(w)}`:""}`}
async function checkVersion(){const el=document.getElementById("verState");if(!el)return;
  try{const v=(await (await fetch("index.html",{cache:"no-store"})).text()).match(/app\.js\?v=(\d+)/)?.[1];
    el.innerHTML=v&&v!==MYV?`<b style="color:var(--alert)">neue Version ${v} da</b> – „App neu laden“ tippen`:`<b style="color:var(--save)">✓ neueste Version</b>`}
  catch(e){el.textContent="offline, nicht prüfbar"}}

function renderTips(){
  const T=[
   ["lidl","Lidl Plus","Personalisierte Coupons, günstigere App-Preise und Belohnungen ab einem bestimmten Monatseinkauf. Coupons vor dem Einkauf aktivieren."],
   ["rewe","Rewe Bonus","Seit dem Payback-Ausstieg Ende 2024 sammelst du in der Rewe-App Euro-Guthaben auf Aktionsartikel und Coupons. Ab 1 € an der Kasse einlösbar."],
   ["netto","Netto App + Payback","Netto Marken-Discount ist seit 2025 bei Payback. Dazu gibt es eigene Coupons in der Netto-App."],
   ["edeka","Payback + Edeka App","Edeka ist seit 2025 bei Payback. Punkte-Coupons vorher in der Payback-App aktivieren, dazu Coupons in der Edeka-App."],
   ["dm","dm App","Digitale Coupons und Aktionen, auch für Lebensmittel und Tierfutter."],
   ["aldi","Aldi Süd","Kaum Coupons, dafür dauerhaft niedrige Preise. Neue Aktionsware kommt montags und donnerstags."]];
  const G=[
   [IC.layers,"Stapeln","Angebotspreis, dann App-Preis, dann Coupon oder Bonus, dazu Payback-Punkte und am Ende Cashback per Kassenbon."],
   [IC.chart,"Fake-Rabatte erkennen","SparRadar speichert jeden Tag die Preise. Nach ein paar Wochen zeigt es dir, ob ein „statt“-Preis wirklich verlangt wurde."],
   [IC.box,"Vorrat bei Tiefpreis","Haltbares wie Katzenfutter, Kaffee, Nudeln oder Getränke nur kaufen, wenn der Grundpreis unter deinem Wunschpreis liegt. Dann gleich für mehrere Wochen."],
   [IC.scale,"Grundpreis zählt","Vergleiche immer den Preis pro kg oder l. Die Großpackung ist nicht automatisch günstiger."],
   [IC.cal,"Montag und Donnerstag","An diesen Tagen starten bei Lidl und Aldi die neuen Aktionen. Unter „Nächste Woche“ siehst du sie schon vorher."],
   [IC.bag,"Too Good To Go","Bäcker und Märkte geben abends übrig gebliebene Lebensmittel als Überraschungstüte ab, meist für etwa ein Drittel des Werts."]];
  return `${renderCoupons()}
   <h3 class="sec-h">Spartipps</h3>
   <section class="panel"><h3>Geht „Extreme Couponing“ wie in den USA auch hier?</h3>
   <p>Nur teilweise. In Deutschland sind Coupons fast immer Händler-Coupons in Apps, oft auf ein Stück pro Einkauf begrenzt. Einen 200-€-Wagen für 0 € schaffst du hier nicht. Einzelne Artikel umsonst oder mit Plus gehen aber, wenn du Händler-App, Payback oder Rewe Bonus, Cashback-Apps und „Gratis testen“-Aktionen der Hersteller kombinierst.</p></section>
   <h3 class="sec-h">So holst du am meisten raus</h3>
   <div class="tips">${G.map(([i,h,p])=>`<div class="tip"><h4><span class="ico">${i}</span>${h}</h4><p>${p}</p></div>`).join("")}</div>
   <h3 class="sec-h">Apps und Programme deiner Märkte</h3>
   <div class="tips">${T.map(([s,prog,txt])=>`<div class="tip"><h4>${sb(s,true)}${esc(sname(s))}</h4><span class="prog">${prog}</span><p>${txt}</p></div>`).join("")}
   <div class="tip"><h4><span class="ico">${IC.layers}</span>Cashback-Apps</h4><span class="prog">Marktguru · Scondoo · Coupies</span><p>Geld zurück auf bestimmte Markenprodukte, egal in welchem Markt gekauft. Kassenbon fotografieren, das Geld kommt aufs Konto oder per PayPal.</p></div>
   <div class="tip"><h4><span class="ico">${IC.bag}</span>Too Good To Go</h4><span class="prog">Abends Essen retten</span><p>Standort Wörth am Rhein wählen und Bäcker und Märkte in der Nähe als Favoriten speichern.</p></div></div>
   <div class="setlink"><button class="btn ghost" id="openSettings">${IC.gear}Einstellungen</button></div>`}

// Handy: Märkte, Kategorien und Sortierung aufgeräumt in einem Fenster statt drei langer Leisten
const SORTS={off:"Höchste Ersparnis",gp:"Bester Grundpreis",p:"Niedrigster Preis"};
function renderFilter(){
  const counts={},cc={};OFFERS.forEach(o=>{counts[o.s]=(counts[o.s]||0)+1;cc[o.c]=(cc[o.c]||0)+1});
  const n=filtered().length;
  const chip=(attr,k,label,on,extra="")=>`<button class="chip${extra}" ${attr}="${k}" aria-pressed="${on}">${label}</button>`;
  const food=Object.entries(CATS).filter(([k])=>!NONFOOD_CATS.includes(k)&&cc[k]),nf=Object.entries(CATS).filter(([k])=>NONFOOD_CATS.includes(k)&&cc[k]);
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Märkte und Filter">
   <div class="sheet-h"><h2>Märkte &amp; Filter</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <h3 class="fh">Märkte</h3>
   <div class="fchips">${chip("data-store","","Alle Märkte",!S.stores.size," plain")}${Object.keys(STORES).filter(k=>counts[k]).map(k=>chip("data-store",k,sb(k)+esc(STORES[k].n)+`<em>${counts[k]}</em>`,S.stores.has(k))).join("")}</div>
   <h3 class="fh">Essen &amp; Drogerie</h3>
   <div class="fchips">${chip("data-cat","","Alle Kategorien",!S.cats.size," plain")}${food.map(([k,v])=>chip("data-cat",k,esc(v),S.cats.has(k)," plain")).join("")}</div>
   ${nf.length?`<h3 class="fh">Weitere Angebote</h3><div class="fchips">${nf.map(([k,v])=>chip("data-cat",k,esc(v),S.cats.has(k)," plain")).join("")}</div>`:""}
   <h3 class="fh">Sortieren</h3>
   <div class="fchips">${Object.entries(SORTS).map(([k,v])=>chip("data-sort",k,v,S.sort===k," plain")).join("")}</div>
   <h3 class="fh">Mindest-Ersparnis</h3>
   <div class="fchips">${[0,20,30,40,50].map(v=>chip("data-fmin",v,v?`ab ${v} %`:"Egal",S.flt.min===v," plain")).join("")}</div>
   <h3 class="fh">Preis bis</h3>
   <div class="fchips">${[0,1,2,5,10,20].map(v=>chip("data-fmax",v,v?`${v} €`:"Egal",S.flt.max===v," plain")).join("")}</div>
   <h3 class="fh">Nur zeigen</h3>
   <div class="fchips">${Object.entries(FLT_LABEL).map(([k,v])=>chip("data-fflag",k,v,!!S.flt[k]," plain")).join("")}</div>
   <p class="fhint">„Nur echte Rabatte“: mit Händler-„statt“-Preis, den SparRadar nicht widerlegt hat. „Ohne App & Karte“: Preis gilt für alle, ohne Lidl Plus, Payback, Coupon o. Ä. „Tiefstpreis“: so günstig wie lange nicht laut Preisverlauf.</p>
   <div class="frow"><button class="switch" data-toggleapp="1" role="switch" aria-checked="${S.useApp}" aria-label="Apps und Coupons einrechnen"></button><span>Apps &amp; Coupons einrechnen</span></div>
   <div class="factions"><button class="btn ghost" data-freset="1">Zurücksetzen</button><button class="btn" data-fdone="1">${n} Angebote zeigen</button></div>
  </div>`}

// Zurück-Taste/-Wischgeste (Handy) und Browser-Zurück: schließt zuerst ein offenes Fenster,
// dann geht es zurück zu „Angebote“, erst danach wird die App verlassen.
let NAV=0,IGNORE_POP=0;
function navSync(){const want=(S.tab!=="offers"?1:0)+(S.sheet?1:0)+(S.lightbox?1:0);
  while(NAV<want){history.pushState({sr:NAV+1},"");NAV++}
  if(NAV>want){const n=NAV-want;NAV=want;IGNORE_POP++;history.go(-n)}}
addEventListener("popstate",()=>{
  if(IGNORE_POP>0){IGNORE_POP--;return}
  if(NAV===0){askExit();return}   // ganz am Anfang angekommen: fragen, ob die App geschlossen werden soll
  NAV=Math.max(0,NAV-1);
  if(S.lightbox)S.lightbox=null;else if(S.sheet)S.sheet=null;else if(S.tab!=="offers"){S.tab="offers";scrollTo({top:0})}
  render()});

// Schutz-Eintrag im Verlauf: das letzte „Zurück“ landet hier und fragt nach, statt die App sofort zu schließen
function askExit(){
  let el=document.getElementById("exitAsk");
  if(!el){el=document.createElement("div");el.id="exitAsk";el.className="exitask";document.body.appendChild(el)}
  el.innerHTML=`<div class="exitbox" role="alertdialog" aria-label="App schließen?"><span class="newsico">${IC.x}</span><h3>SparRadar wirklich schließen?</h3>
   <div class="factions"><button class="btn ghost" id="exitNo">Nein</button><button class="btn" id="exitYes">Ja, schließen</button></div></div>`;
  el.hidden=false}
function closeExit(stay){const el=document.getElementById("exitAsk");if(el)el.hidden=true;
  if(stay){history.pushState({sr:"guard"},"");return}
  if(window.SparRadarApp?.exitApp){window.SparRadarApp.exitApp();return}   // Android-App
  try{window.close()}catch(e){}
  setTimeout(()=>{history.back();toast("Zum Schließen jetzt noch einmal Zurück tippen.")},150)}

function render(){
  document.getElementById("filters").hidden=S.tab!=="offers";
  ["offers","watch","list","tips"].forEach(t=>document.getElementById("tab-"+t).setAttribute("aria-selected",t===S.tab));
  document.getElementById("wk1").textContent=nextLabel();document.getElementById("wk0").textContent=WEEKEND?"Ab Montag":"Jetzt gültig";
  document.getElementById("wk0").setAttribute("aria-pressed",S.week===0);document.getElementById("wk1").setAttribute("aria-pressed",S.week===1);
  const hits=new Set(watchHits(null).flatMap(x=>x.hits.map(o=>o.id))).size;
  const wb=document.getElementById("watchBadge");wb.textContent=hits;wb.hidden=!hits;
  const ln=S.list.filter(id=>byId(id)&&!S.checked.includes(id)).length+S.extra.filter(x=>!S.checked.includes(x.id)).length;
  const lb=document.getElementById("listBadge");lb.textContent=ln;lb.hidden=!ln;
  const nc=S.coupons.filter(cpActive).length,cb=document.getElementById("cpBadge");cb.textContent=nc;cb.hidden=!nc;
  const counts={},ccount={};OFFERS.forEach(o=>{counts[o.s]=(counts[o.s]||0)+1;ccount[o.c]=(ccount[o.c]||0)+1});
  // Markt-Leiste mit Logos: antippen = nur dieser Markt (mehrere möglich), „Alle“ = alles
  document.getElementById("storeChips").innerHTML=`<button class="mtile all" data-store="" aria-pressed="${!S.stores.size}"><span class="sb lg">${IC.layers}</span><span class="mn">Alle</span><em>${OFFERS.length}</em></button>`+Object.keys(STORES).map(k=>`<button class="mtile" data-store="${k}" aria-pressed="${S.stores.has(k)}">${sb(k,true)}<span class="mn">${esc(STORES[k].n.replace(" Jockgrim",""))}</span><em>${counts[k]||0}</em></button>`).join("");
  document.getElementById("catChips").innerHTML=`<button class="chip plain" data-cat="" aria-pressed="${!S.cats.size}">Alle Kategorien</button>`+Object.entries(CATS).filter(([k])=>ccount[k]||S.cats.has(k)).map(([k,n],i,arr)=>`${NONFOOD_CATS.includes(k)&&i&&!NONFOOD_CATS.includes(arr[i-1][0])?'<span class="chipsep" aria-hidden="true"></span>':""}<button class="chip plain" data-cat="${k}" aria-pressed="${S.cats.has(k)}">${n}</button>`).join("");
  document.getElementById("appSw").setAttribute("aria-checked",S.useApp);
  document.getElementById("sort").value=S.sort;
  const act=[].concat(S.cats.size?[catTitle()]:[],S.sort!=="off"?[SORTS[S.sort]]:[],fltSummary());
  const f2=document.getElementById("fcount2");if(f2){f2.textContent=fltCount();f2.hidden=!fltCount()}
  document.getElementById("fsum").textContent=act.length?act.join(" · "):"Alle Kategorien";
  const fc=document.getElementById("fcount");fc.textContent=act.length;fc.hidden=!act.length;
  document.getElementById("qclear").hidden=!S.q;
  document.getElementById("main").innerHTML={offers:renderOffers,watch:renderWatch,list:renderList,tips:renderTips}[S.tab]();
  const sh=document.getElementById("sheet");sh.hidden=!S.sheet;document.body.classList.toggle("lock",!!S.sheet);
  // Scroll-Position nur behalten, wenn dasselbe Fenster neu gezeichnet wird (z. B. nach „Merken“), neues Fenster startet oben
  if(S.sheet==="scan"&&document.getElementById("scanVideo")){} // Kamerabild nicht neu aufbauen
  else if(S.sheet){const y=S.sheet===S._shown?(sh.firstElementChild?.scrollTop||0):0;S._shown=S.sheet;sh.innerHTML=({scan:renderScan,filter:renderFilter,news:renderNews,settings:renderSettings,whatsnew:renderWhatsNew,welcome:renderWelcome,saved:renderSaved,detail:renderDetail,trip:renderTrip}[S.sheet]||renderKracher)();if(sh.firstElementChild)sh.firstElementChild.scrollTop=y}else S._shown=null;
  document.getElementById("appUpd").innerHTML=appUpdateHTML();
  let lbh=document.getElementById("lbHost");if(!lbh){lbh=document.createElement("div");lbh.id="lbHost";document.body.appendChild(lbh)}
  lbh.innerHTML=renderLightbox();
  Scan.sync();
  navSync();
}

// kaputte Fotos durch Illustration ersetzen
document.addEventListener("error",e=>{const t=e.target;if(t.tagName==="IMG"&&t.dataset.logo){t.remove();return}
  if(t.tagName==="IMG"&&t.dataset.thumb){t.closest("button")?.remove();return}if(t.tagName==="IMG"&&t.dataset.cat){t.outerHTML=ILL[t.dataset.cat]||ILL.sonstiges}},true);

document.addEventListener("click",e=>{
  if(e.target.id==="sheet"){S.sheet=null;render();return}
  if(e.target.id==="exitNo"||e.target.id==="exitAsk"){closeExit(true);return}
  if(e.target.id==="exitYes"){closeExit(false);return}
  // Vollbild: Produktbild schließt bei Tipp, Prospektseite nur über ✕ (dort wird gescrollt und gezoomt)
  if(e.target.closest("#lbClose")||(e.target.closest("#lightbox")&&!e.target.closest("#lightbox.pg"))){S.lightbox=null;render();return}
  const b=e.target.closest("button");
  if(!e.target.closest(".sugg,#q,#kwIn"))hideSugg();
  // Artikel antippen (nicht auf Knöpfe/Links) = Detailansicht
  const det=!b&&!e.target.closest("a")&&e.target.closest("[data-detail]");
  if(det){S.detail=det.dataset.detail;S.dImg=0;S.sheet="detail";render();return}
  if(!b)return;
  if(b.dataset.detail){S.detail=b.dataset.detail;S.dImg=0;S.sheet="detail";S._shown=null;render();return}
  if(b.dataset.sugg==="q"){const v=b.dataset.v;S.q=v;document.getElementById("q").value=v;S.limit=60;hideSugg();S.tab="offers";render();return}
  if(b.dataset.sugg==="kw"){const v=b.dataset.v;document.getElementById("kwIn").value=v;hideSugg();document.getElementById("kwForm").requestSubmit();return}
  if(b.id&&b.id.startsWith("tab-")){S.tab=b.id.slice(4);render();scrollTo({top:0});return}
  if(b.id==="wk0"||b.id==="wk1"){S.week=+b.id[2];S.limit=60;render();return}
  if(b.id==="openK"){S.sheet="k";render();return}
  if(b.id==="openFilter"||b.id==="openFilter2"){S.sheet="filter";render();return}
  if(b.dataset.zoom){S.lightbox=b.dataset.zoom;render();return}
  if(b.dataset.dimg!==undefined){S.dImg=+b.dataset.dimg;render();return}
  if(b.id==="openSettings"){S.sheet="settings";render();checkVersion();return}
  if(b.id==="settingsBtn"){S.sheet="settings";render();checkVersion();return}
  if(b.id==="reloadApp"){location.reload();return}
  if(b.id==="appUpdNow"){try{window.SparRadarApp.checkUpdate()}catch(e){location.href=APK_URL}return}
  if(b.id==="syncCopy"){const g=store.get("syncGive",null)||DEF_PICK,on=Object.keys(Sync.PARTS).filter(k=>g[k]);
    copy(`${Sync.code()}#sr:${on.join(",")}`,`Code kopiert (teilt: ${on.map(k=>Sync.PARTS[k].n).join(", ")||"nichts"}). Jetzt schicken und auf dem anderen Gerät einfügen.`);return}
  if(b.dataset.give){const sh={...(store.get("syncGive",null)||DEF_PICK)};sh[b.dataset.give]=!sh[b.dataset.give];store.set("syncGive",sh);render();return}
  if(b.dataset.share){const sh={...Sync.share()};sh[b.dataset.share]=!sh[b.dataset.share];Sync.setShare(sh);render();Sync.pull().then(()=>{toast(sh[b.dataset.share]?`${Sync.PARTS[b.dataset.share].n} wird jetzt geteilt`:`${Sync.PARTS[b.dataset.share].n} bleibt jetzt nur auf diesem Gerät`);render()});return}
  if(b.dataset.pick){const sh={...(store.get("syncPick",null)||DEF_PICK)};sh[b.dataset.pick]=!sh[b.dataset.pick];store.set("syncPick",sh);render();return}
  if(b.id==="syncCreate"){b.disabled=true;toast("Erstelle Code …");Sync.create(store.get("syncPick",null)||DEF_PICK).then(()=>{toast("Fertig! Jetzt „Code kopieren“ und an die anderen Geräte schicken.");render();setTimeout(()=>document.getElementById("syncPanel")?.scrollIntoView({block:"start",behavior:"smooth"}),80)},e=>{b.disabled=false;toast("Hat nicht geklappt: "+e.message)});return}
  if(b.id==="syncMigrate"){if(!confirm("Auf einen SparRadar-Code umziehen? Merkliste, Zettel, Coupons und Geräte werden mitgenommen."))return;b.disabled=true;toast("Ziehe um …");
    Sync.migrate().then(()=>{toast("Umgezogen! Jetzt den neuen Code auf deinen anderen Geräten einfügen.");render()},e=>{b.disabled=false;toast("Hat nicht geklappt: "+e.message)});return}
  if(b.id==="syncMigDone"){const c=Sync.cfg();delete c.from;store.set("sync",c);render();return}
  if(b.id==="syncNow"){Sync.pull().then(()=>toast(Sync.status));return}
  if(b.id==="syncOff"){if(confirm("Verbindung auf diesem Gerät trennen? Deine Listen bleiben hier gespeichert.")){Sync.disconnect();render()}return}
  if(b.dataset.sort){S.sort=b.dataset.sort;render();return}
  if(b.dataset.toggleapp){S.useApp=!S.useApp;save();render();return}
  if(b.dataset.freset){S.stores.clear();S.cats.clear();S.sort="off";S.limit=60;S.flt={min:0,max:0,bio:0,vegan:0,real:0,app:0,noapp:0,low:0};store.set("flt",S.flt);render();return}
  if(b.dataset.fmin!=null){S.flt.min=+b.dataset.fmin;S.limit=60;store.set("flt",S.flt);render();return}
  if(b.dataset.fmax!=null){S.flt.max=+b.dataset.fmax;S.limit=60;store.set("flt",S.flt);render();return}
  if(b.dataset.fflag){const k=b.dataset.fflag;S.flt[k]=S.flt[k]?0:1;S.limit=60;store.set("flt",S.flt);render();return}
  if(b.dataset.fclear){S.flt={min:0,max:0,bio:0,vegan:0,real:0,app:0,noapp:0,low:0};store.set("flt",S.flt);render();return}
  if(b.dataset.fdone){S.sheet=null;render();scrollTo({top:0});return}
  if(b.id==="closeSheet"){S.sheet=null;render();return}
  if(b.id==="more"){S.limit+=60;render();return}
  if(b.dataset.store!==undefined){const k=b.dataset.store;if(!k)S.stores.clear();else S.stores.has(k)?S.stores.delete(k):S.stores.add(k);S.limit=60;render();return}
  if(b.dataset.cat!==undefined){const k=b.dataset.cat;if(!k)S.cats.clear();else S.cats.has(k)?S.cats.delete(k):S.cats.add(k);S.limit=60;render();return}
  if(b.id==="appSw"){S.useApp=!S.useApp;save();render();return}
  if(b.id==="qclear"){S.q="";document.getElementById("q").value="";render();return}
  if(b.dataset.fav){const o=byId(b.dataset.fav);if(!o)return;const i=S.watch.findIndex(w=>norm(w.k)===norm(o.n));if(i>=0){S.watch.splice(i,1);toast(`${o.n} von der Merkliste genommen`)}else{S.watch.push({k:o.n});toast(`${o.n} gemerkt`)}save();render();return}
  if(b.dataset.add){const id=b.dataset.add,i=S.list.indexOf(id);if(i>=0){S.list.splice(i,1);delete S.qty[id]}else{S.list.push(id);toast("Auf den Einkaufszettel gesetzt")}save();render();return}
  if(b.dataset.wsel!=null&&b.dataset.wsel!==""){const i=+b.dataset.wsel;S.wsel=S.wsel===i?null:i;render();return}
  if(b.dataset.cpqlist){const id=b.dataset.cpqlist,o=byId(id);S.detail=id;S.dImg=0;S.sheet="detail";S._shown=null;S.cpq=o&&couponsFor(o).length?null:id;render();
    setTimeout(()=>document.querySelector("#sheet .cpq")?.scrollIntoView({block:"center",behavior:"smooth"}),80);return}
  if(b.dataset.cpq!=null){S.cpq=b.dataset.cpq||null;render();return}
  if(b.dataset.cpqset){const [id,t,v]=b.dataset.cpqset.split("|");cpqSave(id,t,+v);return}
  if(b.dataset.delkw){S.watch.splice(+b.dataset.delkw,1);S.wsel=null;save();render();return}
  if(b.id==="cpFind"){S.cpFind=true;render();loadCashback().then(render);return}
  if(b.dataset.cpfs!=null){S.cpfS=b.dataset.cpfs||null;render();return}
  if(b.id==="cpFindX"){S.cpFind=false;render();return}
  if(b.dataset.cbadd){cbAdd(b.dataset.cbadd);render();return}
  if(b.dataset.cpfno){const no=store.get("cpNo",[]),ids=new Set((CASHBACK?.items||[]).map(a=>"cb:"+a.id));store.set("cpNo",[...no.filter(i=>ids.has(i)),b.dataset.cpfno]);render();return}
  if(b.id==="cpFindAll"){const f=cbFinds().filter(x=>!S.cpfS||!x.a.shops?.length||x.a.shops.includes(S.cpfS)),n=f.reduce((a,x)=>a+cbAdd(x.a.id,true),0);save();toast(`${n} Geld-zurück-Aktionen eingefügt – Kassenbons aufheben!`);render();return}
  if(b.dataset.delcp){const c=S.coupons.splice(+b.dataset.delcp,1)[0];save();toast(`Coupon „${c.k}“ gelöscht`);render();return}
  if(b.dataset.cpshow){const c=S.coupons[+b.dataset.cpshow];S.tab="offers";S.q=c.k;document.getElementById("q").value=c.k;S.stores=new Set(c.s==="all"?[]:[c.s]);S.cats.clear();S.limit=60;render();scrollTo({top:0});return}
  if(b.id==="planToList"){let n=0;weekPlan().forEach(([,g])=>g.items.forEach(o=>{if(!S.list.includes(o.id)){S.list.push(o.id);n++}}));save();toast(n?`${n} Artikel auf den Einkaufszettel gesetzt`:"Schon alles auf dem Zettel");render();return}
  if(b.id==="goWatch"){S.tab="watch";render();return}
  if(b.id==="watchFromSearch"){const k=S.q.trim();if(k&&!S.watch.some(w=>norm(w.k)===norm(k)))S.watch.push({k});save();toast(`„${k}“ wird beobachtet`);S.tab="watch";render();return}
  if(b.id==="clearList"){if(!confirm("Den ganzen Einkaufszettel leeren?"))return;S.list=[];S.extra=[];S.checked=[];save();render();return}
  if(b.id==="clearDone"){S.list=S.list.filter(id=>!S.checked.includes(id));S.extra=S.extra.filter(x=>!S.checked.includes(x.id));S.checked=[];save();render();return}
  if(b.id==="scanBtn"){Scan.last="";Scan.res="";S.sheet="scan";render();return}
  if(b.dataset.swap){const [a,c]=b.dataset.swap.split("|"),i=S.list.indexOf(a);if(i>=0)S.list[i]=c;const n=byId(c);save();toast(n?`Getauscht: jetzt bei ${sname(n.s)}`:"Getauscht");render();return}
  if(b.dataset.check){const id=b.dataset.check,i=S.checked.indexOf(id);
    if(i>=0){S.checked.splice(i,1);const j=S.saved.map(x=>x.off?null:x.id).lastIndexOf(id);if(j>=0)S.saved.splice(j,1)}
    else{S.checked.push(id);try{if(TOUCH())navigator.vibrate?.(15)}catch(e){}wakeOn();
      const o=byId(id);if(o){const v=r2((ref(o)-fin(o))*qty(id));if(v>0){S.saved.push({id,n:o.n,s:o.s,v,d:TODAY});toast(`Im Wagen – ${eur(v)} gespart`)}}
      // Handy: letzter Artikel im Wagen -> Einkauf abgeschlossen
      const all=[...S.list.filter(x=>byId(x)),...S.extra.map(x=>x.id)];
      if(TOUCH()&&all.length&&all.every(x=>S.checked.includes(x))){finishTrip(all,true);return}}
    save();render();return}
  if(b.dataset.qp||b.dataset.qm){const id=b.dataset.qp||b.dataset.qm;S.qty[id]=Math.min(49,Math.max(1,qty(id)+(b.dataset.qp?1:-1)));if(S.qty[id]===1)delete S.qty[id];save();render();return}
  if(b.dataset.mktapp){openMktApp(b.dataset.mktapp);return}
  if(b.dataset.mktauto){store.set("openMktApp",!store.get("openMktApp",true));render();return}
  if(b.dataset.tripfinish){finishTrip([...S.list.filter(x=>byId(x)),...S.extra.map(x=>x.id)].filter(x=>S.checked.includes(x)),false);return}
  if(b.dataset.triprestore){restoreTrip(b.dataset.triprestore);return}
  if(b.dataset.tripopen){S.tripId=b.dataset.tripopen;S.sheet="trip";hideTripPop();render();return}
  if(b.dataset.savedopen){S.sheet="saved";render();return}
  if(b.dataset.saveddel){const x=S.saved[+b.dataset.saveddel];if(x){x.off=1;save();render();toast(`„${x.n}“ zählt nicht mehr`)}return}
  if(b.dataset.savedreset){if(!confirm("Den ganzen Gespart-Zähler auf 0 setzen?"))return;S.saved.forEach(x=>x.off=1);S.sheet=null;save();render();toast("Gespart-Zähler steht wieder auf 0");return}
  if(b.dataset.tripdel){if(!confirm("Diesen Einkauf aus dem Verlauf löschen?"))return;S.trips=S.trips.filter(x=>x.id!==b.dataset.tripdel);S.sheet=null;save();render();return}
  if(b.dataset.tripmore){S.tripLimit=(S.tripLimit||10)+20;render();return}
  if(b.dataset.tpclose){hideTripPop();return}
  if(b.dataset.readd){readd(b.dataset.readd);return}
  if(b.dataset.budget){const v=prompt("Budget für diesen Einkauf in Euro (leer lassen = kein Budget):",S.budget?String(S.budget).replace(".",","):"");if(v===null)return;S.budget=Math.max(0,parseFloat(v.replace(",","."))||0);save();render();return}
  if(b.dataset.delextra){S.extra=S.extra.filter(x=>x.id!==b.dataset.delextra);save();render();return}
  if(b.id==="toTop"){scrollTo({top:0,behavior:"smooth"});return}
  if(b.id==="copyList"){copy(listText(),"Einkaufszettel kopiert");return}
  if(b.id==="shareOther"){navigator.share({title:"Persönliche Einladung zu SparRadar",text:inviteText()}).catch(()=>{});return}
  if(b.dataset.watchname){const k=b.dataset.watchname;if(!S.watch.some(w=>norm(w.k)===norm(k))){S.watch.push({k});save();toast(`„${k}“ auf der Merkliste. Du siehst es, sobald es im Angebot ist.`)}render();return}
  if(b.dataset.showwelcome){S.sheet="welcome";S._shown=null;render();return}
  if(b.dataset.welcome){if(b.dataset.welcome==="sync"){S.sheet="settings";render();setTimeout(()=>document.getElementById("syncPanel")?.scrollIntoView({block:"start",behavior:"smooth"}),80)}else{S.sheet=null;render()}return}
  if(b.dataset.newsdone){S.sheet=null;if(b.dataset.newsdone==="watch")S.tab="watch";render();return}
});
function copy(txt,ok){const fail=()=>toast("Kopieren hat nicht geklappt. Bitte Text markieren und von Hand kopieren.");try{navigator.clipboard.writeText(txt).then(()=>toast(ok),fail)}catch(e){fail()}}
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&S.lightbox){S.lightbox=null;render()}else if(e.key==="Escape"&&S.sheet){S.sheet=null;render()}
  if(e.key==="Enter"&&e.target.matches?.(".card[data-detail]")){S.detail=e.target.dataset.detail;S.dImg=0;S.sheet="detail";render()}});
document.addEventListener("submit",e=>{
  if(e.target.id==="kwForm"){e.preventDefault();const v=document.getElementById("kwIn").value.trim(),mx=parseNum(document.getElementById("kwMax").value);
    if(v){const i=S.watch.findIndex(w=>norm(w.k)===norm(v));if(i>=0)S.watch[i].max=mx||undefined;else S.watch.push(mx?{k:v,max:mx}:{k:v});save();toast(mx?`Vorrats-Alarm: „${v}“ unter ${eur(mx)}/kg`:`„${v}“ wird beobachtet`)}render()}
  if(e.target.id==="extraForm"){e.preventDefault();const v=document.getElementById("extraIn").value.trim();if(v){const x=parseExtra(v),id="x-"+Date.now();S.extra.push(x.p?{id,n:x.n,p:x.p}:{id,n:x.n});if(x.q>1)S.qty[id]=x.q;save();render();document.getElementById("extraIn")?.focus()}return}
  if(e.target.id==="cpqForm"){e.preventDefault();cpqSave(e.target.dataset.id,document.getElementById("cpqType").value,parseNum(document.getElementById("cpqVal").value));return}
  if(e.target.id==="devForm"){e.preventDefault();const v=document.getElementById("devName").value.trim().slice(0,30);store.set("devName",v);Sync.push().then(()=>{toast(v?`Dieses Gerät heißt jetzt „${v}“`:"Name zurückgesetzt");render()});return}
  if(e.target.id==="syncForm"){e.preventDefault();const cp=codeParse(document.getElementById("syncToken").value),t=cp.t;if(cp.p)store.set("syncPick",cp.p);
    if(!/^(ghp_|github_pat_)/.test(t)&&!/^SR-[A-Za-z0-9]{20}$/.test(t)){toast("Das sieht nicht wie ein SparRadar-Code aus (beginnt mit SR-).");return}
    const pick=store.get("syncPick",null)||DEF_PICK;
    toast("Verbinde …");Sync.connect(t,pick).then(()=>{toast(`Verbunden! Geteilt: ${Sync.on().map(p=>Sync.PARTS[p].n).join(", ")||"nichts"}`);render()},err=>toast("Verbinden fehlgeschlagen: "+err.message));return}
  if(e.target.id==="eanForm"){e.preventDefault();const v=document.getElementById("eanIn").value;Scan.last=v;Scan.lookup(v);return}
  if(e.target.id==="cpForm"){e.preventDefault();
    const val=id=>document.getElementById(id).value.trim();
    const v=parseNum(val("cpVal")),k=val("cpKw").replace(/\s+/g," ");
    if(!k||!v){toast("Bitte Artikel und Wert eintragen.");return}
    const c={s:val("cpStore"),prog:val("cpProg"),k,t:val("cpType"),v,to:val("cpTo")||null};
    if(c.t==="pct"&&v>=100){toast("Ein Rabatt muss unter 100 % liegen.");return}
    S.coupons.push(c);save();
    const n=weekOffers().filter(o=>couponsFor(o).includes(c)).length;
    toast(n?`Coupon gespeichert, passt zu ${n} Angebot${n===1?"":"en"}`:"Coupon gespeichert. Gerade passt kein Angebot dazu.");render();return}
});
// Programm passend zum gewählten Markt vorschlagen
document.addEventListener("change",e=>{if(e.target.id==="cpStore")document.getElementById("cpProg").value=defaultProg(e.target.value)});
document.getElementById("q").addEventListener("input",e=>{S.q=e.target.value;S.limit=60;if(S.tab!=="offers")S.tab="offers";render();showSugg("qSugg",S.q,"q")});
document.getElementById("q").addEventListener("focus",e=>showSugg("qSugg",e.target.value,"q"));
document.addEventListener("input",e=>{if(e.target.id==="kwIn")showSugg("kwSugg",e.target.value,"kw");
  if(e.target.id==="syncToken"){const cp=codeParse(e.target.value);if(cp.p){store.set("syncPick",cp.p);
    document.querySelectorAll("[data-pick]").forEach(c=>{const on=cp.p[c.dataset.pick];c.classList.toggle("on",on);c.setAttribute("aria-pressed",on);c.textContent=(on?"✓ ":"")+Sync.PARTS[c.dataset.pick].n})}}
  if(e.target.id==="inviteName"){store.set("inviteName",e.target.value.trim());const a=document.getElementById("inviteWa");if(a)a.href=waLink(inviteText())}});
document.addEventListener("keydown",e=>{if(e.key==="Escape")hideSugg();if(e.key==="Enter"&&e.target.id==="q"){hideSugg();e.target.blur()}});
// Schrift größer (A+): vergrößert die ganze App gleichmäßig, Layout passt sich an
const ZOOM=[1,1.2,1.4],ZOOM_UI=[["A+","Schrift größer"],["A++","Schrift noch größer"],["A−","Wieder normale Schriftgröße"]];
// PC: ganze obere Leiste (Logo, A+, Woche, Reiter) bleibt beim Scrollen oben angeheftet (Handy: Reiter fest unten). Platzhalter verhindert Springen.
const TABS=document.querySelector(".pinbar"),TABS_PH=document.createElement("div");TABS_PH.className="tabs-ph";TABS.before(TABS_PH);
function pinTabs(){const desk=matchMedia("(min-width:721px)").matches,was=TABS.classList.contains("pinned");
  const pin=desk&&(was?TABS_PH:TABS).getBoundingClientRect().top<0;
  if(pin){if(!was){TABS_PH.style.height=TABS.offsetHeight+"px";TABS_PH.style.display="block"}TABS.style.left=TABS_PH.offsetLeft+"px";TABS.style.width=TABS_PH.offsetWidth+"px"}
  else if(was){TABS_PH.style.display="";TABS.style.left=TABS.style.width=""}
  if(pin!==was)TABS.classList.toggle("pinned",pin)}
addEventListener("scroll",pinTabs,{passive:true});function repin(){TABS.classList.remove("pinned");TABS_PH.style.display="";TABS.style.left=TABS.style.width="";pinTabs()}
addEventListener("resize",repin);
function applyZoom(){const i=Math.max(0,ZOOM.indexOf(store.get("zoom",1)));document.documentElement.style.zoom=ZOOM[i]>1?ZOOM[i]:"";
  const b=document.getElementById("zoomBtn");b.textContent=ZOOM_UI[i][0];b.setAttribute("aria-label",ZOOM_UI[i][1]);b.setAttribute("aria-pressed",i>0);if(window.repin)repin();return i}
// Versteckter Zugang zu den Einstellungen: SparRadar-Logo oben links ca. 1 Sekunde gedrückt halten
// (oder 5× schnell antippen). Bewusst ohne sichtbaren Knopf.
(()=>{const el=document.querySelector(".logo");let t=null,taps=0,tt=null;
  const open=()=>{S.sheet="settings";render();checkVersion()};
  el.addEventListener("pointerdown",()=>{clearTimeout(t);t=setTimeout(()=>{t=null;open()},900)});
  ["pointerup","pointerleave","pointercancel"].forEach(ev=>el.addEventListener(ev,()=>{clearTimeout(t);t=null}));
  el.addEventListener("contextmenu",e=>e.preventDefault());
  el.addEventListener("click",()=>{taps++;clearTimeout(tt);tt=setTimeout(()=>taps=0,1500);if(taps>=5){taps=0;open()}});
  el.style.userSelect="none";el.style.webkitUserSelect="none";el.style.webkitTouchCallout="none"})();
document.getElementById("zoomBtn").addEventListener("click",()=>{const i=(Math.max(0,ZOOM.indexOf(store.get("zoom",1)))+1)%ZOOM.length;store.set("zoom",ZOOM[i]);applyZoom();toast(["Normale Schriftgröße","Schrift größer","Schrift sehr groß"][i])});
applyZoom();
document.getElementById("stand").addEventListener("click",e=>{if(e.target.id!=="flyerBtn")return;const i=document.getElementById("flyerInfo");i.hidden=!i.hidden;e.target.setAttribute("aria-expanded",!i.hidden)});
document.getElementById("sort").addEventListener("change",e=>{S.sort=e.target.value;render()});
load();
history.pushState({sr:"guard"},"");   // Schutz-Eintrag für die Frage „wirklich schließen?“
// „Nach oben“-Knopf bei langen Listen
const topBtn=document.createElement("button");topBtn.id="toTop";topBtn.className="totop";topBtn.hidden=true;topBtn.setAttribute("aria-label","Nach oben");
topBtn.innerHTML='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="m6 15 6-6 6 6"/></svg>';
document.body.appendChild(topBtn);addEventListener("scroll",()=>{topBtn.hidden=scrollY<900},{passive:true});

// Bleibt die App lange offen (Windows-Fenster, Handy im Hintergrund): neue Version still neu laden,
// neue Angebote nachladen. Nie mitten in einer Eingabe oder bei offenem Fenster.
const MYV=((document.querySelector('script[src*="app.js"]')||{}).src||"").match(/v=(\d+)/)?.[1];
async function freshen(){
  if(document.hidden||S.sheet||document.activeElement?.matches("input,select,textarea"))return;
  try{
    const v=(await (await fetch("index.html",{cache:"no-store"})).text()).match(/app\.js\?v=(\d+)/)?.[1];
    if(v&&MYV&&v!==MYV){location.reload();return}
    const o=await (await fetch("data/stand.json",{cache:"no-store"})).json();  // winzig, statt jedes Mal alle Angebote zu laden
    if(o.generated&&o.generated!==META.generated)load();
  }catch(e){}
}
setInterval(freshen,5*60*1000);
// Samstag 22 Uhr: offene App wechselt von selbst auf die Angebote ab Montag
setInterval(()=>{if(shopFrom()!==SHOP)location.reload()},60*1000);
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&Date.now()-(freshen.last||0)>60*1000){freshen.last=Date.now();freshen()}});
document.addEventListener("visibilitychange",()=>{if(!document.hidden)Sync.pull()});
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&S.checked.length&&(S.list.length||S.extra.length))wakeOn()});
