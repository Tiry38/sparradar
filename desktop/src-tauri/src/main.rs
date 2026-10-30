// SparRadar für Windows: zeigt die Web-App in einem eigenen Fenster (WebView2).
// Links zu anderen Seiten (Prospekte, Händler) öffnen im Standardbrowser.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{WebviewUrl, WebviewWindowBuilder};

const APP_URL: &str = "https://tiry38.github.io/sparradar/";

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

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(APP_URL.parse().unwrap()))
                .title("SparRadar")
                .inner_size(1200.0, 850.0)
                .min_inner_size(380.0, 600.0)
                .initialization_script(SAME_WINDOW_LINKS)
                .on_navigation(|url| {
                    if is_app(url) {
                        return true;
                    }
                    let _ = std::process::Command::new("rundll32")
                        .args(["url.dll,FileProtocolHandler", url.as_str()])
                        .spawn();
                    false
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("SparRadar konnte nicht starten");
}
