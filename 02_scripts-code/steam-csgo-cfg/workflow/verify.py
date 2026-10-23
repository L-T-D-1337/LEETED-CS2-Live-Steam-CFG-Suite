from pathlib import Path
from copy import deepcopy
import re,json,sys,itertools
from audit_cfg import commands,tokens,audit
from check_inputs import Model
root=Path(sys.argv[1]);checks=[]
def check(name,test):
 assert test,name
 checks.append(name)
def active(s):return [c for l in s.splitlines() for c in commands(l)]
def expand(path,stack=()):
 check('exec path contained '+path.name,path.parent.resolve()==root.resolve())
 check('exec no cycle '+path.name,path.name not in stack)
 seq=[]
 for c in active(path.read_text()):
  t=tokens(c)
  if t[0].lower()=='exec':seq+=expand(root/t[1],stack+(path.name,))
  else:seq.append(c)
 return seq
flat=active((root/'LEETED_Gesamtansicht.cfg.txt').read_text());seq=expand(root/'autoexec.cfg')
check('Chained exec equals complete intended command sequence',seq==flat)
for c in seq:check('Full command byte budget '+tokens(c)[0],len(c.encode('utf-8'))<=384)
b=Model();b.run('\n'.join(seq))
check('Final marker executed',any('LEETED_v1.01.1_10_END' in c for c in b.events))
check('No branding in alias names',not any(re.search(r'dkz|leeted',a,re.I) for a in b.aliases))
check('Save occurs once and after final mouse1 binding',sum(tokens(c)[0].lower()=='host_writeconfig' for c in seq)==1 and next(i for i,c in enumerate(seq) if c=='host_writeconfig')>max(i for i,c in enumerate(seq) if c.lower().startswith('bind mouse1')))
for n,body in b.aliases.items():check('Alias length '+n,len(body.encode())<=384)
check('Boot mycross is visible',b.values.get('crosshair')=='1')
check('Default crosshair migrated',b.values.get('cl_crosshair_length')=='3' and b.values.get('cl_crosshair_thickness')=='2')
forms={'shape_hole':('1','7','4'),'shape_dot':('3','2','2'),'shape_cross':('2','2','1'),'shape_t':('255','1','1')}
for press in range(1,9):
 m=deepcopy(b)
 for _ in range(press):m.down('k');m.up('k')
 selection=m.aliases['gmrcrossnow'];next_key=m.aliases['next_cross'];color=m.aliases['croco']
 m.down('mouse1');check(f'Fire geometry {press}',m.values.get('cl_crosshair_length')=='2' and m.values.get('cl_crosshaircolor_a')=='255' and m.values.get('cl_crosshairstyle')=='1')
 m.up('mouse1');expected=forms[selection]
 check(f'Fire restores selected form {press}',tuple(m.values.get('cl_crosshair_'+p) for p in ['length','thickness','gap'])==expected)
 check(f'Fire preserves next selection {press}',m.aliases['next_cross']==next_key and m.aliases['gmrcrossnow']==selection)
 check(f'Fire preserves chosen color {press}',m.aliases['croco']==color)
 check(f'Fire release visible {press}',m.values.get('crosshair')=='1')
for first,last in [('space','mouse1'),('mouse1','space')]:
 for release in [(first,last),(last,first)]:
  m=deepcopy(b);m.down(first);m.down(last)
  for k in release:m.up(k)
  check(f'Combined releases {first},{last}/{release}',m.values.get('crosshair')=='1' and 'mwheeldown' not in m.binds and m.aliases['refresh_crosshair']=='crosshair_idle')
m=deepcopy(b);m.down('mouse1');m.down('k');m.down('j')
check('K/J while shooting keeps firing renderer',m.values['cl_crosshairstyle']=='1' and m.values['cl_crosshair_recoil']=='1')
chosen=m.aliases['gmrcrossnow'];color=m.aliases['croco'];m.up('mouse1')
check('K/J while shooting saved for release',m.aliases['gmrcrossnow']==chosen and m.aliases['croco']==color and m.values['cl_crosshaircolor_a']=='255')
for press in range(1,7):
 m=deepcopy(b)
 for _ in range(press):m.down('j')
 wanted=tuple(m.values['cl_crosshaircolor_'+c] for c in 'rgb');m.down('mouse1');m.up('mouse1')
 check(f'Color restored after firing {press}',wanted==tuple(m.values['cl_crosshaircolor_'+c] for c in 'rgb'))
