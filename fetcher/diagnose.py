"""Diagnose (03.11.): Taugen Oktober-Schnappschüsse im Internet-Archiv für den Preisverlauf?
Geprüft: welche kaufDA-Seiten unter /Angebote… liegen, und was alte lidl.de-/aldi-sued.de-Produktseiten an Preis/Datum enthalten."""
import collections
import gzip
import json
import re
import time
import urllib.parse
import urllib.request

UA = "SparRadar/1.0 (+https://github.com/Tiry38/sparradar; private Angebots-App)"


def get(u, timeout=90):
    for i in range(3):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=timeout).read()
            return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8", "replace")
        except Exception as e:
            print("  Fehler", u[:100], e)
            time.sleep(10 * (i + 1))
    return None


def cdx(pat, limit=20000):
    q = urllib.parse.urlencode({"url": pat, "from": "20261005", "to": "20261031", "output": "json",
                                "fl": "timestamp,original", "filter": "statuscode:200", "limit": str(limit)})
    t = get("https://web.archive.org/cdx/search/cdx?" + q, 150)
    return json.loads(t or "[]")[1:]


rows = cdx("www.kaufda.de/Angebote*")
urls = collections.Counter(r[1].split("?")[0] for r in rows)
print("=== kaufDA /Angebote*: verschiedene Seiten", len(urls))
for u, n in urls.most_common(100):
    print("  ", n, u)

for pat, words in (("www.lidl.de/p/*", ("hackfleisch", "milch", "butter", "kaese", "joghurt", "banane")),
                   ("www.aldi-sued.de/produkt/*", ("hackfleisch", "milch", "butter", "kaese", "joghurt"))):
    rows = cdx(pat, 8000)
    pick = [r for r in rows if any(w in r[1].lower() for w in words)][:3] or rows[:3]
    print(f"=== {pat}: {len(rows)} Schnappschüsse, Probe:")
    for ts, u in pick:
        h = get(f"https://web.archive.org/web/{ts}id_/{u}")
        print("  ---", ts, u[:140], len(h or ""), "Zeichen")
        if not h:
            continue
        for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S):
            print("   LD:", re.sub(r"\s+", " ", m.group(1))[:900])
        for k in ("price", "Price", "validFrom", "valid_from", "startDate", "gültig", "ab ", "statt", "UVP", "isDropship",
                  "onSaleDate", "wasPrice", "strikePrice", "oldPrice", "inStore", "filial"):
            for m in list(re.finditer(re.escape(k), h))[:2]:
                print(f"   [{k}]", re.sub(r"\s+", " ", h[max(0, m.start() - 120):m.start() + 200]))
        time.sleep(3)
