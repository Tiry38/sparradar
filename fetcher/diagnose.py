"""Diagnose (nur von Hand): prospektewoche.de – stimmen die Daten der Woche 2 (02.11.) wirklich?
Vergleicht Produktkarten im HTML und die Seiten-JSONs /images/prospekte/<markt>/weekN/<seite>.json."""
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


def cards(h):
    out = []
    for m in re.finditer(r'class="product-card-price">([\d.,]+)<', h):
        seg = h[max(0, m.start() - 2500):m.start()]
        t = re.findall(r'class="product-card-(?:title|name|brand)[^"]*"[^>]*>([^<]+)<', seg)
        out.append((t[-2:] if t else "?", m.group(1)))
    return out


for shop in ("rewe",):
    for wk in ("1", "2"):
        st, h = get(f"https://prospektewoche.de/{shop}?week={wk}")
        c = cards(h)
        print(f"\n=== {shop} week={wk} {st} Karten={len(c)}")
        print("  ", c[:15])
        print("  Klassen:", sorted(set(re.findall(r'class="(product-card[^"]*)"', h)))[:30])
        print("  JSON-URLs:", sorted(set(re.findall(r'data-json-url="([^"]+)"', h)))[:30])
        print("  Tabs:", re.findall(r'tab-dates">([^<]+)<', h))
    for wk in ("week1", "week2"):
        for pg in (1, 2):
            st, t = get(f"https://prospektewoche.de/images/prospekte/{shop}/{wk}/{pg}.json")
            print(f"\n--- {wk}/{pg}.json {st} {len(t)}")
            print("  ", t[:1500])
