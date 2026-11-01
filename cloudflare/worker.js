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
  async scheduled(ev, env) {
    await env.DB.prepare("DELETE FROM sync WHERE at < ?").bind(Date.now() - 365 * 864e5).run();
  },
};
