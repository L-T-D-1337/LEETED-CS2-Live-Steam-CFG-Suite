"""Minimal transformations of the delivered v09 tree; deterministic, offline build."""
from pathlib import Path
import sys,json,hashlib
from audit_cfg import commands,tokens
here=Path(__file__).resolve().parent
src=here/'base09.cfg.txt';out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
opt=json.loads((here/'options.json').read_text());raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()==opt['source_sha256'],'Unexpected source'
def alias(n,v):return f'alias "{n}" "{v}"'
def annotated(note,cmd):return '// NEU v10: '+note+'\n'+cmd+'\n'
helpers=[];replacements={};reasons={}
def add(n,body,note):helpers.append(annotated(note,alias(n,body)))
def replace(n,body,note):replacements[n]=body;reasons[n]=note

# Runtime settings; no new physical key bindings required.
add('inspect_on','alias look1 +lookatweapon;alias inspect_toggle inspect_off;echo INSPECT_ON','Inspect bei folgenden Tastendruecken erlauben; startet selbst keine Animation.')
add('inspect_off','alias look1 noop;look0;alias inspect_toggle inspect_on;echo INSPECT_OFF','Automatisches Inspect deaktivieren und vorhandene Eingabe freigeben.')
add('inspect_toggle','inspect_on','Inspect-Schalter; Startwert folgt am Ende.')
add('color_lock_on','alias automatic_white noop;alias color_restore selected_color;alias color_lock_toggle color_lock_off;refresh_crosshair;echo COLOR_LOCK_ON','Automatische Farbwechsel sperren; J bleibt zur bewussten Farbwahl frei.')
add('color_lock_off','alias automatic_white legacy_white;alias color_restore croco;alias color_lock_toggle color_lock_on;refresh_crosshair;echo COLOR_LOCK_OFF','Alten automatischen Weiss-Effekt von movecross erlauben; bewusste J-Auswahl separat behalten.')
add('selected_color','rgb_red','Bewusst gewaehlte J-Farbe getrennt von automatischer Altfarbe speichern.')
add('color_restore','selected_color','Farbrueckstellung nach aktivem Farbschutz.')
add('legacy_white','alias croco rgb_white','Nur bei deaktiviertem Farbschutz automatische Altfarbe Weiss setzen.')
for name,color in [('c_hell','white'),('c_matrix','matrix'),('c_npink','pink'),('c_nweed','weed'),('c_nred','red'),('c_ntkys','cyan')]:
 replace(name,f'alias selected_color rgb_{color};alias croco rgb_{color};refresh_crosshair','Bewusste Farbwahl speichern; Schussprofil waehrend Schiessen nicht ueberschreiben.')
for name in ['dot','cross','hole','t','trill']:
 replace('restore_'+name,'shape_'+name+';color_restore;cl_crosshair_recoil 0;ch1','Gespeichertes Profil und Farbe entsprechend Farbschutz laden; keine Auswahl weiterschalten.')
add('color_lock_toggle','color_lock_off','Farbschutz umschalten.')
add('automatic_white','noop','Farbschutz startet aktiv.')
add('shot_on','alias shot_render shot_selected;alias shot_toggle shot_off;refresh_crosshair;echo SHOT_ON','Schussprofil beim Halten von Maus1 einschalten.')
add('shot_off','alias shot_render mycross;alias shot_toggle shot_on;refresh_crosshair;echo SHOT_OFF','Gewaehltes normales Crosshair auch beim Schiessen anzeigen, Recoil aus.')
add('shot_toggle','shot_off','Schussanzeige an/aus.')
add('shot_circle','alias shot_selected shape_fire;alias shot_style_toggle shot_t;refresh_crosshair;echo SHOT_CIRCLE_WHITE','Weissen dynamischen Kreis auswaehlen.')
add('shot_t','alias shot_selected shape_fire_t;alias shot_style_toggle shot_circle;refresh_crosshair;echo SHOT_T_RED','Grosses rotes T mit Recoil auswaehlen.')
add('shot_style_toggle','shot_t','Kreis und T umschalten, normale Auswahl bleibt erhalten.')
add('shot_selected','shape_fire','Standard-Schussprofil Kreis.')
add('shot_render','shot_selected','Schussanzeige ist standardmaessig aktiv.')

