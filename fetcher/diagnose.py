"""Einmalige Diagnose: dm-Produktsuche – wie findet man alle Aktionen? (Nur von Hand, wenige Abrufe.)"""
import json
import time

import fetch_offers as f

B = "https://product-search.services.dmtech.com/de/search"


def get(q):
    raw = f.http(B + q)
    time.sleep(2)
    try:
        return json.loads(raw or "")
    except ValueError:
        print("kein JSON für", q)
        return {}


f.log("robots:", (f.http("https://product-search.services.dmtech.com/robots.txt") or "")[:300])
d = get("?query=&pageSize=60&currentPage=0")
print("Schlüssel:", [k for k in d if k != "products"], {k: v for k, v in d.items() if not isinstance(v, (list, dict))})
for fa in d.get("facets") or []:
    vals = fa.get("values") or fa.get("facetValues") or []
    print("FACET", fa.get("name") or fa.get("id") or fa.get("key"), "|", json.dumps(fa, ensure_ascii=False)[:300])
print("Produkt-Felder:", sorted((d.get("products") or [{}])[0].keys()))
p0 = (d.get("products") or [{}])[0]
print("Beispiel tileData.price:", json.dumps((p0.get("tileData") or {}).get("price"), ensure_ascii=False)[:500])
print("Beispiel sonst:", json.dumps({k: v for k, v in p0.items() if k not in ("tileData",)}, ensure_ascii=False)[:800])
for q in ("?query=&pageSize=60&currentPage=0&isNew=false&type=search&promotion=true",
          "?query=angebot&pageSize=60&currentPage=0", "?query=kaffee&pageSize=60&currentPage=0"):
    dd = get(q)
    ps = dd.get("products") or []
    red = sum(1 for p in ps if (((p.get("tileData") or {}).get("price") or {}).get("price") or {}).get("previous"))
    print(q, "->", len(ps), "Produkte, davon reduziert:", red, {k: v for k, v in dd.items() if not isinstance(v, (list, dict))})
