"""Checks alias dispatch only. CS2 engine, hardware events and server rules are not emulated."""
from pathlib import Path
from copy import deepcopy
import itertools, json, sys
from audit_cfg import commands,tokens

class Model:
    def __init__(self):
        self.aliases={}; self.binds={}; self.values={}; self.events=[]
        self.inventory={1,2,3,5,6,7,8,10}; self.weapon=1
        self.hand="right";self.inspect=False;self.sprint=False;self.dropped=[];self.lastweapon=1
    def run(self,text,depth=0):
        if depth>100: raise AssertionError('alias recursion')
        for line in text.splitlines():
            for cmd in commands(line):
                t=tokens(cmd)
                if not t: continue
                op=t[0].lower(); args=t[1:]
                if op=='alias':
                    if len(args)>=2:self.aliases[args[0].lower()]=' '.join(args[1:])
                elif op=='bind' and len(args)>1: self.binds[args[0].lower()]=' '.join(args[1:])
                elif op=='unbind': self.binds.pop(args[0].lower(),None)
                elif op in self.aliases: self.run(self.aliases[op],depth+1)
                else:
                    self.events.append(cmd)
                    if op.startswith('slot') and op[4:].isdigit() and int(op[4:]) in self.inventory:
                        self.lastweapon=self.weapon;self.weapon=int(op[4:])
                    if op=="switchhandsright":self.hand="right"
                    elif op=="switchhandsleft":self.hand="left"
                    elif op=="switchhands":self.hand="left" if self.hand=="right" else "right"
                    elif op in ("+lookatweapon","-lookatweapon"):self.inspect=op[0]=="+"
                    elif op in ("+sprint","-sprint"):self.sprint=op[0]=="+"
                    elif op=="lastinv":self.weapon,self.lastweapon=self.lastweapon,self.weapon
                    elif op=="drop":
                        self.dropped.append(self.weapon)
                        if self.weapon!=3:self.inventory.discard(self.weapon)
                    if args or op.startswith(('+','-')): self.values[op]=' '.join(args)
    def down(self,key): self.run(self.binds.get(key,''))
    def up(self,key):
        binding=self.binds.get(key,'')
        if binding.startswith('+'): self.run('-'+binding[1:])

def validate(path):
    base=Model();base.run(Path(path).read_text());base.run('inspect_on');checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    m=deepcopy(base);m.down('space');check('SPACE down binds wheel',m.binds.get('mwheeldown')=='+jump')
    check('SPACE does not add jump',not any(e=='+jump' for e in m.events[-40:]))
    m.up('space');check('SPACE up unbinds wheel','mwheeldown' not in m.binds)
    check('SPACE restores sens',m.values.get('sensitivity')=='1.33')
    # Queries do not replace convar values in the state model.
    check('SPACE restores crosshair',m.values.get('crosshair')=='1')
    m=deepcopy(base);m.run('alias -jumpp ""');m.down('space');m.up('space')
    check('Release guards survive empty old release',m.values.get('crosshair')=='1' and 'mwheeldown' not in m.binds)
    m=deepcopy(base);m.events=[];m.down('v');m.up('v')
    check('Normal V microphone', '+voicerecord' in m.events and '-voicerecord' in m.events)
    m.down('alt');m.down('v');check('ALT+V clutch',m.values.get('cl_clutch_mode')=='1')
    m.up('alt');check('ALT up clears clutch',m.values.get('cl_clutch_mode')=='0')
    m.up('v');m.events=[];m.down('v');m.up('v');check('V restored after ALT','+voicerecord' in m.events)
    keyslots={'z':8,'x':10,'c':6,'f':7}
    for key,slot in keyslots.items():
        m=deepcopy(base);m.down(key)
        check(f'{key} equips correct grenade',m.weapon==slot)
        check(f'{key} runs look1',m.inspect)
        m.up(key);check(f'{key} returns primary',m.weapon==1)
    for inventory,expected in [({1,2,3,8},1),({2,3,8},2),({3,8},3)]:
        m=deepcopy(base);m.inventory=inventory;m.down('z');m.up('z')
        check(f'Weapon fallback {expected}',m.weapon==expected)
    # All ordered pairs of different held grenade keys, in both release orders.
    for a,b in itertools.permutations(keyslots,2):
        for first,last in [(a,b),(b,a)]:
            m=deepcopy(base);m.down(a);m.down(b);m.up(first)
            check(f'Overlap {a}+{b}, release {first}',m.weapon==1)
            m.up(last);check(f'Overlap {a}+{b}, last {last}',m.weapon==1)
    for key,radio in [('z','+radialradio'),('x','+radialradio2'),('c','+radialradio3')]:
        for release in [('alt',key),(key,'alt')]:
            m=deepcopy(base);m.events=[];m.down('alt');m.down(key)
            check(f'ALT {key} opens radio {release}',radio in m.events)
            for k in release:m.up(k)
            check(f'ALT {key} matching radio release {release}','-'+radio[1:] in m.events)
            m.down(key);check(f'ALT {key} restored grenade {release}',m.weapon==keyslots[key])
    for key in keyslots:
        m=deepcopy(base);m.down(key);m.down('alt');m.up(key);m.up('alt')
        check(f'Grenade before ALT {key} no held flag',m.weapon==1)
    m=deepcopy(base);m.down('alt');m.events=[]
    for i in range(6):
        m.down('f');m.up('f')
        radios=[e for e in m.events if e in ('radio1','radio2','radio3')]
        check(f'ALT F radio cycle {i+1}',radios[-1]==f'radio{i%3+1}')
    check('ALT F does not select molotov','slot10' not in m.events)
    # Four-key release permutations cover every intermediate held subset.
    for order in itertools.permutations(keyslots):
        m=deepcopy(base)
        for k in keyslots:m.down(k)
        held=set(keyslots)
        for k in order:
            m.up(k);held.remove(k)
            expected=1 # v10: every grenade release returns to primary
            check(f'Four-key release {"".join(order)} step {k}',m.weapon==expected)
    return {'scope':'static alias/state simulation, not a CS2 runtime test','passed':len(checks),'checks':checks}

if __name__=='__main__':
    result=validate(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2))
    print(result['scope'],result['passed'],'checks passed')
