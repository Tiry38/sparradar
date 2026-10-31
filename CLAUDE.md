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
  - `app.js` – gesamte Logik; Daten liegen pro Gerät in `localStorage` (Merkliste, Einkaufszettel, Coupons).
  - `data/offers.json` und `data/history.json` – werden vom Abruf geschrieben, nicht von Hand ändern.
- `fetcher/fetch_offers.py` – täglicher Angebots-Abruf, nur Python-Standardbibliothek.
- `.github/workflows/angebote.yml` – Abruf jeden Morgen ca. 5:15/6:15 Uhr und zusätzlich **Fr, Sa, So ca. 18:15/19:15 Uhr** (Kevins Wunsch: schon ab Freitag wissen, was nächste Woche im Angebot ist; Lidl/Netto erscheinen ab Freitag, Rewe/Edeka meist am Wochenende), committet nach `docs/data/`.
- **Schnell in die App:** Lidl, Aldi, prospektewoche laufen parallel zu kaufDA (Threads, je Server weiter `PAUSE`). `early_save()` lädt einen Zwischenstand (neue + bisherige Angebote) sofort hoch, sobald ein Markt ≥ 10 neue künftige Angebote hat (nur mit `SR_EARLY_PUSH=1` im Workflow). Sortiment-Seiten: Märkte mit neuem Prospekt zuerst. Der komplette Abruf dauert ca. 35–40 min, neue Märkte sind nach wenigen Minuten drin.
- `.github/workflows/prospekte.yml` + `fetcher/check_new.py` – **Prospekt-Wächter** (Kevins Wunsch: nächste Woche so früh wie möglich): Do–Mo jede Stunde, Di–Mi 3× nur die 5 kaufDA-Händlerseiten + Aldi-Angebotsseite ansehen; neuer Prospekt/Angebot mit Startdatum ab heute (auch Montags-Prospekte, die am selben Tag starten) (nicht in `docs/data/prospekte.json`) -> startet „Angebote abrufen“. Der Abruf merkt sich danach die sichtbaren Prospekte (`check_new.py --save`).
- `android/` – Android-App (WebView auf die Pages-URL), `desktop/src-tauri/` – Windows-App (Tauri 2, WebView2).
- `.github/workflows/apps.yml` – baut `SparRadar.apk` und `SparRadar-Setup.exe` und lädt sie in den Release `apps` hoch. Beide Apps zeigen immer die Online-Version, müssen also nur bei Änderungen in `android/` oder `desktop/` neu gebaut werden.
- **Windows-Updater:** `desktop/src-tauri/src/main.rs` prüft beim Start und alle 6 h `version.json` (Feld `desktop`), lädt bei neuerer Version `SparRadar-Setup.exe`, schließt sich, installiert still (`/S`) und startet neu. Version = `1.0.<Anzahl Commits in desktop/>`. Die Windows-Datei muss also nie von Hand ersetzt werden.
- **Web-App:** lädt sich selbst neu, wenn eine neue `app.js?v=` online ist, und holt neue Angebote nach (prüft alle 5 min und beim Zurückkehren ins Fenster die winzige `docs/data/stand.json`, lädt `offers.json` nur bei neuem Stand).
- **Update-Hinweis in der Web-App:** `docs/app-version.json` (schreibt der Release-Job von `apps.yml`, weil die Web-App den Release wegen CORS nicht lesen kann). Ist die Android-App (User-Agent `SparRadarAndroid/<code>`, alte Versionen erkennbar an `; wv)`) oder das Windows-Programm (`window.__SR_DESKTOP__`) älter, erscheint oben ein grüner Balken. Android-App bietet `SparRadarApp.checkUpdate()` (JS-Brücke) für „Nach App-Update suchen“ und prüft bei jedem Öffnen (höchstens alle 10 min).
- **Android-App-Hülle möglichst nie mehr ändern** (Kevins Wunsch): Jedes APK-Update verlangt in Android Bestätigungen und Warnungen. Alles Neue kommt über die Web-App. Der grüne Update-Balken für Android ist deshalb abgeschaltet; nur in den Einstellungen „Nach App-Update suchen“. Empfohlen für neue Nutzer: **Web-App über Chrome installieren** („App installieren“), ganz ohne APK und ohne Warnungen.
- **Android-Updater:** Die APK prüft beim Start `version.json` im Release `apps` und bietet „Aktualisieren“ an (PackageInstaller, Android fragt selbst nach). Die Versionsnummer = 100 + Anzahl Commits in `android/`. Signiert wird mit dem festen Schlüssel aus dem GitHub-Secret `ANDROID_KEYSTORE` (Base64 einer PKCS12-Datei, Alias `sparradar`). Den Schlüssel **nie** ins Repo legen und nicht austauschen, sonst schlagen alle Updates fehl und jeder muss neu installieren.

