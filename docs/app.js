"use strict";
// SparRadar – Anzeige der täglich abgerufenen Angebote (docs/data/offers.json)

const STORES = {
  lidl:   {n:"Lidl",          m:"Li", c:"#2F6FE4", app:"Lidl Plus",  link:"https://www.lidl.de/", dom:"lidl.de"},
  aldi:   {n:"Aldi Süd",      m:"AS", c:"#1590B5",                   link:"https://www.aldi-sued.de/de/angebote.html", dom:"aldi-sued.de"},
  rewe:   {n:"Rewe",          m:"Re", c:"#D9363E", app:"Rewe Bonus", link:"https://www.kaufda.de/Woerth-am-Rhein/REWE/p-r101", dom:"rewe.de"},
  netto:  {n:"Netto",         m:"Ne", c:"#C99400", app:"Netto App",  link:"https://www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9", dom:"netto-online.de"},
  edeka:  {n:"Edeka Jockgrim",m:"Ed", c:"#1F5FAF", app:"Payback",    link:"https://www.kaufda.de/Jockgrim/EDEKA/p-r107", dom:"edeka.de"},
  scheck: {n:"Scheck-In",     m:"SI", c:"#2E9E5B", app:"Payback",    link:"https://www.scheck-in.de/", manual:true, dom:"scheck-in.de"},
  serpa:  {n:"Serpa Markt",   m:"Se", c:"#D97A12",                   link:"https://www.google.com/search?q=Serpa+Markt+W%C3%B6rth+am+Rhein+Prospekt", manual:true},
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
const S = {tab:"offers",week:0,q:"",stores:new Set(),cat:null,sort:"off",useApp:store.get("useApp",true),
  watch:store.get("watch2",[{k:"Katzenfutter",max:6},{k:"Butter"},{k:"Kaffee"}]),list:store.get("list",[]),
  manual:store.get("manual",[]),coupons:store.get("coupons",[]),extra:store.get("extra",[]),checked:store.get("checked",[]),sheet:null,limit:60};
let OFFERS = [], HIST = {}, META = {}, NAMES = [], APPV = {};
// lokales Datum (nicht UTC), sonst gilt nach Mitternacht noch der Vortag
const TODAY = (d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`)(new Date());

// ---------- Helfer ----------
const eur = v => (v<0?"−":"")+Math.abs(v).toFixed(2).replace(".",",")+" €";
const norm = s => (s||"").toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss").replace(/[^a-z0-9]/g,"");
// nur echte https-Links zulassen (Schutz, falls eine Quelle einmal kaputte oder manipulierte Daten liefert)
const safeUrl = u => /^https:\/\//i.test(u||"") ? u : "";
const esc = s => String(s??"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const parseNum = s => {const v=parseFloat(String(s||"").replace(",","."));return isFinite(v)&&v>0?v:null};
const fmtDate = d => d ? new Date(d+"T12:00:00").toLocaleDateString("de-DE",{weekday:"short",day:"2-digit",month:"2-digit"}) : "";
// Markt-Logo: das Website-Symbol des Markts (wird beim Öffnen geladen, liegt nicht im Repo).
// Lädt es nicht, bleibt das farbige Kürzel darunter sichtbar.
const logoUrl = s => STORES[s]?.dom ? `https://www.google.com/s2/favicons?domain=${STORES[s].dom}&sz=64` : "";
const sb = (s,lg) => `<span class="sb${lg?" lg":""}" style="--c:${(STORES[s]||{}).c||"#888"}" aria-hidden="true">${(STORES[s]||{}).m||"?"}${logoUrl(s)?`<img src="${logoUrl(s)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-logo="1">`:""}</span>`;
const sname = s => (STORES[s]||{}).n || s;
let tt; function toast(m){const t=document.getElementById("toast");t.textContent=m;t.hidden=false;clearTimeout(tt);tt=setTimeout(()=>t.hidden=true,2600)}
const save = () => {store.set("watch2",S.watch);store.set("list",S.list);store.set("useApp",S.useApp);store.set("manual",S.manual);store.set("coupons",S.coupons);store.set("extra",S.extra);store.set("checked",S.checked);Sync.changed()};

// ---------- Geräte verbinden (Handy <-> PC) ----------
// Merkliste, Einkaufszettel, Coupons und eigene Angebote liegen zusätzlich in einem geheimen Gist im
// GitHub-Konto des Nutzers. Der Schlüssel (nur Recht "gist") bleibt auf dem Gerät, nie im Repo.
const Sync = {
  API:"https://api.github.com", FILE:"sparradar-sync.json", DESC:"SparRadar-Sync (Merkliste, Einkaufszettel, Coupons)",
  cfg(){return store.get("sync",null)}, timer:null, busy:false, status:"",
  data(){return {watch:S.watch,list:S.list,manual:S.manual,coupons:S.coupons,extra:S.extra,checked:S.checked}},
  snap(){return JSON.stringify(this.data())},
  async req(path,opt={}){const c=this.cfg();const r=await fetch(this.API+path,{...opt,cache:"no-store",headers:{Authorization:"Bearer "+c.token,Accept:"application/vnd.github+json",...(opt.body?{"Content-Type":"application/json"}:{})}});
    if(r.status===401)throw new Error("Schlüssel ungültig oder abgelaufen");if(!r.ok)throw new Error("GitHub antwortet nicht ("+r.status+")");return r.json()},
  apply(d){S.watch=d.watch||[];S.list=d.list||[];S.manual=d.manual||[];S.coupons=d.coupons||[];S.extra=d.extra||[];S.checked=d.checked||[];
    store.set("extra",S.extra);store.set("checked",S.checked);
    store.set("watch2",S.watch);store.set("list",S.list);store.set("manual",S.manual);store.set("coupons",S.coupons);
    OFFERS=OFFERS.filter(o=>!o.manual).concat(manualOffers())},
  // beide Seiten geändert: nichts verlieren, alles zusammenführen
  merge(a,b){const u=(x,y,k)=>{const m=new Map();[...x,...y].forEach(e=>m.set(k(e),e));return [...m.values()]};
    return {watch:u(a.watch||[],b.watch||[],w=>norm(w.k)),list:[...new Set([...(a.list||[]),...(b.list||[])])],
      manual:u(a.manual||[],b.manual||[],m=>m.id),coupons:u(a.coupons||[],b.coupons||[],c=>[c.s,c.k,c.t,c.v,c.to].join("|")),
      extra:u(a.extra||[],b.extra||[],x=>x.id),checked:[...new Set([...(a.checked||[]),...(b.checked||[])])]}},
  async connect(token){store.set("sync",{token});
    try{const gs=await this.req("/gists?per_page=100");let g=gs.find(x=>x.description===this.DESC&&x.files[this.FILE]);
      if(!g)g=await this.req("/gists",{method:"POST",body:JSON.stringify({description:this.DESC,public:false,files:{[this.FILE]:{content:JSON.stringify({updatedAt:Date.now(),data:this.data()})}}})});
      store.set("sync",{token,gist:g.id});store.set("syncSnap",null);store.set("syncRemoteAt",0);await this.pull(true);return true}
    catch(e){store.set("sync",null);throw e}},
  disconnect(){store.set("sync",null);store.set("syncSnap",null);this.status=""},
  async pull(first){const c=this.cfg();if(!c?.gist||this.busy)return;this.busy=true;
    try{const g=await this.req("/gists/"+c.gist);const f=g.files[this.FILE];
      const raw=f.truncated?await (await fetch(f.raw_url,{cache:"no-store"})).text():f.content;const remote=JSON.parse(raw||"{}");
      const remoteNew=(remote.updatedAt||0)>store.get("syncRemoteAt",0),localNew=this.snap()!==store.get("syncSnap",null);
      if(remoteNew&&remote.data){
        if(localNew&&!first){this.apply(this.merge(remote.data,this.data()));this.busy=false;return this.push()}
        if(first){this.apply(this.merge(remote.data,this.data()))}else this.apply(remote.data);
        store.set("syncRemoteAt",remote.updatedAt);store.set("syncSnap",this.snap());
        if(first){this.busy=false;return this.push()}
        render()}
      else if(localNew){this.busy=false;return this.push()}
      this.ok()}
    catch(e){this.fail(e)}finally{this.busy=false}},
  async push(){const c=this.cfg();if(!c?.gist)return;if(this.busy){this.changed();return}this.busy=true;
    try{const at=Date.now();await this.req("/gists/"+c.gist,{method:"PATCH",body:JSON.stringify({files:{[this.FILE]:{content:JSON.stringify({updatedAt:at,data:this.data()})}}})});
      store.set("syncRemoteAt",at);store.set("syncSnap",this.snap());this.ok()}
    catch(e){this.fail(e)}finally{this.busy=false}},
  changed(){if(!this.cfg()?.gist)return;clearTimeout(this.timer);this.timer=setTimeout(()=>this.push(),1500)},
  ok(){this.status="Verbunden · abgeglichen "+new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})+" Uhr";const el=document.getElementById("syncState");if(el)el.textContent=this.status},
  fail(e){this.status="Abgleich fehlgeschlagen: "+e.message;const el=document.getElementById("syncState");if(el)el.textContent=this.status}
};

