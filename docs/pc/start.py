"""SparRadar-PC-Abruf: läuft unsichtbar ab der Windows-Anmeldung (Verknüpfung im Autostart).

- ca. 1 Minute nach dem Start, danach alle 10 Minuten prüfen: letzter erfolgreicher Abruf älter als 3 Stunden? -> abrufen
- lädt dafür jedes Mal die neueste abruf.py von GitHub (Verbesserungen kommen automatisch), sonst die gespeicherte
- Protokoll: %LOCALAPPDATA%\\SparRadar\\protokoll.txt
Aufruf mit --jetzt: sofort einmal abrufen (sichtbar, für den Test bei der Einrichtung).
"""
import datetime as dt
import importlib.util
import os
import socket
import sys
import time
import traceback
import urllib.request

BASE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "SparRadar")
SRC = "https://raw.githubusercontent.com/Tiry38/sparradar/main/docs/pc/abruf.py"
EVERY_H = 3
NOW = "--jetzt" in sys.argv
os.makedirs(BASE, exist_ok=True)
LOGF = os.path.join(BASE, "protokoll.txt")
LAST = os.path.join(BASE, "letzter-abruf.txt")


def log(*a):
    line = f"{dt.datetime.now():%d.%m. %H:%M:%S}  " + " ".join(str(x) for x in a)
    if NOW:
        try:
            print(line, flush=True)
        except Exception:
            pass
    try:
        if os.path.exists(LOGF) and os.path.getsize(LOGF) > 300_000:
            keep = open(LOGF, encoding="utf-8", errors="replace").read()[-100_000:]
            open(LOGF, "w", encoding="utf-8").write(keep)
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def due():
    try:
        return time.time() - float(open(LAST).read().strip()) > EVERY_H * 3600 - 300
    except Exception:
        return True


def run():
    path = os.path.join(BASE, "abruf.py")
    try:
        req = urllib.request.Request(SRC + f"?t={int(time.time())}", headers={"User-Agent": "SparRadar-PC"})
        code = urllib.request.urlopen(req, timeout=30).read()
        if b"def main(" in code:
            open(path, "wb").write(code)
    except Exception as e:
        log(f"Neueste Programmversion nicht geladen ({e}) – nehme die gespeicherte.")
        if not os.path.exists(path):
            return False  # noch kein Internet
    spec = importlib.util.spec_from_file_location("sr_abruf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main(BASE, log)


def once():
    log("--- Abruf startet ---")
    try:
        ok = run()
    except Exception:
        log("Fehler:", traceback.format_exc())
        ok = False
    if ok:
        open(LAST, "w").write(str(time.time()))
    log("--- fertig ---" if ok else "--- nicht geklappt, nächster Versuch in ca. 30 Minuten ---")
    return ok


if NOW:
    once()
    sys.exit(0)

try:  # nur einmal gleichzeitig laufen
    lock = socket.socket()
    lock.bind(("127.0.0.1", 47391))
except OSError:
    sys.exit(0)

time.sleep(60)  # Internet nach dem Start abwarten
fails = 0
while True:
    if due():
        fails = 0 if once() else fails + 1
    time.sleep(600 if fails == 0 else 1800 if fails < 4 else 3600)
