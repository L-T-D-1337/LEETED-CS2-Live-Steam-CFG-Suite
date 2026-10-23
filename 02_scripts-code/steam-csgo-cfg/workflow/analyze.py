from pathlib import Path
import json,sys,re,hashlib
from check_inputs import Model
from audit_cfg import commands,tokens,audit
here=Path(__file__).resolve().parent;out=Path(sys.argv[1])
models=[]
for p in [here/'base09.cfg.txt',out/'LEETED_Gesamtansicht.cfg.txt']:
 m=Model();m.run(p.read_text());models.append(m)
before,after=models
bindings={k:{'before':before.binds.get(k),'after':after.binds.get(k)} for k in sorted(before.binds.keys()|after.binds.keys()) if before.binds.get(k)!=after.binds.get(k)}
assert bindings=={'enter':{'before':'+ATTACK','after':'+enter_fire'}},bindings
changes={k:{'before':before.aliases.get(k),'after':after.aliases.get(k)} for k in sorted(before.aliases.keys()|after.aliases.keys()) if before.aliases.get(k)!=after.aliases.get(k)}
links=[]
for name,body in after.aliases.items():
 for c in commands(body):
  t=tokens(c);op=t[0].lower()
  if op in after.aliases:links.append({'from':name,'to':op,'kind':'call'})
  if op=='alias' and len(t)>2:
   links.append({'from':name,'to':t[1].lower(),'kind':'assignment','value':' '.join(t[2:])})
doc={'scope':'Final startup alias graph; dynamic assignments shown separately from calls; not a full engine call graph','bindings':after.binds,'aliases':after.aliases,'edges':links,'delta_from_09':{'bindings':bindings,'aliases':changes},'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [here/'base09.cfg.txt',here/'inspiration_original.md']}}
(out/'alias_graph.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2))
(out/'audit.json').write_text(json.dumps(audit(out/'LEETED_Gesamtansicht.cfg.txt'),ensure_ascii=False,indent=2))
template=(here/'visualization.html').read_text()
data={'aliases':after.aliases,'binds':after.binds,'values':after.values,'edges':links}
(out/'LEETED_Ablauf_und_Test.html').write_text(template.replace('__CFG_DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')))
print('Alias graph:',len(after.aliases),'aliases,',len(links),'edges; only Enter wrapper changed.')
