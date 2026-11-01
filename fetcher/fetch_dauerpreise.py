"""Aldi-Süd-Dauerpreise (Normalpreise des ganzen Sortiments) -> docs/data/dauerpreise.json

Kevins Wunsch (01.11.): Auch was gerade nicht im Angebot ist, soll einen echten Preis haben („Milch: bei Aldi immer 0,99 €“).
Quelle: die öffentlichen Kategorie-Seiten von aldi-sued.de (/produkte/<…>/k/<Nummer>, mit ?page=N). robots.txt erlaubt sie
(gesperrt sind nur /tools und /*?q=) – wird vor dem Abruf geprüft. Ehrlicher User-Agent, Pause zwischen den Seiten, 1× pro Woche.
Die Preise stehen im Seiten-Datenblock __NUXT_DATA__ (dieselbe Auswertung wie beim Angebots-Abruf).
Aktionsartikel (mit Verkaufsstart) sind keine Dauerpreise und werden übersprungen. Lidl: nicht möglich (robots.txt sperrt
die Such- und Blätter-Adressen).

Format: {"at": "JJJJ-MM-TT", "src": "aldi-sued.de", "items": [[Name, Marke, Preis, Grundpreis, Einheit, Warengruppe], …]}
"""
import datetime as dt
import os
import re
import sys
import time
import urllib.robotparser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_offers as f  # noqa: E402

BASE = "https://www.aldi-sued.de"
PAUSE = 2.0
MAX_MIN = float(os.environ.get("SR_DP_MINUTES", "45"))  # Zeitbudget, danach wird gespeichert
CAT = re.compile(r'href="(?:https://www\.aldi-sued\.de)?(/(?:de/)?produkte/[^"?#]+/k/\d+)"')
PAGE = re.compile(r'href="(?:https://www\.aldi-sued\.de)?(/(?:de/)?produkte/[^"#]+/k/\d+\?page=(\d+))"')


def robots():
    rp = urllib.robotparser.RobotFileParser()
    rp.parse((f.http(BASE + "/robots.txt") or "").splitlines())
    return rp


def row(it):
    # Diagnose 01.11.: Dauersortiment hat KEIN Verkaufsdatum; Aktionsware hat eins („Verfügbar ab/seit …“, Abzeichen „Aktion“).
    # notForSale steht bei fast allem (= nicht online bestellbar) und sagt nichts. Ein „statt“-Preis ohne Verkaufsdatum ist meist eine
    # dauerhafte Preissenkung (Markenbutter 1,19 -> 1,15 €) – das ist der aktuelle Ladenpreis, also behalten.
    pr = it.get("price") or {}
    if it.get("onSaleDate") or it.get("discontinued"):
        return None
    amount = pr.get("amountRelevant") or pr.get("amount")
    name = f.clean_text(it.get("name") or "")
    if not amount or not name:
        return None
    up = f.unit_price(pr.get("comparisonDisplay") or "")
    brand = it.get("brandName")
    brand = "" if brand in (None, "BIO", "no-brand") else f.clean_text(brand)
    cats = [c.get("name") for c in it.get("categories") or [] if isinstance(c, dict) and c.get("name")]
    return [name, brand, round(amount / 100, 2), up[0] if up else None, up[1] if up else None, cats[-1] if cats else ""]


def main():
    t0 = time.time()
    rp = robots()
    ok = lambda u: rp.can_fetch(f.UA, u)  # noqa: E731
    start = f.http(BASE + "/") or ""
    cats = sorted(set(CAT.findall(start)))
    time.sleep(PAUSE)
    more = f.http(BASE + "/produkte") or ""
    cats = sorted(set(cats) | set(CAT.findall(more)))
    f.log(f"Aldi-Kategorien: {len(cats)}")
    if not cats:
        f.log("  ! keine Kategorie-Links gefunden – nichts geändert")
        return
    got, seen_pages, n = {}, set(), 0
    for path in cats:
        queue = [path]
        while queue:
            if (time.time() - t0) / 60 > MAX_MIN:
                f.log("  Zeitbudget erreicht – speichere, was da ist")
                queue = []
                break
            p = queue.pop(0)
            url = BASE + p
            if p in seen_pages or not ok(url):
                continue
            seen_pages.add(p)
            time.sleep(PAUSE)
            h = f.http(url) or ""
            n += 1
            new = 0
            for it in f.aldi_items(h):
                r = row(it)
                sku = str(it.get("sku") or "")
                if r and sku and sku not in got:
                    got[sku] = r
                    new += 1
            # weitere Seiten derselben Kategorie, solange neue Artikel kommen
            if new:
                for pp, num in PAGE.findall(h):
                    if pp.split("?")[0] == p.split("?")[0] and int(num) <= 40 and pp not in seen_pages:
                        queue.append(pp)
            if n % 25 == 0:
                f.log(f"  {n} Seiten, {len(got)} Artikel ({(time.time() - t0) / 60:.0f} min)")
    items = sorted(got.values(), key=lambda r: (r[5], r[0]))
    f.log(f"Aldi-Dauerpreise: {len(items)} Artikel aus {n} Seiten")
    old = f.load("dauerpreise.json", {}) or {}
    if not items or len(items) < 0.5 * len(old.get("items") or []):
        f.log("  ! deutlich weniger als letztes Mal – alte Liste bleibt")
        return
    f.save("dauerpreise.json", {"at": dt.date.today().isoformat(), "src": "aldi-sued.de", "items": items})


if __name__ == "__main__":
    main()
