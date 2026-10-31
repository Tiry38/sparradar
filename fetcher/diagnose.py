"""Diagnose (nur von Hand): Welche öffentlichen Prospekt-Portale zeigen Rewe/dm für nächste Woche
schon als Text? Prüft robots.txt (Erlaubnis) und den Seiteninhalt (Preise, strukturierte Daten)."""
import html as H
import json
import re
import urllib.parse
import urllib.request
import urllib.robotparser

import fetch_offers as f

PAGES = [
    "https://prospektewoche.de/rewe",
    "https://prospektewoche.de/dm",
    "https://onlineprospekt.de/rewe-prospekt/",
    "https://onlineprospekt.com/prospekte/rewe/",
    "https://www.prospektangebote.de/geschaefte/rewe/prospekte-angebote",
    "https://www.meinprospekt.de/rewe-de",
    "https://www.meinprospekt.de/dm-de",
    "https://www.kimbino.de/rewe/",
]


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", str(e)[:60]), ""


robots = {}
for url in PAGES:
    p = urllib.parse.urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in robots:
        st, txt = get(base + "/robots.txt")
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(txt.splitlines())
        robots[base] = rp
        print(f"\n##### {base} robots.txt {st}")
        print("\n".join(l for l in txt.splitlines() if l.strip())[:900])
    allowed = robots[base].can_fetch(f.UA, url)
    st, h = get(url)
    print(f"\n=== {url} | erlaubt={allowed} | status={st} | {len(h)} Zeichen")
    if not h:
        continue
    print("  Daten:", re.findall(r"\d\d\.\d\d\.(?:20)?\d\d", h)[:12])
    print("  NEXT_DATA" if "__NEXT_DATA__" in h else "", "NUXT" if "__NUXT" in h else "",
          "ld+json:", len(re.findall(r'application/ld\+json', h)))
    for m in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S)[:4]:
        print("  LD:", m.strip()[:400])
    txt = H.unescape(re.sub(r"<[^>]+>", " | ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)))
    txt = re.sub(r"\s*\|\s*(\|\s*)+", " | ", re.sub(r"\s+", " ", txt))
    prices = [m.start() for m in re.finditer(r"\d+[,.]\d\d\s?€", txt)]
    print("  Preise im Text:", len(prices))
    for i in prices[:25]:
        print("   ·", txt[max(0, i - 110):i + 12])
    links = sorted(set(re.findall(r'href="([^"]*(?:rewe|dm)[^"]*)"', h, re.I)))
    print("  Links:", links[:40])
