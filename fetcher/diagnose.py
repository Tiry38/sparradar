"""Diagnose: kaufDA-Händlerseiten für Müller und Scheck-In Center (Maximilian-Center, Wörth-Maximiliansau) finden."""
import json
import re
import time

import fetch_offers as f


def page(url):
    h = f.http(url) or ""
    time.sleep(2)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {}) if m else {}
    return h, pi


def show(url):
    h, pi = page(url)
    main = (pi.get("offers") or {}).get("main") or {}
    items = main.get("items") or []
    br = pi.get("brochures") or {}
    print(f"\n=== {url}: HTML {len(h)}, Angebote {len(items)} von {main.get('totalItems')}")
    for key in ("viewer", "publisher"):
        lst = br.get(key)
        for b in lst if isinstance(lst, list) else []:
            print(f"  Prospekt[{key}] {b.get('id') or b.get('contentId')} {str(b.get('validFrom'))[:10]}–{str(b.get('validUntil'))[:10]}"
                  f" {b.get('publisherName') or ''} {b.get('title') or ''} pages={b.get('pageCount')}")
    pubs = {}
    for it in items:
        pubs[(it.get("publisherName"), it.get("publisherId"))] = pubs.get((it.get("publisherName"), it.get("publisherId")), 0) + 1
    print("  Händler der Angebote:", pubs)
    for it in items[:6]:
        pr = it.get("prices") or {}
        print(f"   {it.get('publisherName')} | {it.get('brand')} {it.get('title')} {pr.get('mainPrice')} statt {pr.get('secondaryPrice')}"
              f" {str(it.get('validFrom'))[:10]} cats={[n.get('name') for p in it.get('categoryPaths') or [] for n in p if isinstance(n, dict)][-2:]}")
    links = ((((pi.get("template") or {}).get("content") or {}).get("OfferLinkbox") or {}).get("PublisherOfferLinkbox") or {}).get("links") or []
    print("  Themen-Links:", [l.get("link_href") for l in links if isinstance(l, dict)][:12])
    return h, pi


# 1) Stadtseiten: Links auf Händlerseiten mit Müller / Scheck-in
for city in ("Woerth-am-Rhein", "Maximiliansau", "Woerth-am-Rhein/Filialen", "Woerth-am-Rhein/Haendler"):
    h, _ = page(f"https://www.kaufda.de/{city}")
    hits = sorted(set(re.findall(r'href="(/[^"]*(?:[Mm]ueller|[Mm]üller|[Ss]check)[^"]*)"', h)))
    print(f"{city}: HTML {len(h)} – Links:", hits[:30])
    print("  Rohtext:", sorted(set(re.findall(r'[^"<>]{0,40}(?:Scheck|Müller|Mueller)[^"<>]{0,40}', h)))[:20])

# 2) wahrscheinliche Händlerseiten direkt
for slug in ("Mueller", "Drogerie-Mueller", "Mueller-Drogerie", "Scheck-in-Center", "Scheck-In-Center", "Scheck-in"):
    for city in ("Woerth-am-Rhein", "Karlsruhe"):
        h, _ = page(f"https://www.kaufda.de/{city}/{slug}")
        m = re.findall(r'href="(/[^"]*/p-r\d+)"', h)
        print(f"{city}/{slug}: HTML {len(h)} – p-r-Links:", sorted(set(x for x in m if re.search(r"(?i)mueller|scheck", x)))[:10])

# 3) Sortiment-Seiten
for slug, t in (("Mueller", "Shampoo"), ("Mueller", "Spielzeug"), ("Drogerie-Mueller", "Shampoo"),
                ("Scheck-in-Center", "Butter"), ("Scheck-In-Center", "Butter")):
    show(f"https://www.kaufda.de/{slug}/Sortiment/{t}")

# 4) robots.txt der Händler-Seiten
for u in ("https://www.mueller.de/robots.txt", "https://www.scheck-in-center.de/robots.txt", "https://scheck-in-center.de/robots.txt"):
    r = f.http(u) or ""
    time.sleep(2)
    print(f"\n{u}: {len(r)} Zeichen\n" + r[:1500])
for u in ("https://www.scheck-in-center.de/", "https://www.scheck-in-center.de/maerkte/", "https://www.scheck-in-center.de/angebote/"):
    r = f.http(u) or ""
    time.sleep(2)
    print(f"\n{u}: {len(r)} Zeichen; Wörth/Maximilian:", sorted(set(re.findall(r'[^"<>]{0,60}(?:W[öo]rth|Maximilian)[^"<>]{0,60}', r)))[:10],
          "Links Angebote/Prospekt:", sorted(set(re.findall(r'href="([^"]*(?:angebot|prospekt|flyer|handzettel)[^"]*)"', r, re.I)))[:15])
