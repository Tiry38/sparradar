"""Einmalige Diagnose: Welche Bildgrößen liefert kaufDA (bonial) wirklich? (Nur von Hand, wenige Abrufe.)"""
import json
import struct
import urllib.request

UA = "SparRadar/1.0 (private Angebotsuebersicht; 1 Abruf pro Tag)"


def size(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
            data = r.read()
            ct = r.headers.get("Content-Type")
    except Exception as e:
        return f"FEHLER {e}"
    w = h = None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
    else:  # JPEG: SOF-Marker suchen
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            m = data[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                break
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return f"{len(data) // 1024} KB, {w}x{h}, {ct}"


offers = json.load(open("../docs/data/offers.json"))["offers"]
pick = [o for o in offers if "palmolive" in ((o.get("b") or "") + o["n"]).lower()][:1]
pick += [o for o in offers if o["s"] == "lidl" and "bonial" in (o.get("img") or "")][:1]
pick += [o for o in offers if o["s"] == "rewe" and "bonial" in (o.get("img") or "")][:1]
for o in pick:
    base = (o.get("il") or o.get("img")).split("?")[0]
    print("\n===", o["s"], o["n"])
    for q in ("?impolicy=SEO-offer-normal", "", "?impolicy=SEO-offer-large", "?impolicy=SEO-offer-zoom",
              "?impolicy=zoomlarge", "?width=1500", "?impolicy=original"):
        print(f"  {q or '(ohne)':32s} {size(base + q)}")