def profile(values):
 pairs=[('cl_crosshairstyle','style'),('cl_crosshair_length','length'),('cl_crosshair_thickness','thickness'),('cl_crosshair_gap','gap'),('cl_crosshaircolor_a','alpha'),('cl_crosshair_drawoutline','outline'),('cl_crosshairdot','dot'),('cl_crosshair_t','t'),('cl_crosshair_recoil','recoil'),('cl_crosshaircolor_r','red'),('cl_crosshaircolor_g','green'),('cl_crosshaircolor_b','blue'),('cl_crosshair_dynamic_spread_limit','dynamic_spread_limit'),('cl_crosshair_dynamic_splitdist','dynamic_splitdist'),('cl_crosshair_dynamic_splitalpha_innermod','dynamic_splitalpha_innermod'),('cl_crosshair_dynamic_splitalpha_outermod','dynamic_splitalpha_outermod'),('cl_crosshair_dynamic_maxdist_splitratio','dynamic_maxdist_splitratio'),('cl_crosshair_screen_height','screen_height')]
 return ['crosshair 1']+[f'{cmd} {values[key]}' for cmd,key in pairs]
for kind,base in [('fire','shot_circle_part'),('fire_t','shot_t_part')]:
 chunks=[];chunk=[]
 for cmd in profile(opt['profiles'][kind]):
  if chunk and len(';'.join(chunk+[cmd]).encode())>180:chunks.append(chunk);chunk=[]
  chunk.append(cmd)
 if chunk:chunks.append(chunk)
 names=[]
 for i,chunk in enumerate(chunks,1):
  n=f'{base}_{i}';names.append(n);add(n,';'.join(chunk),'Kurzer Schussprofil-Teil; Werte konfigurierbar in options.json.')
 if kind=='fire':replace('shape_fire',';'.join(names),'Weisser Kreis, duennere Linie, hoehere dynamische Spreizgrenze.')
 else:add('shape_fire_t',';'.join(names),'Grosses rotes T wie frueher angenaehert; neue maximale Laenge 255 statt alter 1000.')

replace('look1','noop','Zum Testen startet Inspect AUS; inspect_on aktiviert +lookatweapon.')
replace('look0','-lookatweapon','Gueltingen Inspect-Release immer ausfuehren, auch wenn Inspect abgeschaltet ist.')
replace('best_weapon','look0;slot3;slot2;slot1;hand>;refresh_crosshair','Eindeutig Hauptwaffe, ersatzweise Pistole/Messer; rechte Hand, Inspect aus, passende Anzeige.')
for key,target in [('z','check_x'),('x','check_c'),('c','check_f'),('f','check_space')]:
 replace(key+'_gren_up',f'alias check_{key} {target};alias {key}_up noop;best_weapon','Jedes Granaten-Loslassen endet bei der besten Waffe; keine andere Granate/Inspect neu starten.')
