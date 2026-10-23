# Prüfplan und Erkenntnisse · Version 10

## Plan mit überprüfbarem Ergebnis

| Schritt | Vorgehen | Ergebnis / Artefakt |
|---|---|---|
| 1. Quellen sichern | Version 09 als ausführbare Basis von alter Markdown-/Chatvorlage trennen; Hash erfassen | `base09.cfg.txt`, `inspiration_original.md`, Hashes in `alias_graph.json` |
| 2. Ist-Zustand ermitteln | Gesamte Ladefolge ausführen, finale Binds und Aliasziele erfassen | `audit.json`, `alias_graph.json` |
| 3. Rückwege definieren | Waffen-/Hand-/Inspect-/Sens-/Crosshair-Vertrag pro Release festlegen | Gemeinsamer `best_weapon`, eigene Haltezustände |
| 4. Bestehenden Baum ändern | Nur betroffene Definitionen ersetzen; jede Altzeile behalten | `changes.json`, kommentierte Teil-CFGs, Diff |
| 5. Kombinationen prüfen | Paarverflechtungen, Inventare, vier Granatentasten, gezielte drei und mehr Tasten, Modusschalter | `input_tests.json`, `verification.json`, `combinations.json` |
| 6. Unabhängiger Ablaufcheck | Tatsächliche fertige Aliase prüfen; bestätigte Lücken als Regressionen ergänzen | ALT-Reaktivierung, Enter-Angriff, Kauf-Abbruch ergänzt |
| 7. Sichtbar machen | Architektur und interaktive Vorschau aus finalen Aliasdefinitionen erzeugen | `LEETED_Ablauf_und_Test.html`, Aliasgraph |
| 8. Reproduzieren | Frisches ZIP entpacken, offline neu bauen, CFG-Bytes vergleichen | `rebuild.py`; Ergebnis vor Auslieferung geprüft |
| 9. Client-Prüfung | Neu laden und dokumentierte Tastensequenzen im Spiel ausführen | **Noch offen: kein CS2-Client verfügbar** |

Archify war weder als integriertes Werkzeug noch als lokales Programm verfügbar. Deshalb wird der Architekturgraph direkt aus dem CFG-Parser erzeugt. Dies ist kein vorgetäuschter Archify-Lauf. `app_block`/Visualize war ebenfalls nicht verfügbar; die HTML-Übersicht ist der bereitgestellte Ersatz.

## Konkrete Erkenntnisse und Umsetzung

