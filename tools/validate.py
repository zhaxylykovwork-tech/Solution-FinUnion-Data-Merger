"""Release checks and synthetic checks of financial/temporal model invariants.

Only stdlib. Not an integration test or claim about an actual bank.
"""
from pathlib import Path
from decimal import Decimal
import re
import sqlite3
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
FILES={
 'Task1':['README','entities','logical-data-model','data-classification','storage-strategy','reference-model'],
 'Task2':['README','master-systems','data-ownership','data-flows','data-flow-management','data-dependencies'],
 'Task3':['README','target-data-architecture','architecture-options','dwh-lakehouse','data-pipelines','analytical-model','data-products'],
 'Task4':['README','migration-target-state','migration-plan','cutover-plan','migration-risks','tech-roadmap']}

def artifacts():
    for folder,names in FILES.items():
        for name in names:assert (ROOT/folder/(name+'.md')).is_file(),(folder,name)
    checked=0
    for path in ROOT.rglob('*.md'):
        txt=path.read_text(encoding='utf8')
        assert '\ufffd' not in txt,path
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',txt):
            if '://' in target or target.startswith('#'):continue
            dest=(path.parent/target.split('#')[0]).resolve()
            assert dest.is_relative_to(ROOT) and dest.is_file(),(path,target)
            checked+=1
    # Every entity is addressed across governance artefacts, not just listed once.
    for rel in ['Task1/entities.md','Task1/data-classification.md','Task2/master-systems.md','Task2/data-ownership.md']:
        txt=(ROOT/rel).read_text(encoding='utf8')
        assert set(re.findall(r'\| (E\d\d)\b',txt))=={f'E{i:02}' for i in range(1,17)},rel
    diagrams=list(ROOT.glob('Task*/diagrams/*.drawio'))
    assert len(diagrams)==7,len(diagrams)
    for path in diagrams:
        tree=ET.parse(path)
        vertices={n.attrib['id'] for n in tree.findall('.//mxCell') if n.get('vertex')=='1'}
        edges=[n for n in tree.findall('.//mxCell') if n.get('edge')=='1']
        assert vertices and edges,path
        for e in edges:assert e.get('source') in vertices and e.get('target') in vertices,(path,e.attrib)
        ET.parse(path.with_suffix('.svg'))
        assert path.with_suffix('.png').stat().st_size>10000,path
    dfd=ET.parse(ROOT/'Task2/diagrams/transition-dfd.drawio')
    text=' '.join(n.get('value','') for n in dfd.findall('.//mxCell'))
    for i in range(1,21):assert f'F{i:02}' in text,f'F{i:02}'
    for system in ['FU CRM','RB CRM','FU Core','RB Core','FU Cards','RB Cards','FU Loans','RB Loans','DataHub','MDM','DWH','BI']:
        assert system in text,system
    print(f'Artifacts PASS: 25 mandatory task documents; {checked} local links; 16 entities x 4 matrices; 7 Draw.io/SVG/PNG sets; F01-F20.')

def financial_model():
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE posting(source TEXT,id TEXT,tx TEXT,ccy TEXT,dc TEXT,cents INTEGER,version INTEGER,PRIMARY KEY(source,id))')
    # Separate banks can have the same local ID. tx1 is later reversed, tx2 fee remains.
    inputs=[('FU','p1','tx1','RUB','D',10000,1),('FU','p2','tx1','RUB','C',10000,1),
      ('FU','p3','tx2','RUB','D',500,1),('FU','p4','tx2','RUB','C',500,1),
      ('FU','p5','rev1','RUB','D',10000,1),('FU','p6','rev1','RUB','C',10000,1),
      ('RB','p1','tx1','USD','D',20000,2),('RB','p2','tx1','USD','C',20000,2)]
    sql='''INSERT INTO posting VALUES(?,?,?,?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET
      tx=excluded.tx,ccy=excluded.ccy,dc=excluded.dc,cents=excluded.cents,version=excluded.version
      WHERE excluded.version>posting.version'''
    db.executemany(sql,inputs+[inputs[0],('RB','p1','tx1','USD','D',99999,1)])
    assert db.execute('SELECT COUNT(*) FROM posting').fetchone()[0]==8,'duplicate or stale replay changed facts'
    totals=db.execute("SELECT ccy,dc,SUM(cents) FROM posting GROUP BY ccy,dc ORDER BY ccy,dc").fetchall()
    assert totals==[('RUB','C',20500),('RUB','D',20500),('USD','C',20000),('USD','D',20000)],totals
    # Check transaction+currency groups. Global net zero alone could hide errors.
    balance_sql="SELECT source,tx,ccy,SUM(CASE dc WHEN 'D' THEN cents ELSE -cents END) n FROM posting GROUP BY source,tx,ccy HAVING n<>0"
    assert db.execute(balance_sql).fetchall()==[]
    db.execute("DELETE FROM posting WHERE source='RB' AND id='p2'")
    assert db.execute(balance_sql).fetchall()==[('RB','tx1','USD',20000)],'missing posting must fail the gate'
    # Preserve native currencies; reporting FX has an explicit rate and rounding.
    assert (Decimal('200.00')*Decimal('95.1234')).quantize(Decimal('0.01'))==Decimal('19024.68')
    db.close()
    print('Finance PASS: source-scoped keys, duplicate/stale replay, reversal groups, currency totals, missing-row rejection, explicit FX arithmetic.')

def temporal_model():
    db=sqlite3.connect(':memory:')
    db.executescript('''CREATE TABLE dim(sk INTEGER,id TEXT,vfrom TEXT,vto TEXT);
      INSERT INTO dim VALUES(1,'c1','2026-01-01','2026-07-01'),(2,'c1','2026-07-01','9999-12-31');
      CREATE TABLE fact(id TEXT,cid TEXT,at TEXT,cents INTEGER);
      INSERT INTO fact VALUES('f1','c1','2026-06-30',100),('f2','c1','2026-07-01',200),('f3','missing','2026-07-01',300);''')
    result=db.execute('''SELECT f.id,COALESCE(d.sk,0),f.cents FROM fact f LEFT JOIN dim d
      ON f.cid=d.id AND f.at>=d.vfrom AND f.at<d.vto ORDER BY f.id''').fetchall()
    assert result==[('f1',1,100),('f2',2,200),('f3',0,300)],result
    assert sum(r[2] for r in result)==600,'unknown dimension dropped money'
    # Closed report version is distinct from a correction after a late event.
    db.executescript('CREATE TABLE report(version INTEGER PRIMARY KEY,total INTEGER); INSERT INTO report VALUES(1,600),(2,650);')
    assert db.execute('SELECT total FROM report WHERE version=1').fetchone()[0]==600
    db.close()
    print('Temporal PASS: half-open SCD2 boundary, no multiplying join, unknown member preserves total, immutable prior report version.')

if __name__=='__main__':
    artifacts();financial_model();temporal_model()
