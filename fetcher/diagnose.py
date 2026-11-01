"""Diagnose: Mehr Edeka- und dm-Angebote über kaufDA-Händlerseiten anderer Orte?
Jede Händlerseite zeigt 16 Angebote, je Ort eine andere Auswahl. Übernommen werden dürften nur Angebote aus
genau dem Prospekt, der auch für Wörth/Jockgrim gilt (gleiche Prospekt-ID) bzw. inhaltsgleiche Prospekte."""
import collections

import fetch_offers as f

NEAR = """Jockgrim Woerth-am-Rhein Kandel Rheinzabern Ruelzheim Bellheim Hagenbach Herxheim Landau-in-der-Pfalz Germersheim
Speyer Karlsruhe Ettlingen Rastatt Bad-Bergzabern Edenkoben Lingenfeld Rheinstetten Stutensee Bruchsal Philippsburg
Durmersheim Eggenstein-Leopoldshafen Linkenheim-Hochstetten Hassloch""".split()
FAR = "Berlin Hamburg Muenchen Koeln Frankfurt-am-Main Stuttgart Leipzig Dresden Hannover Nuernberg Mannheim Heidelberg".split()


def bid(it):
    return str((it.get("parentContent") or {}).get("id"))


def key(it):
    return (f.norm(it.get("title")), round(float((it.get("prices") or {}).get("mainPrice") or 0), 2))


for store, slug, cities in (("dm", "dm-drogerie-markt/p-r104", NEAR + FAR), ("edeka", "EDEKA/p-r107", NEAR)):
    base_url = f.KD_STORES[store]
    items, total = f.kd_page(base_url)
    base = {bid(it) for it in items}
    known = {key(it) for it in items}
    got = {it.get("id"): it for it in items}
    print(f"\n=== {store}: Heimatseite {len(items)} von {total}, Prospekte {base}")
    other = collections.Counter()
    for city in cities:
        url = f"https://www.kaufda.de/{city}/{slug}"
        if url == base_url:
            continue
        its, tot = f.kd_page(url)
        b = collections.Counter(bid(it) for it in its)
        same = [it for it in its if bid(it) in base]
        hit = sum(key(it) in known for it in its)
        new = [it for it in same if it.get("id") not in got]
        for it in new:
            got[it.get("id")] = it
        for it in its:
            if bid(it) not in base:
                other[(bid(it), it.get("publisherId"))] += 1
        print(f"  {city}: {len(its)} von {tot} | Prospekte {dict(b)} | gleicher Prospekt {len(same)}, neu {len(new)},"
              f" gleich (Name+Preis) {hit} -> zusammen {len(got)}")
    print(f"{store}: zusammen {len(got)} Angebote aus dem eigenen Prospekt; fremde Prospekte: {other.most_common(8)}")
