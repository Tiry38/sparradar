// SparRadar-Sync: kleiner Speicher für Familien-Codes (Einkaufszettel, Merkliste, Coupons).
// Jeder Code = eine zufällige ID (20 Zeichen, nicht erratbar). Kein Konto, keine Namen, keine Passwörter.
// Läuft kostenlos auf Cloudflare Workers + D1. Wird von .github/workflows/sync-server.yml automatisch eingerichtet.
const ORIGINS = ["https://tiry38.github.io", "http://localhost:8765", "http://127.0.0.1:8765"];
const MAX = 1_000_000;           // höchstens 1 MB pro Familie
const NEW_PER_DAY = 300;         // Schutz gegen Missbrauch: so viele neue Codes pro Tag insgesamt
const ID = /^[A-Za-z0-9]{20}$/;

function cors(req) {
  const o = req.headers.get("Origin") || "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
    "Cache-Control": "no-store",
  };
}
const json = (req, body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json" } });

function newId() {
  const a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", out = [];
  while (out.length < 20) for (const x of crypto.getRandomValues(new Uint8Array(32))) if (x < 248 && out.length < 20) out.push(a[x % 62]);
  return out.join("");
}

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });
    const url = new URL(req.url), db = env.DB, now = Date.now();
    const o = req.headers.get("Origin");
    if (o && !ORIGINS.includes(o)) return json(req, { error: "origin" }, 403);

    if (url.pathname === "/" || url.pathname === "/ping") return json(req, { ok: true, app: "SparRadar-Sync" });
    // Wann zuletzt nach neuen Prospekten gesucht wurde (zeigt die App oben neben „Stand“)
    if (url.pathname === "/tick") {
      const r = await db.prepare("SELECT at FROM sync WHERE id = '__tick'").first();
      return json(req, { at: r?.at || 0 });
    }

    if (url.pathname === "/new" && req.method === "POST") {
      const day = new Date().toISOString().slice(0, 10);
      const c = await db.prepare("SELECT COUNT(*) AS n FROM sync WHERE created >= ?").bind(Date.parse(day)).first();
      if ((c?.n || 0) >= NEW_PER_DAY) return json(req, { error: "Heute schon zu viele neue Codes – bitte morgen nochmal." }, 429);
      const id = newId();
      await db.prepare("INSERT INTO sync (id, data, created, at) VALUES (?, '{}', ?, ?)").bind(id, now, now).run();
      return json(req, { id });
    }

    const m = url.pathname.match(/^\/s\/([^/]+)$/);
    if (!m || !ID.test(m[1])) return json(req, { error: "not found" }, 404);
    const id = m[1];

    if (req.method === "GET") {
      const r = await db.prepare("SELECT data FROM sync WHERE id = ?").bind(id).first();
      if (!r) return json(req, { error: "Code unbekannt" }, 404);
      return new Response(r.data, { headers: { ...cors(req), "Content-Type": "application/json" } });
    }
    if (req.method === "PUT") {
      const body = await req.text();
      if (body.length > MAX) return json(req, { error: "zu groß" }, 413);
      try { JSON.parse(body); } catch { return json(req, { error: "kein JSON" }, 400); }
      const r = await db.prepare("UPDATE sync SET data = ?, at = ? WHERE id = ?").bind(body, now, id).run();
      if (!r.meta.changes) return json(req, { error: "Code unbekannt" }, 404);
      return json(req, { ok: true, at: now });
    }
    return json(req, { error: "method" }, 405);
  },
  // Aufräumen: Familien-Codes, die 1 Jahr lang niemand benutzt hat, werden gelöscht
  // Zusätzlich: Taktgeber für die GitHub-Abrufe. GitHubs eigene Zeitpläne kommen bei diesem Repo oft Stunden zu spät
  // oder gar nicht (01.11.: Morgen-Abruf fiel aus). Cloudflare-Cron ist pünktlich und startet die Abrufe per workflow_dispatch.
  // Braucht den Worker-Secret GH_TOKEN (fein-granularer GitHub-Schlüssel, nur dieses Repo, nur „Actions: Read and write“).
  async scheduled(ev, env, ctx) {
    if (ev.cron === "17 3 * * SUN") {
      await env.DB.prepare("DELETE FROM sync WHERE at < ?").bind(Date.now() - 365 * 864e5).run();
      return;
    }
    if (!env.GH_TOKEN) return;
    const d = new Date(ev.scheduledTime), h = d.getUTCHours(), wd = d.getUTCDay(), m = d.getUTCMinutes(); // 0 = So
    const due = [];
    // Kevins Wunsch (01.11.): neue Woche so schnell wie möglich -> Fr/Sa/So und Mo früh alle 5 min nachsehen
    // (Cron „*/5“, je Durchgang nur 6 Seitenaufrufe). Die großen Abrufe laufen weiter nur einmal pro Stunde (Takt :10).
    const full = m >= 10 && m < 15;
    if (full) {
      if (h === 4) due.push("angebote.yml", "cashback.yml");                       // jeden Morgen ca. 5:10/6:10 Uhr
      if (h === 17 && [5, 6, 0].includes(wd)) due.push("angebote.yml");             // Fr, Sa, So abends
      if (h === 2 && wd === 0) due.push("artikelstamm.yml");                        // sonntags nachts
      if ([6, 12, 18].includes(h)) due.push("bilder.yml");                         // Bilder-Wächter 3× am Tag
    }
    const often = ([5, 6, 0].includes(wd) && h >= 5 && h <= 22) || (wd === 1 && h >= 3 && h <= 9); // alle 5 min
    const hourly = full && (wd === 4 ? h >= 5 && h <= 21 : wd === 1 ? h >= 5 && h <= 20 : [2, 3].includes(wd) && [5, 9, 15].includes(h));
    const pros = often || hourly;
    if (pros && !due.includes("angebote.yml")) due.push("prospekte.yml");         // Prospekt-Wächter
    ctx.waitUntil(Promise.all(due.map(f => fetch(`https://api.github.com/repos/Tiry38/sparradar/actions/workflows/${f}/dispatches`, {
      method: "POST",
      headers: { Authorization: "Bearer " + env.GH_TOKEN, Accept: "application/vnd.github+json", "User-Agent": "SparRadar-Taktgeber", "Content-Type": "application/json" },
      body: JSON.stringify({ ref: "main" }),
    }).then(async r => {
      console.log(f, r.status);
      if (r.ok && (f === "prospekte.yml" || f === "angebote.yml")) {  // Suche gestartet -> Zeit für die App merken
        const t = Date.now();
        await env.DB.prepare("INSERT INTO sync (id, data, created, at) VALUES ('__tick', '{}', ?, ?) ON CONFLICT(id) DO UPDATE SET at = excluded.at").bind(t, t).run();
      }
    }))));
  },
};