replace('-jumpp','mnormal;sensx;-buy;space_release_state;best_weapon;proview;sens_refresh','SPACE: Rad-/BUY-Rueckweg, Hauptwaffe rechts, Inspect aus, proview und Sens-Rueckstellung.')
replace('+jumpp','mjump;sens0;+buy;space_press_state;select_held;sens_refresh','SPACE: vorhandene Rauch-Ersatzfolge, Radmodus und Sens 1.87; Bombentaste wird Modusschalter.')
add('space_press_state','alias sens_check_space sens_held;alias check_space equip_z;alias drop_dispatch space_sneak_press','SPACE-Zustand merken; keine Bombe beim folgenden CapsLock-Druck abwerfen.')
add('space_release_state','alias sens_check_space sens_check_quick;alias check_space best_weapon;alias drop_dispatch bomb_down;space_sneak_reset','SPACE-Ende: Standardfunktion Bombendrop und sprint1 wiederherstellen.')
add('space_sneak_on','sprint0;alias space_sneak_toggle space_sneak_off;alias space_move_hold sprint0;echo SPACE_SPRINT0','Angeforderter SPACE-Modus ruft vorhandenes sprint0 auf.')
add('space_sneak_off','sprint1;alias space_sneak_toggle space_sneak_on;alias space_move_hold sprint1;echo SPACE_SPRINT1','Zweiter Druck stellt vorhandenes sprint1 wieder her.')
add('space_sneak_toggle','space_sneak_on','Naechster Druck waehrend SPACE aktiviert sprint0.')
add('space_sneak_reset','sprint1;alias space_sneak_toggle space_sneak_on;alias space_move_hold noop','SPACE-Release beendet den Toggle immer; SHIFT bleibt danach normal nutzbar.')
add('space_move_hold','noop','Temporaren SPACE-Modus nach SHIFT-Release erneut anwenden.')
add('space_sneak_press','alias drop_release noop;space_sneak_toggle','Tastendruck als SPACE-Modusschalter merken: Release darf keine Bombe droppen.')
add('drop_dispatch','bomb_down','Bombentaste im Normalmodus.')
add('drop_release','noop','Release-Aktion wird beim Tastendruck gespeichert.')
add('drop_press','drop_once','Latch verhindert mehrfaches Umschalten beim Halten.')
add('drop_once','alias drop_press noop;drop_dispatch','Genau eine Bomben-/Toggle-Aktion pro Tastendruck.')
add('bomb_down','alias drop_release bomb_up;cl_autohelp 1;slot3;slot5;look1','Normale Bombenauswahl; passende Release-Aktion auch bei spaeterem SPACE merken.')
add('bomb_up','cl_autohelp 0;look0;slot3;slot5;drop;best_weapon','Vor Drop Bombe erneut waehlen: anderer Waffenwechsel waehrend Halten darf nicht Hauptwaffe droppen.')
replace('+dropbomb','drop_press','Stabile Taste: normal Bombendrop, bei SPACE sprint0/sprint1-Toggle.')
replace('-dropbomb','drop_release;alias drop_release noop;alias drop_press drop_once','Gespeicherten Release ausfuehren; Moduswechsel erzeugt keinen falschen Drop.')
replace('+speed','<vol;+sprint;space_move_hold','SHIFT erhalten; aktiver SPACE-Toggle hat Vorrang.')
replace('-speed','vol>;-sprint;space_move_hold','SHIFT-Release darf aktiven SPACE-Toggle nicht aufheben.')
replace('movecross','automatic_white;refresh_crosshair','Bewegungsanzeige wahrt Auswahl; automatisches Weiss nur bei color_lock_off, Schussprofil hat Vorrang.')
replace('croattx','shot_render','Schussanzeige durch optionalen Profil-Dispatcher.')
replace('crosshair_fire','shot_render','Schussprofil an/aus und Kreis/T getrennt von normaler Auswahl.')
replace('-_r','close_radio;grnz;best_weapon','ALT-Release darf keine nach SPACE-/Granaten-Release abgelegte Granate mit Inspect reaktivieren.')
# Both bound attack keys share attack ownership. A forced buy cancellation
# clears both owners so a later unrelated release cannot resurrect firing.
add('fire_check_mouse','fire_check_enter','Maus1 startet nicht gehalten.')
add('fire_check_enter','fire_end','Enter startet nicht gehalten.')
add('fire_refresh','fire_check_mouse','Gemeinsamen Angriffszustand aus beiden Tasten ableiten.')
add('fire_hold','+attack;alias refresh_crosshair crosshair_fire;atx1','Mindestens eine Angriffstaste gehalten: Angriff und Schussanzeige.')
add('fire_end','-attack;alias refresh_crosshair crosshair_idle;mycross;-h_color;sens1;sens_refresh','Letzte Angriffstaste losgelassen: Angriff aus, gespeichertes Profil und Sens zurueck.')
add('fire_cancel','alias fire_check_mouse fire_check_enter;alias fire_check_enter fire_end;fire_end','Kauf-/Abbruchpfad: Angriff samt Anzeige und beiden Haltetasten-Flags beenden.')
replace('+atx','alias fire_check_mouse fire_hold;fire_refresh;shot_trace_down','Maus1 als gehalten merken; gemeinsame Angriffsrueckstellung.')
replace('-atx','alias fire_check_mouse fire_check_enter;fire_refresh;shot_trace_up','Maus1 freigeben; Enter darf weiter schiessen, sonst mycross.')
add('+enter_fire','alias fire_check_enter fire_hold;fire_refresh;shot_trace_down','Enter nutzt dieselbe optionale Schussanzeige wie Maus1.')
add('-enter_fire','alias fire_check_enter fire_end;fire_refresh;shot_trace_up','Enter freigeben; Maus1 darf weiter schiessen.')
replace('rdygo','fire_cancel;he;molo;smoke;slot3;knife;look0','Kaufhelfer beendet Angriff UND Schussanzeige; bestehende Waffenfolge bleibt.')

# Quick-switch variants use the same definitive release as grenade keys.
replace('-qhand','sens0;alias sens_check_qhand sens_check_quicky;best_weapon;sens_refresh','Q-Release: Hauptwaffe rechts, Inspect aus; andere Sens-Haltetasten beachten.')
replace('-quick','sens0;cl_autohelp 0;alias sens_check_quick sens_check_qhand;best_weapon;sens_refresh','Keine kurzzeitigen Granaten/Inspect-Aufrufe im Quick-Release.')
replace('-quicky','sens0;alias sens_check_quicky sens_normal;best_weapon;sens_refresh','Quick-Release mit eindeutiger Waffe/Hand und passendem Crosshair.')
replace('+qhand','sensx;knife;alias sens_check_qhand sens_held;sens_refresh;refresh_crosshair','Messer links mit optionalem Inspect; aktuellen Schusszustand erhalten.')
replace('+quick','<hand;knife;taser;sensx;look1;cl_autohelp 1;alias sens_check_quick sens_held;sens_refresh;refresh_crosshair','Bisherige Messer/Zeus-Folge mit optionalem Inspect und sichtbarer passender Anzeige.')
replace('+quicky','sensx;<hand;knife;c4;look1;alias sens_check_quicky sens_held;sens_refresh;refresh_crosshair','Bisherige Messer/Bomben-Folge; kein dauerhaftes Crosshair-Ausblenden.')
for k in ['z','x','c','f']:
 slots={'smoke':8,'molo':10,'he':6,'flash':7}
 body='<hand;'+(';'.join('slot'+str(slots[n]) for n in reversed(opt['grenade_priority'][k])))+';look1;refresh_crosshair'
 replace('equip_'+k,body,'Vorhandene Granatenprioritaet links; optionales Inspect, gespeicherte Farbe bleibt erhalten.')
