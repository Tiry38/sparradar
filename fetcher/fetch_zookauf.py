"""Zookauf Wörth (Maximilian-Center): Angebote aus dem zookauf-Prospekt lesen (Texterkennung).

Kevin 04.11.: Zookauf Wörth wie Müller/Scheck-In (nur bei Auswahl), mit Bildern und Angeboten.
Quelle (geprüft 04.11.):
- kaufDA kennt „Zookauf Wörth“ (p-r526), zeigt aber keine Prospekte/Angebote -> nicht nutzbar.
- zookauf.de/premiumpartner: „zookauf Wörth“, Maximilianstraße 1, nimmt regelmäßig an der Gemeinschaftswerbung
  teil (Werbeaussage „ZK 8S A4“). zookauf.de hat keine robots.txt (= alles erlaubt).
- Der Prospekt liegt als Blätterkatalog auf file-upload.zookauf.de/flipbooks/<Name>/ (Seitenbilder 1100 px,
  keine Text-Ebene). Link steht auf zookauf.de/seite/aktuelle-angebote bzw. /seite/werbeprospekt-kwNN.
  zookauf-woerth.de ist inzwischen eine fremde Seite (Casino) -> nicht nutzen.
Gelesen wird:
- Preise: rote Ziffern (Euro groß, Cent hochgestellt) -> Ziffern einzeln ausgeschnitten und als Zeile an Tesseract.
  Anzahl gelesener Ziffern muss genau passen, sonst verworfen (Test KW43+KW45: 40 Preise, 0 falsch).
- Name: fett gedruckte Großbuchstaben-Zeilen im selben Kasten (schwarze Schrift, Zierschrift ist farbig -> raus).
- Menge + Grundpreis „85 g Frischebeutel (1 kg = 6,47 €)“: Preis muss zu Menge × Grundpreis passen (±4 %),
  sonst fliegt das Angebot raus. Ohne gedruckten Grundpreis (Leine, Weste) zählt nur der Preis.
Ergebnis docs/data/zookauf-ocr.json {flyers:{Name:{from,to,pages,n,url}}, offers:[{n,b,d,p,gp,cr,pg,img,from,to,fid,url,cat}]}.
Jeder Prospekt wird nur einmal gelesen (ca. 10 s je Seite)."""
import datetime as dt
import html as htmlmod
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "data", "zookauf-ocr.json")
ZK = "https://zookauf.de"
FB = "https://file-upload.zookauf.de/flipbooks"
UA = "SparRadar/1.0 (+https://github.com/Tiry38/sparradar; private Angebots-App)"
PAUSE = 1.5
TMP = tempfile.mkdtemp(prefix="zk")


def log(*a):
    print(*a, flush=True)


def get(url, binary=False):
    for i in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "de-DE"})
            with urllib.request.urlopen(req, timeout=40) as r:
                b = r.read()
            time.sleep(PAUSE)
            return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            time.sleep(PAUSE)
            if e.code in (403, 404, 410):
                return None
        except Exception:
            time.sleep(3 + 3 * i)
    return None


# ---------- Prospekte finden ----------
def page_props(h):
    m = re.search(r'data-page="([^"]*)"', h or "")
    try:
        return json.loads(htmlmod.unescape(m.group(1)))["props"] if m else {}
    except Exception:
        return {}


