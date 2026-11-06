// SparRadar für Windows: zeigt die Web-App in einem eigenen Fenster (WebView2).
// Links zu anderen Seiten (Prospekte, Händler) öffnen im Standardbrowser.
// Das Programm aktualisiert sich selbst: neue Version installieren und neu starten.
// Symbol: wird beim Bauen aus docs/icon.svg erzeugt (Anthrazit/Grün mit Prozentzeichen).
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{WebviewUrl, WebviewWindowBuilder};

const APP_URL: &str = "https://tiry38.github.io/sparradar/";
const REL: &str = "https://github.com/Tiry38/sparradar/releases/download/apps/";
const CHECK_EVERY: std::time::Duration = std::time::Duration::from_secs(6 * 60 * 60);

// Links mit target="_blank" im selben Fenster öffnen, damit on_navigation sie abfangen kann
const SAME_WINDOW_LINKS: &str = r#"
document.addEventListener("click", e => {
  const a = e.target.closest && e.target.closest('a[target="_blank"]');
  if (a) { e.preventDefault(); location.href = a.href; }
}, true);
"#;

fn is_app(url: &tauri::Url) -> bool {
    url.host_str() == Some("tiry38.github.io") && url.path().starts_with("/sparradar")
}

/// Prüft unsichtbar per PowerShell, ob im Release eine neuere Version liegt. Wenn ja:
/// herunterladen, dieses Programm schließen, still installieren (/S) und wieder starten.
/// Ohne Internet oder bei Fehlern passiert einfach nichts.
#[cfg(windows)]
fn check_for_update(version: &str) {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    let Ok(exe) = std::env::current_exe() else { return };
    let script = format!(
        r#"$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$v=(Invoke-RestMethod -UseBasicParsing -Headers @{{'Cache-Control'='no-cache'}} '{rel}version.json').desktop
if(-not $v -or [version]$v -le [version]'{cur}'){{exit}}
$f=Join-Path $env:TEMP 'SparRadar-Update.exe'
Invoke-WebRequest -UseBasicParsing '{rel}SparRadar-Setup.exe' -OutFile $f
Stop-Process -Id {pid} -Force
Start-Sleep -Seconds 1
Start-Process -FilePath $f -ArgumentList '/S' -Wait
Start-Process -FilePath '{exe}'"#,
        rel = REL,
        cur = version,
        pid = std::process::id(),
        exe = exe.display().to_string().replace('\'', "''"),
    );
    let _ = std::process::Command::new("powershell")
        .args(["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", &script])
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();
}

#[cfg(not(windows))]
fn check_for_update(_version: &str) {}

/// Nach einem Update (neue Version beim Start) Windows einmal die Symbole neu laden lassen,
/// sonst zeigen Taskleiste und Desktop-Verknüpfung noch das alte Logo aus dem Symbol-Zwischenspeicher.
#[cfg(windows)]
fn refresh_icons_after_update(version: &str) {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    let Ok(base) = std::env::var("LOCALAPPDATA") else { return };
    let dir = std::path::Path::new(&base).join("SparRadar");
    let file = dir.join("symbol-version.txt");
    if std::fs::read_to_string(&file).map(|v| v.trim() == version).unwrap_or(false) {
        return;
    }
    let _ = std::process::Command::new("ie4uinit.exe")
        .arg("-show")
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();
    let _ = std::fs::create_dir_all(&dir);
    let _ = std::fs::write(&file, version);
}

#[cfg(not(windows))]
fn refresh_icons_after_update(_version: &str) {}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let version = app.package_info().version.to_string();
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(APP_URL.parse().unwrap()))
                .title("SparRadar")
                .inner_size(1200.0, 850.0)
                .maximized(true)
                .min_inner_size(380.0, 600.0)
                .initialization_script(SAME_WINDOW_LINKS)
                // Versionsnummer für die Anzeige in den Einstellungen der Web-App
                .initialization_script(&format!("window.__SR_DESKTOP__ = '{}';", version))
                .on_navigation(|url| {
                    if is_app(url) {
                        return true;
                    }
                    // nur normale Links an Windows weitergeben (Browser, Mail, SMS, Telefon) – nie file:, search-ms: o. Ä.,
                    // die lokale Programme starten könnten (Audit 06.11.)
                    if matches!(url.scheme(), "http" | "https" | "mailto" | "sms" | "tel") {
                        let _ = std::process::Command::new("rundll32")
                            .args(["url.dll,FileProtocolHandler", url.as_str()])
                            .spawn();
                    }
                    false
                })
                .build()?;
            refresh_icons_after_update(&version);
            // beim Start und dann alle 6 Stunden nach einer neuen Programmversion schauen
            std::thread::spawn(move || loop {
                check_for_update(&version);
                std::thread::sleep(CHECK_EVERY);
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("SparRadar konnte nicht starten");
}
