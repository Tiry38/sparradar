# SparRadar – Projektwissen für Claude

Private Angebots-App von Kevin (GitHub: Tiry38). Antworte auf **Deutsch**, einfach und Schritt für Schritt erklärt.
App: https://tiry38.github.io/sparradar/ · Repo: https://github.com/Tiry38/sparradar

## Arbeitsweise
- **Änderungen direkt auf `main` committen und pushen** (kein Pull Request), außer der Nutzer sagt etwas anderes. Nur `main` wird veröffentlicht.
- Vor dem Push `git pull --rebase`: Der Bot committet jeden Morgen neue Daten nach `docs/data/`.
- Nach Änderungen an `docs/app.js` oder `docs/app.css`/`style.css` die Versionsnummer in `docs/index.html` hochzählen (`app.js?v=…`), sonst hält der Browser-Cache die alte Version. Bei größeren Änderungen am Service Worker `CACHE` in `docs/sw.js` hochzählen.
- **Bei jeder neuen App-Version** (`app.js?v=` hochgezählt) in `CHANGES` in `docs/app.js` einen kurzen Eintrag in einfachem Deutsch ergänzen. Den zeigt das Fenster „SparRadar wurde aktualisiert“ nach dem Update.
- Commit-Nachrichten auf Deutsch.
- Fehler rückgängig machen: `git revert` des letzten Commits und auf `main` pushen.

## Aufbau
- `docs/` – die App (statisches HTML/CSS/JS, kein Build-Schritt), läuft auf GitHub Pages. PWA mit `manifest.webmanifest` und `sw.js`.
  - `app.js` – gesamte Logik; Daten liegen pro Gerät in `localStorage` (Merkliste, Einkaufszettel, eigene Angebote, Coupons).
  - `data/offers.json` und `data/history.json` – werden vom Abruf geschrieben, nicht von Hand ändern.
- `fetcher/fetch_offers.py` – täglicher Angebots-Abruf, nur Python-Standardbibliothek.
- `.github/workflows/angebote.yml` – Abruf jeden Morgen ca. 5:15/6:15 Uhr, committet nach `docs/data/`.
- `android/` – Android-App (WebView auf die Pages-URL), `desktop/src-tauri/` – Windows-App (Tauri 2, WebView2).
- `.github/workflows/apps.yml` – baut `SparRadar.apk` und `SparRadar-Setup.exe` und lädt sie in den Release `apps` hoch. Beide Apps zeigen immer die Online-Version, müssen also nur bei Änderungen in `android/` oder `desktop/` neu gebaut werden.
- **Windows-Updater:** `desktop/src-tauri/src/main.rs` prüft beim Start und alle 6 h `version.json` (Feld `desktop`), lädt bei neuerer Version `SparRadar-Setup.exe`, schließt sich, installiert still (`/S`) und startet neu. Version = `1.0.<Anzahl Commits in desktop/>`. Die Windows-Datei muss also nie von Hand ersetzt werden.
- **Web-App:** lädt sich selbst neu, wenn eine neue `app.js?v=` online ist, und holt neue Angebote nach (alle 30 min und beim Zurückkehren ins Fenster).
- **Update-Hinweis in der Web-App:** `docs/app-version.json` (schreibt der Release-Job von `apps.yml`, weil die Web-App den Release wegen CORS nicht lesen kann). Ist die Android-App (User-Agent `SparRadarAndroid/<code>`, alte Versionen erkennbar an `; wv)`) oder das Windows-Programm (`window.__SR_DESKTOP__`) älter, erscheint oben ein grüner Balken. Android-App bietet `SparRadarApp.checkUpdate()` (JS-Brücke) für „Nach App-Update suchen“ und prüft bei jedem Öffnen (höchstens alle 10 min).
- **Android-App-Hülle möglichst nie mehr ändern** (Kevins Wunsch): Jedes APK-Update verlangt in Android Bestätigungen und Warnungen. Alles Neue kommt über die Web-App. Der grüne Update-Balken für Android ist deshalb abgeschaltet; nur in den Einstellungen „Nach App-Update suchen“. Empfohlen für neue Nutzer: **Web-App über Chrome installieren** („App installieren“), ganz ohne APK und ohne Warnungen.
- **Android-Updater:** Die APK prüft beim Start `version.json` im Release `apps` und bietet „Aktualisieren“ an (PackageInstaller, Android fragt selbst nach). Die Versionsnummer = 100 + Anzahl Commits in `android/`. Signiert wird mit dem festen Schlüssel aus dem GitHub-Secret `ANDROID_KEYSTORE` (Base64 einer PKCS12-Datei, Alias `sparradar`). Den Schlüssel **nie** ins Repo legen und nicht austauschen, sonst schlagen alle Updates fehl und jeder muss neu installieren.

## Märkte (Region Wörth am Rhein, ca. 20 km)
| Markt | Quelle |
|---|---|
| Lidl | lidl.de Such-API, Kategorie „Essen & Trinken“ (`category.id=10068374`), nur `store=1` (Filiale) mit Rabatt; plus kaufDA |
| Aldi Süd | aldi-sued.de/de/angebote.html, Daten aus `__NUXT_DATA__` |
| Rewe | kaufDA `Woerth-am-Rhein/REWE/p-r101` |
| Netto Marken-Discount | kaufDA `Woerth-am-Rhein/Netto-Marken-Discount/p-r9` |
| Edeka **Jockgrim** | kaufDA `Jockgrim/EDEKA/p-r107` (ausdrücklich der Markt in Jockgrim) |
| dm | kaufDA `Woerth-am-Rhein/dm-drogerie-markt/p-r104` |
| Scheck-In (Wörth, Maximiliancenter) | nicht automatisch – Nutzer trägt Angebote in der App selbst ein |
| Serpa Markt (Wörth) | nicht automatisch – Nutzer trägt Angebote in der App selbst ein |

