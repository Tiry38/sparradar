"""Geld-zurück-Aktionen ("Gratis testen") für den Coupon-Bericht der App.

Quelle: öffentliche Übersicht auf mystipendium.de (robots.txt erlaubt die Seite, Crawl-delay 10 -> wir holen
genau eine Seite pro Lauf). Übernommen werden nur Fakten (Produkt, Prozent, Höchstbetrag, Fristen, Markt) und der
direkte Link zur Aktionsseite des Herstellers. Keine Bilder, keine Texte, keine Partner-Links (/goto/).
Ergebnis: docs/data/cashback.json
"""
import json, re, html, datetime, pathlib, urllib.request, urllib.robotparser, sys

UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
URL = "https://www.mystipendium.de/geld/cashback-geld-zurueck-aktionen"
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "data" / "cashback.json"
# Märkte der App und Märkte, die es in der Region nicht gibt (Aktion dann nicht nutzbar)
OURS = {"lidl": r"\blidl\b", "aldi": r"\baldi\b", "rewe": r"\brewe\b", "netto": r"\bnetto\b", "edeka": r"\bedeka\b", "dm": r"\bdm\b|dm-markt|dm-märkten"}
OTHER = r"\b(globus|kaufland|penny|rossmann|müller|norma|real|marktkauf|tegut|famila|hit|fressnapf|amazon|online-shop|onlineshop)\b"

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "replace")

def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def date(s, last=False):
    ms = list(re.finditer(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s or ""))  # „01.04.2026 bis 31.12.2026“ -> Enddatum
    m = (ms[-1] if last else ms[0]) if ms else None
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else None

def main():
    rp = urllib.robotparser.RobotFileParser(); rp.parse(get("https://www.mystipendium.de/robots.txt").splitlines())
    if not rp.can_fetch(UA, URL):
        print("robots.txt verbietet die Seite – nichts geholt"); return
    page = get(URL)
    sec = page.split('id="gratis-testen"', 1)[-1].split("<section", 1)[0]
    today = datetime.date.today().isoformat()
    items = []
    for blk in re.split(r'<div class="tbl tbl-competition competition-content"', sec)[1:]:
        cat = re.search(r'data-category="\{&quot;(\w+)&quot;', blk)
        title = re.search(r'<div class="tbl-title">(.*?)</div>', blk, re.S)
        link = re.search(r'<a href="([^"]+)"[^>]*class="tbl-button"', blk) or re.search(r'class="tbl-button"[^>]*href="([^"]+)"', blk)
        if not title or not link or "/goto/" in link.group(1) or not link.group(1).startswith("https://"):
            continue
        f = {txt(k): txt(v) for k, v in re.findall(r"<strong>(.*?)</strong>\s*:(.*?)</li>", blk, re.S)}
        t = re.sub(r"\*NEU\*", "", txt(title.group(1))).strip()
        if re.search(r"garantie", t + f.get("Cashback", "") + link.group(1), re.I):
            continue  # Zufriedenheits-Garantie = nur bei Nichtgefallen, kein echter Rabatt
        cb = f.get("Cashback", "")
        pct = re.search(r"(\d+)\s*%", cb)
        mx = re.search(r"max\.?\s*([\d,]+)\s*€", cb)
        wert = re.search(r"Wert:\s*(?:<[^>]+>\s*)*([\d,]+)\s*€", blk)
        kauf = date(f.get("Aktionszeitraum"), last=True) ; ende = date(f.get("Einsendeschluss"), last=True) or kauf
        if (kauf and kauf < today) or (ende and ende < today):
            continue
        if not kauf and not ende:
            continue  # ohne Datum nicht prüfbar, ob die Aktion noch läuft (meist Cashback-Apps mit eigenem Konto)
        if re.search(r"https://[^/]+\.at(/|$)|/aut/", link.group(1)):
            continue  # Aktion für Österreich
        if re.search(r"exklusiv\s+(bei|in)\b", f.get("Aktionsprodukt", "") + " " + f.get("Teilnahme", ""), re.I) and re.search(OTHER, (f.get("Aktionsprodukt", "") + " " + f.get("Teilnahme", "")).lower()):
            continue  # nur bei einem Markt, den es hier nicht gibt
        how = f.get("Teilnahme", "")
        ab = date((re.search(r"\bvom\s+(\d{1,2}\.\d{1,2}\.\d{4})", how) or [None, None])[1])
        low = how.lower()
        shops = [k for k, rx in OURS.items() if re.search(rx, low)]
        if not shops and re.search(OTHER, low) and not re.search(r"im handel|überall|alle(n)? (händler|märkte|geschäfte)|deutsche[nm]? (lebensmittel)?handel", low):
            continue  # nur bei Märkten, die es hier nicht gibt
        name = re.sub(r"\s+(gratis|kostenlos)\s+(testen|probieren)\b.*$", "", t, flags=re.I).strip()
        iid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
        if any(x["id"] == iid for x in items):
            continue  # gleiche Aktion steht doppelt in der Übersicht
        items.append({
            "id": iid,
            "n": name, "prod": f.get("Aktionsprodukt", "")[:300], "cat": cat.group(1) if cat else "",
            "pct": int(pct.group(1)) if pct else None, "max": float(mx.group(1).replace(",", ".")) if mx else None,
            "w": float(wert.group(1).replace(",", ".")) if wert else None,
            "ab": ab, "kauf": kauf, "ende": ende, "shops": shops, "url": link.group(1),
            "lim": f.get("Anzahl Teilnehmer", "")[:80],
        })
    if not items:
        print("Keine Aktionen erkannt – alte Datei bleibt"); return
    OUT.write_text(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "src": URL, "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(items)} Geld-zurück-Aktionen gespeichert")

if __name__ == "__main__":
    try: main()
    except Exception as e:  # nie den ganzen Abruf stoppen
        print("Geld-zurück-Aktionen nicht geholt:", e, file=sys.stderr)
