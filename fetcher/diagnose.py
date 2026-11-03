"""Diagnose: Was sieht ein GitHub-Server von prospektangebote.de und prospektewoche.de? (03.11.: lokal 812 Müller-Angebote,
im Abruf auf GitHub 0 ohne Fehlermeldung)"""
import re
import time
import urllib.request

import fetch_offers as f

for url in (f"{f.PA}/geschaefte/mueller/angebote", f"{f.PA}/geschaefte/mueller/angebote?page=2",
            f"{f.PA}/anzeigen/angebote/edeka-prospekt-3875720", f"{f.PW}/rewe", f"{f.PA}/robots.txt"):
    req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE,de;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            st, hd, h = r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        st, hd, h = e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        st, hd, h = repr(e), {}, ""
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    print(f"\n=== {url}\n  Status {st}, {len(h)} Zeichen, Titel: {(t.group(1).strip() if t else '-')[:100]}")
    print("  Server:", hd.get("Server"), "| cf-mitigated:", hd.get("cf-mitigated"), "| Angebote:", h.count('js-offer-link-item'))
    print("  Anfang:", re.sub(r"\s+", " ", h[:400]))
    time.sleep(3)
