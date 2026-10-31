"""Diagnose (nur von Hand): alle dm-Aktionsseiten (/neu/aktionen/...) über den öffentlichen Inhalts-Dienst, den dm.de selbst lädt.
Kein Schlüssel, keine Anmeldung; robots.txt von content.services.dmtech.com existiert nicht (404 = keine Einschränkung)."""
import collections
import json
import re
import time
import urllib.request

import fetch_offers as f

CS = "https://content.services.dmtech.com/rootpage-dm-shop-de-de"


def get(path):
    try:
        req = urllib.request.Request(CS + path, headers={"User-Agent": f.UA, "Accept-Language": "de-DE", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        print("  Fehler", path, getattr(e, "code", str(e)[:60]))
        return None


def walk(o, types, links, texts):
    if isinstance(o, dict):
        if "type" in o:
            types[o["type"]] += 1
        lt = o.get("linkTarget")
        if isinstance(lt, str):
            links.add(lt)
        for v in o.values():
            walk(v, types, links, texts)
    elif isinstance(o, list):
        for v in o:
            walk(v, types, links, texts)
    elif isinstance(o, str) and len(o) > 2:
        texts.append(o)


paths = ["/neu/aktionen", "/neu/marken-highlights", "/neu/limited-editions"]
seen = set()
for p in paths[:]:
    d = get(p)
    time.sleep(f.PAUSE)
    types, links, texts = collections.Counter(), set(), []
    walk(d, types, links, texts)
    print(f"\n##### {p} Typen:", dict(types))
    for l in sorted(links):
        print("   Link:", l)
        m = re.match(r"https://www\.dm\.de(/neu/aktionen/[^?#]+)", l)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            paths.append(m.group(1))

for p in paths[3:40]:
    d = get(p)
    time.sleep(f.PAUSE)
    if not d:
        continue
    types, links, texts = collections.Counter(), set(), []
    walk(d, types, links, texts)
    full = " ".join(texts)
    print(f"\n=== {p}")
    print("  Typen:", dict(types))
    print("  Text:", full[:500])
    print("  Daten:", re.findall(r"\d\d\.\d\d\.(?:20\d\d)?\s*[–-]\s*\d\d\.\d\d\.20\d\d|ab \d\d\.\d\d\.|bis \d\d\.\d\d\.", full)[:6])
    print("  Preise/€:", re.findall(r"\d+[,.]\d\d\s*€|\d+\s*%", full)[:10])
    print("  Produkt-Links:", [l for l in links if "/p/" in l or "dan" in l.lower()][:8])
    for k in ("DMProductTeaser", "ProductTeaser", "DMProductList", "DMProductSlider", "ProductSlider"):
        pass
    js = json.dumps(d)
    for key in ("dan", "gtin", "productIds", "query", "filters"):
        hits = re.findall(rf'"{key}"\s*:\s*("[^"]{{1,120}}"|\[[^\]]{{0,200}}\]|\{{[^}}]{{0,200}}\}})', js)
        hits = [h for h in hits if h not in ('{}', '""')]
        if hits:
            print(f"  {key}:", hits[:5])