function histOf(o){const rows=HIST[o.s+"|"+norm(o.n).slice(0,40)]||[];return rows.filter(r=>r[0]<(o.from||TODAY)).map(r=>r[1])}
// Referenzpreis für "Ersparnis": statt-Preis, sonst Durchschnitt aus dem Verlauf, sonst Angebotspreis
function ref(o){if(o.o)return o.o;const h=histOf(o);return h.length>=3?Math.max(o.p,h.reduce((a,b)=>a+b,0)/h.length):o.p}
function steps(o){if(!o.p)return [{l:"Bonus-Aktion",v:0,t:"base"}]; // Rewe-Bonus ohne Preis im Prospekt
  const st=[{l:o.o?"Normalpreis":"Angebotspreis",v:o.o||o.p,t:"base"}];
  if(o.o)st.push({l:"Angebot",v:o.p-o.o,t:"of"});
  if(S.useApp){if(o.ap)st.push({l:(STORES[o.s]||{}).app?STORES[o.s].app+" App-Preis":"App-Preis",v:o.ap-o.p,t:"app"});(o.x||[]).forEach(([t,l,v])=>st.push({l,v:-v,t}))
    // eigene Coupons: werden in der eingetragenen Reihenfolge auf den jeweils aktuellen Preis angewendet
    couponsFor(o).forEach(c=>{const cur=st.reduce((a,s)=>a+s.v,0),d=cpValue(c,cur);if(d>0.004)st.push({l:cpLabel(c),v:-d,t:c.t==="punkte"||c.prog==="Cashback-App"?"cb":"coupon"})})}
  return st}

// ---------- Meine Coupons ----------
const PROGS = ["Lidl Plus","Rewe Bonus","Payback","Netto App","Edeka App","dm App","Cashback-App","Hersteller-Coupon","Sonstiges"];
const CP_TYPES = {euro:"€ Rabatt / Guthaben",pct:"% Rabatt",preis:"Coupon-Preis (zahlst nur …)",punkte:"Payback-Extrapunkte"};
const defaultProg = s => ({lidl:"Lidl Plus",rewe:"Rewe Bonus",netto:"Payback",edeka:"Payback",scheck:"Payback",dm:"dm App",all:"Cashback-App"})[s]||"Sonstiges";
const cpActive = c => !c.to || c.to>=TODAY;
const couponsFor = o => S.coupons.filter(c=>cpActive(c)&&(c.s==="all"||c.s===o.s)&&c.k.split(/\s+/).every(w=>matches(o,w)));
function cpValue(c,cur){
  if(c.t==="euro")return c.v;
  if(c.t==="pct")return Math.round(cur*c.v)/100;
  if(c.t==="preis")return Math.max(0,cur-c.v);
  if(c.t==="punkte")return c.v/100; // 1 Payback-Punkt = 1 Cent
  return 0}
function cpValueTxt(c){return c.t==="euro"?"−"+eur(c.v):c.t==="pct"?`−${String(c.v).replace(".",",")} %`:c.t==="preis"?"für "+eur(c.v):`${c.v} Extra-°P`}
const cpLabel = c => `${c.prog} ${cpValueTxt(c)}`;
const fin = o => Math.round(steps(o).reduce((a,s)=>a+s.v,0)*100)/100;
const offPct = o => {const r=ref(o);return r>0?Math.max(0,Math.round((1-fin(o)/r)*100)):0};
const unit = o => o.gp ? o.gp.v*(fin(o)/o.p) : null;
const unitTxt = o => o.gp ? `1 ${o.gp.u} = ${eur(unit(o))}` : "";
// Suche: Artikelname, Marke und Markt. Die Beschreibung nur als Notlösung, der Kategoriename nie
// (sonst findet „Milch“ alles aus „Milch, Käse & Eier“).
const hay = o => o._hay ??= norm([o.n,o.b,sname(o.s)].join(" "));
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
function watchMatch(o,k){
  if(matches(o,k))return true;
  const t=wTokens(k);if(!t.length)return false;
  const txt=hay(o)+" "+hayD(o);
  if(t.every(x=>txt.includes(x)))return true;
  return t.length>1&&t[0].length>=4&&!WATCH_WEAK.has(t[0])&&txt.includes(t[0])&&/versch|sorten|oderweitere/.test(norm(o.d)+norm(o.n))}
