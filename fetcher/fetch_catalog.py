"""SparRadar: Artikelstamm für die Vorschläge in Suche und Merkliste.

Quelle: die offiziellen Datenexporte von Open Food Facts und Open Beauty Facts (offene Datenbanken,
Lizenz ODbL, Download ausdrücklich erlaubt). Daraus werden die in Deutschland verkauften Artikel
gefiltert – zuerst alle, die bei unseren Märkten (Lidl, Aldi, Rewe, Netto, Edeka, dm) erfasst sind,
dann die meistgescannten übrigen. So kann man beim Tippen genau den Artikel auswählen, den man
beobachten will, auch wenn er gerade nicht im Angebot ist.

Läuft einmal pro Woche (.github/workflows/artikelstamm.yml). Der Export wird gestreamt (nicht
gespeichert), nur Python-Standardbibliothek.
Ergebnis: docs/data/catalog.json (Liste von Artikelnamen „Marke Produkt Menge“).
"""
import csv
import gzip
import io
import json
import os
import re
import sys
import urllib.request

UA = "SparRadar/1.0 (private Angebotsuebersicht; https://github.com/Tiry38/sparradar)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "data", "catalog.json")
EXPORTS = [
    "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz",
    "https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv.gz",
]
OUR_STORES = re.compile(r"lidl|aldi|rewe|netto|edeka|\bdm\b|dm-drogerie", re.I)
MAX_ITEMS = 70000  # Obergrenze, damit die Datei für die App klein bleibt (wird erst beim Tippen geladen)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def norm(s):
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("_", " ")).strip(" ,;-")


def label(name, brand, qty):
    """'Tassimo Morning Café' + 'Jacobs' + '21 Portionen' -> 'Jacobs Tassimo Morning Café 21 Portionen'"""
    name = clean(name)
    if len(name) < 3 or not re.search(r"[A-Za-zÄÖÜäöü]{2}", name):
        return None
    brand = clean((brand or "").split(",")[0])
    qty = clean(qty)[:20]
    text = name
    if brand and norm(brand) not in norm(name):
        text = f"{brand} {name}"
    if qty and norm(qty) not in norm(text):
        text = f"{text} {qty}"
    return text[:90]


def scan(url):
    """Export streamen und deutsche Artikel sammeln: (bei unseren Märkten?, Scans, Name)."""
    csv.field_size_limit(10**9)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    found, rows = [], 0
    with urllib.request.urlopen(req, timeout=120) as r:
        text = io.TextIOWrapper(gzip.GzipFile(fileobj=r), encoding="utf-8", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t", quoting=csv.QUOTE_NONE)
        head = next(reader)
        col = {h: i for i, h in enumerate(head)}
        need = ["product_name", "brands", "quantity", "countries_tags"]
        if any(h not in col for h in need):
            log("  ! Unerwartete Spalten:", head[:30])
            return found
        i_n, i_b, i_q, i_c = (col[h] for h in need)
        i_s = col.get("stores")
        i_u = col.get("unique_scans_n")
        width = max(col.values()) + 1
        for row in reader:
            rows += 1
            if len(row) < width or "en:germany" not in row[i_c]:
                continue
            n = label(row[i_n], row[i_b], row[i_q])
            if not n:
                continue
            ours = bool(i_s is not None and OUR_STORES.search(row[i_s] or ""))
            try:
                scans = int(float(row[i_u])) if i_u is not None and row[i_u] else 0
            except ValueError:
                scans = 0
            found.append((ours, scans, n))
    log(f"  {url.split('/')[2]}: {rows} Zeilen gelesen, {len(found)} Artikel aus Deutschland")
    return found


def main():
    allf = []
    for url in EXPORTS:
        try:
            allf += scan(url)
        except Exception as e:  # eine kaputte Quelle soll die andere nicht stoppen
            log("  ! Export fehlgeschlagen:", url, repr(e))
    # zuerst Artikel unserer Märkte, dann nach Beliebtheit (Scans)
    allf.sort(key=lambda t: (not t[0], -t[1]))
    seen, out = set(), []
    for _, _, n in allf:
        k = norm(n)
        if k and k not in seen:
            seen.add(k)
            out.append(n)
            if len(out) >= MAX_ITEMS:
                break
    log("Artikelstamm:", len(out), "Artikel, davon bei unseren Märkten:", sum(1 for t in allf if t[0]))
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