def flyers():
    """Blätterkatalog-Namen von zookauf.de (Angebotsseite + Werbeseiten aus der Sitemap) + Probe der Kalenderwochen."""
    names, ab = {}, {}
    pages = {f"{ZK}/seite/aktuelle-angebote"}
    sm = get(f"{ZK}/sitemap.xml") or ""
    pages |= {u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if re.search(r"/seite/[^/]*(prospekt|handzettel|werb)", u)}
    for u in sorted(pages):
        h = get(u)
        if not h:
            continue
        txt = htmlmod.unescape(json.dumps(page_props(h).get("page") or {}, ensure_ascii=False)) + h
        txt = txt.replace("\\/", "/")
        for nm in re.findall(r"file-upload\.zookauf\.de/flipbooks/([A-Za-z0-9_\-]+)/", txt):
            names.setdefault(nm, u)
            m = re.search(r"g(?:ü|&uuml;|u)ltig ab (?:dem )?(\d\d)\.(\d\d)\.(\d{4})", txt, re.I)
            if m:
                ab[nm] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        for sub in re.findall(r'href="(https://zookauf\.de/seite/werbeprospekt[^"#]*)"', h.replace("&quot;", '"')):
            if sub not in pages:
                h2 = get(sub) or ""
                for nm in re.findall(r"file-upload\.zookauf\.de/flipbooks/([A-Za-z0-9_\-]+)/", h2.replace("\\/", "/")):
                    names.setdefault(nm, sub)
    kw = dt.date.today().isocalendar()[1]
    for w in range(kw - 2, kw + 3):
        nm = f"Prospekt_KW{w:02d}" if w < 10 else f"Prospekt_KW{w}"
        if nm not in names and get(f"{FB}/{nm}/blaetterkatalog/blaetterkatalog/xml/catalog.xml"):
            names[nm] = f"{ZK}/seite/aktuelle-angebote"
    return names, ab


def catalog(nm):
    x = get(f"{FB}/{nm}/blaetterkatalog/blaetterkatalog/xml/catalog.xml") or ""
    m = re.search(r'nofpages="(\d+)"', x)
    return int(m.group(1)) if m else 0


def page_url(nm, i):
    return f"{FB}/{nm}/blaetterkatalog/blaetterkatalog/large/bk_{i}.jpg"


