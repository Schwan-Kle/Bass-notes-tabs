# Bass-Tab Übungsplayer

Web-App zum Eintippen, Abspielen und Üben von Noten und Tabs: Bass, Gitarre, Klavier, Gesang und Schlagzeug, auch mehrere Spuren pro Stück. Mit Metronom, Schleife, Übe-Tempo, Notenlese-Training, MusicXML-Import und PDF-Druck. Läuft offline.

**Adresse:** https://schwan-kle.github.io/bass-notes-tabs/

## Installieren
- **Android/Tablet:** Adresse in Chrome öffnen → ⋮ → „App installieren“.
- **PC:** Adresse in Chrome oder Edge öffnen → Installieren-Symbol in der Adresszeile.
- **Updates** kommen automatisch beim nächsten Öffnen mit Internet (App ggf. ganz schließen und neu öffnen).

## Daten sichern
- Stücke werden automatisch im Gerät gespeichert, getrennt je Gerät und Browser.
- Websitedaten der App nicht löschen, sonst sind die Stücke weg.
- Sichern und Übertragen auf ein anderes Gerät: ☰ → „Alle Stücke sichern (Backup-Datei)“, auf dem anderen Gerät „Datei öffnen“.
- Fotos (📷 Vorlage) und Audio-Aufnahmen sind **nicht** im Backup enthalten.

## Dateien
`index.html` (die ganze App), `manifest.json`, `sw.js` (Offline-Speicher, Cache-Version bei jeder Änderung hochzählen), `icon-192.png`, `icon-512.png`, `.nojekyll`.

## Bibliothek
☰ → „📚 Bibliothek“: 16 mitgelieferte Stücke (Lieder, Klassik, Übungen) als MusicXML in `lib/`, Liste in `lib/index.json`, dazu Links zu Seiten mit freien MusicXML-Noten.
Erzeugt werden die Dateien mit `python3 tools/bibliothek.py` (Stücke dort eintragen, dann Cache-Version in `sw.js` hochzählen).

## Inhalte und Rechte
- Lieder und Klassik: nur gemeinfreie Melodien (Komponist über 70 Jahre tot bzw. traditionell), eigener Notensatz ohne Vorlage einer fremden Ausgabe, ohne Liedtexte.
- Übungen: eigene Muster.
- Notensatz der Bibliothek: CC0 (frei nutzbar). Quelle und Lizenz stehen je Stück in der App und in `lib/index.json`.
- Eigene Stücke und importierte Dateien bleiben auf dem Gerät.