const hitW = (o,w) => watchMatch(o,w.k) && (!w.max || (unit(o)!=null && unit(o)<=w.max+1e-9));
const TOMORROW=(d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`)(new Date(Date.now()+864e5));
const validTxt = o => o.from && o.from>TODAY ? "ab "+fmtDate(o.from) : o.to===TODAY ? "nur noch heute" : o.to===TOMORROW ? "nur noch bis morgen" : o.to ? "bis "+fmtDate(o.to) : "";
const tagHTML = v => {v=Math.max(v,0);const e=Math.floor(v+1e-9),c=Math.round((v-e)*100);return `<span class="eu">${e||"-"}</span><span class="ct">.${String(c).padStart(2,"0")}</span>`};
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
const imgTag = (o,cls="") => safeUrl(o.img) ? `<img src="${esc(sharp(o.img))}" alt="${esc(o.n)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" class="${cls}" data-cat="${o.c}">` : (ILL[o.c]||ILL.sonstiges);
function thumb(o,big){return `<div class="thumb" style="--cc:${CC[o.c]||CC.sonstiges}">${imgTag(o)}${big?"":sb(o.s)}${offPct(o)?`<span class="off">−${offPct(o)} %</span>`:""}</div>`}

// ---------- Daten ----------
const weekOffers = () => OFFERS.filter(o => S.week ? (o.from && o.from>TODAY) : (!o.from || o.from<=TODAY));
function filtered(){
  let r=weekOffers();
  if(S.stores.size)r=r.filter(o=>S.stores.has(o.s));
  if(S.cat)r=r.filter(o=>o.c===S.cat);
  const qt=S.q.trim().split(/\s+/).filter(Boolean);if(qt.length)r=searchOffers(r,S.q);
  const f0={off:(a,b)=>offPct(b)-offPct(a)||fin(a)-fin(b),gp:(a,b)=>((unit(a)??1e9)-(unit(b)??1e9)),p:(a,b)=>((a.p>0?fin(a):1e9)-(b.p>0?fin(b):1e9))}[S.sort];
  // immer zuerst nach der gewählten Sortierung (Standard: stärkster Rabatt), bei Gleichstand der passendere Name
  const f=qt.length?(a,b)=>f0(a,b)||relevance(a,qt)-relevance(b,qt):f0;
  return r.sort(f)}
const score = o => {const v=verdict(o).t;return offPct(o)+(v==="low"?8:0)-(v==="fake"?40:0)+(S.useApp?((o.x||[]).length+couponsFor(o).length)*3+(o.ap?3:0):0)};
const ranked = () => weekOffers().filter(o=>o.p>0).sort((a,b)=>score(b)-score(a));
const watchHits = wk => S.watch.map(w=>({w,hits:OFFERS.filter(o=>(wk==null||(wk?o.from>TODAY:!o.from||o.from<=TODAY))&&hitW(o,w))}));

function manualOffers(){return S.manual.filter(m=>!m.to||m.to>=TODAY).map(m=>({...m,src:"selbst eingetragen",manual:true}))}
async function load(){
  try{
    const [o,h,nm]=await Promise.all([fetch("data/offers.json",{cache:"no-store"}).then(r=>r.json()),fetch("data/history.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({})),fetch("data/names.json",{cache:"no-store"}).then(r=>r.json()).catch(()=>({}))]);
    NAMES=Object.keys(nm||{});
    fetch("app-version.json",{cache:"no-store"}).then(r=>r.json()).then(v=>{APPV=v||{};render()}).catch(()=>{});
    META=o;HIST=h;
    OFFERS=o.offers.filter(x=>!x.to||x.to>=TODAY).concat(manualOffers());
    const g=new Date(o.generated);
    const pr=flyerInfo();
    document.getElementById("stand").innerHTML=`Wörth am Rhein · Stand ${g.toLocaleDateString("de-DE",{weekday:"short",day:"2-digit",month:"2-digit"})}, ${g.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})} Uhr · ${OFFERS.length} Angebote${pr.sum?`<br><button class="flyer" id="flyerBtn" aria-expanded="false">${pr.sum}</button>`:""}`;
    document.getElementById("flyerInfo").innerHTML=pr.rows;
  }catch(e){
    OFFERS=manualOffers();
    document.getElementById("stand").textContent="Wörth am Rhein · Angebote konnten nicht geladen werden";
    toast("Angebote konnten nicht geladen werden. Bitte später neu öffnen.");
  }
  OFFERS.forEach(o=>{if(!o.id)o.id="m-"+norm(o.n)+"-"+o.p});
  const before=S.coupons.length;S.coupons=S.coupons.filter(cpActive);if(S.coupons.length!==before)save(); // abgelaufene Coupons aufräumen
  render();  if(OFFERS.length)checkNews();
  checkWhatsNew(); // nur wenn kein anderes Fenster offen ist, sonst beim nächsten Öffnen
  Sync.pull(); // Listen vom anderen Gerät holen (nur wenn verbunden)
}
// Wie aktuell sind die Prospekte? Häufigster Zeitraum je Markt, dazu wann die nächsten starten
function flyerInfo(){
  const mode=a=>{const c={};a.forEach(x=>{if(x)c[x]=(c[x]||0)+1});return Object.entries(c).sort((x,y)=>y[1]-x[1])[0]?.[0]};
  const d=x=>new Date(x+"T12:00:00").toLocaleDateString("de-DE",{day:"2-digit",month:"2-digit"});
  const wd=x=>new Date(x+"T12:00:00").toLocaleDateString("de-DE",{weekday:"short"}).replace(".","")+" "+d(x);
  // Wochenprospekt = Enddatum in den nächsten 8 Tagen (Dauerangebote bis Jahresende zählen nicht)
  const soon=new Date(Date.now()+8*864e5).toISOString().slice(0,10),week=a=>{const w=a.filter(o=>o.to&&o.to<=soon);return w.length?w:a};
  const auto=OFFERS.filter(o=>!o.manual),now=auto.filter(o=>!o.from||o.from<=TODAY),next=auto.filter(o=>o.from&&o.from>TODAY);
  const to=mode(week(now).map(o=>o.to)),nf=next.map(o=>o.from).sort()[0];
  const sum=[to?"Prospekte bis "+wd(to):"",nf?"neue ab "+wd(nf):""].filter(Boolean).join(" · ");
  const rows=Object.keys(STORES).filter(s=>auto.some(o=>o.s===s)).map(s=>{
    const n=week(now.filter(o=>o.s===s)),f=mode(n.map(o=>o.from)),t=mode(n.map(o=>o.to)),nx=next.filter(o=>o.s===s).map(o=>o.from).sort()[0];
    return `<span>${sb(s)}${esc(sname(s))}: ${f&&t?d(f)+"–"+d(t):t?"bis "+d(t):"laufend"}${nx?` · neu ab ${d(nx)}`:""}</span>`}).join("");
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
  fetch("data/catalog.json").then(r=>r.json()).then(a=>{CATALOG=Array.isArray(a)?a:[];CATALOG_N=CATALOG.map(norm);then&&then()}).catch(()=>{CATALOG=[];CATALOG_N=[]})}
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
  return `<div class="sugg" role="listbox" aria-label="Vorschläge">${list.map(x=>`<button type="button" role="option" data-sugg="${kind}" data-v="${esc(x.t)}"><span>${esc(x.t)}</span>${x.n?`<em class="on">${x.n} im Angebot</em>`:`<em>nicht im Angebot</em>`}</button>`).join("")}</div>`}
function showSugg(id,q,kind){const el=document.getElementById(id);if(!el)return;el.innerHTML=suggHTML(q,kind);
  if(!CATALOG)loadCatalog(()=>{const inp=document.getElementById(kind==="q"?"q":"kwIn");if(inp&&document.activeElement===inp)showSugg(id,inp.value,kind)})}
const hideSugg=()=>["qSugg","kwSugg"].forEach(id=>{const el=document.getElementById(id);if(el)el.innerHTML=""});

// ---------- Teilen ----------
const APP_URL="https://tiry38.github.io/sparradar/",APK_URL="https://github.com/Tiry38/sparradar/releases/download/apps/SparRadar-App.apk";
// wa.me öffnet WhatsApp (Handy-App bzw. WhatsApp Web am PC), dort nur noch den Kontakt antippen
const waLink = t => "https://wa.me/?text="+encodeURIComponent(t);
const SHARE_TXT = `Schau mal: SparRadar zeigt alle Angebote rund um Wörth am Rhein (Lidl, Aldi, Rewe, Netto, Edeka, dm) 🛒\n${APP_URL}\n\nAls Android-App zum Installieren:\n${APK_URL}`;
function listText(){const items=S.list.map(byId).filter(Boolean),g={};items.forEach(o=>(g[o.s]=g[o.s]||[]).push(o));
  const ex=S.extra.length?"\n\nSONSTIGES\n"+S.extra.map(x=>"- "+x.n).join("\n"):"";
  return "🛒 Einkaufszettel\n\n"+Object.entries(g).map(([s,os])=>sname(s).toUpperCase()+"\n"+os.map(o=>`- ${o.n}${o.d?" ("+o.d+")":""} ${eur(fin(o))}${comboLabels(o).length?" mit "+comboLabels(o).join(" + "):""}`).join("\n")).join("\n\n")+ex}
const WA_ICON='<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></svg>';

// ---------- Ansichten ----------
function card(o,bestIds){
  const fav=S.watch.some(w=>norm(w.k)===norm(o.n)),inL=S.list.includes(o.id),vd=verdict(o),cl=comboLabels(o);
  // App-Preis direkt beim Preis: „Lidl Plus App-Preis 1,49 €“; mehrere Vorteile zusammen = „Mit Kombi“
  const combo=cl.length?`<div class="combo"><div class="top">${IC.layers} ${cl.length===1?esc(cl[0]):"Mit Kombi"}<b>${eur(fin(o))}</b></div>${cl.length>1?`<div class="src">${cl.map(esc).join(" + ")}</div>`:""}</div>`:"";
  return `<article class="card" data-detail="${esc(o.id)}" tabindex="0" aria-label="${esc(o.n)}: Details anzeigen">${thumb(o)}
   <div class="body">
   <span class="store">${esc(sname(o.s))}${o.b?" · "+esc(o.b):""}</span>
   ${o.manual?'<span class="manual">selbst eingetragen</span>':""}
   <div class="name">${esc(o.n)}<small>${esc(o.d||"")}</small></div>
   ${o.ao?`<span class="aonly">${IC.bag}Preis nur mit ${esc(o.ao)}</span>`:""}
   <div class="pricerow">${o.bo?`<div class="bonustag"><b>${eur(o.bo)}</b><small>Bonus-Guthaben</small></div>`:`<div class="tag" aria-label="${eur(o.p)}">${tagHTML(o.p)}</div>`}
     <div class="was">${o.o?`<s>statt ${eur(o.o)}</s>`:""}<span class="gp">${unitTxt(o)}</span>${bestIds.has(o.id)?'<br><span class="best">Bester Grundpreis</span>':""}</div></div>
   <div class="hist ${vd.t}" title="${esc(vd.l)}">${spark(o)}${vd.s}</div>
   ${combo}
   <div class="card-foot"><span class="valid${o.to===TODAY||o.to===TOMORROW?" last":""}">${validTxt(o)}</span>
     <button class="ibtn" data-fav="${esc(o.id)}" aria-pressed="${fav}" aria-label="${fav?"Von Merkliste entfernen":"Auf Merkliste setzen"}" title="Merken">${IC.star}</button>
     <button class="ibtn add" data-add="${esc(o.id)}" aria-pressed="${inL}" aria-label="${inL?"Vom Einkaufszettel nehmen":"Auf den Einkaufszettel"}" title="Einkaufszettel">${inL?IC.check:IC.plus}</button></div>
   </div></article>`}

function kracherBtn(){const k=ranked()[0];if(!k)return"";
  return `<button class="kracher" id="openK" aria-label="Kracher öffnen">
   <span class="boom">${IC.flame}</span>
   <span><span class="eyebrow">Kracher ${S.week?"demnächst":"der Woche"}</span><span class="what" style="display:block">${esc(k.n)} bei ${esc(sname(k.s))}</span><span class="how" style="display:block">${comboLabels(k).length?"Kombi: "+comboLabels(k).join(" + "):verdict(k).fresh?[ref(k)>fin(k)?"statt "+eur(ref(k)):"",validTxt(k)].filter(Boolean).join(" · "):verdict(k).l} · antippen für Details</span></span>
   <span class="big"><b>${eur(fin(k))}</b>${offPct(k)?`<span>−${offPct(k)} %</span>`:""}</span></button>`}

function renderOffers(){
  if(!OFFERS.length)return `<div class="empty"><b>Noch keine Angebote</b>Sobald der tägliche Abruf gelaufen ist, erscheinen hier die Angebote.</div>`;
  const r=filtered(),bestIds=new Set();
  if((S.q.trim()||S.cat)&&r.length>1){const by={};r.forEach(o=>{if(unit(o)==null)return;const k=o.gp.u;if(!by[k]||unit(o)<unit(by[k]))by[k]=o});Object.values(by).forEach(o=>bestIds.add(o.id))}
  const hitCount=new Set(watchHits(S.week).flatMap(x=>x.hits.map(o=>o.id))).size;
  const title=S.q.trim()?`„${esc(S.q.trim())}“ im Angebot`:S.cat?CATS[S.cat]:(S.week?"Angebote, die bald starten":"Angebote, die jetzt gelten");
  const shown=r.slice(0,S.limit);
  return `${kracherBtn()}
   ${hitCount?`<button class="alertbar" id="goWatch">${IC.bell}${hitCount} Angebote passen zu deiner Merkliste</button>`:""}
   <div class="meta"><h2>${title}</h2><span>${r.length} von ${weekOffers().length} Angeboten</span></div>
   ${r.length?`<div class="grid">${shown.map(o=>card(o,bestIds)).join("")}</div>${r.length>shown.length?`<button class="btn ghost more" id="more">${r.length-shown.length} weitere anzeigen</button>`:""}`:
    `<div class="empty"><b>Gerade nicht im Angebot</b>Setz den Begriff auf deine Merkliste. Sobald ein Markt ihn reduziert, siehst du es dort.<br><br><button class="btn" id="watchFromSearch">${IC.bell} „${esc(S.q.trim()||"Suche")}“ beobachten</button></div>`}
   ${S.q.trim()?moreArticles(r):""}
   <div class="demo">${IC.bag}<span><b>Quellen:</b> Lidl und Aldi Süd direkt von deren Websites, Rewe, Netto, Edeka Jockgrim und dm aus den Prospekten bei kaufDA. Gezeigt werden alle Angebote: Lebensmittel, Getränke, Drogerie und auch Haushalt, Technik, Mode, Garten und mehr. Scheck-In und Serpa trägst du über „+ Angebot eintragen“ selbst ein. Persönliche App-Coupons kann SparRadar nicht sehen. Prüfe sie vor dem Einkauf in der jeweiligen App.</span></div>`}

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

// ---------- Detailansicht eines Artikels ----------
// hochaufgelöste Prospektseite (kaufDA): dort ist auch Kleingedrucktes lesbar
const pageImg = o => o.bid&&o.pg&&/^[0-9a-f-]{20,}$/i.test(o.bid) ? `https://content-media.bonial.biz/${o.bid}/zoomlarge_page_${+o.pg}.jpg` : "";
const dImages = o => [...new Set([o.il||o.img,o.img,...(o.ims||[])].filter(u=>safeUrl(u)).map(sharp))];
function renderDetail(){
  const o=byId(S.detail);if(!o)return `<div class="sheet"><div class="sheet-h"><h2>Artikel</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div><div class="empty"><b>Nicht mehr im Angebot</b></div></div>`;
  const ims=dImages(o),cur=ims[Math.min(S.dImg||0,ims.length-1)],inL=S.list.includes(o.id),fav=S.watch.some(w=>norm(w.k)===norm(o.n)),vd=verdict(o),st=steps(o);
  const hist=(HIST[o.s+"|"+norm(o.n).slice(0,40)]||[]).slice(-8).reverse();
  const share=`${o.n}${o.b?" ("+o.b+")":""} bei ${sname(o.s)}: ${o.bo?eur(o.bo)+" Bonus":eur(fin(o))}${offPct(o)?` (−${offPct(o)} %)`:""}${validTxt(o)?", "+validTxt(o):""}\n\nGefunden mit SparRadar: ${APP_URL}`;
  const link=safeUrl(o.url)||STORES[o.s]?.link||"";
  return `<div class="sheet detail" role="dialog" aria-modal="true" aria-label="${esc(o.n)}">
   <div class="sheet-h">${sb(o.s,true)}<h2>${esc(sname(o.s))}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <div class="dpic" style="--cc:${CC[o.c]||CC.sonstiges}">${cur?`<button class="dzoom" data-zoom="${esc(cur)}" aria-label="Bild groß anzeigen"><img src="${esc(cur)}" alt="${esc(o.n)}" referrerpolicy="no-referrer" data-cat="${o.c}"></button>`:(ILL[o.c]||ILL.sonstiges)}${offPct(o)?`<span class="off">−${offPct(o)} %</span>`:""}${cur?`<span class="zhint">Antippen zum Vergrößern</span>`:""}</div>
   ${ims.length>1?`<div class="dthumbs">${ims.map((u,i)=>`<button data-dimg="${i}" aria-pressed="${u===cur}" aria-label="Bild ${i+1}"><img src="${esc(u)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-thumb="1"></button>`).join("")}</div>`:""}
   <div class="dinfo">
    ${o.b?`<span class="store">${esc(o.b)}</span>`:""}
    <h3 class="dtitle">${esc(o.n)}</h3>
    ${o.d?`<p class="dsub">${esc(o.d)}</p>`:""}
    ${o.ao?`<span class="aonly">${IC.bag}Preis nur mit ${esc(o.ao)}</span>`:""}
    <div class="dprice">${o.bo?`<div class="bonustag"><b>${eur(o.bo)}</b><small>Bonus-Guthaben</small></div>`:`<div class="tag xl">${tagHTML(fin(o))}</div>`}
     <div>${ref(o)>fin(o)&&!o.bo?`<s>statt ${eur(ref(o))}</s><br><b style="color:var(--save)">Du sparst ${eur(ref(o)-fin(o))}</b>`:""}${unitTxt(o)?`<div class="gp">${esc(unitTxt(o))}</div>`:""}</div></div>
    ${st.length>1?`<div class="stack">${st.map((x,i)=>i===0?`<div><span>${esc(x.l)}</span><span>${eur(x.v)}</span></div>`:`<div class="neg"><span>− ${esc(x.l)}</span><span>${eur(x.v)}</span></div>`).join("")}<div class="res"><span>Du zahlst effektiv</span><span>${eur(fin(o))}</span></div></div>`:""}
    <dl class="dfacts">
     <dt>Gültig</dt><dd>${o.from&&o.to?fmtDate(o.from)+" – "+fmtDate(o.to):validTxt(o)||"laufend"}${o.to===TODAY?' <b class="last">nur noch heute</b>':""}</dd>
     <dt>Markt</dt><dd>${esc(sname(o.s))}</dd>
     ${o.pg?`<dt>Prospekt</dt><dd>Seite ${esc(o.pg)}</dd>`:""}
     ${o.cat?.length?`<dt>Kategorie</dt><dd>${o.cat.map(esc).join(" › ")}</dd>`:`<dt>Kategorie</dt><dd>${esc(CATS[o.c]||"")}</dd>`}
     <dt>Quelle</dt><dd>${esc(o.src||"")}</dd>
    </dl>
    ${o.inf?`<div class="dtext"><h4>Beschreibung</h4><p>${esc(o.inf)}</p></div>`:""}
    <div class="verdict ${vd.t}">${spark(o,90,24)}<span>${esc(vd.l)}</span></div>
    ${hist.length?`<div class="dtext"><h4>Preisverlauf</h4><ul class="dhist">${hist.map(([d,p])=>`<li><span>${fmtDate(d)}</span><b>${eur(p)}</b></li>`).join("")}</ul></div>`:""}
    <div class="dactions">
     <button class="btn" data-add="${esc(o.id)}">${inL?IC.check+"Auf dem Zettel":IC.plus+"Auf den Einkaufszettel"}</button>
     <button class="btn ghost" data-fav="${esc(o.id)}">${IC.star}${fav?"Gemerkt":"Merken"}</button>
     ${pageImg(o)?`<button class="btn ghost" data-zoom="${esc(pageImg(o))}">📄 Prospektseite ${esc(o.pg)} ansehen</button>`:""}
     <a class="btn wa" href="${waLink(share)}" target="_blank" rel="noopener">${WA_ICON}Teilen</a>
     ${link?`<a class="btn ghost" href="${esc(link)}" target="_blank" rel="noopener">Beim Händler ansehen</a>`:""}
    </div>
   </div>
  </div>`}
