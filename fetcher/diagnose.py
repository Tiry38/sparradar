"""Diagnose (nur von Hand): Aufbau der Prospekt-Daten auf prospektewoche.de (Rewe, dm, Edeka)."""
import json
import re
import urllib.request

import fetch_offers as f


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", str(e)[:60]), ""


st, sm = get("https://prospektewoche.de/sitemap.xml")
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
print("SITEMAP", st, len(locs), [u for u in locs if re.search(r"dm|drog|edeka|rewe|netto|aldi|lidl", u, re.I)][:40])

for path in ("/rewe", "/rewe?week=1", "/rewe?week=2", "/edeka", "/dm-drogerie-markt", "/dm-drogerie"):
    st, h = get("https://prospektewoche.de" + path)
    print(f"\n=== {path} {st} {len(h)}")
    for m in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S):
        try:
            j = json.loads(m)
        except Exception as e:
            print("  LD-Fehler", e, m[:200])
            continue
        if j.get("@type") == "ItemList":
            el = j.get("itemListElement") or []
            print("  ITEMLIST", j.get("name"), j.get("numberOfItems"), len(el))
            for x in el[:4]:
                print("   ", json.dumps(x, ensure_ascii=False)[:900])
            keys = {}
            for x in el:
                it = x.get("item") or {}
                for k, v in it.items():
                    keys.setdefault(k, 0)
                    keys[k] += 1
                    if isinstance(v, dict):
                        for k2 in v:
                            keys.setdefault(k + "." + k2, 0)
                            keys[k + "." + k2] += 1
            print("  FELDER", keys)
            print("  OHNE PREIS", [((x.get("item") or {}).get("name")) for x in el if not ((x.get("item") or {}).get("offers") or {}).get("price")][:20])
    i = h.find("Knoppers")
    if i > 0:
        print("  HTML um Knoppers:", re.sub(r"\s+", " ", h[i - 1500:i + 1500]))
