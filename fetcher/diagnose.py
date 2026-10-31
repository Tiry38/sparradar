"""Diagnose (nur von Hand): Welche Preisfelder liefern die Quellen bei hohen Rabatten?
Gesucht: „niedrigster Preis der letzten 30 Tage“ (PAngV §11), „UVP“, Grundpreis usw."""
import json

import fetch_offers as f


def show(tag, obj):
    print(tag, json.dumps(obj, ensure_ascii=False)[:900])


# kaufDA: Händlerseiten + ein paar Sortiment-Seiten, alle Preisobjekte mit hohem Rabatt
seen = 0
for url in list(f.KD_STORES.values()) + ["https://www.kaufda.de/Netto-Marken-Discount/Sortiment/Butter",
                                        "https://www.kaufda.de/Edeka/Sortiment/Joghurt",
                                        "https://www.kaufda.de/Lidl/Sortiment/Eis"]:
    try:
        items, _ = f.kd_page(url)
    except Exception as e:
        print("FEHLER", url, e)
        continue
    for it in items:
        pr = it.get("prices") or {}
        p, o = pr.get("mainPrice") or 0, pr.get("secondaryPrice") or 0
        if seen < 3 or (p and o and p / o <= 0.6):
            seen += 1
            show("KD " + str(it.get("publisherName")) + " | " + str(it.get("title")), {"prices": pr, "keys": sorted(it.keys())})

# Lidl: Preisobjekte mit hohem Rabatt
raw = f.http("https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1&q=eis&fetchsize=60&offset=0")
d = json.loads(raw)
n = 0
for it in d.get("items") or []:
    g = ((it.get("gridbox") or {}).get("data")) or {}
    pr = g.get("price") or {}
    if n < 3 or (pr.get("oldPrice") and pr.get("price") and pr["price"] / pr["oldPrice"] <= 0.6):
        n += 1
        show("LIDL " + str(g.get("fullTitle")), {"price": pr, "lidlPlus": g.get("lidlPlus"), "keys": sorted(g.keys())})