## Design und Bedienung (Stand 31.10.)
- **Logo:** weißes Preisschild mit Prozentzeichen auf Farbverlauf Anthrazit -> Grün (`docs/icon.svg`, `icon-maskable.svg`, `logo-tag.svg` für die Logo-Kacheln, PNGs, `og.png`, `og-einladung.png`, Android `ic_launcher_*.xml`). Bei Logo-Änderung alle diese Dateien neu erzeugen und die Windows-Version (Commit in `desktop/`) hochzählen.
- **Einladung:** `docs/einladung.html?von=<Name>` (Name nur im Link, nicht im Repo), installiert die Web-App über Chrome (keine APK, keine Warnung). Empfohlener Weg für alle Nutzer.
- **Detailansicht:** Artikel antippen -> großes Bild, weitere Bilder (`il`, `ims`), Beschreibung (`inf`), Kategorien (`cat`), Prospektseite (`pg`), Preisrechnung, Preisverlauf; Bild antippen = Vollbild.
- **Zurück-Taste:** History-Einträge (`navSync`) + Schutz-Eintrag; ganz am Ende Frage „wirklich schließen?“ (Android: `SparRadarApp.exitApp()`).
- **Android-Updater:** Download-Manager + Androids Installer (nicht PackageInstaller-Session, die startete nicht zuverlässig); automatischer Hinweis nur einmal pro Version.

## Märkte (Region Wörth am Rhein, ca. 20 km)
| Markt | Quelle |
|---|---|
| Lidl | lidl.de Such-API (`fetchsize` max. 60, mit `offset` blättern) + kaufDA Händlerseite + kaufDA-Sortiment-Seiten |
| Aldi Süd | aldi-sued.de/de/angebote.html + alle verlinkten **Tagesseiten** `/angebote/JJJJ-MM-TT` (dort steht die nächste Woche schon Tage vorher; robots.txt erlaubt es), Daten aus `__NUXT_DATA__` |
| Rewe | kaufDA `Woerth-am-Rhein/REWE/p-r101` |
| Netto Marken-Discount | kaufDA `Woerth-am-Rhein/Netto-Marken-Discount/p-r9` |
| Edeka **Jockgrim** | kaufDA `Jockgrim/EDEKA/p-r107` + Sortiment-Seiten `Edeka/Sortiment/…` + Stichwortseiten Karlsruhe, nur Prospekte mit gleichem Inhalt wie Jockgrim (`same_flyer`). edeka.de sperrt automatische Abrufe (403). |
| dm | kaufDA Händlerseite + Stichwortseiten Karlsruhe (keine Sortiment-Seiten; die dm-Produktsuche verbietet Abrufe per robots.txt) |

**Wichtig:** kaufDA-Händlerseiten zeigen nur 16 Angebote, `?page=` blättert nicht (kaufDA mischt nur die Reihenfolge). Die übrigen Angebote kommen über die öffentlichen **Sortiment-Seiten** `kaufda.de/<Händler>/Sortiment/<Begriff>` (Lidl, Netto, REWE; `fetch_sortiment()`), bei Rewe/Edeka gefiltert auf die Prospekte der lokalen Händlerseite. Die interne kaufDA-Schnittstelle wird bewusst nicht genutzt.
Zusätzlich fragt der Abruf kaufDA-Stichwortseiten für Karlsruhe ab (`/Karlsruhe/Angebote/<Begriff>`, Umlaute ausgeschrieben: Käse → Kaese). Für Wörth gibt es keine Stichwortseiten.