function renderLightbox(){const u=S.lightbox,pg=/zoomlarge_page_/.test(u||"");return u?`<div class="lightbox${pg?" pg":""}" id="lightbox" role="dialog" aria-label="Bild groß"><img src="${esc(u)}" alt="" referrerpolicy="no-referrer"${pg?' class="page"':""}><button class="ibtn lbclose" id="lbClose" aria-label="Schließen">${IC.x}</button></div>`:""}

// ---------- „Was ist neu“ nach einem Update ----------
// Bei jeder neuen Version hier oben einen Eintrag ergänzen (Schlüssel = Nummer aus app.js?v= in index.html)
const CHANGES={
  42:["Detailansicht: „Prospektseite ansehen“ zeigt die ganze Prospektseite gestochen scharf – mit zwei Fingern heranzoomen."],
  41:["Update-Fenster sieht sauber aus, Bilder schärfer."],
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
  if(last==null&&!WAS_USER){store.set("seenVersion",MYV);return}
  if(S.sheet)return;
  if(String(last)===String(MYV))return;
  const vs=Object.keys(CHANGES).map(Number).sort((a,b)=>b-a);
  let pick=vs.filter(v=>v>(+last||0)&&v<=+MYV);
  if(!pick.length)pick=vs.filter(v=>v<=+MYV).slice(0,1);
  S.whatsNew=pick.flatMap(v=>CHANGES[v]).slice(0,7);
  store.set("seenVersion",MYV);S.sheet="whatsnew";render()}
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
  const seen=new Set(store.get("seenHits",[])),fresh=hits.filter(o=>!seen.has(o.id));
  store.set("seenHits",hits.map(o=>o.id));
  if(!fresh.length)return;
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
  const top=S.useApp?r.filter(o=>o!==k&&((o.x||[]).length||o.ap||couponsFor(o).length)).slice(0,5):[];
  const rest=r.filter(o=>o!==k&&!top.includes(o)).slice(0,8-top.length);
  const lows=r.filter(o=>verdict(o).t==="low").slice(0,5),fakes=weekOffers().filter(o=>verdict(o).t==="fake").slice(0,5);
  const plan=weekPlan();
  const drow=o=>`<div class="drow" data-detail="${esc(o.id)}"><div class="mini" style="--cc:${CC[o.c]||CC.sonstiges}">${imgTag(o)}</div>
    <div class="t">${esc(o.n)}<small>${esc(sname(o.s))}${o.b?" · "+esc(o.b):""} · ${esc(o.d||"")}</small><div class="pills">${offPct(o)?`<span class="pill of">−${offPct(o)} %</span>`:""}${steps(o).filter(s=>!["base","of"].includes(s.t)).map(s=>`<span class="pill ${s.t==="cb"?"cb":""}">${esc(s.l)}</span>`).join("")}</div></div>
    <div class="pr"><b>${eur(fin(o))}</b>${ref(o)>fin(o)?`<s>${eur(ref(o))}</s>`:""}</div></div>`;
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Kracher">
   <div class="sheet-h"><span style="width:38px;height:38px;border-radius:11px;background:#E5332A;color:#FFE27A;display:grid;place-items:center;transform:rotate(-8deg)">${IC.flame}</span><h2>Kracher ${S.week?"demnächst":"der Woche"}</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <section class="hero">${thumb(k,true)}
    <div class="info">
     <div class="store" style="gap:9px">${sb(k.s,true)}${esc(sname(k.s))} · ${validTxt(k)}</div>
     <h3>${esc(k.n)}<small>${esc([k.b,k.d,unitTxt(k)].filter(Boolean).join(" · "))}</small></h3>
     <div style="display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap"><div class="tag xl">${tagHTML(fin(k))}</div>${ref(k)>fin(k)?`<div class="was" style="text-align:left"><s>statt ${eur(ref(k))}</s><b style="color:var(--save);font-size:1rem">Du sparst ${eur(ref(k)-fin(k))} (${offPct(k)} %)</b></div>`:""}</div>
     <div class="stack">${st.map((s,i)=>i===0?`<div><span>${esc(s.l)}</span><span>${eur(s.v)}</span></div>`:`<div class="neg"><span>− ${esc(s.l)}</span><span>${eur(s.v)}</span></div>`).join("")}<div class="res"><span>Du zahlst effektiv</span><span>${eur(fin(k))}</span></div></div>
     <div class="verdict ${vd.t}">${spark(k,90,24)}<span>${esc(vd.l)}</span></div>
     <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" data-add="${esc(k.id)}">${inL?IC.check+"Auf dem Zettel":IC.plus+"Auf den Einkaufszettel"}</button><button class="btn ghost" data-fav="${esc(k.id)}">${IC.star}Merken</button><a class="btn wa" href="${waLink(`🔥 ${k.n}${k.b?" ("+k.b+")":""} bei ${sname(k.s)} für ${eur(fin(k))}${offPct(k)?` (−${offPct(k)} %)`:""}${validTxt(k)?", "+validTxt(k):""}\n\nGefunden mit SparRadar: ${APP_URL}`)}" target="_blank" rel="noopener">${WA_ICON}Teilen</a></div>
    </div></section>
   ${top.length?`<h3 class="sec-h">Beste Kombi-Deals</h3><p style="margin:-8px 0 0;color:var(--muted);font-size:.88rem">Angebot + App-Preis, Bonus-Guthaben und deine Coupons zusammengerechnet.</p><div class="rows">${top.map(drow).join("")}</div>`:""}
   <h3 class="sec-h">Weitere Top-Angebote</h3><div class="rows">${rest.map(drow).join("")}</div>
   <h3 class="sec-h">Dein Wochenplan</h3>
   ${plan.length?`<p style="margin:-8px 0 0;color:var(--muted);font-size:.88rem">Für deine Merkliste lohnen sich ${plan.length} ${plan.length===1?"Markt":"Märkte"}:</p>
    <div class="plan">${plan.map(([s,g])=>`<div class="stop"><h4>${sb(s)}${esc(sname(s))}${g.save>0.005?`<em>spart ${eur(g.save)}</em>`:""}</h4><ul>${g.items.map(o=>`<li>${esc(o.n)}: ${eur(fin(o))}${unitTxt(o)?" ("+unitTxt(o)+")":""}</li>`).join("")}</ul></div>`).join("")}</div>
    <div><button class="btn" id="planToList">${IC.plus}Wochenplan auf den Einkaufszettel</button></div>`
    :'<div class="empty"><b>Noch kein Plan</b>Gerade ist nichts von deiner Merkliste im Angebot.</div>'}
   <div class="two">
    <section class="panel"><h3 style="color:var(--save)">Echte Tiefpreise</h3>${lows.length?`<div class="rows">${lows.map(o=>`<div style="display:flex;justify-content:space-between;gap:10px;font-size:.9rem"><span>${esc(o.n)} <span style="color:var(--muted)">${esc(sname(o.s))}</span></span><b style="font-variant-numeric:tabular-nums">${eur(fin(o))}</b></div>`).join("")}</div>`:"<p>Der Preisverlauf baut sich noch auf. Nach ein paar Tagen erscheinen hier die echten Tiefpreise.</p>"}</section>
    <section class="panel"><h3 style="color:var(--alert)">Vorsicht, Fake-Rabatt</h3>${fakes.length?`<div class="rows">${fakes.map(o=>`<div style="font-size:.9rem"><b>${esc(o.n)}</b> <span style="color:var(--muted)">${esc(sname(o.s))}</span><br><span style="color:var(--muted)">${esc(verdict(o).l)}</span></div>`).join("")}</div>`:"<p>Keine verdächtigen Rabatte gefunden.</p>"}</section>
   </div></div>`}

function renderAdd(){
  const opts=Object.entries(STORES).map(([k,s])=>`<option value="${k}" ${k==="scheck"?"selected":""}>${esc(s.n)}</option>`).join("");
  const copts=Object.entries(CATS).map(([k,n])=>`<option value="${k}">${n}</option>`).join("");
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Angebot eintragen">
   <div class="sheet-h"><h2>Angebot eintragen</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   <p style="margin:0;color:var(--muted)">Für Märkte ohne automatischen Abruf, zum Beispiel Scheck-In oder Serpa. Prospekt öffnen, Angebot abtippen, fertig. Es zählt dann bei Merkliste, Kracher und Einkaufszettel mit.</p>
   <div class="links">${Object.entries(STORES).filter(([,s])=>s.manual).map(([k,s])=>`<a class="btn ghost sm" href="${s.link}" target="_blank" rel="noopener">${esc(s.n)}: Prospekt öffnen</a>`).join("")}</div>
   <form class="form" id="addForm">
    <div class="row"><label>Markt<select id="fStore">${opts}</select></label><label>Kategorie<select id="fCat">${copts}</select></label></div>
    <label>Artikel<input id="fName" required placeholder="z. B. Schweinenackensteaks" autocomplete="off"></label>
    <label>Marke oder Menge (optional)<input id="fDesc" placeholder="z. B. 1 kg, mariniert" autocomplete="off"></label>
    <div class="row"><label>Angebotspreis in €<input id="fPrice" required inputmode="decimal" placeholder="5,99"></label><label>Statt-Preis (optional)<input id="fOld" inputmode="decimal" placeholder="7,99"></label></div>
    <div class="row"><label>Grundpreis € pro kg/l (optional)<input id="fGp" inputmode="decimal" placeholder="5,99"></label><label>Gültig bis<input id="fTo" type="date"></label></div>
    <button class="btn" type="submit">${IC.plus}Angebot speichern</button>
   </form>
   ${S.manual.length?`<h3 class="sec-h">Deine Einträge</h3><div class="rows">${S.manual.map((m,i)=>`<div class="drow"><div class="mini" style="--cc:${CC[m.c]||CC.sonstiges}">${ILL[m.c]||ILL.sonstiges}</div><div class="t">${esc(m.n)}<small>${esc(sname(m.s))} · ${m.to?"bis "+fmtDate(m.to):"ohne Ende"}</small></div><div class="pr"><b>${eur(m.p)}</b><button class="ibtn" data-delman="${i}" aria-label="${esc(m.n)} löschen">${IC.x}</button></div></div>`).join("")}</div>`:""}
  </div>`}

