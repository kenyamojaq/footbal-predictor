from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
needle="['BET','1',36,'3-0'],"
insert="['BET','1',36,'3-0'],['BET','1',32,'3-1'],"
if "['BET','1',32,'3-1']" not in s:
    if needle not in s:
        raise SystemExit('Critical notes history insertion point missing')
    s=s.replace(needle,insert,1)
p.write_text(s,encoding='utf-8')
