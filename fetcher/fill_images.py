"""SparRadar Bilder-Wächter: Jeder Artikel in der App soll ein Bild haben.

Läuft mehrmals am Tag (.github/workflows/bilder.yml). Geht alle Artikelnamen durch
(Angebote, docs/data/names.json, Artikelstamm docs/data/catalog.json) und sucht für jeden
Artikel ohne Bild eines:
  1. gleicher Name (Schreibweise egal) in unseren eigenen Daten (Angebote, names-img, Artikelstamm),
  2. gleicher Markenartikel mit anderer Packungsgröße/Sorte (gleiche Marke + gleiche Produktwörter),
  3. Bilder aus dem offiziellen Open-Food-/Beauty-Facts-Datenexport (sammelt fetch_catalog.py wöchentlich
     in docs/data/img-pool.json). Die Such-Schnittstelle wird NICHT genutzt: robots.txt verbietet /cgi und /api.
  4. Produktseiten von Aldi Süd und Lidl: deren öffentliche Produkt-Sitemaps (robots.txt nennt sie ausdrücklich)
     werden einmal gelesen, passende Seite (Marke + Produktwörter im Seitennamen) -> Produktfoto (og:image).
  5. Gelöschte Aldi-Produktseiten (Aktionsware, HTTP 410) aus dem Internet-Archiv (robots.txt erlaubt es).
Netz-Abrufe nur mit Pause (PAUSE) und höchstens SR_IMG_MAX Seiten je Lauf (0 = keine Netz-Suche).
Ergebnis: docs/data/img-extra.json {Artikelname: Bild-Adresse}. Fehlversuche merkt sich
docs/data/img-miss.json (neuer Versuch nach 7 Tagen). Nie fremde Bilder raten: es müssen Marke
und Produktwörter passen.
"""
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "docs", "data")
UA = "SparRadar/1.0 (private Angebotsuebersicht; https://github.com/Tiry38/sparradar)"
OFF_IMG = {"f": "https://images.openfoodfacts.org/images/products/",
           "b": "https://images.openbeautyfacts.org/images/products/"}
FILL = re.compile(r"^(\d.*|g|kg|ml|l|cl|x|xl|xxl|st|stk|stueck|pack|packung|bigpack|big|cups?|portionen|kapseln|"
                  r"und|mit|fuer|der|die|das|von|oder|je|ca|im|in|aus|zum|zur|de|la|le|the|of|bio|neu)$")


PAUSE = 2.0
MAX_NET = int(os.environ.get("SR_IMG_MAX", "250"))
SITEMAPS = {"aldi": "https://www.aldi-sued.de/sitemap_products.xml", "lidl": "https://www.lidl.de/static/sitemap.xml"}


def http(u, limit=None):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
            if r.headers.get("Content-Encoding") == "gzip" or u.endswith(".gz"):
                b = gzip.decompress(b)
            return b.decode("utf-8", "replace")
    except Exception as e:
        log("   !", u[:90], str(e)[:60])
        return None


def sitemap_urls(u, want, depth=0):
    """Alle Seiten-Adressen einer Sitemap (auch Sitemap-Index), gefiltert auf Produktseiten (want = Regex)."""
    x = http(u)
    time.sleep(PAUSE)
    if not x:
        return []
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", x)
    if "<sitemapindex" in x and depth < 2:
        out = []
        for l in locs:
            if re.search(r"product|produkt|/p/|sitemap", l, re.I):
                out += sitemap_urls(l, want, depth + 1)
        return out
    return [l for l in locs if re.search(want, l)]


def slug_name(url):
    """https://www.aldi-sued.de/produkt/ironmaxx-squeebarista-65-ml-salted-caramel-000000000759556001 -> Wörter"""
    path = urllib.parse.urlparse(url).path.rstrip("/")
    parts = [p for p in path.split("/") if p]
    slug = parts[-2] if len(parts) >= 2 and re.fullmatch(r"p\d+", parts[-1]) else parts[-1]
    slug = re.sub(r"\.html$", "", slug)
    return " ".join(w for w in slug.split("-") if not re.fullmatch(r"\d{6,}", w))