m=deepcopy(b);m.down('b');m.events=[];m.down('space');m.up('space')
check('SPACE never releases B jump','-jump' not in m.events)
check('SPACE BUY retained','buymenu' in m.events)
m=deepcopy(b);m.run('b_jump');check('B simple jump alternative',m.binds['b']=='+jump')
m.run('b_duckjump');check('B requested combo',m.binds['b']=='+duckjump')
m=deepcopy(b);m.events=[];m.down('n');check('N no blocked jumpthrow sequence',m.events==['+jump'])
# Validate migrated crosshair schema against pinned game dump (not proof of live execution).
limits={'cl_crosshair_length':(0,255),'cl_crosshair_thickness':(1,31),'cl_crosshair_gap':(0,128),'cl_crosshaircolor_a':(0,255)}
old=set('cl_crosshairsize cl_crosshairthickness cl_crosshairgap cl_crosshairalpha cl_crosshaircolor cl_crosshairusealpha cl_crosshair_outlinethickness cl_fixedcrosshairgap cl_crosshairgap_useweaponvalue'.split())
def scan(c):
 t=tokens(c);op=t[0].lower()
 if op in ('alias','bind') and len(t)>2:
  for sub in commands(' '.join(t[2:])):scan(sub)
 else:
  check('No legacy crosshair command '+op,op not in old)
  if op in limits and len(t)>1:
   value=float(t[1]);lo,hi=limits[op];check('Legal crosshair integer '+c,value.is_integer() and lo<=value<=hi)
for c in seq:scan(c)
# Every original line recorded as changed must appear verbatim as an ALT comment.
text=(root/'LEETED_Gesamtansicht.cfg.txt').read_text()
changes=json.loads((root/'changes.json').read_text())
check('All changed original lines retained',all('// ALT: '+v['old']+'\n' in text for v in changes))
check('Balanced quotes',not audit(root/'LEETED_Gesamtansicht.cfg.txt')['quote_candidates'])
# User's exact V4 sharecode and no follow-recoil in every idle profile.
share=json.loads((Path(__file__).parent/'sharecode.json').read_text())
expected_code={tokens(c)[0]:tokens(c)[1] for l in share['convars'].splitlines() for c in commands(l)}
expected_code.update({'cl_crosshair_length':'2','cl_crosshair_thickness':'1','cl_crosshair_gap':'4','cl_crosshair_drawoutline':'0','cl_crosshaircolor_g':'255','cl_crosshaircolor_b':'255','cl_crosshair_dynamic_spread_limit':'255'}) # v10 authorized circle overrides
check('Sharecode roundtrip exact',share['code']==share['roundtrip'])
for form in ['crossdot','crosscross','crosshole','crosst','trill']:
 m=deepcopy(b);m.run(form)
 check(form+' idle recoil off',m.values['cl_crosshair_recoil']=='0')
 saved_form=m.aliases['gmrcrossnow'];saved_color=m.aliases['croco']
 for cycle in range(3):
  m.down('mouse1')
  check(form+' shot code plus requested size2 '+str(cycle),all(m.values.get(k)==v for k,v in expected_code.items()))
  m.up('mouse1')
  check(form+' release recoil off '+str(cycle),m.values['cl_crosshair_recoil']=='0')
  check(form+' selection preserved '+str(cycle),(m.aliases['gmrcrossnow'],m.aliases['croco'])==(saved_form,saved_color))
 m.run('reco1')
 check(form+' old recoil toggle stays off idle',m.values['cl_crosshair_recoil']=='0')
 m.down('mouse1');m.down('k');m.down('j')
 check(form+' K/J cannot overwrite shot code',all(m.values.get(k)==v for k,v in expected_code.items()))
 m.up('mouse1');check(form+' new selection release recoil off',m.values['cl_crosshair_recoil']=='0')
prior=json.loads((Path(__file__).parent/'previous06.json').read_text())
for name,line in prior.items():check('Version06 ALT retained '+name,'// ALT: '+line+'\n' in text)
m=deepcopy(b);m.events=[];m.down('mouse1');m.up('mouse1')
check('Primary fire press and release emitted','+attack' in m.events and '-attack' in m.events)
m=deepcopy(b);m.weapon=1;m.down('q')
check('Q hold selects knife',m.weapon==3)
m.up('q');check('Q release returns available primary',m.weapon==1)
check('MOUSE1 final binding exists',b.binds.get('mouse1')=='+atx' and '+atx' in b.aliases and '-atx' in b.aliases)
check('Crosshair selection and color binds exist',b.binds.get('k')=='+cross_pick' and b.binds.get('j')=='cr_x')
check('No nested exec for shot profile',all(not any(tokens(c)[0]=='exec' for c in commands(body)) for name,body in b.aliases.items() if name.startswith('shot_profile_')))
# Version09 requested sensitivity, grenade fallback, SPACE release and scope checks.
prior08=json.loads((Path(__file__).parent/'previous08.json').read_text())
for name,line in prior08.items():check('Version08 ALT retained '+name,'// ALT: '+line+'\n' in text)
check('Default sensitivity 1.33',b.values['sensitivity']=='1.33')
check('Inspect aliases restored',b.aliases['look1']=='noop' and b.aliases['look0']=='-lookatweapon')
for name in ['quick','qhand','quicky']:
 for first,last in [('space',name),(name,'space')]:
  for release_order in [(first,last),(last,first)]:
   m=deepcopy(b);down={'space':'+space_mode',name:'+'+name};up={'space':'-space_mode',name:'-'+name}
   m.run(down[first]);m.run(down[last])
   check('Held sensitivity '+name+str(release_order),m.values['sensitivity']=='1.87')
   m.down('mouse1');m.up('mouse1')
   check('Fire respects held sensitivity '+name+str(release_order),m.values['sensitivity']=='1.87')
   m.run(up[release_order[0]])
   check('Other held key retains 1.87 '+name+str(release_order),m.values['sensitivity']=='1.87')
   m.run(up[release_order[1]])
   check('Last release restores 1.33 '+name+str(release_order),m.values['sensitivity']=='1.33')
