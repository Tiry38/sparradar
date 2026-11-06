"""Scheck-In Center: Angebote aus dem Prospekt lesen (Texterkennung).

kaufDA zeigt vom Scheck-In-Prospekt (~420 Angebote) nur immer dieselben ersten 16, eine öffentliche Liste gibt es
nirgends (geprüft 02.11.: meinprospekt = dieselben 12, marktguru = nur abgelaufene, prospektangebote = keine
Einzelangebote, scheck-in-center.de verbietet Abrufe). prospektangebote.de zeigt aber den ganzen Prospekt als
Seitenbilder (robots.txt erlaubt /anzeigen/angebote/…, Bilder auf img.offers-cdn.net). Laut Fußnote gilt der Prospekt
für alle Scheck-In Center, also auch Wörth.

Ablauf je Seite:
1. Preise: rote Ziffern finden (Euro groß, Cent hochgestellt), jede Ziffer mit Vorlagen aus `ocr_digits.json`
   vergleichen (kein Tesseract für Preise: der verwechselt in dieser Schrift 2 und 4). Unsichere Ziffer = Preis weg.
2. Text: Tesseract (deutsch) liefert Wörter mit Position; Zeilen -> Absätze; fett = Artikelname, normal = Beschreibung.
3. Zuordnung: Absatz links neben dem Preis (unten bündig) oder direkt darüber. Nur eindeutige Paare werden
   übernommen (kein zweiter Absatz fast gleich nah, Absatz passt nicht ebenso gut zu einem anderen Preis).
4. Der Absatz wird nochmal vergrößert gelesen (bessere Namen).
5. Durchgestrichener Preis (UVP/statt) über `read_was`: nur wenn er genau zum roten „-NN%“-Kästchen passt.
Jedes Angebot zeigt in der App den Prospekt-Ausschnitt (`cr`) und beim Antippen die ganze Seite (`il`) –
so lässt sich jeder Preis im Original prüfen.

Braucht: tesseract-ocr + tesseract-ocr-deu, numpy, opencv-python-headless (nur im Workflow installiert).
Ergebnis: docs/data/scheck-ocr.json {flyers: {id: {from, to, pages, n}}, offers: [...]}. Ein Prospekt wird nur
einmal gelesen; abgelaufene fliegen raus. fetch_offers.py übernimmt die Angebote (Doppelte zu kaufDA fliegen raus).
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "docs", "data")
OUT = os.path.join(DATA, "scheck-ocr.json")
PA = "https://www.prospektangebote.de"
CDN = "https://img.offers-cdn.net"
UA = "SparRadar/1.0 (+https://github.com/Tiry38/sparradar; private Angebots-App)"
PAUSE = 2.0
os.environ.setdefault("OMP_THREAD_LIMIT", "1")


def log(*a):
    print(*a, flush=True)


def get(url, binary=False):
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40)
            b = r.read()
            return b if binary else b.decode("utf-8", "replace")
        except Exception as e:
            log(f"  Fehler {url}: {e}")
            time.sleep(5 * (i + 1))
    return None


# ---------- Preise ----------
_T = json.load(open(os.path.join(HERE, "ocr_digits.json")))
GW, GH = _T["w"], _T["h"]
TL, TX = [], []
for d, rows in _T["t"].items():
    for r in rows:
        TL.append(d)
        TX.append([int(c) for c in bin(int(r, 16))[2:].zfill(GW * GH)])
TX = np.array(TX, np.int16)


def gnorm(m):
    return (cv2.resize(m, (GW, GH), interpolation=cv2.INTER_AREA) > 100).astype(np.int16).ravel()


def digit(m):
    dist = (TX != gnorm(m)).sum(1)
    j = int(dist.argmin())
    return TL[j] if dist[j] <= 90 else "?"


def read_prices(im):
    b, g, r = [im[:, :, i].astype(int) for i in range(3)]
    red = ((r > 150) & (g < 90) & (b < 110) & (r - g > 90)).astype(np.uint8) * 255
    n, lab, st, _ = cv2.connectedComponentsWithStats(red, 8)
    comps = [tuple(int(v) for v in st[i]) + (i,) for i in range(1, n) if st[i][3] >= 20 and st[i][4] >= 120]
    used, out = set(), []
    big = sorted([c for c in comps if c[3] >= 40 and c[2] <= c[3] * 1.1 and c[4] / (c[2] * c[3]) < 0.85],
                 key=lambda c: (c[1] // 30, c[0]))
    for c in big:
        if c[5] in used:
            continue
        H, top = c[3], c[1]
        eur, x1 = [c], c[0] + c[2]
        for d in sorted(comps, key=lambda d: d[0]):
            if d[5] != c[5] and d[5] not in used and abs(d[3] - H) <= 0.12 * H and abs(d[1] - top) <= 0.1 * H and 0 <= d[0] - x1 <= 0.5 * H:
                eur.append(d)
                x1 = d[0] + d[2]
        ct = [d for d in sorted(comps, key=lambda d: d[0])
              if 0.4 * H <= d[3] <= 0.75 * H and abs(d[1] - top) <= 0.12 * H and 0 <= d[0] - x1 <= 0.6 * H][:2]
        if len(ct) != 2 or ct[1][0] - (ct[0][0] + ct[0][2]) > 0.4 * H:
            continue
        for d in eur + ct:
            used.add(d[5])
        s = "".join(digit((lab[d[1]:d[1] + d[3], d[0]:d[0] + d[2]] == d[5]).astype(np.uint8) * 255) for d in eur)
        s += "." + "".join(digit((lab[d[1]:d[1] + d[3], d[0]:d[0] + d[2]] == d[5]).astype(np.uint8) * 255) for d in ct)
        if not re.fullmatch(r"\d{1,3}\.\d\d", s):
            continue
        out.append({"box": (c[0], top, ct[1][0] + ct[1][2], max(d[1] + d[3] for d in eur)), "p": float(s)})
    return out


# ---------- Durchgestrichener Preis (UVP / statt) ----------
# Klein (11 px), durchgestrichen, rechts unter den Cent-Ziffern; darüber oft das Wort „UVP“, über dem Preis ein rotes
# Kästchen „-33%“. Tesseract liest die Zahl unsicher (5,99 -> 5,29; 4,79 -> 4,75). Darum: Ziffern an festen Stellen
# mit Vorlagen (`ocr_uvp.json`) vergleichen, aber nur unter den Zahlen, die genau zum gedruckten Prozentwert passen
# (Prospekt rundet ab: floor((UVP - Preis) / UVP * 100)). Ohne lesbares Kästchen oder bei knappem Ergebnis: nichts.
_U = json.load(open(os.path.join(HERE, "ocr_uvp.json")))
UT = {d: np.array(v, np.float32) for d, v in _U["t"].items()}


def _small_bands(im, box):
    x0, y0, x1, y1 = box
    H = y1 - y0
    h, w = im.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 + int(.45 * (x1 - x0))), max(0, y0 + int(.45 * H)), min(w, x1 + int(.5 * H)), min(h, y1 + int(.35 * H))
    s = im[Y0:Y1, X0:X1].astype(int)
    b, g, r = s[:, :, 0], s[:, :, 1], s[:, :, 2]
    m = (((r > 120) & (r - g > 60) & (r - b > 40)) | ((.3 * r + .59 * g + .11 * b) < 150)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        if hh > .17 * H or ww > .4 * H or a < 4 or x == 0 or y == 0:
            continue  # Preisziffern, angeschnittene Teile, Staub
        keep[lab == i] = 1
    rows, bands, i = keep.sum(1), [], 0
    while i < len(rows):
        if rows[i]:
            j = i
            while j < len(rows) and rows[j]:
                j += 1
            if j - i >= 5:
                bands.append((i, j))
            i = j
        else:
            i += 1
    return keep, bands, X0, Y0


def _cells(g):
    W = g.shape[1]
    nd = 3 if W < 38 else 4  # „5.99“ ~33 px, „27.99“ ~42 px
    sc = W / (nd * _U["a"] + _U["dot"] - 1.0)
    xs, x = [], 0.0
    for i in range(nd):
        if i == nd - 2:
            x += _U["dot"]
        xs.append(x)
        x += _U["a"]
    out = []
    for x in xs:
        a, e = int(round(x * sc)), min(W, int(round((x + _U["gw"]) * sc)))
        c = cv2.resize(g[:, a:e], (_U["pw"], _U["ph"]), interpolation=cv2.INTER_AREA)
        c = c - c.mean()
        out.append((c / (np.linalg.norm(c) + 1e-6)).ravel())
    return out


def _badge(im, box):
    """Prozent im roten Kästchen über dem Preis („-33%“), sonst None."""
    x0, y0, x1, y1 = box
    H = y1 - y0
    h, w = im.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 - int(.3 * H)), max(0, y0 - int(.75 * H)), min(w, x1 + int(.4 * H)), y0 + int(.1 * H)
    s = im[Y0:Y1, X0:X1].astype(int)
    b, g, r = s[:, :, 0], s[:, :, 1], s[:, :, 2]
    red = ((r > 150) & (g < 90) & (b < 120)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(red, 8)
    best = None
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        if ww > .6 * H and .2 * H < hh < .6 * H and a > .5 * ww * hh and (best is None or y > best[1]):
            best = (x, y, ww, hh)
    if not best:
        return None
    x, y, ww, hh = best
    wh = (s[y + 2:y + hh - 2, x + 2:x + ww - 2].min(2) > 170).astype(np.uint8)
    img = cv2.copyMakeBorder(cv2.resize(255 - wh * 255, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC).astype(np.uint8),
                             20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    fd, tp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    cv2.imwrite(tp, img)
    t = subprocess.run(["tesseract", tp, "-", "--psm", "7", "-c", "tessedit_char_whitelist=-0123456789%"],
                       capture_output=True, text=True).stdout.replace(" ", "").strip()
    os.remove(tp)
    m = re.fullmatch(r"-(\d{1,2})%", t)
    return int(m.group(1)) if m and 5 <= int(m.group(1)) <= 80 else None


def read_was(im, box, p):
    """Durchgestrichener Preis zu Preis p: (Preis, UVP?) oder None."""
    pct = _badge(im, box)
    if not pct:
        return None
    keep, bands, X0, Y0 = _small_bands(im, box)
    if not bands:
        return None
    a, b = bands[-1]
    nb = keep[a:b]
    cols = np.where(nb.any(0))[0]
    c0, c1 = cols[0], cols[-1] + 1
    nb = nb[:, c0:c1]
    if not (28 <= c1 - c0 <= 46 and 8 <= b - a <= 15) or not (nb.sum(1) > .6 * nb.shape[1]).any():
        return None  # keine Zahl in passender Größe oder nicht durchgestrichen
    g = 255 - cv2.cvtColor(im[Y0 + a:Y0 + b, X0 + c0:X0 + c1], cv2.COLOR_BGR2GRAY).astype(np.float32)
    cl = _cells(g)
    sim = {d: [float((t @ v).max()) for v in cl] for d, t in UT.items()}
    free = "".join(max(sim, key=lambda d: sim[d][i]) for i in range(len(cl)))
    R = []
    for c in range(int(round(p * 100)) + 1, int(round(p * 300)) + 1):
        u = c / 100
        st = f"{u:.2f}".replace(".", "")
        if len(st) == len(cl) and int((u - p) / u * 100 + 1e-9) == pct:
            R.append((sum(sim[d][i] for i, d in enumerate(st)), u, st))
    if not R:
        return None
    R.sort(reverse=True)
    sc, u, st = R[0]
    if len(R) > 1 and sc - R[1][0] < 0.15:
        return None  # zwei Zahlen fast gleich gut -> unsicher
    if sum(x != y for x, y in zip(st, free)) > 1:
        return None  # Ziffern allein gelesen weichen zu stark ab
    return u, len(bands) >= 2  # zwei Zeilen = „UVP“ + Zahl, eine = eigener früherer Preis


# ---------- Text ----------
def tess(path, psm):
    return subprocess.run(["tesseract", path, "-", "-l", "deu", "--psm", str(psm), "tsv"],
                          capture_output=True, text=True).stdout


def runlen(dark):
    tr = np.abs(np.diff(dark.astype(int), axis=1)).sum() / 2
    return dark.sum() / tr if tr else 0


def words(path, gray):
    W = []
    for ln in tess(path, 3).splitlines()[1:]:
        f = ln.split("\t")
        if len(f) < 12 or not f[11].strip() or float(f[10]) < 25:
            continue
        x, y, w, h = map(int, f[6:10])
        t = f[11].strip()
        if h < 8 or h > 60 or not re.search(r"[A-Za-zÄÖÜäöüß0-9]", t):
            continue
        W.append({"t": t, "x": x, "y": y, "w": w, "h": h, "b": (int(f[2]), int(f[3]), int(f[4])),
                  "bold": runlen(gray[y:y + h, x:x + w] < 120) >= 4.2})
    return W


def mk_lines(W, P):
    G = {}
    for w in W:
        if any(p["box"][0] - 8 <= w["x"] + w["w"] / 2 <= p["box"][2] + 8 and p["box"][1] - 8 <= w["y"] + w["h"] / 2 <= p["box"][3] + 8 for p in P):
            continue
        G.setdefault(w["b"], []).append(w)
    L = []
    for ws in G.values():
        ws.sort(key=lambda w: w["x"])
        cur = [ws[0]]
        for w in ws[1:]:
            if w["x"] - (cur[-1]["x"] + cur[-1]["w"]) > 2.2 * np.median([v["h"] for v in cur]):
                L.append(cur)
                cur = [w]
            else:
                cur.append(w)
        L.append(cur)
    return sorted(({"ws": ws, "x0": min(w["x"] for w in ws), "x1": max(w["x"] + w["w"] for w in ws),
                    "y0": int(np.median([w["y"] for w in ws])), "y1": int(np.median([w["y"] + w["h"] for w in ws])),
                    "h": float(np.median([w["h"] for w in ws]))} for ws in L), key=lambda l: (l["y0"], l["x0"]))


def paras(L):
    Ps = []
    for l in L:
        best = None
        for p in Ps:
            q = p["ls"][-1]
            gap = l["y0"] - q["y1"]
            if not (-0.3 * l["h"] <= gap <= 1.1 * max(l["h"], q["h"])):
                continue
            ov = min(l["x1"], q["x1"]) - max(l["x0"], q["x0"])
            al = min(abs(l["x0"] - q["x0"]), abs(l["x1"] - q["x1"]), abs((l["x0"] + l["x1"]) / 2 - (q["x0"] + q["x1"]) / 2))
            if ov <= 0.25 * min(l["x1"] - l["x0"], q["x1"] - q["x0"]) and al > 15:
                continue
            if best is None or gap < best[0]:
                best = (gap, p)
        if best:
            best[1]["ls"].append(l)
        else:
            Ps.append({"ls": [l]})
    for p in Ps:
        p["x0"] = min(l["x0"] for l in p["ls"])
        p["x1"] = max(l["x1"] for l in p["ls"])
        p["y0"], p["y1"] = p["ls"][0]["y0"], p["ls"][-1]["y1"]
        p["bold"] = sum(w["bold"] and len(w["t"]) >= 3 for l in p["ls"] for w in l["ws"])
    return [p for p in Ps if p["bold"]]


def score(T, P):
    px0, py0, px1, py1 = P["box"]
    H, s = py1 - py0, []
    if px0 - 160 <= T["x1"] <= px0 + 15 and py0 - 0.6 * H <= T["y1"] <= py1 + 0.5 * H:  # links daneben, unten bündig
        s.append(abs(px0 - T["x1"]) * 0.5 + abs(T["y1"] - py1) * 0.5)
    if py0 - 260 <= T["y1"] <= py0 + 15 and (abs(T["x0"] - px0) <= 70 or T["x0"] - 20 <= (px0 + px1) / 2 <= T["x1"] + 20):  # darüber
        s.append((py0 - T["y1"]) * 0.5 + min(abs(T["x0"] - px0), 60) * 0.5 + 20)
    return min(s) if s else None


def split_name(seq):
    name, desc = [], []
    for t, bold in seq:
        if bold and (not desc or (name and desc[-1] in ("oder", "und", "&", "/"))):
            if desc and name:
                name.append(desc.pop())
            name.append(t)
        elif name or not bold:
            desc.append(t)
    return " ".join(name), " ".join(desc)


def reread(gray, box, avoid):
    """Absatz vergrößert nochmal lesen; nach oben erweitern, solange direkt darüber Text steht (verlorene 1. Zeile)."""
    x0, y0, x1, y1 = box
    dark = gray < 110
    while y0 - 22 > 0 and dark[y0 - 22:y0, x0:x1].mean() > 0.02 and not any(
            a[0] - 5 < x1 and x0 < a[2] + 5 and a[1] - 5 < y0 and y0 - 22 < a[3] + 5 for a in avoid):
        y0 -= 22
    while y0 > 0 and dark[y0, x0:x1].mean() > 0.003:
        y0 -= 1
    crop = cv2.resize(gray[max(0, y0 - 4):y1 + 6, max(0, x0 - 6):x1 + 6], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    f = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    cv2.imwrite(f, crop)
    out = tess(f, 6)
    os.unlink(f)
    seq = []
    for ln in out.splitlines()[1:]:
        q = ln.split("\t")
        if len(q) < 12 or not q[11].strip() or float(q[10]) < 20 or not re.search(r"[A-Za-zÄÖÜäöüß0-9]", q[11]):
            continue
        x, y, w, h = map(int, q[6:10])
        seq.append((q[11].strip(), runlen(crop[y:y + h, x:x + w] < 110) / 2 >= 4.2))
    return split_name(seq), (x0, y0, x1, y1)


def tidy(s):
    s = re.sub(r"(\w)- (?=[a-zäöüß])", r"\1", s)                     # Trennstriche am Zeilenende
    s = re.sub(r"\b(\d+(?:[,.-]\d+)?) ?8\b(?![,.]\d)", r"\1 g", s)    # „100 8“/„1008“ = 100 g (g wird als 8 gelesen)
    s = re.sub(r"\b(\d{2,3})8\b(?![,.]\d)", r"\1 g", s)
    s = re.sub(r"\(\s*[1Il]\s*(kg|L|l)\b", r"(1 \1", s)
    s = s.replace("„", "").replace("“", "").replace("®", "")
    s = re.sub(r"\s+(je|JE|Je)$", "", s.strip())
    return re.sub(r"\s+", " ", s).strip(" ,;:-")


def page_offers(path):
    im = cv2.imread(path)
    if im is None:
        return []
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    P = read_prices(im)
    Ts = paras(mk_lines(words(path, gray), P))
    S = [[score(t, p) for t in Ts] for p in P]
    taken = [p["box"] for p in P] + [(t["x0"], t["y0"], t["x1"], t["y1"]) for t in Ts]
    out = []
    for i, p in enumerate(P):
        c = sorted((s, j) for j, s in enumerate(S[i]) if s is not None)
        if not c:
            continue
        s, j = c[0]
        if len(c) > 1 and c[1][0] - s < 25:
            continue  # zwei Texte fast gleich nah -> unsicher
        others = [S[k][j] for k in range(len(P)) if k != i and S[k][j] is not None]
        if others and min(others) - s < 25:
            continue  # Text passt genauso gut zu einem anderen Preis -> unsicher
        t = Ts[j]
        tb = (t["x0"], t["y0"], t["x1"], t["y1"])
        (name, desc), tb = reread(gray, tb, [a for a in taken if a != tb and a != p["box"]])
        name, desc = tidy(name), tidy(desc)
        if len(re.sub(r"[^A-Za-zÄÖÜäöüß]", "", name)) < 4:
            continue
        # Ausschnitt für die Karte: Text + Preis, etwas Rand, nach oben Platz für das Produktfoto
        X0, Y0 = min(tb[0], p["box"][0]) - 15, min(tb[1], p["box"][1]) - 15
        X1, Y1 = max(tb[2], p["box"][2]) + 15, max(tb[3], p["box"][3]) + 15
        Y0 -= int((Y1 - Y0) * 0.6)
        hh, ww = gray.shape
        X0, Y0, X1, Y1 = max(0, X0), max(0, Y0), min(ww, X1), min(hh, Y1)
        cr = [round(Y0 / hh * 100, 1), round((ww - X1) / ww * 100, 1), round((hh - Y1) / hh * 100, 1), round(X0 / ww * 100, 1)]
        o = {"n": name, "d": desc, "p": p["p"], "cr": cr}
        w = read_was(im, p["box"], p["p"])
        if w:
            o["o"], o["ou"] = w[0], 1 if w[1] else 0
        out.append(o)
    return out


# ---------- Prospekte ----------
def flyers():
    h = get(f"{PA}/geschaefte/scheck-in-center/prospekte-angebote") or ""
    ids = list(dict.fromkeys(re.findall(r"/anzeigen/angebote/(scheck-in-center-prospekt-(\d+))", h)))
    out = []
    for slug, fid in ids:
        time.sleep(PAUSE)
        f = get(f"{PA}/anzeigen/angebote/{slug}") or ""
        m = re.search(r"Gültig von (\d\d)/(\d\d)/(\d{4}) bis (\d\d)/(\d\d)/(\d{4})", f)
        pg = re.search(r"let flyerPages = (\[.*?\]);", f)
        if not m or not pg:
            log(f"  Prospekt {fid}: kein Datum/keine Seiten")
            continue
        start = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        end = f"{m.group(6)}-{m.group(5)}-{m.group(4)}"
        pages = [x["page"] for x in json.loads(pg.group(1))]
        out.append({"id": fid, "from": start, "to": end, "pages": pages, "url": f"{PA}/anzeigen/angebote/{slug}"})
    if not ids:  # GitHub-Server bekommen von prospektangebote nur „202, leer“ -> Prospektliste vom PC-Abruf (docs/pc/abruf.py)
        try:
            pc = json.load(open(os.path.join(DATA, "pc-pa.json"), encoding="utf-8"))
            if (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(pc["at"])).days <= 4:
                out = [f for f in pc.get("scheck") or [] if f.get("id") and f.get("pages")]
                log(f"  Prospektliste vom PC-Abruf ({pc['at']}): {len(out)} Prospekt(e)")
        except Exception as e:
            log(f"  kein PC-Abruf da ({e})")
    return out


def main():
    today = dt.date.today().isoformat()
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {"flyers": {}, "offers": []}
    keep_f = {k: v for k, v in old.get("flyers", {}).items() if v.get("to", "") >= today}
    keep_o = [o for o in old.get("offers", []) if o.get("fid") in keep_f]
    tmp = tempfile.mkdtemp()
    changed = len(keep_f) != len(old.get("flyers", {}))
    # schon gelesene Prospekte: durchgestrichene Preise nachlesen (einmal je Prospekt, Merker „wv“)
    for fid, fv in keep_f.items():
        if fv.get("wv"):
            continue
        pages = {}
        for o in keep_o:
            if o.get("fid") == fid and o.get("il"):
                pages.setdefault(o["pg"], []).append(o)
        got = 0
        for pg, rows in sorted(pages.items()):
            time.sleep(PAUSE)
            b = get(rows[0]["il"], binary=True)
            im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR) if b else None
            if im is None:
                continue
            for pr in read_prices(im):
                hit = [o for o in rows if abs(o["p"] - pr["p"]) < .001]
                if len(hit) != 1:
                    continue  # Preis auf der Seite nicht eindeutig einem Angebot zuzuordnen
                w = read_was(im, pr["box"], pr["p"])
                if w:
                    hit[0]["o"], hit[0]["ou"] = w[0], 1 if w[1] else 0
                    got += 1
        fv["wv"] = 1
        changed = True
        log(f"Prospekt {fid}: {got} durchgestrichene Preise (UVP/statt) nachgelesen")
    for fl in flyers():
        if fl["to"] < today or fl["id"] in keep_f:
            continue
        log(f"Prospekt {fl['id']} ({fl['from']} bis {fl['to']}, {len(fl['pages'])} Seiten)")
        got = []
        for n, pth in enumerate(fl["pages"], 1):
            time.sleep(PAUSE)
            b = get(CDN + pth.replace("%s", "large"), binary=True)
            if not b:
                continue
            fp = os.path.join(tmp, f"p{n}.jpg")
            open(fp, "wb").write(b)
            try:
                po = page_offers(fp)
            except Exception as e:
                log(f"  Seite {n}: {e}")
                continue
            for o in po:
                o.update({"pg": n, "img": CDN + pth.replace("%s", "normal"), "il": CDN + pth.replace("%s", "large"),
                          "from": fl["from"], "to": fl["to"], "fid": fl["id"], "url": fl["url"]})
            got += po
            log(f"  Seite {n}: {len(po)} Angebote")
        if len(got) < 20:
            log(f"  nur {len(got)} Angebote erkannt – Prospekt wird beim nächsten Mal nochmal versucht")
            continue
        keep_f[fl["id"]] = {"from": fl["from"], "to": fl["to"], "pages": len(fl["pages"]), "n": len(got), "wv": 1}
        keep_o += got
        changed = True
        log(f"  -> {len(got)} Angebote")
    if changed or not os.path.exists(OUT):
        with open(OUT + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                       "src": "prospektangebote.de (Prospektseiten, Texterkennung)", "flyers": keep_f, "offers": keep_o},
                      f, ensure_ascii=False, separators=(",", ":"))
        os.replace(OUT + ".tmp", OUT)  # erst fertig schreiben, dann tauschen (kein halbes JSON bei Abbruch)
    log(f"Scheck-In: {len(keep_o)} Angebote aus {len(keep_f)} Prospekt(en)")


if __name__ == "__main__":
    if len(sys.argv) > 1:  # Test: einzelne Seitenbilder
        for p in sys.argv[1:]:
            for o in page_offers(p):
                print(o)
    else:
        main()
