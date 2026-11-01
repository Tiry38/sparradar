"""Diagnose: Liefert das reparierte Nachtragen (gzip, Übersichtsseiten raus) jetzt Preise aus dem Internet-Archiv?"""
import collections
import time

import backfill_history as b

snaps = []
for kind, pat in b.PATTERNS:
    t = time.time()
    got = b.cdx(pat)
    print(f"{pat}: {len(got)} Schnappschüsse ({time.time() - t:.0f}s)")
    snaps += [[kind, r[0], r[1]] for r in got]
th = b.thin(snaps)
print("gesamt", len(snaps), "-> nötig", len(th))
c = collections.Counter(s[2].split("?")[0].rstrip("/").split("/")[-1] for s in th)
print("Seiten:", len(c), c.most_common(12))
for kind, ts, url in th[:: max(1, len(th) // 4)][:4]:
    t = time.time()
    h = b.get(f"https://web.archive.org/web/{ts}id_/{url}")
    offs = (b.offers_kd(h) if kind == "kd" else b.offers_aldi(h, url)) if h else []
    print(f"\n{ts} {url}: {time.time() - t:.1f}s len={len(h) if h else 0} Angebote={len(offs)}")
    for o in offs[:4]:
        print("  ", o["s"], o["n"][:35], o["p"], o.get("from"), b.day_of(o, ts), b.f.hist_tag(o))
