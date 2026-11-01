import re, urllib.request, urllib.robotparser, html
UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30)
    return r.status, r.read().decode("utf-8", "replace")
def txt(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
C = ["https://www.sparwelt.de/gratis/cashback", "https://www.mydealz.de/gruppe/geld-zurueck", "https://www.mydealz.de/rss/gruppe/geld-zurueck",
     "https://www.mydealz.de/gruppe/gratis-testen", "https://www.mydealz.de/rss/gruppe/gratis-testen", "https://www.mydealz.de/rss/hot"]
rob = {}
for u in C:
    host = "/".join(u.split("/")[:3])
    if host not in rob:
        rp = urllib.robotparser.RobotFileParser()
        try: rp.parse(get(host + "/robots.txt")[1].splitlines())
        except Exception as e: print("robots-Fehler", host, e)
        rob[host] = rp
    ok = rob[host].can_fetch(UA, u)
    print("\n####", u, "robots erlaubt:", ok)
    if not ok: continue
    try: st, p = get(u)
    except Exception as e: print("Fehler", e); continue
    print("Status", st, "Größe", len(p))
    items = re.findall(r"<item>(.*?)</item>", p, re.S)
    if items:
        for it in items[:25]:
            t = re.search(r"<title>(.*?)</title>", it, re.S); print("  *", txt(t.group(1).replace("<![CDATA[", "").replace("]]>", ""))[:120])
    else:
        heads = re.findall(r"<(h2|h3)[^>]*>(.*?)</\1>", p, re.S)
        for _, h in heads[:40]: print("  -", txt(h)[:120])
        cls = re.findall(r'class="([^"]*(?:card|teaser|deal|thread|item)[^"]*)"', p)
        from collections import Counter; print("  Klassen:", Counter(cls).most_common(8))