## Was in die App gehört
- **Alle Angebote** der Märkte (Wunsch von Kevin, auch für seine Mutter): Lebensmittel, Getränke, Katzenfutter, Drogerie & Pflege **und Non-Food** (Haushalt, Tierbedarf, Baby, Technik, Mode, Wohnen, Garten, Freizeit/Reisen, Sonstiges).
- Kategorien: `CATS` (Essen & Drogerie) und `NF_CATS` (Non-Food) + `classify()` in `fetcher/fetch_offers.py`. Die Kategorie-Schlüssel müssen mit `CATS` in `docs/app.js` übereinstimmen.
- **Kevins Vorgabe: Die Artikelbeschreibung darf die Kategorie NICHT beeinflussen** (Wein mit „passt zu Fisch“ landete bei Fleisch & Fisch). `classify(title, brand, food, cats)` nutzt nur Artikelname + Marke + die **zwei genauesten** Händler-Warengruppen (`cats[-2:]`; weiter oben sortiert kaufDA oft falsch, z. B. Jackfrucht unter „Tierfutter“). Reihenfolge: Langnese-Honig -> Alkohol (`ALCOHOL`) -> Regeln der eigenen Welt (Lebensmittel bzw. Non-Food, je nach Quelle) auf Name, dann auf Warengruppe (`CAT_HINTS`) -> Regeln der anderen Welt.
- Wortgrenzen beachten (Rinde≠Rind, Kleber≠Leber, Genuss≠Nuss, Altenburger≠Burger, Vollkorn≠Korn, Rotweinsauce≠Rotwein). Marken wie Lupilu (Kleidung UND Spielzeug) nicht als Kategorie-Hinweis nutzen.

## Prüfen vor jedem Push (immer, für Handy UND Windows-App)
- Jeder Tab, jede Kategorie, jeder Markt anklickbar; jede Seite und jedes Fenster bis ganz unten scrollbar; kein seitliches Scrollen.
- Mit Maus (PC/Windows): alle Chips sichtbar (Leisten brechen um). Mit Touch (Handy): Leisten seitlich wischbar.
- Test mit Playwright (Chromium = gleiche Engine wie WebView2 und Android-WebView) in 390×844 (Touch), 800×600 und 1920×1080.

## Bewusste Entscheidungen – nicht ändern ohne ausdrücklichen Wunsch
- **Keine Push-Benachrichtigungen.** Wurden gebaut und auf Wunsch wieder komplett entfernt. Der Nutzer schaut selbst in die App.
- **Keine Logins** für Lidl Plus, Rewe Bonus, Payback o. Ä. Es gibt keine offiziellen Schnittstellen. Die Passwörter lägen im öffentlichen Repo, und es drohen Kontosperren. Stattdessen gibt es **„Meine Coupons“** zum Selbst-Eintragen (Tab „Coupons“).
- **Geräte verbinden (Sync):** Merkliste, Einkaufszettel und Coupons synchronisieren über ein geheimes Gist im GitHub-Konto des Nutzers (`Sync` in `docs/app.js`, Datei `sparradar-sync.json`). Der GitHub-Schlüssel (nur Recht `gist`) wird pro Gerät im Tab „Coupons“ eingetragen und liegt nur im `localStorage`, nie im Repo. Konflikte werden zusammengeführt, nichts geht verloren.
- **Einstellungen** (Teilen per WhatsApp, Geräte verbinden, App-Downloads, Infos) öffnen sich über den Knopf **„Einstellungen“ ganz unten im Tab „Coupons“** (Kevins Wunsch, das komplett Versteckte hat verwirrt). Zusätzlich weiterhin: SparRadar-Logo lange drücken oder 5× antippen.
- **Einkaufszettel = Einkaufswagen** (Kevins Wunsch, 31.10.): antippen = im Wagen (rutscht nach unten, Vibration, Bildschirm bleibt an per Wake Lock). **Nur am Handy** (`TOUCH()` = hover:none + pointer:coarse) schließt der letzte Artikel den Einkauf ab (`finishTrip`): Zettel leer, Einkauf in `S.trips` (localStorage `sr_trips`, im Sync), kurzes Popup `#tripPop` mit „Zurückholen“ (`restoreTrip`) und „Bericht ansehen“ (Fenster `trip`). Am PC kein automatisches Abschließen. „Meine Einkäufe“ (`tripsHTML`): Monatsbericht (ausgegeben, gespart, Einkäufe, Ø, nach Markt, letzte 6 Monate) + alle Einkäufe. Dazu Mengen (`S.qty`, +/−, „3x Joghurt“), eigene Einträge mit Preis („Brot 1,99“, `parseExtra`), Budget (`S.budget`), „Wieder kaufen“ aus dem Verlauf (`freqHTML`, nimmt wenn möglich das aktuelle Angebot). Teilen per `wa.me`-Link.
- **Zusatz-Filter** (`S.flt`, localStorage `sr_flt`, `fltOk()`): Mindest-Ersparnis, Preis bis, Bio, vegan, nur echte Rabatte, ohne App & Karte, Tiefstpreis. Handy im Fenster „Kategorien & Filter“, PC über Knopf „Mehr Filter“.
- **Hinweis beim Öffnen:** neue Merklisten-Treffer seit dem letzten Öffnen (`seenHits`) – kein Push, nur in der App.
- **Vorschläge/Suche:** `BASE_WORDS` + `docs/data/names.json` (alle je gesehenen Artikelnamen, auch Lidl ohne Rabatt). Suche nur in Name, Marke, Markt; Kategoriename nur bei exakter Eingabe.
- **Bedienung:** „A+“-Knopf (3 Schriftstufen per CSS-`zoom`), am Handy Märkte/Kategorien/Sortierung im Fenster „Märkte & Filter“. Look: Farbverläufe in `docs/look.css`.
- **Sperren nicht umgehen:** rewe.de und netto-online.de blocken automatische Abrufe (403). Diese Sperren nicht umgehen, keine API-Schlüssel aus Websites auslesen (z. B. bei Marktguru). Nur öffentliche Seiten, die robots.txt erlaubt, mit ehrlichem User-Agent, höchstens einmal pro Tag (Ausnahme: zusätzliche Abend-Abrufe Fr/Sa/So) und mit Pausen (`PAUSE`).
- Das Repository ist öffentlich (nötig für kostenloses GitHub Pages). Keine Passwörter, Tokens oder persönlichen Daten hineinschreiben.

