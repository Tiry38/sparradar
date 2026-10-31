"""SparRadar: Artikelstamm für die Vorschläge in Suche und Merkliste.

Quelle: Open Food Facts und Open Beauty Facts (offene Datenbanken, Lizenz ODbL, Nutzung ausdrücklich
erlaubt). Geholt werden die in Deutschland meistgescannten Produkte, damit man beim Tippen genau den
Artikel auswählen kann, den man beobachten will – auch wenn er gerade nicht im Angebot ist.

Läuft einmal pro Woche (.github/workflows/artikelstamm.yml), mit Pausen zwischen den Abrufen.
Ergebnis: docs/data/catalog.json (Liste von Artikelnamen „Marke Produkt Menge“).
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "SparRadar/1.0 (private Angebotsuebersicht; https://github.com/Tiry38/sparradar)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "data", "catalog.json")
PAUSE = 7  # Open Food Facts erlaubt ca. 10 Suchanfragen pro Minute
SOURCES = [  # (Datenbank, maximale Seiten à 1000 Produkte)
    ("https://de.openfoodfacts.org", 45),
    ("https://de.openbeautyfacts.org", 8),
]
FIELDS = "product_name_de,product_name,brands,quantity"


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            log(f"  ! Versuch {attempt + 1} fehlgeschlagen: {e}")
            time.sleep(PAUSE * (attempt + 2))
    return None


def norm(s):
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("_", " ")).strip(" ,;-")


def label(p):
    """'Jacobs' + 'Tassimo Latte Macchiato' + '8 Portionen' -> 'Jacobs Tassimo Latte Macchiato 8 Portionen'"""
    name = clean(p.get("product_name_de") or p.get("product_name"))
    if len(name) < 3 or not re.search(r"[A-Za-zÄÖÜäöü]{2}", name):
        return None
    brand = clean((p.get("brands") or "").split(",")[0])
    qty = clean(p.get("quantity"))[:20]
    text = name
    if brand and norm(brand) not in norm(name):
        text = f"{brand} {name}"
    if qty and norm(qty) not in norm(text):
        text = f"{text} {qty}"
    return text[:90]


def fetch(base, pages):
    names = []
    for page in range(1, pages + 1):
        q = urllib.parse.urlencode({
            "action": "process", "json": 1, "page_size": 1000, "page": page, "sort_by": "unique_scans_n",
            "tagtype_0": "countries", "tag_contains_0": "contains", "tag_0": "germany", "fields": FIELDS,
        })
        data = get(f"{base}/cgi/search.pl?{q}")
        time.sleep(PAUSE)
        prods = (data or {}).get("products") or []
        if not prods:
            break
        names += [n for n in map(label, prods) if n]
        log(f"  {base.split('//')[1]} Seite {page}: {len(prods)} Produkte")
    return names


def main():
    seen, out = set(), []
    for base, pages in SOURCES:
        for n in fetch(base, pages):
            k = norm(n)
            if k and k not in seen:
                seen.add(k)
                out.append(n)
    log("Artikelstamm:", len(out), "Artikel")
    if len(out) < 5000:
        log("! Zu wenige Artikel, alter Artikelstamm bleibt stehen.")
        sys.exit(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)


if __name__ == "__main__":
    main()
