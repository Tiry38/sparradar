"""Diagnose (nur von Hand): Edeka-/Rewe-/dm-Angebote der nächsten Woche identifizieren.
Vergleicht Händler-Kennungen (publisherId) der lokalen Seiten mit den Sortiment-Seiten und prüft rewe.de."""
import collections
import json
import re
import urllib.request

import fetch_offers as f


def nd(url):
    h = f.http(url) or ""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    return (json.loads(m.group(1)).get("props") or {}).get("pageProps") or {} if m else {}


def items_of(pp):
    pi = pp.get("pageInformation") or {}
    out = list(((pi.get("offers") or {}).get("main") or {}).get("items") or [])
    for k, v in (pp.get("pageInformation") or {}).items():
        pass
    return out


def show(label, items):
    c = collections.Counter((it.get("publisherName"), it.get("publisherId"), str(it.get("validFrom"))[:10],
                             str((it.get("parentContent") or {}).get("id"))) for it in items)
    print(f"\n=== {label}: {len(items)} Angebote")
    for k, n in c.most_common(12):
        print("   ", n, k)


for store, url in f.KD_STORES.items():
    pp = nd(url)
    show(f"Lokal {store}", items_of(pp))
    pi = pp.get("pageInformation") or {}
    for key in ("viewer", "publisher", "sector"):
        lst = (pi.get("brochures") or {}).get(key)
        for b in lst if isinstance(lst, list) else []:
            print("   PROSPEKT", key, "|", b.get("title"), "|", str(b.get("validFrom"))[:10], "|",
                  {k: b.get(k) for k in ("publisherId", "publisherName", "publisher", "id") if k in b})

for slug in ("Edeka", "REWE", "DM"):
    for term in ("Kaffee", "Butter", "Kaese", "Aktionen"):
        pp = nd(f"https://www.kaufda.de/{slug}/Sortiment/{term}")
        show(f"Sortiment {slug}/{term}", items_of(pp))

pp = nd("https://www.kaufda.de/Berlin/EDEKA/p-r107")
for key in ("viewer", "publisher"):
    for b in (pp.get("pageInformation") or {}).get("brochures", {}).get(key) or []:
        if isinstance(b, dict):
            print("BERLIN EDEKA", key, b.get("title"), str(b.get("validFrom"))[:10], {k: b.get(k) for k in ("publisherId", "publisherName", "id") if k in b})

for path in ("/angebote/nationale-angebote/topangebote/", "/angebote/nationale-angebote/getraenke/", "/angebote/nationale-angebote/kuehlung/"):
    try:
        req = urllib.request.Request("https://www.rewe.de" + path, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            h = r.read().decode("utf-8", "replace")
            print("REWE.DE", path, r.status, len(h), re.findall(r"(?:gültig|ab)[^<]{0,40}\d\d\.\d\d\.", h)[:3])
    except Exception as e:
        print("REWE.DE", path, getattr(e, "code", e))
