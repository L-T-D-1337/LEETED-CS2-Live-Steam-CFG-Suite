"""Static CFG audit; does not emulate the CS2 input system or server restrictions."""
import json, re, sys
from collections import defaultdict
from pathlib import Path

def commands(text):
    # Split semicolons outside quotes; // comments apply outside quotes.
    out, cur, quoted, i = [], [], False, 0
    while i < len(text):
        c = text[i]
        if c == '\\' and i+1 < len(text) and text[i+1] == '"':
            cur.extend(text[i:i+2]); i += 2; continue
        if c == '"': quoted = not quoted
        if not quoted and text[i:i+2] == '//': break
        if not quoted and c == ';':
            if ''.join(cur).strip(): out.append(''.join(cur).strip())
            cur = []
        else: cur.append(c)
        i += 1
    if ''.join(cur).strip(): out.append(''.join(cur).strip())
    return out

def tokens(cmd):
    return [x[1:-1].replace('\\"','"') if x.startswith('"') and x.endswith('"') else x
            for x in re.findall(r'"(?:\\.|[^"\\])*"|[^\s"]+', cmd)]

def audit(path):
    lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    aliases, binds, settings = defaultdict(list), defaultdict(list), defaultdict(list)
    allcmd, syntax = [], []
    for n, line in enumerate(lines, 1):
        for cmd in commands(line):
            t = tokens(cmd)
            if not t: continue
            allcmd.append((n,t))
            op = t[0].lower()
            if op == 'alias' and len(t) >= 3: aliases[t[1].lower()].append((n, ' '.join(t[2:])))
            elif op in ('bind','unbind') and len(t) >= 2: binds[t[1].lower()].append((n,' '.join(t[2:]) if op == 'bind' else '(unbound)'))
            elif op not in ('echo','alias') and len(t)>1: settings[op].append((n,' '.join(t[1:])))
            if len(re.findall(r'(?<!\\)"',cmd)) % 2: syntax.append((n,cmd))
    return dict(lines=len(lines), aliases=dict(aliases), binds=dict(binds), settings=dict(settings), commands=allcmd, quote_candidates=syntax)

if __name__ == '__main__':
    result = audit(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False, indent=2),encoding='utf-8')
    print(json.dumps({k:len(v) if isinstance(v,dict) else v for k,v in result.items() if k not in ('commands','quote_candidates')},ensure_ascii=False))
    print('Quote candidates:',result['quote_candidates'])
    for kind in ('aliases','binds'):
        print(kind.upper())
        for key, values in result[kind].items():
            if len(values)>1 and len({v for _,v in values})>1:
                print(key, values)