## Automatische Rabatt-Prüfung (Kevins Wunsch: hohe Rabatte genauestens prüfen, echte dürfen NICHT abgewertet werden)
- `checkDeal()` in `docs/app.js` läuft bei jedem Laden über alle Angebote, `fake_old()` in `fetcher/fetch_offers.py` schon beim Abruf.
- **Feld `ou`** (vom Abruf): 0 = „statt“ ist eigener früherer Preis des Markts (kaufDA `secondaryPriceIsUVP=false`, Lidl `discount.fromRecommendedPrice=false`) -> laut PAngV § 11 niedrigster Preis der letzten 30 Tage = **bestätigt**. 1 = UVP -> Karte zeigt „UVP“ statt „statt“.
- **Entfernt** (`rk.t="fix"`): „statt“ = Kilo-/Literpreis, = Preis der ganzen Packung, = Preis der größeren Packung bei gleichem Grundpreis.
- **Ab 40 % geprüft** (82 % der Lebensmittel-Rabatte liegen unter 40 %, nur ~1 % ab 60 %): Händlerangabe, Grundpreis, gleicher Artikel bei anderem Markt (pro kg/l oder gleiche Menge), Preisverlauf, „statt“ = genau 3×/4×… Preis.
- Zustände: `ok` ✅ bestätigt (oben, leichter Bonus beim Kracher) · `open` 🔍 noch nicht bestätigt, aber kein Gegenbeweis (**voller Rang, nicht grau**) · `warn` ⚠️ widerlegt (grau „?“, Sortierung mit realistischer Ersparnis) · `fix` 🔧 falscher statt-Preis entfernt.

