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
OUT_IMG = os.path.join(ROOT, "docs", "data", "catalog-img.json")  # kleines Produktbild je Eintrag (gleiche Reihenfolge)
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
        i_i = col.get("image_small_url")
        host = "b" if "beauty" in url else "f"  # f = Open Food Facts, b = Open Beauty Facts
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
            img = ""
            if i_i is not None:
                m = re.search(r"/images/products/(.+?)\.jpg$", row[i_i] or "")
                if m:
                    img = host + ":" + m.group(1)  # kurz: "f:400/041/702/5005/front_de.12.200"
            found.append((ours, scans, n, img))
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
    seen, out = {}, []
    out_img = []
    for _, _, n, img in allf:
        k = norm(n)
        if not k:
            continue
        if k in seen:  # doppelter Artikel: Bild vom Doppelten übernehmen, falls der erste keins hat
            if img and not out_img[seen[k]]:
                out_img[seen[k]] = img
            continue
        if len(out) >= MAX_ITEMS:
            continue
        seen[k] = len(out)
        out.append(n)
        out_img.append(img)
    log("Artikelstamm:", len(out), "Artikel, davon bei unseren Märkten:", sum(1 for t in allf if t[0]))
    if len(out) < 5000:
        log("! Zu wenige Artikel, alter Artikelstamm bleibt stehen.")
        sys.exit(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out_img, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT_IMG)
    img_pool(allf, out, out_img)


def img_pool(allf, out, out_img):
    """Bilder-Wächter: Für Artikelnamen ohne Bild (names.json + Artikelstamm) im GANZEN Export einen passenden
    Artikel mit Bild suchen (gleiche Marke + Produktwörter). Ergebnis docs/data/img-pool.json {Name: "f:pfad"}."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from fill_images import Pool
    try:
        with open(os.path.join(ROOT, "docs", "data", "names.json"), encoding="utf-8") as f:
            names = list(json.load(f))
    except Exception:
        names = []
    need = list(dict.fromkeys([n for n in names] + [n for n, i in zip(out, out_img) if not i]))
    pool = Pool()
    for _, _, n, img in allf:
        if img:
            pool.add(n, img)
    res = {}
    for n in need:
        u = pool.find(n) or pool.find(n, loose=True)  # notfalls gleiche Marke + Produktlinie, andere Sorte
        if u:
            res[n] = u
    with open(os.path.join(ROOT, "docs", "data", "img-pool.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    log("Bilder-Pool:", len(res), "von", len(need), "Artikeln ohne Bild gefunden")


if __name__ == "__main__":
    main()
