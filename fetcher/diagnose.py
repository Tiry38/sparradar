"""Diagnose: Warum liefert das Nachtragen aus dem Internet-Archiv 0 Preise? Liest ein paar alte Schnappschüsse."""
import json
import re
import time
import urllib.parse
import urllib.request

import backfill_history as b
import fetch_offers as f


def get(u, to=30):
    t = time.time()
    try:
        req = urllib.request.Request(u, headers={"User-Agent": f.UA})
        with urllib.request.urlopen(req, timeout=to) as r:
            return r.read().decode("utf-8", "replace"), round(time.time() - t, 1), r.status
    except Exception as e:
        return None, round(time.time() - t, 1), str(e)[:90]


q = {"url": "www.kaufda.de/Lidl/Sortiment/*", "from": "20260901", "to": "20261031", "output": "json",
     "fl": "timestamp,original,digest,statuscode,mimetype", "filter": "statuscode:200", "collapse": "digest", "limit": "40"}
txt, sec, st = get("https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(q), 60)
print("CDX", sec, "s", st)
rows = json.loads(txt)[1:] if txt else []
print(len(rows), "Zeilen, z. B.", rows[:3])
for ts, url, *_ in rows[::8][:5]:
    for form in ("id_", ""):
        h, sec, st = get(f"https://web.archive.org/web/{ts}{form}/{url}")
        time.sleep(2)
        print(f"\n{ts} {form or 'ohne id_'} {url}: {sec}s {st} len={len(h) if h else 0}")
        if not h:
            continue
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
        print("  NEXT_DATA:", bool(m), "| <title>", (re.search(r"<title>(.*?)</title>", h, re.S) or [None, "-"])[1][:80])
        if not m:
            print("  Anfang:", re.sub(r"\s+", " ", h[:300]))
            continue
        d = json.loads(m.group(1))
        pp = (d.get("props") or {}).get("pageProps") or {}
        print("  pageProps-Schlüssel:", list(pp)[:12])
        pi = pp.get("pageInformation") or {}
        print("  pageInformation-Schlüssel:", list(pi)[:15])
        items = ((pi.get("offers") or {}).get("main") or {}).get("items") or []
        print("  items:", len(items), "| Händler:", sorted({str(i.get("publisherName")) for i in items})[:5])
        if items:
            print("  Beispiel-Schlüssel:", list(items[0])[:20])
            print("  Preise:", items[0].get("prices"))
        offs = b.offers_kd(h)
        print("  offers_kd:", len(offs), [(o["n"][:30], o["p"], o.get("from")) for o in offs[:3]])