def page_img(html):
    for pat in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                r'"image"\s*:\s*\[?\s*"(https://[^"]+)"'):
        m = re.search(pat, html or "")
        if m and m.group(1).startswith("https://"):
            return m.group(1).replace("&amp;", "&")
    return None


def wayback_aldi(name):
    """Gelöschte Aldi-Produktseite im Internet-Archiv suchen (Seitenname beginnt mit Marke-Produktlinie)."""
    t = toks(name)
    if len(t) < 2:
        return None, None
    q = urllib.parse.urlencode({"url": f"www.aldi-sued.de/produkt/{t[0]}-{t[1]}", "matchType": "prefix", "output": "json",
                                "fl": "timestamp,original", "filter": "statuscode:200", "collapse": "urlkey", "limit": "30"})
    txt = http("https://web.archive.org/cdx/search/cdx?" + q)
    time.sleep(PAUSE)
    try:
        rows = json.loads(txt)[1:] if txt and txt.strip() else []
    except Exception:
        rows = []
    if not rows:
        return None, None
    pool = Pool()
    for ts, orig in rows:
        pool.add(slug_name(orig), f"{ts}|{orig}")
    hit = pool.find(name)
    if not hit:
        return None, None
    ts, orig = hit.split("|", 1)
    return ts, orig


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def load(name, default):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def norm(s):
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("è", "e")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def toks(s):
    return [t for t in (norm(w) for w in re.findall(r"[A-Za-zÄÖÜäöüßéè0-9]+", s or "")) if len(t) > 1 and not FILL.match(t)]


def cat_url(c):
    return OFF_IMG[c[0]] + c[2:] + ".jpg" if c and c[1] == ":" and c[0] in OFF_IMG else c


class Pool:
    """Alle bekannten Bilder: exakt per norm(Name) und nach Marke (erstes Wort) für die Ähnlichkeitssuche."""

    def __init__(self):
        self.exact, self.brand = {}, {}

    def add(self, name, url):
        if not url or not name:
            return
        k = norm(name)
        if k and k not in self.exact:
            self.exact[k] = url
        t = toks(name)
        if len(t) >= 2:
            self.brand.setdefault(t[0], []).append((set(t[1:]), t[1], url))

    def find(self, name, loose=False):
        """loose=True: notfalls gleiche Marke + gleiche Produktlinie in anderer Sorte (z. B. IronMaxx SqueeBarista
        Dark Chocolate für Caramel – gleiche Packung). Nur wenn die Produktlinie ein echtes Wort ist (>= 5 Zeichen)."""
        k = norm(name)
        if k in self.exact:
            return self.exact[k]
        t = toks(name)
        if len(t) < 2:
            return None
        if loose:
            if len(t[1]) < 5:
                return None
            best, bu = -1, None
            for ws, first, url in self.brand.get(t[0], ()):
                if first == t[1]:
                    sc = len(set(t[1:]) & ws) - 0.01 * len(ws)
                    if sc > best:
                        best, bu = sc, url
            return bu
        want = set(t[1:])
        best, bu = 0, None
        for ws, first, url in self.brand.get(t[0], ()):
            # Produktlinie (erstes Wort nach der Marke) muss passen, dazu mind. 60 % der übrigen Wörter
            if first != t[1] and t[1] not in ws:
                continue
            same = len(want & ws)
            score = same / max(len(want), len(ws))
            if same >= min(2, len(want)) and same >= 0.6 * len(want) and score > best:
                best, bu = score, url
        return bu


