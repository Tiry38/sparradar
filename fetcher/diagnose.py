"""Einmalige Diagnose: Liefert kaufDA die Prospektseite unter /<Prospekt-ID>/zoomlarge_page_<Seite>.jpg?"""
import struct
import urllib.request

import fetch_offers as f


def size(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f.UA}), timeout=30) as r:
            data = r.read()
    except Exception as e:
        return f"FEHLER {e}"
    i, w, h = 2, None, None
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        if data[i + 1] in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            break
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return f"OK {len(data) // 1024} KB, {w}x{h}"


for store in ("netto", "lidl", "rewe"):
    items, _ = f.kd_page(f.KD_STORES[store])
    for it in items[:2]:
        pc = it.get("parentContent") or {}
        u = f"https://content-media.bonial.biz/{pc.get('id')}/zoomlarge_page_{(pc.get('page') or {}).get('number')}.jpg"
        print(store, it.get("title"), "->", u, "->", size(u))
