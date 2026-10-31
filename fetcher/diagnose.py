"""Einmalige Diagnose: Wie viele Angebote liefern die Quellen wirklich, gibt es weitere Seiten?
Nur von Hand starten (Workflow „Diagnose“). Wenige Abrufe mit Pausen, ehrlicher User-Agent."""
import json
import time
import urllib.parse

import fetch_offers as f


def walk(o, path="", depth=0, out=None):
    """Listen mit Länge und auffällige Zähler/Seiten-Felder auflisten."""
    out = [] if out is None else out
    if depth > 6:
        return out
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}"
            if any(w in k.lower() for w in ("total", "count", "page", "next", "more", "limit", "offset", "cursor")) and not isinstance(v, (dict, list)):
                out.append(f"  FELD {p} = {v!r}"[:200])
            walk(v, p, depth + 1, out)
    elif isinstance(o, list):
        if o and len(o) > 2:
            out.append(f"  LISTE {path} [{len(o)}]")
        if o:
            walk(o[0], path + "[0]", depth + 1, out)
    return out


def kd(url):
    h = f.http(url)
    time.sleep(f.PAUSE)
    print("\n=== kaufDA", url, "->", "OK" if h else "FEHLER", len(h or ""), "Zeichen")
    if not h:
        return
    import re
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        print("  kein __NEXT_DATA__")
        return
    d = json.loads(m.group(1))
    pp = (d.get("props") or {}).get("pageProps") or {}
    print("  pageProps-Schlüssel:", list(pp)[:30])
    pi = pp.get("pageInformation") or {}
    print("  pageInformation-Schlüssel:", list(pi)[:40])
    for line in walk(pp)[:80]:
        print(line)
    offers = (pi.get("offers") or {})
    for k, v in offers.items():
        items = (v or {}).get("items") if isinstance(v, dict) else None
        print(f"  offers.{k}: {len(items) if isinstance(items, list) else type(v).__name__}", {kk: vv for kk, vv in (v or {}).items() if kk != 'items'} if isinstance(v, dict) else "")
    br = pi.get("brochures") or pp.get("brochures")
    if br:
        print("  BROSCHUEREN-Beispiel:", json.dumps(br if isinstance(br, dict) else br[:2], ensure_ascii=False)[:1500])
    items = ((offers.get("main") or {}).get("items") or [])
    if items:
        print("  Angebot-Beispiel:", json.dumps(items[0], ensure_ascii=False)[:1200])
        pubs = {}
        for it in items:
            pubs[it.get("publisherName")] = pubs.get(it.get("publisherName"), 0) + 1
        print("  Händler in main:", pubs)


def lidl(q):
    url = "https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1" + q
    raw = f.http(url)
    time.sleep(f.PAUSE)
    print("\n=== Lidl", q, "->", "OK" if raw else "FEHLER")
    if not raw:
        return
    d = json.loads(raw)
    items = d.get("items") or []
    disc = 0
    for it in items:
        pr = ((it.get("gridbox") or {}).get("data") or {}).get("price") or {}
        if (pr.get("discount") or {}).get("showDiscount") or (pr.get("oldPrice") or 0) > (pr.get("price") or 0):
            disc += 1
    print(f"  items={len(items)} davon mit Rabatt={disc}", {k: v for k, v in d.items() if not isinstance(v, (list, dict))})
    for line in walk({k: v for k, v in d.items() if k != "items"})[:30]:
        print(line)
    for it in items[:40]:
        g = (it.get("gridbox") or {}).get("data") or {}
        if "tassimo" in (g.get("fullTitle") or "").lower() or q.endswith("tassimo"):
            print("   ", g.get("fullTitle"), (g.get("price") or {}).get("price"), (g.get("price") or {}).get("oldPrice"), g.get("stores"), g.get("canonicalUrl"))


if __name__ == "__main__":
    for u in f.KD_STORES.values():
        kd(u)
    kd(f.KD_STORES["lidl"] + "?page=2")
    kd(f"https://www.kaufda.de/{f.KD_CITY}/Angebote/Tassimo")
    lidl("&category.id=10068374&fetchsize=500&offset=0")
    lidl("&category.id=10068374&fetchsize=500&offset=500")
    lidl("&q=tassimo&fetchsize=100&offset=0")
    lidl("&q=kaffee&fetchsize=200&offset=0")
