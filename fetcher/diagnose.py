"""Einmalige Diagnose: Wo stehen App-Preise (Lidl Plus, Rewe Bonus, Netto-App, Payback) in den Daten?
Nur von Hand starten (Workflow „Diagnose“). Wenige Abrufe mit Pausen, ehrlicher User-Agent."""
import json
import re

import fetch_offers as f

HINT = re.compile(r"plus|\bapp\b|bonus|payback|coupon|mitglied|vorteil", re.I)


def kd(name, url, pages=4):
    keys, pkeys, shown = set(), set(), 0
    for page in range(1, pages + 1):
        items, total = f.kd_page(url if page == 1 else f"{url}?page={page}")
        for it in items:
            keys |= set(it)
            pkeys |= set(it.get("prices") or {})
            txt = json.dumps({k: v for k, v in it.items() if k not in ("offerImages",)}, ensure_ascii=False)
            if HINT.search(txt) and shown < 6:
                shown += 1
                print(f"  [{name}] {it.get('title')} | desc={it.get('description')!r}")
                print("     prices=", json.dumps(it.get("prices"), ensure_ascii=False))
                rest = {k: v for k, v in it.items() if k not in ("offerImages", "prices", "title", "description", "categoryPaths", "parentContent")}
                print("     rest=", json.dumps(rest, ensure_ascii=False)[:900])
    print(f"=== {name}: Felder={sorted(keys)}")
    print(f"    Preis-Felder={sorted(pkeys)}")


def lidl():
    raw = f.http("https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1&category.id=10068374&fetchsize=60&offset=0")
    d = json.loads(raw or "{}")
    keys = set()
    for it in d.get("items") or []:
        g = (it.get("gridbox") or {}).get("data") or {}
        keys |= set(g)
        if g.get("lidlPlus"):
            print("  [lidl.de] Lidl Plus:", g.get("fullTitle"), json.dumps(g.get("lidlPlus"), ensure_ascii=False)[:600], "| price=", json.dumps(g.get("price"), ensure_ascii=False)[:400])
    print("=== lidl.de gridbox-Felder:", sorted(keys))


if __name__ == "__main__":
    for name, url in f.KD_STORES.items():
        kd(name, url)
    lidl()