# ---------- Texterkennung ----------
def tess(img, psm=7, wl=None, tsv=False, lang=None):
    p = os.path.join(TMP, "t.png")
    cv2.imwrite(p, img)
    cmd = ["tesseract", p, "-", "--psm", str(psm)]
    if lang:
        cmd += ["-l", lang]
    if wl:
        cmd += ["-c", "tessedit_char_whitelist=" + wl]
    if tsv:
        cmd += ["tsv"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.stdout


def redmask(im):
    b, g, r = [im[..., i].astype(np.int16) for i in range(3)]
    return ((r > 160) & (g < 95) & (b < 95) & (r - g > 100)).astype(np.uint8) * 255


def comps(m):
    n, _, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    return [tuple(int(v) for v in st[i]) for i in range(1, n)]


def _glyph_line(m, boxes, H):
    parts = []
    for i, (x, y, w, h, _) in enumerate(boxes):
        g = 255 - m[y:y + h, x:x + w]
        parts += [cv2.resize(g, (max(1, int(w * H / h)), H)), np.full((H, H // 2 if i == boxes.index(boxes[-1]) else H // 6), 255, np.uint8)]
    return parts


def prices(im):
    """Rote Preise „0,55“ (Euro groß, Cent hochgestellt) -> [{x,y,x1,y1,p}]"""
    m = redmask(im)
    C = [c for c in comps(m) if c[4] > 15]
    big = sorted([c for c in C if 30 <= c[3] <= 160 and 0.2 < c[2] / c[3] < 1.3 and c[4] < 0.8 * c[2] * c[3]], key=lambda c: c[0])
    out, used = [], set()
    for i, c in enumerate(big):
        if i in used:
            continue
        grp = [c]
        used.add(i)
        for j, d in enumerate(big):
            if j in used:
                continue
            last = grp[-1]
            if abs(d[1] - c[1]) < 0.2 * c[3] and abs(d[3] - c[3]) < 0.2 * c[3] and -2 <= d[0] - (last[0] + last[2]) < 0.5 * c[3]:
                grp.append(d)
                used.add(j)
        x1 = grp[-1][0] + grp[-1][2]
        y0 = min(g[1] for g in grp)
        h = max(g[3] for g in grp)
        cents = sorted([d for d in C if x1 - 2 <= d[0] <= x1 + 1.4 * h and abs(d[1] - y0) < 0.2 * h
                        and 0.35 * h < d[3] < 0.7 * h and d[2] < 0.6 * h], key=lambda d: d[0])
        if len(cents) != 2 or len(grp) > 3:
            continue
        val = None
        for H in (60, 48, 80):
            row = []
            for k, g in enumerate(grp):
                gg = 255 - m[g[1]:g[1] + g[3], g[0]:g[0] + g[2]]
                row += [cv2.resize(gg, (max(1, int(g[2] * H / g[3])), H)), np.full((H, H // 6), 255, np.uint8)]
            row.append(np.full((H, H // 2), 255, np.uint8))
            for d in cents:
                gg = 255 - m[d[1]:d[1] + d[3], d[0]:d[0] + d[2]]
                row += [cv2.resize(gg, (max(1, int(d[2] * H / d[3])), H)), np.full((H, H // 6), 255, np.uint8)]
            img = cv2.copyMakeBorder(np.hstack(row), 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
            t = re.sub(r"\D", "", tess(img, 7, "0123456789"))
            if len(t) == len(grp) + 2 and not (len(grp) > 1 and t[0] == "0"):
                val = int(t) / 100
                break
        if val:
            out.append({"x": grp[0][0], "y": y0, "x1": cents[-1][0] + cents[-1][2], "y1": y0 + h, "p": val})
    return out


def white_boxes(im):
    """helle Angebotskästen (Prospekt: weiße Kästen mit Zackenrand) -> [(x,y,x1,y1)], überlappende zusammengelegt"""
    b = im.astype(np.int16)
    mn, mx = b.min(2), b.max(2)
    m = ((mn >= 228) & (mx - mn <= 16)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    H, W = m.shape
    R = [(x, y, x + w, y + h) for x, y, w, h, a in comps(m) if w > 0.18 * W and h > 0.05 * H and a > 0.15 * w * h and w * h < 0.6 * W * H]
    changed = True
    while changed:
        changed = False
        for i in range(len(R)):
            for j in range(i + 1, len(R)):
                a, c = R[i], R[j]
                if a[0] < c[2] + 8 and c[0] < a[2] + 8 and a[1] < c[3] + 8 and c[1] < a[3] + 8:
                    R[i] = (min(a[0], c[0]), min(a[1], c[1]), max(a[2], c[2]), max(a[3], c[3]))
                    del R[j]
                    changed = True
                    break
            if changed:
                break
    return R


def ink_black(im, x, y, x1, y1):
    """Anteil schwarzer/grauer Schrift an den dunklen Pixeln (Zierschrift ist blau/grün/rot)"""
    c = im[max(0, y):y1, max(0, x):x1].astype(np.int16)
    if not c.size:
        return 0
    mn, mx = c.min(2), c.max(2)
    dark = mx < 150
    if dark.sum() < 5:
        return 0
    return float(((mx - mn < 40) & dark).sum()) / float(dark.sum())


def ocr_words(im, box, inv=False):
    """Wörter im Bereich (Tesseract „sparse text“, 2-fach vergrößert) in Seiten-Koordinaten"""
    x, y, x1, y1 = box
    g = cv2.cvtColor(im[y:y1, x:x1], cv2.COLOR_BGR2GRAY)
    if inv:
        g = 255 - g
    g = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    W = []
    for r in tess(g, 11, tsv=True, lang="deu").splitlines()[1:]:
        r = r.split("\t")
        if len(r) < 12 or not r[11].strip() or float(r[10]) < 0:
            continue
        wx, wy, ww, wh = (int(v) // 2 for v in r[6:10])
        W.append({"t": r[11].strip(), "x": x + wx, "y": y + wy, "x1": x + wx + ww, "y1": y + wy + wh, "h": wh, "c": float(r[10])})
    return W


def ocr_lines(im, box, inv=False):
    """Wörter zu Zeilen: gleiche Höhe, gleiche Grundlinie, kleiner Abstand (keine Spalten-Vermischung)"""
    W = sorted(ocr_words(im, box, inv), key=lambda w: (w["x"]))
    L = []
    for w in W:
        for e in L:
            last = e["w"][-1]
            hh = max(last["h"], w["h"])
            if abs(w["y1"] - last["y1"]) < 0.45 * hh and 0 <= w["x"] - last["x1"] < 1.6 * hh and abs(w["h"] - last["h"]) < 0.5 * hh:
                e["w"].append(w)
                break
        else:
            L.append({"w": [w]})
    out = []
    for e in L:
        ws = e["w"]
        out.append({"t": " ".join(w["t"] for w in ws), "w": ws, "x": min(w["x"] for w in ws), "y": min(w["y"] for w in ws),
                    "x1": max(w["x1"] for w in ws), "y1": max(w["y1"] for w in ws), "inv": inv})
        out[-1]["h"] = int(np.median([w["h"] for w in ws]))
    return sorted(out, key=lambda e: (e["y"], e["x"]))


DECO = re.compile(r"WEITERE|SORTEN|ANGEBOT|LIMITIERT|ERHÄLTLICH|M[ÄA]RKTE IN|DEINER N[ÄA]HE|ZOOKAUF|GÜLTIG|AKTIONSPREIS|UNSER NEUES|"
                  r"HEIMTIER-JOURNAL|KOSTENLOS|UNTERSTÜTZE|TIERHEIM|WUNSCHLISTE|FOLGE UNS", re.I)


def head_words(e, im):
    """Wörter einer Überschrift-Zeile: GROSSBUCHSTABEN, Schrifthöhe wie Artikelnamen (Zierschrift ist größer)"""
    if DECO.search(e["t"]):
        return []
    return [w for w in e["w"] if re.fullmatch(r"[A-ZÄÖÜ][A-ZÄÖÜß'’&+\-]*[A-ZÄÖÜ!\-]|[&+]", w["t"].strip(".,:;‚“\"")) and 11 <= w["h"] <= 30
            and w["c"] > 40 and plain(im, w, e["inv"])]


def plain(im, w, inv):
    """Prospekt-Schrift auf ruhigem Grund (Kasten), nicht Aufdruck auf einer Packung:
    schwarz auf weiß bzw. weiß auf einfarbigem Grund"""
    c = im[w["y"]:w["y1"], w["x"]:w["x1"]].astype(np.int16)
    if c.size == 0:
        return False
    mn, mx = c.min(2), c.max(2)
    if not inv:
        bg = (mn > 210) & (mx - mn < 30)
        ink = mx < 120
        return bg.mean() > 0.2 and (ink & (mx - mn < 45)).sum() >= 0.9 * max(1, ink.sum()) and (bg | ink).mean() > 0.7
    txt = (mn > 200) & (mx - mn < 40)
    rest = c[~txt]
    return txt.mean() > 0.15 and len(rest) > 10 and float(rest.std(0).mean()) < 30


def is_head(e, im):
    hw = head_words(e, im)
    return len("".join(w["t"] for w in hw)) >= 3 and sum(len(w["t"]) for w in hw) >= 0.6 * len(re.sub(r"\s", "", e["t"]))


AMT = re.compile(r"(?:(\d+)\s*[x×]\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)\b", re.I)
GPR = re.compile(r"1\s*(kg|l)\s*[=:]\s*(\d+)[.,]\s?(\d\d)", re.I)


def amount_of(t):
    """„6 x 50 g Frischebeutel (1 kg = 8,30 €)“ -> (Menge in kg/l, Grundpreis, Einheit) oder None"""
    t = re.sub(r"(\d)\s+9\s+(?=[A-ZÄÖÜ][a-zäöü])", r"\1 g ", t)  # „85 9 Frischebeutel“: g als 9 gelesen
    t = re.sub(r"(\d)\s?9(?=Beutel|Schale|Dose|Packung|Snack)", r"\1 g ", t)
    g = GPR.search(t)
    a = AMT.search(t.split("(")[0])
    if not g or not a:
        return None
    n = int(a.group(1) or 1)
    v = float(a.group(2).replace(",", "."))
    u = a.group(3).lower()
    q = n * v / (1000 if u in ("g", "ml") else 1)
    return q, float(f"{g.group(2)}.{g.group(3)}"), g.group(1).lower()


def prose(e):
    """normale Textzeile (Beschreibung), kein Bild-Rauschen"""
    toks = e["t"].split()
    good = [t for t in toks if re.fullmatch(r"[„“\"(]?[A-Za-zÄÖÜäöüß][a-zäöüß\-]*[,.;:!)“\"]?|[&+\-–]|\d+", t)]
    return 9 <= e["h"] <= 24 and len(toks) and sum(map(len, good)) >= 0.75 * sum(map(len, toks))


def reread(im, e):
    """kleine Zeile (Menge/Grundpreis) nochmal 4-fach vergrößert lesen"""
    c = im[max(0, e["y"] - 4):e["y1"] + 4, max(0, e["x"] - 4):e["x1"] + 4]
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    if e.get("inv"):
        g = 255 - g
    g = cv2.resize(g, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    g = cv2.copyMakeBorder(g, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    return tess(g, 7, lang="deu").strip()


def tidy_name(lines):
    words = []
    s = " ".join(lines)
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)  # Trennstrich am Zeilenende
    for w in s.split():
        w = re.sub(r"^[^\wÄÖÜ&+'’]+|[^\wÄÖÜ&+'’!-]+$", "", w)
        if not w:
            continue
        if w.isupper() and len(w) <= 4 and not re.search(r"[AEIOUÄÖÜ]", w):
            words.append(w)  # HPC, XXL
        elif re.fullmatch(r"[A-ZÄÖÜß'’&+\-]+", w) or w.isupper():
            words.append("-".join(p[:1] + p[1:].lower() for p in w.split("-")))
        else:
            words.append(w)
    return " ".join(words).replace("’S", "’s").replace("'S", "'s")


def animal(txt):
    t = txt.lower()
    if re.search(r"katz|samtpfote|kitten|stubentiger|freigänger|\bcat\b|sheba|felix|whiskas|gourmet|miamor|catsan|dreamies|perfect fit", t):
        if re.search(r"streu|spiel|kratz|toilette", t):
            return "Katzenbedarf"
        return "Katzenfutter"
    if re.search(r"hund|welpe|dog|rinti|happy dog|bosch|leine|geschirr", t):
        return "Hundefutter" if re.search(r"futter|snack|nahrung|knochen|dose|schale|meateez|kau", t) else "Hundebedarf"
    return "Tierbedarf"


def page_offers(im):
    H, W = im.shape[:2]
    P = prices(im)
    boxes = white_boxes(im)
    cache = {}
    found = []
    for pr in P:
        cx, cy = (pr["x"] + pr["x1"]) / 2, (pr["y"] + pr["y1"]) / 2
        inb = [b for b in boxes if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]]
        if inb:
            reg = min(inb, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        else:
            reg = (max(0, pr["x"] - 480), max(0, pr["y"] - 520), min(W, pr["x1"] + 200), min(H, pr["y1"] + 160))
        if reg not in cache:
            if inb:
                cache[reg] = ocr_lines(im, reg)
            else:  # freier Bereich (z. B. farbiger Kasten): Nachbar-Kästen ausblenden, weiße Schrift mitlesen
                im2 = im.copy()
                for bx in boxes:
                    im2[bx[1]:bx[3], bx[0]:bx[2]] = 255
                cache[reg] = ocr_lines(im2, reg) + ocr_lines(im2, reg, inv=True)
        L = cache[reg]
        heads = [e for e in L if is_head(e, im)]
        # Überschrift-Blöcke: direkt untereinander, links bündig
        blocks = []
        for e in sorted(heads, key=lambda e: e["y"]):
            for bl in blocks:
                last = bl[-1]
                if 0 <= e["y"] - last["y1"] < 1.1 * last["h"] and abs(e["x"] - bl[0]["x"]) < 30:
                    bl.append(e)
                    break
            else:
                blocks.append([e])
        if not blocks:
            continue

        def dist(bl):
            bx = (min(e["x"] for e in bl) + max(e["x1"] for e in bl)) / 2
            by = (bl[0]["y"] + bl[-1]["y1"]) / 2
            d = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
            return d * (1.6 if by > cy else 1)
        bl = min(blocks, key=dist)
        # Beschreibung: Zeilen direkt unter der Überschrift (gleiche Spalte), bis zur Mengenangabe
        desc, amts = [], []
        y = bl[-1]["y1"]
        for e in sorted(L, key=lambda e: e["y"]):
            if e in bl or e["y"] < bl[-1]["y"] or e["inv"] != bl[0]["inv"]:
                continue
            if abs(e["x"] - bl[0]["x"]) < 40 and e["y"] - y < 2.2 * max(12, e["h"]) and not is_head(e, im):
                if amount_of(e["t"]) or re.search(r"\(\s*\d?\s*k?g|kg\s*=|\d\s*(?:g|kg|ml|l)\s+\w*(?:beutel|dose|schale|packung)", e["t"], re.I):
                    break
                if prose(e):
                    desc.append(e["t"])
                    y = e["y1"]
        for e in L:
            a = amount_of(e["t"])
            if not a and re.search(r"\d.*(?:kg|\(|=)", e["t"]):
                a = amount_of(reread(im, e))
            if a:
                ex, ey = (e["x"] + e["x1"]) / 2, (e["y"] + e["y1"]) / 2
                amts.append((abs(ex - cx) + abs(ey - cy), a, e["t"]))
        ok = [x for x in sorted(amts, key=lambda x: x[0]) if abs(x[1][0] * x[1][1] - pr["p"]) <= max(0.04 * pr["p"], 0.03)]
        if amts and not ok:
            log(f"    verworfen: {tidy_name([e['t'] for e in bl])} {pr['p']:.2f} € passt zu keinem Grundpreis "
                f"({'; '.join(a[2] for a in sorted(amts, key=lambda x: x[0])[:2])})")
            continue
        lines = [" ".join(w["t"] for w in head_words(e, im)) for e in bl]
        brand = tidy_name(lines[:1]) if len(lines) > 1 else None
        name = tidy_name(lines[1:] if brand else lines)
        if len(re.sub(r"[^A-Za-zÄÖÜäöü]", "", name)) < 3:
            continue
        amt = ok[0] if ok else None
        d = " ".join(desc)
        d = re.sub(r"(\w)-\s+(\w)", r"\1\2", d)
        if amt:
            q, g, u = amt[1]
            qs = f"{q:g} {u}" if q >= 1 else f"{round(q * 1000):g} {'g' if u == 'kg' else 'ml'}"
            d = (d + f" {qs} (1 {u} = {g:.2f} €)".replace(".", ",")).strip()
        x0 = min(reg[0], pr["x"]); y0 = min(reg[1], pr["y"]); x1 = max(reg[2], pr["x1"]); y1 = max(reg[3], pr["y1"])
        found.append({"n": name, "b": brand, "d": d[:300], "p": pr["p"],
                      "gp": {"v": amt[1][1], "u": amt[1][2]} if amt else None, "chk": 1 if amt else 0,
                      "cat": animal(" ".join(lines) + " " + d),
                      "cr": [round(100 * y0 / H, 1), round(100 * (W - x1) / W, 1), round(100 * (H - y1) / H, 1), round(100 * x0 / W, 1)]})
    # gleicher Artikel zweimal im Kasten (Sheba Beutel + Schale, beide 0,55) -> einmal
    out, seen = [], set()
    for o in found:
        k = (o["b"], o["n"], o["p"], (o["gp"] or {}).get("v"))
        if k not in seen:
            seen.add(k)
            out.append(o)
    return out


def validity(ims, ab):
    """„Gültig vom 07.11. – 14.11.2026“ unten auf den Seiten; sonst „gültig ab“ der Webseite + 8 Tage"""
    for im in ims:
        H = im.shape[0]
        c = im[int(H * .88):, :]
        hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
        m = ((hsv[..., 2] > 200) & (hsv[..., 1] < 60)).astype(np.uint8) * 255
        t = tess(cv2.resize(255 - m, None, fx=2, fy=2), 11, lang="deu")
        r = re.search(r"(\d\d)\.(\d\d)\.?\s*[-–—]\s*(\d\d)\.(\d\d)\.(\d{4})", t)
        if r:
            y2 = int(r.group(5))
            y1 = y2 - 1 if int(r.group(2)) > int(r.group(4)) else y2
            return f"{y1}-{r.group(2)}-{r.group(1)}", f"{y2}-{r.group(4)}-{r.group(3)}"
    if ab:
        d = dt.date.fromisoformat(ab)
        return ab, (d + dt.timedelta(days=7)).isoformat()
    return None, None


def read_flyer(nm, url, ab):
    n = catalog(nm)
    if not n:
        return None, []
    ims, offers = [], []
    for i in range(1, n + 1):
        b = get(page_url(nm, i), binary=True)
        if not b:
            ims.append(None)
            continue
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
        ims.append(im)
    fr, to = validity([im for im in ims if im is not None], ab)
    for i, im in enumerate(ims, 1):
        if im is None:
            continue
        t0 = time.time()
        got = page_offers(im)
        log(f"  {nm} Seite {i}: {len(got)} Angebote ({time.time() - t0:.0f} s)")
        for o in got:
            o.update({"pg": i, "img": page_url(nm, i), "from": fr, "to": to, "fid": nm, "url": url})
            offers.append(o)
    return {"from": fr, "to": to, "pages": n, "n": len(offers), "url": url}, offers


def main():
    today = dt.date.today().isoformat()
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {"flyers": {}, "offers": []}
    names, ab = flyers()
    log(f"Zookauf-Prospekte: {', '.join(names) or 'keine'}")
    fl = {k: v for k, v in (old.get("flyers") or {}).items() if (v.get("to") or "9") >= today}
    offers = [o for o in old.get("offers") or [] if o.get("fid") in fl]
    for nm, url in names.items():
        if nm in fl and not os.environ.get("SR_ZK_FORCE"):
            continue
        info, got = read_flyer(nm, url, ab.get(nm))
        if not info:
            continue
        if info["to"] and info["to"] < today:
            log(f"  {nm}: abgelaufen ({info['to']})")
            continue
        fl[nm] = info
        offers = [o for o in offers if o.get("fid") != nm] + got
        log(f"  {nm}: {len(got)} Angebote, gültig {info['from']} bis {info['to']}")
    json.dump({"at": dt.datetime.now().isoformat(timespec="seconds"), "src": "zookauf.de Prospekt (Texterkennung)",
               "flyers": fl, "offers": offers}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"Zookauf: {len(offers)} Angebote in {len(fl)} Prospekten")


if __name__ == "__main__":
    if len(sys.argv) > 1:  # Test: python fetch_zookauf.py seite.jpg …
        for f in sys.argv[1:]:
            for o in page_offers(cv2.imread(f)):
                print(f"{os.path.basename(f)}: {o['b'] or ''} | {o['n']} | {o['p']:.2f} | gp={o['gp']} | {o['cat']} | {o['d'][:70]}")
    else:
        main()