| Befund | Belegbarer Ablauf | Reparatur |
|---|---|---|
| Granaten-Release konnte Inspect sofort neu starten | `*_gren_up → select_held → equip_* → look1` | Jedes Granaten-Release führt zu `best_weapon` |
| Rechte Hand fehlte im allgemeinen Waffenrückweg | Version 09: `best_weapon` enthielt Slots und look0, aber keinen Handwechsel | Rechte Hand nach der Waffenwahl explizit setzen |
| SPACE-Release konnte eine weitere gehaltene Granate auswählen | Version 09: `-jumpp → select_held` | Eindeutiger Waffenrückweg, dann proview und Sens |
| ALT-Release konnte einen schon abgeschlossenen Rückweg rückgängig machen | Z halten → SPACE halten → ALT halten → SPACE loslassen → ALT loslassen; `-_r → select_held` | `-_r` beendet Funk und geht zur besten Waffe; kein erneutes Inspect |
| Normalfarbe und automatischer Farbeffekt waren nicht sauber getrennt | `movecross` rief `c_hell` auf und überschreibt damit die gespeicherte Farbe | `selected_color` für bewusste Farbe; Farbschutz und Altfarbe getrennt |
| Profilrückstellung darf den Auswahlzyklus nicht aufrufen | Frühere gemeldete Weiterwahl nach Schuss; genaue ursprüngliche Client-Ursache nicht belegt | Direkte `restore_*`-Aliase aus 09 erhalten; K-Latch erhalten |
| Moduswechsel konnte eine andere Release-Aktion auslösen | SPACE + Bombentaste, danach SPACE zuerst loslassen | `drop_release` wird beim Tastendruck gespeichert |
| Verzögerter Drop könnte zwischenzeitlich gewählte Waffe treffen | Bombentaste halten → SPACE/Quick-Waffenwechsel → Bombentaste loslassen | Vor Drop Messer/Bombe erneut wählen; Inventar-/Servergrenze dokumentieren |
| Enter hatte keine Schussanzeige | Finaler Bind `enter +ATTACK` umgeht `+atx` | Gemeinsame Angriffseigentümer für Maus1 und Enter; letzte Freigabe beendet Angriff |
| Kaufhelfer stoppt Angriff, aber nicht Anzeige | Maus1 halten → Kaufbindung mit `rdygo` → `-attack`, Schussrenderer bleibt aktiv | `fire_cancel` setzt Eingabe, Anzeige und beide Halteflags zurück |
| Quick-Release führte unnötige Granaten-/Inspect-Zwischenschritte aus | `-quick → he;smoke;molo;...` | Direkter gemeinsamer Waffenrückweg |
| Alte Vorlage ist kein sauberer aktueller CFG-Quelltext | Sechs Zeilen, fast gesamter Code in einer Zeile; `crosscoss`, verschachtelte Quotes, alte Commands | Nur als historische Referenz sichern; keine automatische Ausführung/Migration darüber |
| Simulatormodell muss Abfragen korrekt behandeln | `alias name` darf keine leere Neudefinition sein | Abfragen erhalten Zustand; `alias name ""` leert ausdrücklich |
| Aliasgraph darf Zuweisungen nicht als Aufrufe darstellen | `alias check_z equip_z` führt equip_z nicht sofort aus | Graph trennt `call` und `assignment` |

## Zustandsregeln

- Jede Granaten-, SPACE- oder Quick-Freigabe: beste verfügbare Waffe, rechte Hand, Inspect-Eingabe aus.
- Neue Tastendrücke dürfen danach wieder eine andere Waffe auswählen; die Rückstellung sperrt keine späteren Eingaben.
- SPACE-Release: Rad ungebunden, proview aktiv, sprint1, Caps-Toggle zurückgesetzt. Sens bleibt 1.87 nur bei einem weiteren gehaltenen Quick-Alias.
- Schussanzeige ist vom normalen Form-/Farbspeicher unabhängig. K/J während des Schießens ändern die spätere normale Auswahl.
- Maus1/Enter teilen sich den Angriff. Freigabe einer Taste beendet nicht die noch gehaltene andere. Ein erzwungener Kauf-Abbruch beendet beide Besitzer bis zum nächsten Tastendruck.
- Inspect aus verhindert neue automatische Inspect-Eingaben; look0 bleibt eine gültige Eingabefreigabe.
- Physische Bind-Belegung bleibt erhalten; Enter erhält einen Funktionswrapper für dieselbe Angriffsfunktion. Keine neuen belegten Tasten für Optionen.

## Grenzen der Aussage

Die statischen Prüfungen sind endlich und decken dokumentierte Kombinationen ab, nicht jede mögliche beliebig lange Eingabefolge. Sie bestätigen Aliaslogik, Werte, gespeicherte Altzeilen, Befehlslängen und Ladefolge. Sie bestätigen keine Client-Animation, native Key-ID-Behandlung, Match-/Workshop-Berechtigung oder Serverfilter.

Die neuen Modusfunktionen werden bewusst über kurze Aliasdefinitionen aufgebaut. Maximaler vollständiger aktiver Befehl: 258 UTF-8-Bytes; konservatives Budget: 384. Jeder Abschnitt bleibt ungefähr 18 KB. Dies sind Build-Grenzen, keine behaupteten offiziellen Engine-Limits.

Die Begriffe sprint0/sprint1 werden gemäß bestehender CFG verwendet. Es wird nicht allein aus den Aliasnamen geschlossen, welcher Modus im Client tatsächlich schneller ist. Die Live-Prüfung dieses gewünschten Toggles bleibt erforderlich.
