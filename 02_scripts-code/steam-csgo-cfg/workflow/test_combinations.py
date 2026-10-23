"""Bounded state tests. Tests alias events, not engine animation/input filtering."""
from pathlib import Path
from copy import deepcopy
import json,itertools,sys
from check_inputs import Model
root=Path(sys.argv[1]);base=Model();base.run((root/'LEETED_Gesamtansicht.cfg.txt').read_text())
checks=[];cases=0
def check(name,ok):
 assert ok,name
 checks.append(name)
def rgb(m):return tuple(m.values.get('cl_crosshaircolor_'+k) for k in 'rgb')
def released(m,name):
 check(name+' right hand',m.hand=='right')
 check(name+' inspect released',not m.inspect)
 expected=next((x for x in [1,2,3] if x in m.inventory),m.weapon)
 check(name+' best available weapon',m.weapon==expected)
def invariant(m,held,name):
 check(name+' sensitivity',m.values['sensitivity']==('1.87' if held&{'space','q'} else '1.33'))
 if not held&{'mouse1','enter'}:
  check(name+' idle recoil off',m.values['cl_crosshair_recoil']=='0')
  wanted=deepcopy(m);wanted.run('selected_color')
  check(name+' selected idle color',rgb(m)==rgb(wanted))
 else:
  check(name+' firing white circle',m.values['cl_crosshairstyle']=='1' and rgb(m)==('255','255','255') and m.values['cl_crosshair_recoil']=='1')

# Both modes, all unordered key pairs and every legal interleaving of their
# press/release events (six per pair). Includes sequential and overlapping use.
keys=['space','q','z','x','c','f','alt','v','capslock','shift','mouse1','enter','k','j']
for inspect in [False,True]:
 for a,b in itertools.combinations(keys,2):
  events=[(a,1),(a,0),(b,1),(b,0)]
  for order in itertools.permutations(events):
   if order.index((a,1))>order.index((a,0)) or order.index((b,1))>order.index((b,0)):continue
   m=deepcopy(base);m.run('inspect_on' if inspect else 'inspect_off');held=set();bomb_mode=None
   name=f'pair inspect={inspect} {order}'
   for key,down in order:
    before=len(m.dropped)
    if down:
     if key=='capslock':bomb_mode='space' not in held
     held.add(key);m.down(key)
    else:
     grenade_release=key in 'zxcf' and m.aliases[key+'_up']==key+'_gren_up'
     held.discard(key);m.up(key)
     if key in ['space','q'] or grenade_release:released(m,name+' '+key)
     if key=='capslock':
      check(name+' captured bomb action',len(m.dropped)-before==(1 if bomb_mode else 0))
      if bomb_mode:check(name+' drops bomb only',m.dropped[-1]==5)
    invariant(m,held,name+f' after {key}:{down}')
   check(name+' no stuck inspect',not m.inspect)
   check(name+' wheel free','mwheeldown' not in m.binds)
   cases+=1

# Every press permutation and release permutation for the four grenade keys.
for press in itertools.permutations('zxcf'):
 for release in itertools.permutations('zxcf'):
  m=deepcopy(base);m.run('inspect_on')
  for k in press:m.down(k)
  for k in release:m.up(k);released(m,'four '+''.join(press)+'/'+''.join(release)+' '+k)
  cases+=1

# All grenade inventories with/without primary/secondary, both inspect modes.
priority={'z':[8,10,6,7],'x':[10,6,7,8],'c':[6,7,8,10],'f':[7,8,10,6],'space':[8,10,6,7]}
for inspect,mask,weapons in itertools.product([False,True],range(16),[{1,2,3},{2,3},{3}]):
 for key,order in priority.items():
  m=deepcopy(base);m.run('inspect_on' if inspect else 'inspect_off');m.inventory=set(weapons)|{v for i,v in enumerate([6,7,8,10]) if mask&(1<<i)};m.weapon=min(weapons)
  expected=next((x for x in order if x in m.inventory),m.weapon)
  m.down(key);check('inventory selection '+str((inspect,mask,weapons,key)),m.weapon==expected)
  check('inspect option '+str((inspect,mask,weapons,key)),m.inspect==inspect)
  m.up(key);released(m,'inventory release '+str((inspect,mask,weapons,key)));cases+=1

# All normal profiles/colors, both shot modes and enabled states. K/J and a
# grenade release during fire must preserve the selected shot or idle mode.
for form,color,shot,enabled in itertools.product(['crossdot','crosscross','crosshole','crosst','trill'],['c_hell','c_matrix','c_npink','c_nweed','c_nred','c_ntkys'],['shot_circle','shot_t'],[True,False]):
 m=deepcopy(base);m.run(';'.join([form,color,shot,'shot_on' if enabled else 'shot_off']));chosen=m.aliases['mycross'];wanted=rgb(m);n=f'profiles {form}/{color}/{shot}/{enabled}'
 m.down('mouse1');m.down('z');m.up('z')
 check(n+' selected pointer preserved',m.aliases['mycross']==chosen)
 check(n+' shot switch',m.values['cl_crosshair_recoil']==('1' if enabled else '0'))
 if enabled:
  check(n+' geometry',m.values['cl_crosshair_length']==('2' if shot=='shot_circle' else '255') and m.values['cl_crosshair_thickness']=='1')
  check(n+' color',rgb(m)==(('255','255','255') if shot=='shot_circle' else ('255','0','0')))
 m.up('mouse1');check(n+' restore',m.aliases['mycross']==chosen and rgb(m)==wanted and m.values['cl_crosshair_recoil']=='0');cases+=1