## Preisvergleich, Zettel, Gespart, Scanner (31.10.)
- **Gleicher Artikel woanders:** `tokKey()` (Wörter aus Marke + Name, Reihenfolge egal) + `sameElsewhere()` rechnet Preise über den Grundpreis bzw. gleiche Packungsgröße auf dieselbe Menge um. Genutzt von Rabatt-Prüfung, Detail-„Preisvergleich“ (`compareHTML`) und Zettel-Tipp „Woanders günstiger“ (`swapTips`, Knopf „Tauschen“).
- **Gespart-Zähler:** Abhaken auf dem Zettel speichert `{id,n,s,v,d}` in `S.saved` (localStorage `sr_saved`, auch im Sync). Ent-Haken nimmt es wieder raus. Anzeige `savedHTML()` oben im Zettel.
- **Barcode-Scanner:** Knopf im Suchfeld (`#scanBtn`), Fenster `renderScan`/`Scan`. Erkennung per `BarcodeDetector` (Chrome Android), sonst ZXing aus `docs/vendor/zxing.min.js` (MIT, lädt nur bei Bedarf). EAN -> Name über Open Food Facts / Open Beauty Facts API (CORS, ohne Schlüssel). Die alte APK hat keine Kamera-Berechtigung -> Hinweis auf Chrome-Installation; Nummer kann auch eingetippt werden.
- **Vorteil ohne „statt“-Preis** (`perk()`, blaues Abzeichen + „💡 Dein Vorteil“ im Detail): 1) dieselbe Packung im selben Markt vorher teurer („bisher“, aus OFFERS bzw. Preisverlauf), 2) Großpackung günstiger pro kg/l als kleinere Packung im selben Markt (`coreKey` ohne XXL/Maxi), 3) günstigster aller Märkte. Zählt NICHT in `offPct`/Sortierung, ist kein Händler-„statt“-Preis.
- **Bilder in der Vorschlagsliste** (Suche + Merkliste): `sugImg()` nimmt das Bild aus den Angeboten, sonst `docs/data/names-img.json` (vom Angebots-Abruf, z. B. Lidl-Sortiment) oder `docs/data/catalog-img.json` (vom Artikelstamm-Abruf, gleiche Reihenfolge wie `catalog.json`, kurz `f:`/`b:` + Pfad bei Open Food/Beauty Facts). Beide Dateien lädt die App erst beim ersten Vorschlag.
- **Wochenend-Wechsel** (Kevins Wunsch): Samstag ab 22 Uhr und sonntags (`SHOP`/`WEEKEND` in `docs/app.js`) zeigt die ganze App die Angebote ab Montag; was Samstag endet, fällt raus (Zettel: Abschnitt „Abgelaufen“ mit Tausch-Knopf, `OLD`). Fehlende Märkte nennt `missingHTML()`.
- **Vorschau (`pv`)**: Edeka aus dem regionalen kaufDA-Prospekt (gleiche `publisherId`), Rewe aus prospektewoche.de (`fetch_prospektewoche`, nur die Seiten-JSONs `/images/prospekte/rewe/weekN/<n>.json` – deren schema.org-Liste trägt das falsche Datum). `drop_previews()` wirft die Vorschau eines Markts komplett raus, sobald ≥ 10 echte Angebote derselben Woche da sind (Kevin: „echte Daten sofort rein, Vorschau weg“). dm hat keine frühe Quelle.
- **Umschalter „Nächste Woche“** (früher „Demnächst“): `nextLabel()` zeigt „Ab Donnerstag“ o. ä., wenn kommende Angebote noch diese Woche starten.
- **dm (31.10. geprüft):** dm veröffentlicht nichts vorab (kein Prospekt bei kaufDA/meinprospekt/marktguru u. a.; die kaufDA-Prospekte „ab 02.11“ auf der dm-Seite sind Rossmann/Müller-Werbung). dm.de-Aktionen kommen über `content.services.dmtech.com` (nur Texte/Coupons für dm-Konto), Produkte+Preise nur über `product-search.services.dmtech.com` = robots.txt `Disallow: /` -> **nicht nutzen**. Lösung: Prospekt-Wächter auch Mo–Mi 3×/Tag, App-Hinweis in `missingHTML()`.
- **Aldi Süd** liefert kein UVP-Merkmal (nur `wasPriceDisplay`, `savingsDisplay`) -> dort nur Marktvergleich/Preisverlauf.

## App-Funktionen (Überblick)
Suche nur in Angeboten · Filter nach Markt und Kategorie · Sortierung nach Ersparnis/Grundpreis/Preis · „Jetzt gültig“/„Demnächst“ · **Kracher**-Button (bestes Angebot inkl. Kombi aus App-Preis, Rewe-Bonus, eigenen Coupons) · Preisverlauf mit Tiefstpreis- und Fake-Rabatt-Erkennung · Merkliste mit Wunsch-Grundpreis (Vorrats-Alarm) · Wochenplan · Einkaufszettel im Kassenbon-Stil (Summe pro Markt, Tausch-Tipps) · Gespart-Zähler · Barcode-Scanner · Preisvergleich · Meine Coupons · Spartipps · echte Produktfotos (Fallback: gezeichnete Illustrationen).

## Testen
- Abruf lokal: `python fetcher/fetch_offers.py` (dauert ca. 3–5 Minuten). Auf Kevins Windows-PC scheitert Aldi lokal an einem Zertifikatsfehler, auf GitHub funktioniert es.
- App lokal: `python -m http.server 8765 --directory docs`, dann http://localhost:8765 öffnen.
- Abruf auf GitHub von Hand starten: Actions → „Angebote abrufen“ → „Run workflow“ (oder `gh workflow run angebote.yml`).