function renderWatch(){
  const wh=watchHits(null);
  const hits=[...new Map(wh.flatMap(x=>x.hits).map(o=>[o.id,o])).values()].sort((a,b)=>offPct(b)-offPct(a));
  return `<section class="panel"><h3>Was soll ich für dich beobachten?</h3>
    <p>Begriff oder Marke eingeben. Mit Wunschpreis wird daraus ein <b>Vorrats-Alarm</b>: Treffer zählen nur, wenn der Grundpreis darunter liegt. Die Zahl am Tab „Merkliste“ zeigt dir beim Öffnen, wie viele Treffer gerade im Angebot sind.</p>
    <form class="addrow" id="kwForm"><input id="kwIn" placeholder="z. B. Mozzarella, Felix, Cola" autocomplete="off"><input id="kwMax" class="sm" inputmode="decimal" placeholder="max. €/kg (optional)" autocomplete="off"><button class="btn" type="submit">${IC.plus}Merken</button></form>
    <div id="kwSugg"></div>
    <div class="kw">${S.watch.map((w,i)=>{const n=wh[i].hits.length;return `<span class="kwchip">${esc(w.k)}${w.max?`<em>≤ ${eur(w.max)}/kg</em>`:""}<span class="n ${n?"":"zero"}">${n}</span><button data-delkw="${i}" aria-label="${esc(w.k)} entfernen">${IC.x}</button></span>`}).join("")||'<span style="color:var(--muted)">Noch nichts gemerkt.</span>'}</div>
   </section>
   <div class="meta"><h2>Deine Treffer</h2><span>${hits.length} Angebote</span></div>
   ${hits.length?`<div class="grid">${hits.slice(0,60).map(o=>card(o,new Set())).join("")}</div>`:'<div class="empty"><b>Keine Treffer</b>Gerade ist nichts von deiner Merkliste reduziert oder unter deinem Wunschpreis.</div>'}`}

function renderList(){
  const items=S.list.map(byId).filter(Boolean),extra=S.extra;
  const addRow=`<form class="addrow" id="extraForm"><input id="extraIn" placeholder="Eigener Eintrag, z. B. Brot, Eier, Spülmittel" autocomplete="off"><button class="btn" type="submit">${IC.plus}Dazu</button></form>`;
  if(!items.length&&!extra.length)return `${addRow}<div class="empty"><b>Dein Einkaufszettel ist leer</b>Tippe bei einem Angebot auf Plus, übernimm im Kracher-Fenster deinen Wochenplan oder schreib oben selbst etwas dazu. SparRadar sortiert alles nach Markt.</div>`;
  const groups={};items.forEach(o=>(groups[o.s]=groups[o.s]||[]).push(o));
  const open=items.filter(o=>!S.checked.includes(o.id));
  const sum=items.reduce((a,o)=>a+fin(o),0),reg=items.reduce((a,o)=>a+ref(o),0),rest=open.reduce((a,o)=>a+fin(o),0);
  const todo=[...new Set(items.flatMap(comboLabels))];
  const done=id=>S.checked.includes(id);
  const line=(id,name,price,label)=>`<div class="rline${done(id)?" done":""}"><button class="rcheck" data-check="${esc(id)}" aria-pressed="${done(id)}" aria-label="${esc(name)} ${done(id)?"nicht mehr abhaken":"abhaken"}"><i></i><span>${esc(name)}${label||""}</span></button><span>${price}</span><button data-${id.startsWith("x-")?"delextra":"add"}="${esc(id)}" aria-label="${esc(name)} entfernen">${IC.x}</button></div>`;
  const nDone=[...items.map(o=>o.id),...extra.map(x=>x.id)].filter(done).length;
  return `${addRow}<div class="receipt"><h3>EINKAUFSZETTEL</h3><div class="sub">${Object.keys(groups).length+(extra.length?1:0)} ${Object.keys(groups).length+(extra.length?1:0)===1?"Abschnitt":"Abschnitte"} · ${items.length+extra.length} Artikel${nDone?` · ${nDone} erledigt`:""}</div>
   <div class="rhint">Tipp: Beim Einkaufen auf einen Artikel tippen, um ihn abzuhaken.</div>
   ${Object.entries(groups).map(([s,os])=>`<div class="rgroup"><div class="rs">${sb(s)}${esc(sname(s))}</div>
     ${os.map(o=>line(o.id,o.n,eur(fin(o)),comboLabels(o).length?" *":"")).join("")}</div>`).join("")}
   ${extra.length?`<div class="rgroup"><div class="rs">${IC.bag}Sonstiges</div>${extra.map(x=>line(x.id,x.n,"")).join("")}</div>`:""}
   ${items.length?`<div class="rtot"><div class="big"><span>SUMME</span><span>${eur(sum)}</span></div>${nDone&&rest<sum-.004?`<div><span>Noch offen</span><span>${eur(rest)}</span></div>`:""}${reg>sum+.004?`<div><span>Normalpreis</span><span>${eur(reg)}</span></div><div class="sv"><span>GESPART</span><span>${eur(reg-sum)}</span></div>`:""}</div>`:""}
   ${todo.length?`<div style="margin-top:12px;font-size:.78rem;color:var(--muted)">* Vor dem Einkauf in der App aktivieren:<br>${todo.map(esc).join(" · ")}</div>`:""}</div>
   <div class="ractions"><a class="btn wa" href="${waLink(listText())}" target="_blank" rel="noopener">${WA_ICON}Per WhatsApp schicken</a><button class="btn ghost" id="copyList">Als Text kopieren</button>${nDone?'<button class="btn ghost" id="clearDone">Erledigte entfernen</button>':""}<button class="btn ghost" id="clearList">Zettel leeren</button></div>`}

