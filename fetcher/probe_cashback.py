"""Einmaliger Test: Welche öffentlichen Quellen für Geld-zurück-Aktionen erlauben das Lesen (robots.txt) und liefern brauchbare Daten?"""
import urllib.request, urllib.robotparser, re, sys, time
UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"}), timeout=25)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
SITES = {
 "https://www.mydealz.de": ["/rss/freebies", "/rss/gruppe/gratis-testen", "/rss/gruppe/cashback", "/rss/hot"],
 "https://www.mein-deal.com": ["/feed/", "/category/gratis/feed/", "/tag/geld-zurueck/feed/", "/tag/gratis-testen/feed/"],
 "https://www.dealdoktor.de": ["/feed/", "/tag/geld-zurueck/feed/", "/tag/gratis-testen/feed/"],
 "https://www.kaufda.de": ["/insights/aktuelle-cashback-aktionen-zum-sparen/"],
 "https://www.mystipendium.de": ["/geld/cashback-geld-zurueck-aktionen"],
 "https://schnaeppchenfuchs.com": ["/feed", "/kostenlos/cashback-geld-zurueck-aktionen"],
 "https://www.monsterdealz.de": ["/feed/"],
 "https://www.gratis-testen.org": ["/feed/"],
}
for base, paths in SITES.items():
    st, rb = get(base + "/robots.txt")
    rp = urllib.robotparser.RobotFileParser(); rp.parse(rb.splitlines() if st == 200 else [])
    print(f"\n===== {base} robots={st}")
    if st == 200:
        for l in rb.splitlines():
            if re.match(r"(?i)\s*(user-agent|disallow|allow|crawl-delay)", l): print("   R:", l.strip()[:120])
    for p in paths:
        u = base + p; ok = rp.can_fetch(UA, u) if st == 200 else True
        time.sleep(3)
        if not ok: print(f"-- {p}: robots VERBIETET"); continue
        s, body = get(u)
        items = re.findall(r"<item>.*?<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>.*?<link>(.*?)</link>.*?(?:<pubDate>(.*?)</pubDate>)?", body, re.S)
        print(f"-- {p}: HTTP {s}, {len(body)} Zeichen, {len(items)} RSS-Einträge")
        for t, l, d in items[:25]: print("   *", (d or "")[:16], "|", re.sub(r"\s+", " ", t)[:110], "|", l[:90])
        if not items and s == 200:
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)
            txt = re.sub(r"<[^>]+>", " ", txt); txt = re.sub(r"\s+", " ", txt)
            for m in re.finditer(r"([^.]{0,90}(?:Geld[- ]zur(?:ü|ue)ck|Cashback|gratis testen|Einsendeschluss)[^.]{0,120})", txt, re.I):
                print("   ~", m.group(1)[:200])
                if m.start() > 60000: break
