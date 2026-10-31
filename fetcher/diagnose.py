"""Diagnose (nur von Hand): Ab wann sind die Angebote der NÄCHSTEN Woche in welcher Quelle öffentlich?
Zeigt je Markt die Prospekte mit Gültigkeit und prüft Aldi Süd und lidl.de auf künftige Angebote."""
import datetime as dt
import json
import re

import fetch_offers as f

today = dt.date.today().isoformat()
print("Heute:", today)

# kaufDA: Prospekte je Händlerseite (Titel, gültig ab/bis)
for store, url in f.KD_STORES.items():
    h = f.http(url)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
    if not m:
        print(store, "keine Daten")
        continue
    pi = json.loads(m.group(1))["props"]["pageProps"]["pageInformation"]
    for key, lst in (pi.get("brochures") or {}).items():
        for b in (lst if isinstance(lst, list) else []):
            if isinstance(b, dict):
                if key != "viewer" and (b.get("validFrom") or "")[:10] <= today:
                    continue  # nur Hauptprospekt + alles, was erst künftig gilt
                print("KD", store, key, "|", str(b.get("title"))[:50], "|", b.get("validFrom"), "->", b.get("validUntil"),
                      "| Seiten", b.get("pageCount"), "| id", b.get("id") or b.get("contentId"))
    items = (pi.get("offers") or {}).get("main", {}).get("items") or []
    fut = [it for it in items if (it.get("validFrom") or "")[:10] > today]
    print("KD", store, "Angebote auf der Seite:", len(items), "davon künftig:", len(fut))

# Aldi Süd: Links zu Angebots-Wochen und künftige Startdaten
h = f.http("https://www.aldi-sued.de/de/angebote.html") or ""
links = sorted(set(re.findall(r'href="(/de/angebote[^"#?]*)"', h)))
print("ALDI Links:", links[:40])
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
if m:
    data = json.loads(m.group(1))
    dates = {}
    for i, v in enumerate(data):
        if isinstance(v, dict) and "onSaleDate" in v and "sku" in v:
            it = f.nuxt_resolve(data, i)
            d = str(it.get("onSaleDate"))[:10]
            dates[d] = dates.get(d, 0) + 1
    print("ALDI Startdaten:", dict(sorted(dates.items())))
for path in links:
    if re.search(r"\d|montag|donnerstag|freitag|naechste|vorschau|woche", path):
        hh = f.http("https://www.aldi-sued.de" + path) or ""
        mm = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', hh, re.S)
        n = 0
        ds = {}
        if mm:
            dd = json.loads(mm.group(1))
            for i, v in enumerate(dd):
                if isinstance(v, dict) and "onSaleDate" in v and "sku" in v:
                    n += 1
                    d = str(f.nuxt_resolve(dd, i).get("onSaleDate"))[:10]
                    ds[d] = ds.get(d, 0) + 1
        print("ALDI Seite", path, "Artikel:", n, dict(sorted(ds.items())))

# lidl.de: Artikel mit Startdatum in der Zukunft
fut = {}
for q in ("&category.id=10068374", "&q=angebot"):
    raw = f.http("https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1" + q + "&fetchsize=60&offset=0")
    try:
        items = json.loads(raw).get("items") or []
    except (TypeError, ValueError):
        items = []
    for it in items:
        pr = ((it.get("gridbox") or {}).get("data") or {}).get("price") or {}
        d = str(pr.get("startDate") or "")[:10]
        if d > today:
            fut[d] = fut.get(d, 0) + 1
print("LIDL künftige Startdaten (Stichprobe):", fut)