Zusätzlich fragt der Abruf kaufDA-Stichwortseiten für Karlsruhe ab (`/Karlsruhe/Angebote/<Begriff>`, Umlaute ausgeschrieben: Käse → Kaese). Für Wörth gibt es keine Stichwortseiten.

## Was in die App gehört
- **Alle Angebote** der Märkte (Wunsch von Kevin, auch für seine Mutter): Lebensmittel, Getränke, Katzenfutter, Drogerie & Pflege **und Non-Food** (Haushalt, Tierbedarf, Baby, Technik, Mode, Wohnen, Garten, Freizeit/Reisen, Sonstiges).
- Kategorien: `CATS` (Essen & Drogerie) und `NF_CATS` (Non-Food) + `classify()` in `fetcher/fetch_offers.py`. Erst nach Artikelname, dann nach ganzem Text. Die Kategorie-Schlüssel müssen mit `CATS` in `docs/app.js` übereinstimmen.

## Prüfen vor jedem Push (immer, für Handy UND Windows-App)
- Jeder Tab, jede Kategorie, jeder Markt anklickbar; jede Seite und jedes Fenster bis ganz unten scrollbar; kein seitliches Scrollen.
- Mit Maus (PC/Windows): alle Chips sichtbar (Leisten brechen um). Mit Touch (Handy): Leisten seitlich wischbar.
- Test mit Playwright (Chromium = gleiche Engine wie WebView2 und Android-WebView) in 390×844 (Touch), 800×600 und 1920×1080.

## Bewusste Entscheidungen – nicht ändern ohne ausdrücklichen Wunsch
- **Keine Push-Benachrichtigungen.** Wurden gebaut und auf Wunsch wieder komplett entfernt. Der Nutzer schaut selbst in die App.
- **Keine Logins** für Lidl Plus, Rewe Bonus, Payback o. Ä. Es gibt keine offiziellen Schnittstellen. Die Passwörter lägen im öffentlichen Repo, und es drohen Kontosperren. Stattdessen gibt es **„Meine Coupons“** zum Selbst-Eintragen (Tab „Coupons“).
- **Geräte verbinden (Sync):** Merkliste, Einkaufszettel, Coupons und eigene Angebote synchronisieren über ein geheimes Gist im GitHub-Konto des Nutzers (`Sync` in `docs/app.js`, Datei `sparradar-sync.json`). Der GitHub-Schlüssel (nur Recht `gist`) wird pro Gerät im Tab „Coupons“ eingetragen und liegt nur im `localStorage`, nie im Repo. Konflikte werden zusammengeführt, nichts geht verloren.
- **Einstellungen** (Teilen per WhatsApp, Geräte verbinden, App-Downloads, Infos) öffnen sich nur versteckt: **SparRadar-Logo oben links ca. 1 Sekunde gedrückt halten** (oder 5× schnell antippen). Kein sichtbarer Knopf (Kevins Mutter soll nicht hineinkommen), **nicht** im Coupons-Tab.
- **Einkaufszettel:** abhaken (antippen), eigene Einträge (`S.extra`), „Erledigte entfernen“; Teilen per `wa.me`-Link.
- **Hinweis beim Öffnen:** neue Merklisten-Treffer seit dem letzten Öffnen (`seenHits`) – kein Push, nur in der App.
- **Vorschläge/Suche:** `BASE_WORDS` + `docs/data/names.json` (alle je gesehenen Artikelnamen, auch Lidl ohne Rabatt). Suche nur in Name, Marke, Markt; Kategoriename nur bei exakter Eingabe.
- **Bedienung:** „A+“-Knopf (3 Schriftstufen per CSS-`zoom`), am Handy Märkte/Kategorien/Sortierung im Fenster „Märkte & Filter“. Look: Farbverläufe in `docs/look.css`.
- **Sperren nicht umgehen:** rewe.de und netto-online.de blocken automatische Abrufe (403). Diese Sperren nicht umgehen, keine API-Schlüssel aus Websites auslesen (z. B. bei Marktguru). Nur öffentliche Seiten, die robots.txt erlaubt, mit ehrlichem User-Agent, höchstens einmal pro Tag und mit Pausen (`PAUSE`).
- Das Repository ist öffentlich (nötig für kostenloses GitHub Pages). Keine Passwörter, Tokens oder persönlichen Daten hineinschreiben.

## App-Funktionen (Überblick)
Suche nur in Angeboten · Filter nach Markt und Kategorie · Sortierung nach Ersparnis/Grundpreis/Preis · „Jetzt gültig“/„Demnächst“ · **Kracher**-Button (bestes Angebot inkl. Kombi aus App-Preis, Rewe-Bonus, eigenen Coupons) · Preisverlauf mit Tiefstpreis- und Fake-Rabatt-Erkennung · Merkliste mit Wunsch-Grundpreis (Vorrats-Alarm) · Wochenplan · Einkaufszettel im Kassenbon-Stil · eigene Angebote eintragen · Meine Coupons · Spartipps · echte Produktfotos (Fallback: gezeichnete Illustrationen).

## Testen
- Abruf lokal: `python fetcher/fetch_offers.py` (dauert ca. 3–5 Minuten). Auf Kevins Windows-PC scheitert Aldi lokal an einem Zertifikatsfehler, auf GitHub funktioniert es.
- App lokal: `python -m http.server 8765 --directory docs`, dann http://localhost:8765 öffnen.
- Abruf auf GitHub von Hand starten: Actions → „Angebote abrufen“ → „Run workflow“ (oder `gh workflow run angebote.yml`).
