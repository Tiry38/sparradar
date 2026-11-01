// SparRadar Service Worker: App offline verfügbar, Angebote immer frisch (Netz zuerst, sonst Cache)
const CACHE = "sparradar-v4";
const SHARE = "sr-share"; // geteilter Kassenbon (Teilen-Menü einer anderen App -> SparRadar), nur kurz auf dem Gerät
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon.svg"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== SHARE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // „Teilen“ aus einer anderen App (z. B. digitaler Kassenbon): Datei/Text kurz ablegen, dann App mit ?bon=1 öffnen
  if (e.request.method === "POST" && url.origin === location.origin && url.pathname.endsWith("/share-target")) {
    e.respondWith((async () => {
      try {
        const fd = await e.request.formData(), c = await caches.open(SHARE);
        await Promise.all((await c.keys()).map(k => c.delete(k)));
        const f = fd.getAll("bon").find(x => x && x.size);
        if (f) await c.put("bon-file", new Response(f, { headers: { "Content-Type": f.type || "application/octet-stream", "X-Name": encodeURIComponent(f.name || "") } }));
        const t = [fd.get("title"), fd.get("text"), fd.get("url")].filter(Boolean).join("\n");
        if (t) await c.put("bon-text", new Response(t, { headers: { "Content-Type": "text/plain;charset=utf-8" } }));
      } catch (err) {}
      return Response.redirect(new URL("./?bon=1", url).href, 303);
    })());
    return;
  }
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    // am Browser-Cache vorbei, damit neue App-Versionen und Angebote sofort ankommen
    fetch(new Request(e.request.url, { cache: "no-cache" }))
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request).then(r => r || caches.match("index.html")))
  );
});
