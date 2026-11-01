"""SparRadar Bilder-Wächter: Jeder Artikel in der App soll ein Bild haben.

Läuft mehrmals am Tag (.github/workflows/bilder.yml). Geht alle Artikelnamen durch
(Angebote, docs/data/names.json, Artikelstamm docs/data/catalog.json) und sucht für jeden
Artikel ohne Bild eines:
  1. gleicher Name (Schreibweise egal) in unseren eigenen Daten (Angebote, names-img, Artikelstamm),
  2. gleicher Markenartikel mit anderer Packungsgröße/Sorte (gleiche Marke + gleiche Produktwörter),
  3. Open-Food-Facts-/Open-Beauty-Facts-Suche (offene Datenbanken, robots.txt erlaubt,
     ehrlicher User-Agent, Pausen, höchstens MAX_NET Anfragen pro Lauf).
Ergebnis: docs/data/img-extra.json {Artikelname: Bild-Adresse}. Fehlversuche merkt sich
docs/data/img-miss.json (neuer Versuch nach 7 Tagen). Nie fremde Bilder raten: es müssen Marke
und Produktwörter passen.
"""
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
MAX_NET = int(os.environ.get("SR_IMG_MAX", "120"))
PAUSE = 6.5  # Open Food Facts erlaubt ca. 10 Suchanfragen pro Minute
OFF_IMG = {"f": "https://images.openfoodfacts.org/images/products/",
           "b": "https://images.openbeautyfacts.org/images/products/"}
FILL = re.compile(r"^(\d.*|g|kg|ml|l|cl|x|xl|xxl|st|stk|stueck|pack|packung|bigpack|big|cups?|portionen|kapseln|"
                  r"und|mit|fuer|der|die|das|von|oder|je|ca|im|in|aus|zum|zur|de|la|le|the|of|bio|neu)$")


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

    def find(self, name):
        k = norm(name)
        if k in self.exact:
            return self.exact[k]
        t = toks(name)
        if len(t) < 2:
            return None
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


def off_search(name):
    """Open Food Facts / Open Beauty Facts: Volltextsuche, erstes Ergebnis mit Bild, dessen Marke + Wörter passen."""
    t = toks(name)
    if len(t) < 2:
        return None
    for host, key in (("world.openfoodfacts.org", "f"), ("world.openbeautyfacts.org", "b")):
        q = urllib.parse.urlencode({"search_terms": name, "search_simple": 1, "action": "process", "json": 1,
                                    "page_size": 10, "fields": "product_name,product_name_de,brands,image_front_small_url,image_small_url"})
        try:
            req = urllib.request.Request(f"https://{host}/cgi/search.pl?{q}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                prods = json.loads(r.read().decode("utf-8", "replace")).get("products", [])
        except Exception as e:
            log("   ! Suche", host, str(e)[:60])
            prods = []
        time.sleep(PAUSE)
        p = Pool()
        for x in prods:
            url = x.get("image_front_small_url") or x.get("image_small_url")
            if not url:
                continue
            nm = x.get("product_name_de") or x.get("product_name") or ""
            br = (x.get("brands") or "").split(",")[0].strip()
            full = nm if norm(br) and norm(br) in norm(nm) else f"{br} {nm}"
            p.add(full, url)
        hit = p.find(name)
        if hit:
            return hit
    return None


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

    cutoff = (date.today() - timedelta(days=7)).isoformat()
    todo = [n for n in rest if miss.get(n, "") < cutoff]
    # zuerst Namen aus echten Angeboten, dann der Artikelstamm
    todo.sort(key=lambda n: n not in names)
    net = 0
    for n in todo[:MAX_NET]:
        u = off_search(n)
        if u:
            extra[n] = u; net += 1; miss.pop(n, None)
            pool.add(n, u)
        else:
            miss[n] = today
    log("Per Suche gefunden:", net, "von", min(len(todo), MAX_NET), "· offen:", len(rest) - net)

    keep = set(names) | set(cat)
    extra = {k: v for k, v in extra.items() if k in keep and isinstance(v, str) and v.startswith("https://")}
    miss = {k: v for k, v in miss.items() if k in keep and k not in extra}
    save("img-extra.json", extra)
    save("img-miss.json", miss)
    left = sum(1 for n in need if n not in extra)
    log(f"img-extra.json: {len(extra)} Bilder · noch ohne Bild: {left}")


if __name__ == "__main__":
    main()
