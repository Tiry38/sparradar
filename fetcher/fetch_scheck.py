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
        out.append({"n": name, "d": desc, "p": p["p"], "cr": cr})
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
        keep_f[fl["id"]] = {"from": fl["from"], "to": fl["to"], "pages": len(fl["pages"]), "n": len(got)}
        keep_o += got
        changed = True
        log(f"  -> {len(got)} Angebote")
    if changed or not os.path.exists(OUT):
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                       "src": "prospektangebote.de (Prospektseiten, Texterkennung)", "flyers": keep_f, "offers": keep_o},
                      f, ensure_ascii=False, separators=(",", ":"))
    log(f"Scheck-In: {len(keep_o)} Angebote aus {len(keep_f)} Prospekt(en)")


if __name__ == "__main__":
    if len(sys.argv) > 1:  # Test: einzelne Seitenbilder
        for p in sys.argv[1:]:
            for o in page_offers(p):
                print(o)
    else:
        main()
