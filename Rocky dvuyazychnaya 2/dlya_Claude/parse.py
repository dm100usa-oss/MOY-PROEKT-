import re, json
def clean(t):
    t=re.sub(r'`[^`]*`','',t).replace('**','').strip()
    return re.sub(r'\s+',' ',t)
chs=[]
for i in range(1,6):
    txt=open(f'/home/claude/rocky/rocky_cap{i}_pares.md').read()
    en={int(m.group(1)):clean(m.group(2)) for m in re.finditer(r'^\*\*(\d+) EN\.\*\* (.+)$',txt,re.M)}
    es={int(m.group(1)):clean(m.group(2)) for m in re.finditer(r'^\*\*(\d+) ES\.\*\* (.+)$',txt,re.M)}
    chs.append([(en[k],es[k]) for k in sorted(en)])
bl=open('/home/claude/rocky/rocky_bloques_palabras_preguntas.md').read()
blocks=[]
for n in range(1,6):
    m=re.search(r'## Bloque %d - ([^\n]*)\n(.*?)(?=\n---|\n## Notas|\Z)'%n,bl,re.S); body=m.group(2)
    words=[(a.strip(),b.strip()) for a,b in re.findall(r'^\| ([^|]+?) \| ([^|]+?) \|$',body,re.M) if a.strip() not in('English','---')]
    qs=re.findall(r'^\d\. (.+)\n\s+\*(.+)\*$',body,re.M)
    blocks.append({'words':words,'qs':qs})
json.dump({'chs':chs,'blocks':blocks},open('/home/claude/book/text.json','w'),ensure_ascii=False,indent=1)
for c,b in zip(chs,blocks): print(len(c),len(b['words']),len(b['qs']))
print(chs[1][21][0]); print(chs[0][0][1][:80])
