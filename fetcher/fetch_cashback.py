"""Geld-zurück-Aktionen ("Gratis testen") für den Coupon-Bericht der App.

Quellen: öffentliche Übersichten auf mystipendium.de und sparwelt.de (robots.txt erlaubt beide Seiten; wir holen
je genau eine Seite pro Lauf, 10 s Pause dazwischen). Übernommen werden nur Fakten (Produkt, Prozent, Höchstbetrag, Fristen, Markt) und der
direkte Link zur Aktionsseite des Herstellers. Keine Bilder, keine Texte, keine Partner-Links (/goto/).
Ergebnis: docs/data/cashback.json
"""
import json, re, html, datetime, pathlib, urllib.request, urllib.robotparser, sys, time

UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
URL = "https://www.mystipendium.de/geld/cashback-geld-zurueck-aktionen"
URL2 = "https://www.sparwelt.de/gratis/cashback"
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "data" / "cashback.json"
# Märkte der App und Märkte, die es in der Region nicht gibt (Aktion dann nicht nutzbar)
OURS = {"lidl": r"\blidl\b", "aldi": r"\baldi\b", "rewe": r"\brewe\b", "netto": r"\bnetto\b", "edeka": r"\bedeka\b", "dm": r"\bdm\b|dm-markt|dm-märkten"}
OTHER = r"\b(globus|kaufland|penny|rossmann|müller|norma|real|marktkauf|tegut|famila|hit|fressnapf|amazon|online-shop|onlineshop|apotheke|apotheken|budni|otto|mediamarkt|saturn)\b"

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "replace")

def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def date(s, last=False):
    ms = list(re.finditer(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s or ""))  # „01.04.2026 bis 31.12.2026“ -> Enddatum
    m = (ms[-1] if last else ms[0]) if ms else None
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else None

def allowed(u):
    rp = urllib.robotparser.RobotFileParser(); rp.parse(get("/".join(u.split("/")[:3]) + "/robots.txt").splitlines())
    ok = rp.can_fetch(UA, u)
    if not ok: print("robots.txt verbietet", u, "– nicht geholt")
    return ok

def shops_of(low):
    """Märkte der App, die die Aktion nennt; None = nur bei Märkten, die es hier nicht gibt."""
    shops = [k for k, rx in OURS.items() if re.search(rx, low)]
    if not shops and re.search(OTHER, low) and not re.search(r"im handel|überall|alle(n)? (händler|märkte|geschäfte)|deutsche[nm]? (lebensmittel)?handel|im lebensmitteleinzelhandel", low):
        return None
    return shops

def mystipendium():
    if not allowed(URL): return []
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
        shops = shops_of(how.lower())
        if shops is None:
            continue  # nur bei Märkten, die es hier nicht gibt
        name = re.sub(r"\s+(gratis|kostenlos)\s+(testen|probieren)\b.*$", "", t, flags=re.I).strip()
        iid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
        if any(x["id"] == iid for x in items):
            continue  # gleiche Aktion steht doppelt in der Übersicht
        items.append({
            "id": iid,
            "n": name, "prod": f.get("Aktionsprodukt", "")[:300], "cat": cat.group(1) if cat else "",
            "typ": "pct", "pct": int(pct.group(1)) if pct else None, "max": float(mx.group(1).replace(",", ".")) if mx else None,
            "w": float(wert.group(1).replace(",", ".")) if wert else None,
            "ab": ab, "kauf": kauf, "ende": ende, "shops": shops, "url": link.group(1),
            "lim": f.get("Anzahl Teilnehmer", "")[:80], "src": "mystipendium.de",
        })
    print("mystipendium.de:", len(items))
    return items

DROG = r"billy boy|skyn|durex|deo|zahnpasta|zahncreme|binden|kondom|shampoo|duschgel|waschmittel|spül|lenor|gillette|tena|salbe|creme|rasier|always|wäsche|reiniger|zewa|tücher|windel|pflaster"
TIER = r"tierfutter|katzen|hunde|hund\b|katze\b|cesar|whiskas|felix|sheba"

def money(s):
    return float(s.replace(".", "").replace(",", ".")) if s else None