def main():
    today = date.today().isoformat()
    offers = load("offers.json", {})
    offers = offers.get("offers", []) if isinstance(offers, dict) else offers
    names = load("names.json", {})
    nimg = load("names-img.json", {})
    cat = load("catalog.json", [])
    cimg = load("catalog-img.json", [])
    extra = load("img-extra.json", {})
    miss = load("img-miss.json", {})

    pool = Pool()
    for o in offers:
        if o.get("img"):
            full = o["n"] if not o.get("b") or norm(o["b"]) in norm(o["n"]) else f"{o['b']} {o['n']}"
            pool.add(full, o["img"]); pool.add(o["n"], o["img"])
    for n, u in nimg.items():
        pool.add(n, u)
    for i, n in enumerate(cat):
        if i < len(cimg) and cimg[i]:
            pool.add(n, cat_url(cimg[i]))
    for n, u in extra.items():
        pool.add(n, u)
    for n, c in load("img-pool.json", {}).items():  # Datenexport: weitere Artikel mit Bild (nicht im Artikelstamm)
        pool.add(n, cat_url(c))

    need = []
    for n in names:
        if n not in nimg and n not in extra:
            need.append(n)
    for i, n in enumerate(cat):
        if not (i < len(cimg) and cimg[i]) and n not in extra:
            need.append(n)
    need = list(dict.fromkeys(need))
    log("Ohne Bild:", len(need), "Artikel")

    local = 0
    rest = []
    for n in need:
        u = pool.find(n)
        if u:
            extra[n] = u; local += 1
        else:
            rest.append(n)
    log("Aus eigenen Daten gefunden:", local)

    # 4./5. Netz-Suche: Aldi-/Lidl-Produktseiten (Sitemaps) und gelöschte Aldi-Seiten im Internet-Archiv.
    # Erst die, die noch nie probiert wurden oder deren letzter Versuch >= 7 Tage her ist.
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    # miss-Wert „JJJJ-MM-TT+n“ = schon im Netz gesucht; ältere Einträge ohne „+n“ kannten die Netz-Quellen noch nicht.
    todo = [n for n in rest if not str(miss.get(n, "")).endswith("+n") or miss[n][:10] <= cutoff]
    net = 0
    if MAX_NET and todo:
        shops = Pool()
        for shop, sm in SITEMAPS.items():
            urls = sitemap_urls(sm, r"/produkt/|/p/[^/]+/p\d+")
            log(f"Sitemap {shop}: {len(urls)} Produktseiten")
            for u in urls:
                shops.add(slug_name(u), u)
        found, tried = 0, set()
        # Durchgang 1: aktuelle Produktseiten (Sitemap-Treffer), Durchgang 2: Internet-Archiv
        for n in todo:
            if net >= MAX_NET:
                break
            page = shops.find(n)
            if page:
                html = http(page); net += 1; time.sleep(PAUSE)
                img = page_img(html)
                if img:
                    extra[n] = img; found += 1; log("   +", n, "->", img[:100])
        for n in todo:
            if net >= MAX_NET:
                break
            if n in extra:
                continue
            ts, orig = wayback_aldi(n); net += 1
            if ts:
                html = http(f"https://web.archive.org/web/{ts}id_/{orig}"); net += 1; time.sleep(PAUSE)
                im = page_img(html)
                if im:  # Bild über das Archiv laden (Original-Adresse kann schon gelöscht sein)
                    extra[n] = f"https://web.archive.org/web/{ts}im_/{im}"; found += 1; log("   + (Archiv)", n, "->", im[:90])
            tried.add(n)
        # Durchgang 3: gleiche Marke + Produktlinie, andere Sorte (eigene Daten, dann Aldi-/Lidl-Produktseiten)
        for n in todo:
            if n in extra:
                continue
            u = pool.find(n, loose=True)
            if not u and net < MAX_NET:
                page = shops.find(n, loose=True)
                if page:
                    html = http(page); net += 1; time.sleep(PAUSE)
                    u = page_img(html)
            if u:
                extra[n] = u; found += 1; log("   ~ (gleiche Produktlinie)", n, "->", u[:90])
        for n in tried:
            if n not in extra:
                miss[n] = today + "+n"
        rest = [n for n in rest if n not in extra]
        log(f"Aus Aldi-/Lidl-Produktseiten und Archiv gefunden: {found} ({net} Abrufe)")

    for n in rest:
        miss.setdefault(n, today)
    log("Noch ohne Bild:", len(rest))

    keep = set(names) | set(cat)
    extra = {k: v for k, v in extra.items() if k in keep and isinstance(v, str) and v.startswith("https://")}
    miss = {k: v for k, v in miss.items() if k in keep and k not in extra}
    save("img-extra.json", extra)
    save("img-miss.json", miss)
    left = sum(1 for n in need if n not in extra)
    log(f"img-extra.json: {len(extra)} Bilder · noch ohne Bild: {left}")


if __name__ == "__main__":
    main()
