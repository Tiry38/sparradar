"""Diagnose: Wie kommen mehr Edeka- und dm-Angebote legal in die App?
1) prospektewoche.de: gibt es Edeka (Südwest) und dm? 2) kaufDA-Sortiment Edeka: welche Prospekte werden abgelehnt?
3) dm: liefern andere Städte / ?page= andere 16 Angebote?"""
import collections
import re
import time

import fetch_offers as f

today = time.strftime("%Y-%m-%d")
print("=== robots.txt prospektewoche ===")
rb = f.http(f.PW + "/robots.txt") or ""
print("\n".join(l for l in rb.splitlines() if l.strip())[:1500])

# lokale Edeka-Seite (Jockgrim): bekannte Artikel + Prospekt-IDs
loc = f.KD_STORES["edeka"]
items, total = f.kd_page(loc)
info = f.KD_INFO[loc]
print("\nEdeka Jockgrim:", len(items), "von", total, "| pubs", info["pubs"], "| Prospekte", sorted(info["brochures"])[:8])
for it in items[:3]:
    print("  ", it.get("title"), (it.get("prices") or {}).get("mainPrice"), it.get("validFrom"), it.get("validUntil"), (it.get("parentContent") or {}).get("id"))

for shop in ("edeka", "dm"):
    time.sleep(2)
    h = f.http(f"{f.PW}/{shop}") or ""
    tabs = re.findall(r'tab-dates">([^<]+)<', h)
    print(f"\n=== prospektewoche {shop}: {len(h)} Zeichen, Wochen {tabs}")
    print("   Untertitel:", re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)[:2], re.findall(r'(?i)region[^<"]{0,60}', h)[:5])
    try:
        got = f.fetch_prospektewoche(shop, shop)
    except Exception as e:
        print("   Fehler", e)
        got = []
    print(f"   {shop}: {len(got)} Angebote", collections.Counter((o.get('from'), o.get('to')) for o in got).most_common(3))
    for o in got[:5]:
        print("    ", o["n"][:40], o["p"], o.get("b"), o.get("gp"))
    if shop == "edeka":
        kn = info["known"]
        hit = [o for o in got if (f.norm(o["n"]), round(o["p"], 2)) in kn]
        print("   gleiche Artikel+Preis wie Jockgrim:", len(hit), [o["n"][:25] for o in hit[:6]])
        names = {f.norm(it.get("title")): (it.get("prices") or {}).get("mainPrice") for it in items}
        for o in got:
            if f.norm(o["n"]) in names:
                print("    Name gleich:", o["n"][:30], "pw", o["p"], "kaufDA", names[f.norm(o["n"])])

# kaufDA-Sortiment Edeka: Prospekte, Händler-Kennung, Zeitraum
terms = "Butter Milch Kaese Joghurt Hackfleisch Haehnchen Wurst Lachs Obst Gemuese Kartoffeln Brot Nudeln Kaffee Tee Schokolade Chips Bier Wein Wasser Saft Cola Katzenfutter Shampoo Waschmittel".split()
found = []
for t in terms:
    its, _ = f.kd_page(f"https://www.kaufda.de/Edeka/Sortiment/{t}")
    found += its
uniq = {it.get("id"): it for it in found}.values()
print(f"\n=== kaufDA Edeka-Sortiment: {len(found)} gefunden, {len(uniq)} verschieden")
g = collections.defaultdict(list)
for it in uniq:
    pc = it.get("parentContent") or {}
    g[(str(pc.get("id")), it.get("publisherId"), str(it.get("validFrom"))[:10], str(it.get("validUntil"))[:10])].append(it)
pubc = collections.Counter(k[1] for k in g for _ in g[k])
print("Händler-Kennungen:", pubc.most_common(8))
ok_now = f.same_flyer(list(uniq), info["known"], {b for b in info["brochures"] if b and b != "None"})
print("heute angenommen (same_flyer):", sum(len(v) for k, v in g.items() if k[0] in ok_now), "Artikel aus", len(ok_now & {k[0] for k in g}), "Prospekten")
# Kette: Prospekte mit >= 2 gleichen Artikeln wie schon angenommene Prospekte
acc, kn = set(ok_now), set(info["known"])
for k, v in g.items():
    if k[0] in acc:
        kn |= {(f.norm(i.get("title")), round(float((i.get("prices") or {}).get("mainPrice") or 0), 2)) for i in v}
for _ in range(6):
    new = set()
    for k, v in g.items():
        if k[0] in acc:
            continue
        n = sum((f.norm(i.get("title")), round(float((i.get("prices") or {}).get("mainPrice") or 0), 2)) in kn for i in v)
        if n >= 2:
            new.add(k[0])
            kn |= {(f.norm(i.get("title")), round(float((i.get("prices") or {}).get("mainPrice") or 0), 2)) for i in v}
    if not new:
        break
    acc |= new
print("mit Kette angenommen:", sum(len(v) for k, v in g.items() if k[0] in acc), "Artikel aus", len(acc & {k[0] for k in g}), "Prospekten")
# gleiche Händler-Kennung + gleicher Zeitraum wie Jockgrim
per = {(k[2], k[3]) for k in g if k[0] in ok_now}
print("Zeitraum Jockgrim:", per)
same = [k for k in g if k[1] in info["pubs"] and (k[2], k[3]) in per]
print("gleiche Kennung + Zeitraum:", sum(len(g[k]) for k in same), "Artikel aus", len(same), "Prospekten")
# Preis-Widersprüche (gleicher Name, anderer Preis) innerhalb gleiche Kennung + Zeitraum
pr = collections.defaultdict(set)
for k in same:
    for i in g[k]:
        pr[f.norm(i.get("title"))].add(round(float((i.get("prices") or {}).get("mainPrice") or 0), 2))
conf = {n: p for n, p in pr.items() if len(p) > 1}
print("Namen mit verschiedenen Preisen:", len(conf), "von", len(pr), list(conf.items())[:8])
print("andere Zeiträume/Kennungen (Top):", collections.Counter((k[1], k[2], k[3]) for k in g if k not in same).most_common(6))

# dm: andere Städte, ?page=2
print("\n=== dm Händlerseiten")
allids = {}
for city in ("Woerth-am-Rhein", "Karlsruhe", "Landau-in-der-Pfalz", "Speyer", "Germersheim", "Kandel", "Rastatt", "Ettlingen"):
    for url in (f"https://www.kaufda.de/{city}/dm-drogerie-markt/p-r104",):
        its, tot = f.kd_page(url)
        ids = {it.get("id") for it in its}
        new = ids - set(allids)
        for it in its:
            allids[it.get("id")] = it
        print(f"  {city}: {len(its)} von {tot}, neu {len(new)}, zusammen {len(allids)}")
its, tot = f.kd_page("https://www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104?page=2")
print("  Wörth ?page=2:", len(its), "neu", len({it.get('id') for it in its} - set(allids)))
time.sleep(2)
h = f.http("https://www.kaufda.de/robots.txt") or ""
print("\nkaufDA robots (Auszug):", [l for l in h.splitlines() if l.lower().startswith(("disallow", "user-agent"))][:30])