m=deepcopy(b);m.down('mouse1');check('Firing alone uses standard sens',m.values['sensitivity']=='1.33');m.up('mouse1')
priorities={'z':[8,10,6,7],'x':[10,6,7,8],'c':[6,7,8,10],'f':[7,8,10,6],'space':[8,10,6,7]}
for mask in range(16):
 available={slot for bit,slot in enumerate([8,10,6,7]) if mask&(1<<bit)}
 for key,priority in priorities.items():
  m=deepcopy(b);m.inventory={1,2,3}|available;m.weapon=1;m.run('inspect_on');m.events=[];m.down(key)
  expected=next((slot for slot in priority if slot in available),1)
  check('Grenade fallback '+key+' '+str(mask),m.weapon==expected)
  looks=[e.lower() for e in m.events if e.lower() in ('+lookatweapon','-lookatweapon')]
  check('Grenade inspect '+key+' '+str(mask),looks[-1]=='+lookatweapon')
  m.up(key);check('Grenade release primary '+key+' '+str(mask),m.weapon==1)
  if key=='space':
   looks=[e.lower() for e in m.events if e.lower() in ('+lookatweapon','-lookatweapon')]
   check('SPACE final look0 '+str(mask),looks[-1]=='-lookatweapon')
   check('SPACE proview '+str(mask),tuple(m.values.get(k) for k in ['viewmodel_presetpos','viewmodel_offset_x','viewmodel_offset_y','viewmodel_offset_z','viewmodel_fov'])==('0','2.5','-2','-2','54'))
for key in ['z','x','c','f']:
 for release_order in [('space',key),(key,'space')]:
  m=deepcopy(b);m.down('space');m.down(key)
  m.up(release_order[0]);expected=1
  check('SPACE/grenade overlap '+str(release_order),m.weapon==expected)
  if release_order[0]=='space':
   looks=[e.lower() for e in m.events if e.lower() in ('+lookatweapon','-lookatweapon')]
   check('SPACE release wins inspect '+key,looks[-1]=='-lookatweapon')
  m.up(release_order[1]);check('SPACE/grenade last release '+str(release_order),m.weapon==1)
# Selection lock: repeated key-down cannot advance, and firing never advances selection.
m=deepcopy(b);m.down('k');chosen=m.aliases['mycross'];next_step=m.aliases['next_cross']
for _ in range(5):m.down('k')
check('K held selects once',m.aliases['mycross']==chosen and m.aliases['next_cross']==next_step)
m.up('k');m.down('k');m.up('k');check('Next physical K press advances',m.aliases['mycross']!=chosen)
for profile,renderer in [('crosshole','restore_hole'),('crossdot','restore_dot'),('crosscross','restore_cross'),('crosst','restore_t'),('trill','restore_trill')]:
 m=deepcopy(b);m.run(profile);check('Direct selected restore '+profile,m.aliases['mycross']==renderer)
 expected={k:v for k,v in m.values.items() if k in ['cl_crosshairstyle','cl_crosshair_length','cl_crosshair_thickness','cl_crosshair_gap','cl_crosshaircolor_a','cl_crosshair_t','cl_crosshair_recoil']}
 next_step=m.aliases['next_cross']
 # Deliberately corrupt the legacy pointer: restoring must not execute a selector through it.
 m.run('alias gmrcrossnow next_cross');m.down('mouse1');m.up('mouse1')
 check('Release independent from legacy pointer '+profile,m.aliases['mycross']==renderer and m.aliases['next_cross']==next_step and all(m.values[k]==v for k,v in expected.items()))
(root/'verification.json').write_text(json.dumps({'scope':'Static alias dispatch, schema and exec order; no CS2 engine/filter/animation test','passed':len(checks),'checks':checks},indent=2))
print(len(checks),'static checks passed')
# Produce unresolved dispatch inventory for manual review, without treating absent dump entries as engine errors.
registry={}
for fn in ['commands.txt','convars.txt']:
 for l in (Path(__file__).parent/fn).read_text().splitlines():
  if l and not l[0].isspace():registry[l.split()[0].lower()]=l
inputs='attack attack2 jump duck sprint forward back left right turnleft turnright turnup turndown moveup movedown klook use strafe zoom yaw pitch forwardback rightleft speed reload voicerecord showscores'.split()
known=set(registry)|set(b.aliases)|{sign+c for c in inputs for sign in ['+','-']}|{'buy','drop','yaw','pitch','fallback','getout','needrop','use'}
unknown={}
for n,body in b.aliases.items():
 for c in commands(body):
  op=tokens(c)[0].lower()
  if op not in known:unknown.setdefault(op,[]).append(n)
print('Unresolved static aliases:',json.dumps(unknown))