function renderCoupons(){
  const act=S.coupons.map((c,i)=>({c,i})).filter(x=>cpActive(x.c));
  const wo=weekOffers();
  const sopts=`<option value="all">Alle Märkte (z. B. Cashback-App)</option>`+Object.entries(STORES).map(([k,s])=>`<option value="${k}" ${k==="rewe"?"selected":""}>${esc(s.n)}</option>`).join("");
  const popts=PROGS.map(p=>`<option ${p==="Rewe Bonus"?"selected":""}>${p}</option>`).join("");
  const topts=Object.entries(CP_TYPES).map(([k,n])=>`<option value="${k}">${n}</option>`).join("");
  const plus=7;const d=new Date(Date.now()+plus*864e5).toISOString().slice(0,10);
  return `<section class="panel"><h3>Meine Coupons</h3>
    <p>Coupon in Lidl Plus, der Rewe-App, bei Payback oder in einer Cashback-App aktiviert? Kurz hier eintragen. SparRadar rechnet ihn dann in alle passenden Angebote, den Kracher und den Einkaufszettel ein. Abgelaufene Coupons verschwinden von selbst.</p>
    <form class="form" id="cpForm">
     <div class="row"><label>Markt<select id="cpStore">${sopts}</select></label><label>Programm<select id="cpProg">${popts}</select></label></div>
     <label>Gilt für (Artikel oder Marke)<input id="cpKw" required placeholder="z. B. Kaffee, Jacobs, Katzenfutter" autocomplete="off"></label>
     <div class="row"><label>Art<select id="cpType">${topts}</select></label><label>Wert<input id="cpVal" required inputmode="decimal" placeholder="z. B. 1,00 oder 20"></label></div>
     <div class="row"><label>Gültig bis<input id="cpTo" type="date" value="${d}"></label><label style="align-self:end"><button class="btn" type="submit">${IC.plus}Coupon speichern</button></label></div>
    </form>
    ${act.length?`<div class="rows">${act.map(({c,i})=>{const n=wo.filter(o=>couponsFor(o).includes(c)).length;
      return `<div class="drow"><div class="mini" style="--cc:${(STORES[c.s]||{}).c||"#2B3034"};display:grid;place-items:center">${c.s==="all"?`<span class="sb lg" style="--c:#2B3034">%</span>`:sb(c.s,true)}</div>
       <div class="t">${esc(c.k)}<small>${esc(c.s==="all"?"Alle Märkte":sname(c.s))} · ${esc(c.prog)} · ${c.to?"bis "+fmtDate(c.to):"ohne Ende"}</small>
        <div class="pills"><span class="pill ${n?"cb":""}">${n?`passt zu ${n} Angebot${n===1?"":"en"}`:"gerade kein passendes Angebot"}</span></div></div>
       <div class="pr"><b>${esc(cpValueTxt(c))}</b><div style="display:flex;gap:6px;justify-content:flex-end;margin-top:4px">${n?`<button class="btn ghost sm" data-cpshow="${i}">Zeigen</button>`:""}<button class="ibtn" data-delcp="${i}" aria-label="Coupon ${esc(c.k)} löschen">${IC.x}</button></div></div></div>`}).join("")}</div>`
      :'<div class="empty" style="padding:16px"><b>Noch keine Coupons</b>Trag oben deinen ersten aktivierten Coupon ein.</div>'}
    ${S.useApp?"":`<p style="color:var(--alert)">„Apps &amp; Coupons einrechnen“ ist ausgeschaltet. Coupons werden gerade nicht berücksichtigt.</p>`}
   </section>`}

function renderSync(){
  const c=Sync.cfg();
  return `<section class="panel" id="syncPanel"><h3>📱 ↔ 💻 Geräte verbinden</h3>
   ${c?.gist?`<p><b>Handy und PC sind verbunden.</b> Merkliste, Einkaufszettel, Coupons und eigene Angebote gleichen sich automatisch ab.</p>
     <p id="syncState">${esc(Sync.status||"Verbunden")}</p>
     <p><b>Zweites Gerät verbinden:</b> Code kopieren, an dich selbst schicken (z. B. WhatsApp oder E-Mail) und auf dem anderen Gerät hier einfügen.</p>
     <div class="links"><button class="btn sm" id="syncCopy">Code kopieren</button><button class="btn ghost sm" id="syncNow">Jetzt abgleichen</button><button class="btn ghost sm" id="syncOff">Verbindung trennen</button></div>`
   :`<p>Damit du auf Handy und PC dieselbe Merkliste, denselben Einkaufszettel und dieselben Coupons siehst. Einmal pro Gerät den Schlüssel eintragen, danach läuft alles unsichtbar im Hintergrund.</p>
     <p><b>Schon ein Gerät verbunden?</b> Dort „Code kopieren“ drücken, dir schicken und hier einfügen. Fertig.</p>
     <details class="steps-d"><summary>Noch kein Gerät verbunden? So bekommst du den Code (einmalig, am besten am PC)</summary>
     <ol class="steps"><li><a href="https://github.com/settings/tokens/new?scopes=gist&description=SparRadar" target="_blank" rel="noopener">Hier tippen</a> und bei GitHub anmelden.</li><li>Bei „Expiration“ <b>No expiration</b> auswählen. Der Haken bei <b>gist</b> ist schon gesetzt, sonst nichts anhaken.</li><li>Ganz unten auf den grünen Knopf <b>Generate token</b>.</li><li>Den langen Code, der mit <code>ghp_</code> anfängt, kopieren und unten einfügen.</li></ol></details>
     <form class="addrow" id="syncForm"><input id="syncToken" type="password" placeholder="Code einfügen (ghp_…)" autocomplete="off" spellcheck="false"><button class="btn" type="submit">Verbinden</button></form>
     <p style="font-size:.8rem">Der Schlüssel bleibt nur auf diesem Gerät und darf nur deinen geheimen SparRadar-Notizzettel bei GitHub lesen und schreiben.</p>`}
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
   <p>Lade Familie und Freunde ein. Sie bekommen eine Einladung mit Logo, tippen auf <b>„SparRadar installieren“</b> und haben die App auf dem Startbildschirm – ohne Warnungen, mit automatischen Updates.</p>
   <label class="inv-name">Dein Name auf der Einladung<input id="inviteName" value="${esc(n)}" placeholder="z. B. Kevin" maxlength="30" autocomplete="off"></label>
   <div class="links"><a class="btn wa inv-btn" id="inviteWa" href="${waLink(inviteText())}" target="_blank" rel="noopener">${WA_ICON}Einladung per WhatsApp senden</a>${navigator.share?'<button class="btn ghost" id="shareOther">Anders teilen …</button>':""}
    <a class="btn ghost sm" href="${inviteUrl()}" target="_blank" rel="noopener">Vorschau ansehen</a></div>
  </section>`}