def sw_name(t):
    """„2x TUC kaufen, 1x Geld zurück“ -> „TUC“, „JACOBS Ganze Bohne - 5€ Cashback“ -> „JACOBS Ganze Bohne“."""
    n = re.sub(r"^\s*gratis (testen|probieren)\s*:\s*", "", t, flags=re.I)
    amount = r"(\d[\d,.]*\s*(€|%)|cashback|geld zurück|gratis|zurück)"
    parts = [x for x in re.split(r"\s+[-–]\s+|:\s+", n) if x.strip()]
    keep = [x for x in parts if not re.match(r"^\s*" + amount, x, re.I)] or parts
    n = keep[0]
    m = re.search(r"\bauf\s+(?:eine?n?\s+)?(?:(?:flasche|packung|dose)\s+)?(?:ausgewählte\s+)?(.+)$", n, re.I)
    if m and re.match(r"^\s*" + amount, n, re.I): n = m.group(1)
    n = re.sub(r",?\s*(\d+\s*(x|×)?\s*)?(geld zurück|gratis|cashback|1\s*packung gratis).*$", "", re.sub(r"\s+kaufen\b.*$", "", n, flags=re.I), flags=re.I)
    n = re.sub(r"^\s*\d+\s*(?:x|×)?\s*(?:packungen|packung|flaschen|flasche|stück|dosen|dose)?\s*", "", n, flags=re.I)
    n = re.sub(r"\s+(gratis|kostenlos)\s+(testen|probieren).*$|\s+bei\s+(rewe|dm|lidl|aldi|edeka|netto)\b.*$|\s+(aktions)?produkte?\b|[!*]", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip(" ,.-–")

def sparwelt():
    if not allowed(URL2): return []
    page = get(URL2)
    today = datetime.date.today().isoformat()
    items = []
    for c in page.split("@container/deal w-full relative")[1:]:
        c = c.split("Mehr erfahren", 1)[0]
        uid = re.search(r'data-content-uuid="deal:(\d+)"', c)
        kind = re.search(r"<span[^>]*>\s*(\w+)\s*</span>\s*<h2", c)
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", c, re.S)
        if not uid or not h2: continue
        t = txt(h2.group(1)); body = c[h2.end():]; text = txt(body); low = (t + " " + text).lower()
        zr = re.search(r"aktionszeitraum[^:]*?(?:</strong>)?\s*:\s*(.*?)</p>", body, re.I | re.S)
        kauf = date(txt(zr.group(1)), last=True) if zr else None
        es = re.search(r"(einsendeschluss|upload bis|teilnahmeschluss)[^:]*?(?:</strong>)?\s*:\s*(.*?)</p>", body, re.I | re.S)
        ende = (date(txt(es.group(2)), last=True) if es else None) or kauf
        if not kauf or kauf < today or (ende and ende < today):
            continue
        hrefs = [h for h in re.findall(r'href="(https://[^"]+)"', body) if "sparwelt" not in h]
        if not hrefs: continue
        url = re.match(r"https://[^/]+", hrefs[0]).group(0) + "/"
        if re.search(r"\.at/$", url) or "garantie" in low: continue
        shops = shops_of(low)
        if shops is None: continue
        typ = pct = eur = mx = None; need = 1
        nf = re.search(r"^\s*(\d)\s*(?:x|×)?\s*.{0,60}?kaufen,?\s*(?:1|eine?n?|das günstigere)\s*(?:x|×)?\s*.{0,25}?(geld zurück|gratis|kaufpreis)", t, re.I)
        e = re.search(r"(\d+(?:,\d{1,2})?)\s*€\s*(cashback|zurück|geld zurück|rückerstattung)", t, re.I)
        pc = re.search(r"(\d{1,3})\s*%\s*(cashback|geld zurück|zurück|erstattung)", t, re.I)
        if nf: typ, need = "nfor", int(nf.group(1))
        elif e:
            typ, eur = "eur", money(e.group(1))
            q = re.search(r"^\s*(\d)\s*(?:x|×|packungen|flaschen|produkte|aktionsprodukte)", t, re.I)
            need = int(q.group(1)) if q else 1
        elif pc: typ, pct = "pct", int(pc.group(1))
        elif (kind and kind.group(1).lower() == "gratis") or re.search(r"gratis (testen|probieren)", t, re.I): typ, pct = "pct", 100
        if not typ or need < 1 or need > 6: continue
        m = re.search(r"(?:maximal|max\.?|erstattungsbetrag beträgt|höchstens|bis zu)\s*(?:jedoch\s*)?(\d+,\d{2})\s*(?:€|eur)", text, re.I)
        mx = money(m.group(1)) if m else None
        mn = re.search(r"ab\s*(?:einem\s*einkaufswert\s*von\s*)?(\d+(?:,\d{2})?)\s*€\s*(einkaufswert|einkauf)?", low)
        name = sw_name(t)
        if len(name) < 3 or re.match(r"(tierfutter|ausgewählte|produkte|marken|alle)\b", name, re.I): continue
        prod = re.search(r"aktionsproduk\w*[^:]*?(?:</strong>)?\s*:\s*(.*?)</p>", body, re.I | re.S)
        items.append({
            "id": "sw" + uid.group(1), "n": name, "prod": txt(prod.group(1))[:300] if prod else "",
            "cat": "drogerie" if re.search(DROG, low) else "tiernahrung" if re.search(TIER, low) else "lebensmittel",
            "typ": typ, "pct": pct, "eur": eur, "need": need, "max": mx,
            "min": money(mn.group(1)) if mn and mn.group(2) else None, "w": None,
            "ab": date(txt(zr.group(1))) if zr and date(txt(zr.group(1))) and date(txt(zr.group(1))) > today else None,
            "kauf": kauf, "ende": ende, "shops": shops, "url": url, "lim": "", "src": "sparwelt.de",
        })
    print("sparwelt.de:", len(items))
    return items

def brand(n):
    return re.sub(r"[^a-z0-9äöüß]", "", (n.split() or [""])[0].lower())

def main():
    items = mystipendium()
    try:
        time.sleep(10)
        for x in sparwelt():
            if any(brand(x["n"]) == brand(y["n"]) and x["typ"] == y.get("typ", "pct") for y in items):
                continue  # dieselbe Aktion aus der anderen Übersicht
            items.append(x)
    except Exception as e:
        print("sparwelt.de nicht geholt:", e, file=sys.stderr)
    if not items:
        print("Keine Aktionen erkannt – alte Datei bleibt"); return
    OUT.write_text(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "src": [URL, URL2], "items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(items)} Geld-zurück-Aktionen gespeichert")

if __name__ == "__main__":
    try: main()
    except Exception as e:  # nie den ganzen Abruf stoppen
        print("Geld-zurück-Aktionen nicht geholt:", e, file=sys.stderr)