add('mode_status','echo LEETED_MODES;alias look1;alias automatic_white;alias shot_selected;alias shot_render;alias space_sneak_toggle;selection_status','Aktive Optionen und Auswahl ohne Zustandsaenderung ausgeben.')

def transform(c,top=True):
 t=tokens(c)
 if not t:return c
 op=t[0].lower()
 if op=='alias' and len(t)>2:
  n=t[1].lower()
  if top and n in replacements:return alias(t[1],replacements[n])
  # Only raw engine inspect calls are normalized recursively. Never replace
  # nested alias assignments using the top-level definition table.
  if n in ('look0','look1'):return c
  body=';'.join(transform(x,False) for x in commands(' '.join(t[2:])))
  return alias(t[1],body) if body!=';'.join(commands(' '.join(t[2:]))) else c
 if op=='bind' and len(t)>2:
  if t[1].lower()=='enter' and ' '.join(t[2:]).lower()=='+attack':return 'bind enter +enter_fire'
  body=';'.join(transform(x,False) for x in commands(' '.join(t[2:])))
  return f'bind "{t[1]}" "{body}"' if body!=';'.join(commands(' '.join(t[2:]))) else c
 if op in ('+lookatweapon','-lookatweapon'):return 'look1' if op[0]=='+' else 'look0'
 if op=='echo' and 'LEETED_v1.01.1_09_END' in c:return c.replace('_09_END','_10_END')
 return c

init=['inspect_on' if opt['inspect_enabled'] else 'inspect_off','color_lock_on' if opt['color_lock_enabled'] else 'color_lock_off','shot_circle' if opt['shot_profile']=='circle' else 'shot_t','shot_on' if opt['shot_enabled'] else 'shot_off','look0','hand>','sens_refresh','refresh_crosshair']
groups=helpers[:];changes=[]
for num,line in enumerate(raw.decode().splitlines(),1):
 cs=commands(line)
 if cs==['host_writeconfig']:groups.append(annotated('Startoptionen nach allen Altdefinitionen anwenden.',';'.join(init)))
 ns=[transform(c) for c in cs]
 if ns!=cs:
  t=tokens(cs[0]);note=reasons.get(t[1].lower() if t[0].lower()=='alias' else '', 'Direkte Inspect-Aufrufe ueber look1/look0 zentralisieren bzw. Versionsmarker erneuern.')
  groups.append('// ALT: '+line+'\n'+annotated(note,'\n'.join(ns)))
  changes.append({'line':num,'old':line,'new':ns,'reason':note})
 else:groups.append(line+'\n')
flat='// LEETED v1.01.1_10 - auf Basis 09; Startoptionen am Ende.\n'+''.join(groups)
active=[c for l in flat.splitlines() for c in commands(l)]
assert all(len(c.encode())<=opt['max_command_bytes'] for c in active)
(out/'LEETED_Gesamtansicht.cfg.txt').write_text(flat)
parts=[];part=''
for g in groups:
 if part and len((part+g).replace('\n','\r\n').encode())>opt['max_part_bytes']:parts.append(part);part=''
 part+=g
if part:parts.append(part)
for old in out.glob('LEETED_05_*.cfg'):old.unlink()
for i,part in enumerate(parts,1):
 if i<len(parts):part+=f'// NEU: Naechsten Abschnitt laden.\nexec LEETED_05_{i+1:02d}.cfg\n'
 (out/f'LEETED_05_{i:02d}.cfg').write_bytes(part.replace('\n','\r\n').encode())
(out/'autoexec.cfg').write_bytes(b'// LEETED v1.01.1_10 - alle Teil-CFGs daneben ablegen.\r\nexec LEETED_05_01.cfg\r\n')
(out/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
meta={'version':opt['version'],'source_sha256':opt['source_sha256'],'parts':len(parts),'changed_source_lines':len(changes),'max_active_command_bytes':max(len(c.encode()) for c in active),'engine_tested':False}
(out/'build.json').write_text(json.dumps(meta,indent=2));print(meta)