function renderSettings(){
  const g=META.generated?new Date(META.generated):null;
  return `<div class="sheet" role="dialog" aria-modal="true" aria-label="Einstellungen">
   <div class="sheet-h"><span class="newsico">${IC.gear}</span><h2>Einstellungen</h2><button class="ibtn" id="closeSheet" aria-label="Schließen">${IC.x}</button></div>
   ${renderShare()}
   ${renderSync()}
   <section class="panel"><h3>SparRadar als App</h3><p>Android: APK aufs Handy laden und öffnen. Windows: Setup starten. Beide aktualisieren sich danach selbst und zeigen immer die neueste Version.</p>
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
   ["scheck","Payback (Edeka-Verbund)","Scheck-In gehört zum Edeka-Verbund, auch dort gilt Payback. Angebote trägst du über „+ Angebot eintragen“ ein."],
   ["dm","dm App","Digitale Coupons und Aktionen, auch für Lebensmittel und Tierfutter."],
   ["aldi","Aldi Süd","Kaum Coupons, dafür dauerhaft niedrige Preise. Neue Aktionsware kommt montags und donnerstags."],
   ["serpa","Serpa Markt","Wochenprospekt prüfen und starke Angebote selbst eintragen."]];
  const G=[
   [IC.layers,"Stapeln","Angebotspreis, dann App-Preis, dann Coupon oder Bonus, dazu Payback-Punkte und am Ende Cashback per Kassenbon."],
   [IC.chart,"Fake-Rabatte erkennen","SparRadar speichert jeden Tag die Preise. Nach ein paar Wochen zeigt es dir, ob ein „statt“-Preis wirklich verlangt wurde."],
   [IC.box,"Vorrat bei Tiefpreis","Haltbares wie Katzenfutter, Kaffee, Nudeln oder Getränke nur kaufen, wenn der Grundpreis unter deinem Wunschpreis liegt. Dann gleich für mehrere Wochen."],
   [IC.scale,"Grundpreis zählt","Vergleiche immer den Preis pro kg oder l. Die Großpackung ist nicht automatisch günstiger."],
   [IC.cal,"Montag und Donnerstag","An diesen Tagen starten bei Lidl und Aldi die neuen Aktionen. Unter „Demnächst“ siehst du sie schon vorher."],
   [IC.bag,"Too Good To Go","Bäcker und Märkte geben abends übrig gebliebene Lebensmittel als Überraschungstüte ab, meist für etwa ein Drittel des Werts."]];
  return `${renderCoupons()}
   <h3 class="sec-h">Spartipps</h3>
   <section class="panel"><h3>Geht „Extreme Couponing“ wie in den USA auch hier?</h3>
   <p>Nur teilweise. In Deutschland sind Coupons fast immer Händler-Coupons in Apps, oft auf ein Stück pro Einkauf begrenzt. Einen 200-€-Wagen für 0 € schaffst du hier nicht. Einzelne Artikel umsonst oder mit Plus gehen aber, wenn du Händler-App, Payback oder Rewe Bonus, Cashback-Apps und „Gratis testen“-Aktionen der Hersteller kombinierst.</p></section>
   <h3 class="sec-h">So holst du am meisten raus</h3>
   <div class="tips">${G.map(([i,h,p])=>`<div class="tip"><h4><span class="ico">${i}</span>${h}</h4><p>${p}</p></div>`).join("")}</div>
   <h3 class="sec-h">Apps und Programme deiner Märkte</h3>
   <div class="tips">${T.map(([s,prog,txt])=>`<div class="tip"><h4>${sb(s,true)}${esc(sname(s))}</h4><span class="prog">${prog}</span><p>${txt}</p><a href="${STORES[s].link}" target="_blank" rel="noopener" style="font-size:.84rem">Angebote ansehen</a></div>`).join("")}
   <div class="tip"><h4><span class="ico">${IC.layers}</span>Cashback-Apps</h4><span class="prog">Marktguru · Scondoo · Coupies</span><p>Geld zurück auf bestimmte Markenprodukte, egal in welchem Markt gekauft. Kassenbon fotografieren, das Geld kommt aufs Konto oder per PayPal.</p></div>
   <div class="tip"><h4><span class="ico">${IC.bag}</span>Too Good To Go</h4><span class="prog">Abends Essen retten</span><p>Standort Wörth am Rhein wählen und Bäcker und Märkte in der Nähe als Favoriten speichern.</p><a href="https://www.toogoodtogo.com/de" target="_blank" rel="noopener" style="font-size:.84rem">toogoodtogo.com</a></div></div>
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
   <div class="fchips">${chip("data-cat","","Alle Kategorien",!S.cat," plain")}${food.map(([k,v])=>chip("data-cat",k,esc(v),S.cat===k," plain")).join("")}</div>
   ${nf.length?`<h3 class="fh">Weitere Angebote</h3><div class="fchips">${nf.map(([k,v])=>chip("data-cat",k,esc(v),S.cat===k," plain")).join("")}</div>`:""}
   <h3 class="fh">Sortieren</h3>
   <div class="fchips">${Object.entries(SORTS).map(([k,v])=>chip("data-sort",k,v,S.sort===k," plain")).join("")}</div>
   <div class="frow"><button class="switch" data-toggleapp="1" role="switch" aria-checked="${S.useApp}" aria-label="Apps und Coupons einrechnen"></button><span>Apps &amp; Coupons einrechnen</span></div>
   <div class="factions"><button class="btn ghost" data-freset="1">Zurücksetzen</button><button class="btn" data-fdone="1">${n} Angebote zeigen</button></div>
   <button class="btn ghost sm" data-openadd="1" style="justify-self:start">+ Angebot selbst eintragen</button>
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
  document.getElementById("wk0").setAttribute("aria-pressed",S.week===0);document.getElementById("wk1").setAttribute("aria-pressed",S.week===1);
  const hits=new Set(watchHits(null).flatMap(x=>x.hits.map(o=>o.id))).size;
  const wb=document.getElementById("watchBadge");wb.textContent=hits;wb.hidden=!hits;
  const ln=S.list.filter(id=>byId(id)&&!S.checked.includes(id)).length+S.extra.filter(x=>!S.checked.includes(x.id)).length;
  const lb=document.getElementById("listBadge");lb.textContent=ln;lb.hidden=!ln;
  const nc=S.coupons.filter(cpActive).length,cb=document.getElementById("cpBadge");cb.textContent=nc;cb.hidden=!nc;
  const counts={},ccount={};OFFERS.forEach(o=>{counts[o.s]=(counts[o.s]||0)+1;ccount[o.c]=(ccount[o.c]||0)+1});
  // Markt-Leiste mit Logos: antippen = nur dieser Markt (mehrere möglich), „Alle“ = alles
  document.getElementById("storeChips").innerHTML=`<button class="mtile all" data-store="" aria-pressed="${!S.stores.size}"><span class="sb lg">${IC.layers}</span><span class="mn">Alle</span><em>${OFFERS.length}</em></button>`+Object.keys(STORES).filter(k=>counts[k]||!STORES[k].manual).map(k=>`<button class="mtile" data-store="${k}" aria-pressed="${S.stores.has(k)}">${sb(k,true)}<span class="mn">${esc(STORES[k].n.replace(" Jockgrim",""))}</span><em>${counts[k]||0}</em></button>`).join("");
  document.getElementById("catChips").innerHTML=`<button class="chip plain" data-cat="" aria-pressed="${!S.cat}">Alle Kategorien</button>`+Object.entries(CATS).filter(([k])=>ccount[k]||S.cat===k).map(([k,n],i,arr)=>`${NONFOOD_CATS.includes(k)&&i&&!NONFOOD_CATS.includes(arr[i-1][0])?'<span class="chipsep" aria-hidden="true"></span>':""}<button class="chip plain" data-cat="${k}" aria-pressed="${S.cat===k}">${n}</button>`).join("");
  document.getElementById("appSw").setAttribute("aria-checked",S.useApp);
  document.getElementById("sort").value=S.sort;
  const act=[].concat(S.cat?[CATS[S.cat]]:[],S.sort!=="off"?[SORTS[S.sort]]:[]);
  document.getElementById("fsum").textContent=act.length?act.join(" · "):"Alle Kategorien";
  const fc=document.getElementById("fcount");fc.textContent=act.length;fc.hidden=!act.length;
  document.getElementById("qclear").hidden=!S.q;
  document.getElementById("main").innerHTML={offers:renderOffers,watch:renderWatch,list:renderList,tips:renderTips}[S.tab]();
  const sh=document.getElementById("sheet");sh.hidden=!S.sheet;document.body.classList.toggle("lock",!!S.sheet);
  // Scroll-Position nur behalten, wenn dasselbe Fenster neu gezeichnet wird (z. B. nach „Merken“), neues Fenster startet oben
  if(S.sheet){const y=S.sheet===S._shown?(sh.firstElementChild?.scrollTop||0):0;S._shown=S.sheet;sh.innerHTML=({add:renderAdd,filter:renderFilter,news:renderNews,settings:renderSettings,whatsnew:renderWhatsNew,detail:renderDetail}[S.sheet]||renderKracher)();if(sh.firstElementChild)sh.firstElementChild.scrollTop=y}else S._shown=null;
  document.getElementById("appUpd").innerHTML=appUpdateHTML();
  let lbh=document.getElementById("lbHost");if(!lbh){lbh=document.createElement("div");lbh.id="lbHost";document.body.appendChild(lbh)}
  lbh.innerHTML=renderLightbox();
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
  if(b.dataset.sugg==="q"){const v=b.dataset.v;S.q=v;document.getElementById("q").value=v;S.limit=60;hideSugg();S.tab="offers";render();return}
  if(b.dataset.sugg==="kw"){const v=b.dataset.v;document.getElementById("kwIn").value=v;hideSugg();document.getElementById("kwForm").requestSubmit();return}
  if(b.id&&b.id.startsWith("tab-")){S.tab=b.id.slice(4);render();scrollTo({top:0});return}
  if(b.id==="wk0"||b.id==="wk1"){S.week=+b.id[2];S.limit=60;render();return}
  if(b.id==="openK"){S.sheet="k";render();return}
  if(b.id==="openAdd"||b.dataset.openadd){S.sheet="add";render();return}
  if(b.id==="openFilter"){S.sheet="filter";render();return}
  if(b.dataset.zoom){S.lightbox=b.dataset.zoom;render();return}
  if(b.dataset.dimg!==undefined){S.dImg=+b.dataset.dimg;render();return}
  if(b.id==="openSettings"){S.sheet="settings";render();checkVersion();return}
  if(b.id==="settingsBtn"){S.sheet="settings";render();checkVersion();return}
  if(b.id==="reloadApp"){location.reload();return}
  if(b.id==="appUpdNow"){try{window.SparRadarApp.checkUpdate()}catch(e){location.href=APK_URL}return}
  if(b.id==="syncCopy"){copy(Sync.cfg().token,"Code kopiert. Jetzt an dich selbst schicken und auf dem anderen Gerät einfügen.");return}
  if(b.id==="syncNow"){Sync.pull().then(()=>toast(Sync.status));return}
  if(b.id==="syncOff"){if(confirm("Verbindung auf diesem Gerät trennen? Deine Listen bleiben hier gespeichert.")){Sync.disconnect();render()}return}
  if(b.dataset.sort){S.sort=b.dataset.sort;render();return}
  if(b.dataset.toggleapp){S.useApp=!S.useApp;save();render();return}
  if(b.dataset.freset){S.stores.clear();S.cat=null;S.sort="off";S.limit=60;render();return}
  if(b.dataset.fdone){S.sheet=null;render();scrollTo({top:0});return}
  if(b.id==="closeSheet"){S.sheet=null;render();return}
  if(b.id==="more"){S.limit+=60;render();return}
  if(b.dataset.store!==undefined){const k=b.dataset.store;if(!k)S.stores.clear();else S.stores.has(k)?S.stores.delete(k):S.stores.add(k);S.limit=60;render();return}
  if(b.dataset.cat!==undefined){S.cat=b.dataset.cat||null;S.limit=60;render();return}
  if(b.id==="appSw"){S.useApp=!S.useApp;save();render();return}
  if(b.id==="qclear"){S.q="";document.getElementById("q").value="";render();return}
  if(b.dataset.fav){const o=byId(b.dataset.fav);if(!o)return;const i=S.watch.findIndex(w=>norm(w.k)===norm(o.n));if(i>=0){S.watch.splice(i,1);toast(`${o.n} von der Merkliste genommen`)}else{S.watch.push({k:o.n});toast(`${o.n} gemerkt`)}save();render();return}
  if(b.dataset.add){const id=b.dataset.add,i=S.list.indexOf(id);if(i>=0)S.list.splice(i,1);else{S.list.push(id);toast("Auf den Einkaufszettel gesetzt")}save();render();return}
  if(b.dataset.delkw){S.watch.splice(+b.dataset.delkw,1);save();render();return}
  if(b.dataset.delcp){const c=S.coupons.splice(+b.dataset.delcp,1)[0];save();toast(`Coupon „${c.k}“ gelöscht`);render();return}
  if(b.dataset.cpshow){const c=S.coupons[+b.dataset.cpshow];S.tab="offers";S.q=c.k;document.getElementById("q").value=c.k;S.stores=new Set(c.s==="all"?[]:[c.s]);S.cat=null;S.limit=60;render();scrollTo({top:0});return}
  if(b.dataset.delman){const m=S.manual.splice(+b.dataset.delman,1)[0];OFFERS=OFFERS.filter(o=>!(o.manual&&o.id===m.id));save();render();return}
  if(b.id==="planToList"){let n=0;weekPlan().forEach(([,g])=>g.items.forEach(o=>{if(!S.list.includes(o.id)){S.list.push(o.id);n++}}));save();toast(n?`${n} Artikel auf den Einkaufszettel gesetzt`:"Schon alles auf dem Zettel");render();return}
  if(b.id==="goWatch"){S.tab="watch";render();return}
  if(b.id==="watchFromSearch"){const k=S.q.trim();if(k&&!S.watch.some(w=>norm(w.k)===norm(k)))S.watch.push({k});save();toast(`„${k}“ wird beobachtet`);S.tab="watch";render();return}
  if(b.id==="clearList"){if(!confirm("Den ganzen Einkaufszettel leeren?"))return;S.list=[];S.extra=[];S.checked=[];save();render();return}
  if(b.id==="clearDone"){S.list=S.list.filter(id=>!S.checked.includes(id));S.extra=S.extra.filter(x=>!S.checked.includes(x.id));S.checked=[];save();render();return}
  if(b.dataset.check){const id=b.dataset.check,i=S.checked.indexOf(id);if(i>=0)S.checked.splice(i,1);else S.checked.push(id);save();render();return}
  if(b.dataset.delextra){S.extra=S.extra.filter(x=>x.id!==b.dataset.delextra);save();render();return}
  if(b.id==="toTop"){scrollTo({top:0,behavior:"smooth"});return}
  if(b.id==="copyList"){copy(listText(),"Einkaufszettel kopiert");return}
  if(b.id==="shareOther"){navigator.share({title:"Persönliche Einladung zu SparRadar",text:inviteText()}).catch(()=>{});return}
  if(b.dataset.watchname){const k=b.dataset.watchname;if(!S.watch.some(w=>norm(w.k)===norm(k))){S.watch.push({k});save();toast(`„${k}“ auf der Merkliste. Du siehst es, sobald es im Angebot ist.`)}render();return}
  if(b.dataset.newsdone){S.sheet=null;if(b.dataset.newsdone==="watch")S.tab="watch";render();return}
});
function copy(txt,ok){const fail=()=>toast("Kopieren hat nicht geklappt. Bitte Text markieren und von Hand kopieren.");try{navigator.clipboard.writeText(txt).then(()=>toast(ok),fail)}catch(e){fail()}}
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&S.lightbox){S.lightbox=null;render()}else if(e.key==="Escape"&&S.sheet){S.sheet=null;render()}
  if(e.key==="Enter"&&e.target.matches?.(".card[data-detail]")){S.detail=e.target.dataset.detail;S.dImg=0;S.sheet="detail";render()}});
