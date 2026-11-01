"""Diagnose (nur von Hand): Bildquellen für den Bilder-Wächter prüfen.
robots.txt von aldi-sued.de und lidl.de, Aldi-Produktseite/-Suche/-Sitemap und Lidl-Suche für einen Artikel ohne Bild."""
import re
import time
import urllib.request
import urllib.robotparser

import fetch_offers as f


def get(u, n=None):
    req = urllib.request.Request(u, headers={"User-Agent": f.UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read(n) if n else r.read()
        return r.status, r.headers.get("content-type", ""), b.decode("utf-8", "replace")


def robots(host, paths):
    try:
        _, _, txt = get(f"https://{host}/robots.txt")
    except Exception as e:
        print(host, "robots.txt:", str(e)[:80]); return
    rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines())
    for p in paths:
        print(host, p, "erlaubt:", rp.can_fetch(f.UA, f"https://{host}{p}"))
    print("   ", " | ".join(l for l in txt.splitlines() if l.strip())[:3000])


robots("www.aldi-sued.de", ["/produkt/ironmaxx-squeebarista-65-ml-salted-caramel-000000000759556001", "/suche?query=ironmaxx",
                            "/de/suche.html?search=ironmaxx", "/sitemap.xml"])
robots("www.lidl.de", ["/q/api/search?q=ironmaxx", "/p/x/p100"])

for u in ["https://www.aldi-sued.de/produkt/ironmaxx-squeebarista-65-ml-salted-caramel-000000000759556001",
          "https://www.aldi-sued.de/suche?query=squeebarista",
          "https://www.aldi-sued.de/sitemap.xml"]:
    try:
        st, ct, html = get(u)
        print("\n==", u, st, ct, len(html))
        print("   og:image", re.findall(r'<meta[^>]+og:image[^>]+>', html)[:3])
        print("   title", re.findall(r"<title>(.*?)</title>", html, re.S)[:1])
        print("   imgs", list(dict.fromkeys(re.findall(r'https://[^"\'\s]+?\.(?:jpg|jpeg|png|webp)', html)))[:8])
        print("   produkt-links", list(dict.fromkeys(re.findall(r'/produkt/[a-z0-9\-]+', html)))[:10])
        print("   sitemaps", re.findall(r"<loc>(.*?)</loc>", html)[:20])
        print("   nuxt", bool(re.search(r"__NUXT_DATA__", html)))
        i = html.find("squeebarista"); print("   ctx", html[max(0, i - 300):i + 600] if i >= 0 else "-")
    except Exception as e:
        print("\n==", u, "FEHLER", str(e)[:120])
    time.sleep(3)

try:
    st, ct, raw = get("https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1&q=ironmaxx&fetchsize=10")
    import json
    d = json.loads(raw)
    print("\n== Lidl ironmaxx numFound", d.get("numFound"))
    for it in d.get("items") or []:
        g = (it.get("gridbox") or {}).get("data") or {}
        print("   ", g.get("fullTitle") or g.get("title"), "|", g.get("image"))
except Exception as e:
    print("Lidl FEHLER", str(e)[:120])
