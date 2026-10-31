"""Diagnose (nur von Hand): Wie groß (Pixel) sind die Angebotsbilder je Markt/Quelle wirklich?"""
import json
import os
import random
import re
import struct
import time
import urllib.request

import fetch_offers as f


def dims(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        if b[12:16] == b"VP8 ":
            w, h = struct.unpack("<HH", b[26:30]); return w & 0x3fff, h & 0x3fff
        if b[12:16] == b"VP8L":
            v = int.from_bytes(b[21:25], "little"); return (v & 0x3fff) + 1, ((v >> 14) & 0x3fff) + 1
        if b[12:16] == b"VP8X":
            return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1; continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9]); return w, h
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def get(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": f.UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read(), r.headers.get("Content-Type")
    except Exception as e:
        return None, str(e)[:60]


offers = json.load(open(os.path.join(f.DATA, "offers.json")))["offers"]
random.seed(1)
groups = {}
for o in offers:
    u = o.get("img") or ""
    src = "pw" if "prospektewoche" in u else "lidl.de" if "lidl.de" in u else "aldi" if "aldi" in u else "bonial"
    groups.setdefault((o["s"], src), []).append(o)
for (s, src), lst in sorted(groups.items()):
    small = 0
    print(f"\n##### {s} {src} ({len(lst)})")
    for o in random.sample(lst, min(8, len(lst))):
        b, ct = get(o["img"])
        d = dims(b) if b else None
        small += bool(d and max(d) < 400)
        print(f"  {d} {len(b) if b else ct} {ct if b else ''} {o['n'][:40]} {o['img']}")
        for v in (o["img"] + "?impolicy=SEO-offer-normal", re.sub(r"/[^/]+$", "/original.jpg", o["img"])) if src == "bonial" and not d or (d and max(d) < 400 and src == "bonial") else ():
            b2, ct2 = get(v); print("     alt", dims(b2) if b2 else ct2, v)
        time.sleep(0.5)
    print("  klein (<400px):", small)