document.addEventListener("submit",e=>{
  if(e.target.id==="kwForm"){e.preventDefault();const v=document.getElementById("kwIn").value.trim(),mx=parseNum(document.getElementById("kwMax").value);
    if(v){const i=S.watch.findIndex(w=>norm(w.k)===norm(v));if(i>=0)S.watch[i].max=mx||undefined;else S.watch.push(mx?{k:v,max:mx}:{k:v});save();toast(mx?`Vorrats-Alarm: „${v}“ unter ${eur(mx)}/kg`:`„${v}“ wird beobachtet`)}render()}
  if(e.target.id==="extraForm"){e.preventDefault();const v=document.getElementById("extraIn").value.trim();if(v){S.extra.push({id:"x-"+Date.now(),n:v});save();render();document.getElementById("extraIn")?.focus()}return}
  if(e.target.id==="syncForm"){e.preventDefault();const t=document.getElementById("syncToken").value.trim();
    if(!/^(ghp_|github_pat_)/.test(t)){toast("Das sieht nicht wie ein GitHub-Schlüssel aus (beginnt mit ghp_).");return}
    toast("Verbinde …");Sync.connect(t).then(()=>{toast("Verbunden! Deine Listen sind jetzt auf allen Geräten gleich.");render()},err=>toast("Verbinden fehlgeschlagen: "+err.message));return}
  if(e.target.id==="cpForm"){e.preventDefault();
    const val=id=>document.getElementById(id).value.trim();
    const v=parseNum(val("cpVal")),k=val("cpKw").replace(/\s+/g," ");
    if(!k||!v){toast("Bitte Artikel und Wert eintragen.");return}
    const c={s:val("cpStore"),prog:val("cpProg"),k,t:val("cpType"),v,to:val("cpTo")||null};
    if(c.t==="pct"&&v>=100){toast("Ein Rabatt muss unter 100 % liegen.");return}
    S.coupons.push(c);save();
    const n=weekOffers().filter(o=>couponsFor(o).includes(c)).length;
    toast(n?`Coupon gespeichert, passt zu ${n} Angebot${n===1?"":"en"}`:"Coupon gespeichert. Gerade passt kein Angebot dazu.");render();return}
  if(e.target.id==="addForm"){e.preventDefault();
    const val=id=>document.getElementById(id).value.trim();
    const p=parseNum(val("fPrice"));if(!p||!val("fName")){toast("Bitte Artikel und Preis eintragen.");return}
    const gp=parseNum(val("fGp"));
    const m={s:val("fStore"),c:val("fCat"),n:val("fName"),d:val("fDesc"),p,o:parseNum(val("fOld")),gp:gp?{v:gp,u:"kg"}:null,to:val("fTo")||null,x:[]};
    m.id="m-"+norm(m.s+m.n)+"-"+Date.now();
    S.manual.push(m);OFFERS.push({...m,src:"selbst eingetragen",manual:true});save();toast(`${m.n} eingetragen`);render()}
});
// Programm passend zum gewählten Markt vorschlagen
document.addEventListener("change",e=>{if(e.target.id==="cpStore")document.getElementById("cpProg").value=defaultProg(e.target.value)});
document.getElementById("q").addEventListener("input",e=>{S.q=e.target.value;S.limit=60;if(S.tab!=="offers")S.tab="offers";render();showSugg("qSugg",S.q,"q")});
document.getElementById("q").addEventListener("focus",e=>showSugg("qSugg",e.target.value,"q"));
document.addEventListener("input",e=>{if(e.target.id==="kwIn")showSugg("kwSugg",e.target.value,"kw");
  if(e.target.id==="inviteName"){store.set("inviteName",e.target.value.trim());const a=document.getElementById("inviteWa");if(a)a.href=waLink(inviteText())}});
document.addEventListener("keydown",e=>{if(e.key==="Escape")hideSugg();if(e.key==="Enter"&&e.target.id==="q"){hideSugg();e.target.blur()}});
// Schrift größer (A+): vergrößert die ganze App gleichmäßig, Layout passt sich an
const ZOOM=[1,1.2,1.4],ZOOM_UI=[["A+","Schrift größer"],["A++","Schrift noch größer"],["A−","Wieder normale Schriftgröße"]];
function applyZoom(){const i=Math.max(0,ZOOM.indexOf(store.get("zoom",1)));document.documentElement.style.zoom=ZOOM[i]>1?ZOOM[i]:"";
  const b=document.getElementById("zoomBtn");b.textContent=ZOOM_UI[i][0];b.setAttribute("aria-label",ZOOM_UI[i][1]);b.setAttribute("aria-pressed",i>0);return i}
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
    const o=await (await fetch("data/offers.json",{cache:"no-store"})).json();
    if(o.generated!==META.generated)load();
  }catch(e){}
}
setInterval(freshen,30*60*1000);
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&Date.now()-(freshen.last||0)>5*60*1000){freshen.last=Date.now();freshen()}});
document.addEventListener("visibilitychange",()=>{if(!document.hidden)Sync.pull()});