# Runtime option transitions while firing and while inspecting.
m=deepcopy(base);m.run('c_nweed;shot_t');m.down('mouse1');m.run('shot_off');check('Disable shot midhold',m.values['cl_crosshair_recoil']=='0' and rgb(m)==('155','255','0'))
m.run('shot_on');check('Enable shot midhold',m.values['cl_crosshair_recoil']=='1' and rgb(m)==('255','0','0'))
m.run('shot_style_toggle');check('Toggle T to circle midhold',m.values['cl_crosshairstyle']=='1' and rgb(m)==('255','255','255'))
m.up('mouse1');check('Options retain idle color',rgb(m)==('155','255','0'))
m.run('inspect_on');m.down('z');check('Inspect starts',m.inspect);m.run('inspect_off');check('Inspect off releases immediately as input',not m.inspect);m.up('z')
m.run('c_npink;movecross');check('Protected movement color',rgb(m)==('255','0','255'))
m.run('color_lock_off;movecross');check('Legacy automatic white optional',rgb(m)==('255','255','255'))
m.run('shot_t');m.down('mouse1');m.run('movecross');check('Automatic white cannot overwrite firing T',rgb(m)==('255','0','0'))
m.up('mouse1');m.run('color_lock_on');check('Reenable restores deliberately chosen color',rgb(m)==('255','0','255'))

# SPACE + bomb toggle: repeated down is ignored; SHIFT and release ordering.
for release in [('space','capslock'),('capslock','space')]:
 m=deepcopy(base);m.down('space');m.down('capslock')
 check('First toggle sprint0 '+str(release),not m.sprint)
 for _ in range(5):m.down('capslock')
 check('Held bomb key does not repeat toggle '+str(release),not m.sprint)
 m.down('shift');m.up('shift');check('SHIFT respects active sprint0 '+str(release),not m.sprint)
 for k in release:m.up(k)
 check('SPACE always sprint1 '+str(release),m.sprint and m.aliases['space_sneak_toggle']=='space_sneak_on')
 check('No drop from toggle '+str(release),not m.dropped)
m=deepcopy(base);m.down('space')
for expected in [False,True,False,True]:
 m.down('capslock');m.up('capslock');check('Alternating toggle '+str(len(checks)),m.sprint==expected)
m.up('space');check('Toggle fully reset',m.sprint and not m.dropped)

# Caps first, then SPACE plus grenade/quick release: cannot drop the primary.
for middle in ['z','x','c','f','q']:
 m=deepcopy(base);m.down('capslock');m.down('space');m.down(middle);m.up(middle);m.up('space');m.up('capslock')
 check('Reacquire bomb after '+middle,m.dropped==[5] and 1 in m.inventory);released(m,'bomb final '+middle)

# Three-way ALT re-entry regression reported by independent review.
for grenade in 'zxcf':
 m=deepcopy(base);m.run('inspect_on');m.down(grenade);m.down('space');m.down('alt');m.up('space');released(m,'SPACE before ALT '+grenade);m.up('alt');released(m,'ALT must not resurrect grenade '+grenade);m.up(grenade)
# Two firing keys: first release keeps attack; last release ends it.
for first,last in [('mouse1','enter'),('enter','mouse1')]:
 m=deepcopy(base);m.down(first);m.down(last);m.events=[];m.up(first)
 check('Other attack key remains '+first,'-attack' not in m.events and m.values['cl_crosshair_recoil']=='1')
 m.up(last);check('Last attack key ends '+last,'-attack' in m.events and m.values['cl_crosshair_recoil']=='0')
# Actual buy bindings that reach rdygo stop attack and its visual state.
buy_keys=[k for k,v in base.binds.items() if 'rdygo' in v.lower()]
check('Buy regressions have real bindings',bool(buy_keys))
for key in buy_keys:
 m=deepcopy(base);m.down('mouse1');m.down('enter');m.events=[];m.down(key)
 check('Buy cancels fire '+key,'-attack' in m.events and m.values['cl_crosshair_recoil']=='0' and m.aliases['refresh_crosshair']=='crosshair_idle')
 m.events=[];m.up('enter');m.up('mouse1');check('Buy release cannot restart fire '+key,'+attack' not in m.events)

result={'scope':'Finite alias/event simulation; no CS2 engine, animation, server or focus emulation','cases':cases,'assertions':len(checks),'coverage':['All 91 pairs of 14 keys, six event interleavings, two inspect modes','All 24 x 24 press/release permutations of four grenade keys','16 grenade inventories x three weapon inventories x five keys x two inspect modes','Five normal profiles x six colors x two shot profiles x shot on/off','Mid-hold option changes, bomb ownership, toggle latch, SHIFT precedence'],'checks':checks}
(root/'combinations.json').write_text(json.dumps(result,indent=2));print(cases,'cases;',len(checks),'assertions passed')
