"""Generate matching editable Draw.io, SVG and PNG from explicit diagram geometry.

No network renderer. Python stdlib + Pillow. All labels and routes are kept in
source so exported images and editable nodes remain consistent.
"""
from pathlib import Path
from html import escape
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('C:/Windows/Fonts/arial.ttf')
if not FONT.exists():
    FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
COLORS = {'process':'#e7f0ff','store':'#fff1d4','external':'#f1f3f5','entity':'#e4f4ed'}

def node(key, x, y, w, h, lines, kind='process'):
    return dict(key=key,x=x,y=y,w=w,h=h,lines=lines,kind=kind)

def edge(a,b,points,label='',at=None,dashed=False):
    return dict(a=a,b=b,points=points,label=label,at=at,dashed=dashed)

def render(folder,name,title,subtitle,nodes,edges,W,H,footer):
    out=ROOT/folder/'diagrams';out.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']
    mx=ET.Element('mxfile',host='app.diagrams.net',version='24.7.17')
    diagram=ET.SubElement(mx,'diagram',name=title,id=name)
    model=ET.SubElement(diagram,'mxGraphModel',dx=str(W),dy=str(H),grid='1',gridSize='10',page='1',pageWidth=str(W),pageHeight=str(H))
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    def font(size):return ImageFont.truetype(str(FONT),size)
    def text(x,y,s,size=20,color='#182c47'):
        d.text((x,y),s,font=font(size),fill=color)
        svg.append(f'<text x="{x}" y="{y+size-3}" font-family="Arial,DejaVu Sans,sans-serif" font-size="{size}" fill="{color}">{escape(s)}</text>')
    text(35,22,title,32);text(35,72,subtitle,20)
    tc=ET.SubElement(root,'mxCell',id='title',value=title+'<br>'+subtitle,style='text;html=1;fontSize=24;align=left;verticalAlign=top;',vertex='1',parent='1')
    ET.SubElement(tc,'mxGeometry',x='35',y='20',width=str(W-70),height='90',**{'as':'geometry'})
    bykey={n['key']:n for n in nodes}
    # Draw connections before boxes; labels are placed only in intentional gaps.
    for i,e in enumerate(edges):
        pts=e['points'];color='#60728b'
        if e['dashed']:
            for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
                length=math.hypot(x2-x1,y2-y1)
                for k in range(0,int(length),14):
                    z=min(k+8,length)
                    d.line([(x1+(x2-x1)*k/length,y1+(y2-y1)*k/length),(x1+(x2-x1)*z/length,y1+(y2-y1)*z/length)],fill=color,width=2)
        else:d.line(pts,fill=color,width=2)
        dash=' stroke-dasharray="7 5"' if e['dashed'] else ''
        svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
        a,b=pts[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0])
        tri=[b,(b[0]-11*math.cos(angle-.45),b[1]-11*math.sin(angle-.45)),(b[0]-11*math.cos(angle+.45),b[1]-11*math.sin(angle+.45))]
        d.polygon(tri,fill=color)
        svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in tri)+'" fill="'+color+'"/>')
        if e['label'] and e['at']:
            x,y=e['at'];lines=e['label'].split('\n');lw=max(d.textlength(t,font=font(18)) for t in lines)
            assert x+lw<W-10 and y+len(lines)*24<H,(name,e['label'])
            for n in nodes:
                overlap=(x<n['x']+n['w'] and x+lw>n['x'] and y<n['y']+n['h'] and y+len(lines)*24>n['y'])
                assert not overlap,(name,'edge label overlaps node',e['label'],n['key'])
            d.rectangle((x-4,y-3,x+lw+4,y+len(lines)*24),fill='white')
            svg.append(f'<rect x="{x-4}" y="{y-3}" width="{lw+8}" height="{len(lines)*24+3}" fill="white"/>')
            for j,s in enumerate(lines):text(x,y+j*24,s,18)
        sn,tn=bykey[e['a']],bykey[e['b']]
        anchors=f"exitX={(pts[0][0]-sn['x'])/sn['w']};exitY={(pts[0][1]-sn['y'])/sn['h']};entryX={(pts[-1][0]-tn['x'])/tn['w']};entryY={(pts[-1][1]-tn['y'])/tn['h']};exitPerimeter=0;entryPerimeter=0;"
        cell=ET.SubElement(root,'mxCell',id=f'e{i}',value=e['label'].replace('\n','<br>'),style='edgeStyle=none;html=1;endArrow=block;endFill=1;strokeColor=#60728b;fontSize=16;'+anchors+('dashed=1;' if e['dashed'] else ''),edge='1',parent='1',source=e['a'],target=e['b'])
        geo=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
        arr=ET.SubElement(geo,'Array',**{'as':'points'})
        for x,y in pts[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
    for n in nodes:
        x,y,w,h=n['x'],n['y'],n['w'],n['h'];fill=COLORS[n['kind']]
        assert x>=0 and y>=110 and x+w<=W and y+h<=H-90,(name,n['key'])
        d.rounded_rectangle((x,y,x+w,y+h),radius=8,fill=fill,outline='#60728b',width=2)
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#60728b" stroke-width="2"/>')
        for i,s in enumerate(n['lines']):
            size=21 if i==0 else 18
            assert d.textlength(s,font=font(size))<=w-24,(name,n['key'],s)
            assert 14+(i+1)*26<=h,(name,n['key'],'height')
            text(x+12,y+12+i*26,s,size)
        cell=ET.SubElement(root,'mxCell',id=n['key'],value='<br>'.join(escape(s) for s in n['lines']),style=f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#60728b;fontSize=18;align=left;spacing=12;',vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    for i,s in enumerate(footer):text(35,H-70+i*25,s,18)
    fc=ET.SubElement(root,'mxCell',id='footer',value='<br>'.join(footer),style='text;html=1;align=left;fontSize=18;',vertex='1',parent='1')
    ET.SubElement(fc,'mxGeometry',x='35',y=str(H-70),width=str(W-70),height='65',**{'as':'geometry'})
    (out/(name+'.svg')).write_text('\n'.join(svg+['</svg>']),encoding='utf8')
    ET.indent(mx);ET.ElementTree(mx).write(out/(name+'.drawio'),encoding='utf-8',xml_declaration=True)
    im.save(out/(name+'.png'))

def context():
    ns=[node('ops',40,180,380,220,['FU/RB operational systems','CRM, Core, Cards, Loans','8 отдельных источников','Создают свои банковские факты'],'external'),node('crm',40,590,380,170,['FU CRM / RB CRM','Получают golden projection','ID / crosswalk / reference'],'external'),node('p',730,330,450,250,['P0 Единая платформа данных','Принять / Validate / Enrich','MDM + Integration + DWH','Aggregate / Read / publish','BI + DataHub'],'process'),node('st',40,940,380,150,['Data Steward','Решения / reference approval'],'external'),node('employee',1510,230,350,170,['Сотрудник банка','Запрос / управленческий отчёт'],'external'),node('reg',1510,700,350,170,['Регуляторный потребитель','Утверждённый пакет / ack','Отправка только после sign-off'],'external')]
    es=[edge('ops','p',[(420,290),(550,290),(550,370),(730,370)],'F01–F08\nИсходные данные',(465,195)),edge('p','crm',[(730,480),(600,480),(600,675),(420,675)],'F11F/F11R\nGolden profile',(460,600)),edge('st','p',[(420,980),(640,980),(640,540),(730,540)],'F18 решения',(455,930)),edge('p','st',[(850,580),(850,1060),(420,1060)],'F19 очередь',(670,1080)),edge('employee','p',[(1510,265),(1300,265),(1300,380),(1180,380)],'F20 Read request',(1260,190)),edge('p','employee',[(1180,450),(1400,450),(1400,350),(1510,350)],'F15 отчёт',(1240,475)),edge('p','reg',[(1180,530),(1320,530),(1320,785),(1510,785)],'F16 закрытый пакет',(1340,650))]
    render('Task2','context','DFD L0 | Контекст платформы данных, 3 месяца','Один процесс P0. Внешние потоки сбалансированы с детализацией; operational мастера не перемещены в P0.',ns,es,1940,1220,['Серые — внешние участники относительно P0. Синий — единый процесс платформы.','F18/F19 и F20/F15 — вход и результат. Технический ack F16 фиксирует доставка, не финансовую приёмку.'])

def transition():
    ns=[]
    names=[('fucrm','FU CRM','F01'),('rbcrm','RB CRM','F02'),('fucore','FU Core','F03'),('rbcore','RB Core','F04'),('fucards','FU Cards','F05'),('rbcards','RB Cards','F06'),('fuloans','FU Loans','F07'),('rbloans','RB Loans','F08')]
    es=[]
    for i,(key,title,fid) in enumerate(names):
        y=150+i*140
        ns.append(node(key,35,y,260,90,[title,f'{fid} source data'],'external'))
        es.append(edge(key,'il',[(295,y+45),(450,y+45),(450,645),(600,645)],fid,(325,y+13)))
    ns.extend([node('il',600,470,340,300,['P1 Integration Layer','Adapters / source contracts','Validate / normalize codes','Read / Create / Update','Delete tombstones','Staging + event log'],'process'),node('mdm',1120,180,350,220,['P2 MDM Customer Hub','Match / Enrich / Validate','Customer / crosswalk','Reference / consent projection','Gold history + outbox'],'store'),node('dwh',1120,600,350,220,['D1/P3 PostgreSQL DWH','Staging / conformed core','Aggregate / reconcile','Atomic publish_version','Marts + report snapshots'],'store'),node('bi',1670,590,320,150,['P4 BI / metrics','Read / Aggregate','Certified views only'],'process'),node('emp',2210,590,330,150,['Сотрудник','Запрос и отчёт с as_of'],'external'),node('reg',1670,890,320,150,['Регуляторный потребитель','Утверждённый export'],'external'),node('cat',1120,1090,350,150,['D2 DataHub','Metadata / owner / lineage','Без raw ПДн'],'store'),node('st',1670,180,320,170,['Steward','Queue / match decisions','Reference approval'],'external'),node('crmp',600,140,340,150,['FU CRM / RB CRM','Golden projection (F11F/R)','Те же внешние CRM'],'external')])
    es.extend([edge('il','mdm',[(940,510),(1010,510),(1010,250),(1120,250)],'F09 proposals',(970,420)),edge('mdm','il',[(1120,340),(1060,340),(1060,560),(940,560)],'F10 gold',(960,575)),edge('il','crmp',[(700,470),(700,290)],'F11F/F11R\nEnrich/Update/Delete',(730,335)),edge('il','dwh',[(940,700),(1120,700)],'F12 facts',(960,660)),edge('mdm','dwh',[(1295,400),(1295,600)],'F13 dimensions',(1310,465)),edge('dwh','bi',[(1470,665),(1670,665)],'F14 marts',(1510,625)),edge('bi','emp',[(1990,690),(2210,690)],'F15 отчёт',(2030,705)),edge('emp','bi',[(2210,625),(1990,625)],'F20 запрос',(2025,590)),edge('dwh','reg',[(1470,760),(1560,760),(1560,975),(1670,975)],'F16 package',(1500,850)),edge('mdm','st',[(1470,230),(1670,230)],'F19 review',(1500,190)),edge('st','mdm',[(1670,310),(1470,310)],'F18 decisions',(1495,325)),edge('il','cat',[(770,770),(770,1165),(1120,1165)],'F17 IL schema',(790,1080),True),edge('mdm','cat',[(1450,400),(1520,400),(1520,1060),(1380,1060),(1380,1090)],'F17 MDM',(1480,1000),True),edge('dwh','cat',[(1295,820),(1295,1090)],'F17 DWH',(1310,960),True),edge('bi','cat',[(1830,740),(2070,740),(2070,1190),(1470,1190)],'F17 BI metadata',(1750,1210),True)])
    render('Task2','transition-dfd','DFD L1 | Промежуточное состояние, 3 месяца','F01–F20: реестр data-flows.md. Слева — восемь source systems; P1–P4 и D1/D2 раскрывают платформу P0.',ns,es,2600,1390,['Жёлтые — хранилища с ответственным процессом. Синие — обработка. Серые — внешние участники. Пунктир — metadata.','CRM показаны второй раз как получатели F11; это те же системы. F01–F08 сходятся в ingestion, не смешивая source keys.'])

def logical():
    from erd import build
    build(node,edge,render)

def target():
    ns=[node('ops',30,180,360,200,['Operational systems','FU CRM / Core / Cards / Loans','Document registry','RB — только до gates'],'external'),node('hub',30,600,360,200,['MDM Hub','Customer / Reference','Match + stewardship','Gold history / outbox'],'store'),node('int',600,180,390,200,['Integration Layer','ESB/API adapters для команд','CDC/export + Kafka events','Versioned schema contracts']),node('land',1200,180,380,200,['Private raw landing','Source snapshots / deltas','Manifest / hash / offsets','Replay / protected quarantine'],'store'),node('dwh',1200,600,380,220,['PostgreSQL DWH','Staging → core → marts','Reconcile / atomic publish','Immutable report versions','Согласованные native totals'],'store'),node('lake',1850,180,430,220,['Iceberg Lakehouse','Private object store + Parquet','REST transactional catalog','Spark batch / microbatch','Snapshots + maintenance'],'store'),node('sql',1850,600,430,170,['Trino SQL / risk analysis','Authorized curated tables','Исследования / исторические KPI']),node('bi',1200,1080,380,170,['BI / регуляторные пакеты','Certified metrics / masked views','Finance sign-off и as_of'],'external'),node('air',600,600,390,170,['Airflow orchestration','Batch DAG / backfill / DQ','Git SQL + run manifests']),node('cat',600,1080,390,170,['DataHub governance','Owner / schema / lineage','Metadata, без raw payload'],'store')]
    es=[edge('hub','int',[(390,640),(470,640),(470,330),(600,330)],'Gold / projection',(475,520)),edge('ops','int',[(390,260),(600,260)],'CDC / export',(425,220)),edge('int','land',[(990,260),(1200,260)],'events / files',(1030,220)),edge('land','dwh',[(1390,380),(1390,600)],'P1 ELT',(1410,465)),edge('land','lake',[(1580,260),(1850,260)],'P3/P4',(1650,220)),edge('lake','sql',[(2065,400),(2065,600)],'curated snapshots',(2080,470)),edge('sql','dwh',[(1850,690),(1580,690)],'Approved aggregates\nPinned snapshot / DQ',(1605,725)),edge('hub','dwh',[(390,710),(500,710),(500,870),(1390,870),(1390,820)],'Gold / reference projections',(720,880)),edge('int','hub',[(700,380),(700,450),(200,450),(200,600)],'Proposals',(260,470)),edge('dwh','bi',[(1390,820),(1390,1080)],'P5 certified publish',(1410,970)),edge('air','dwh',[(990,660),(1200,660)],'DAG / DQ',(1030,620),True),edge('air','lake',[(900,600),(900,120),(2065,120),(2065,180)],'Batch orchestration',(1080,100),True),edge('dwh','cat',[(1200,790),(1080,790),(1080,1150),(990,1150)],'lineage',(1070,1000),True),edge('lake','cat',[(2250,400),(2350,400),(2350,1320),(800,1320),(800,1250)],'Schemas / lineage / run IDs',(1690,1325),True),edge('hub','cat',[(210,800),(210,1150),(600,1150)],'Owner / lineage',(260,1100),True)]
    render('Task3','target','To-Be | Целевая архитектура, 12 месяцев','Operational commands остаются в operational systems/ESB; показанные стрелки — данные и управление аналитикой.',ns,es,2440,1460,['Сплошные — данные. Пунктир — orchestration/metadata. Airflow также оркестрирует exports; DataHub каталогизирует все critical assets.','DataHub ≠ Iceberg transactional catalog. Cards events не дублируют ledger Posting при публикации DWH.'])

def star():
    ns=[node('fact',750,480,480,350,['fact_posting','PK posting_sk','UNIQUE source_system+posting_id','FK customer/account/product/branch','FK bank/currency/booking_date','ledger_transaction_id / payment_ref?','dc / amount / signed_amount','source_position / publish_version'],'store')]
    dims=[('customer',50,180,['dim_customer (SCD2)','PK customer_sk','global ID / segment / intervals']),('account',50,530,['dim_account (SCD2)','PK account_sk','source account / type / status']),('product',50,880,['dim_product (SCD2)','PK product_sk','product / tariff version / interval']),('branch',1510,180,['dim_branch (SCD2)','PK branch_sk','bank / region / interval']),('bank',1510,530,['dim_bank','PK bank_sk','origin bank / legal entity']),('currency',1510,880,['dim_currency','PK currency_sk','currency_code / minor_unit']),('date',750,1120,['dim_date','PK date_sk','bank calendar / reporting period'])]
    es=[]
    for key,x,y,lines in dims:
        w=430 if key!='date' else 480
        ns.append(node(key,x,y,w,150,lines,'entity'))
    es.extend([edge('fact','customer',[(750,520),(620,520),(620,255),(480,255)],'1 dimension : N facts',(490,300)),edge('fact','account',[(750,620),(480,620)],'1 : N',(570,580)),edge('fact','product',[(750,740),(620,740),(620,955),(480,955)],'1 : N',(540,865)),edge('fact','branch',[(1230,520),(1380,520),(1380,255),(1510,255)],'1 : N',(1395,300)),edge('fact','bank',[(1230,620),(1510,620)],'1 : N',(1330,580)),edge('fact','currency',[(1230,740),(1380,740),(1380,955),(1510,955)],'1 : N',(1400,865)),edge('fact','date',[(990,830),(990,1120)],'1 : N',(1010,975))])
    render('Task3','analytical-star','OLAP | Звезда проведённых бухгалтерских записей','Одна запись fact = одна source Posting. FK обязательны; sk=0 — unknown dimension без потери суммы.',ns,es,2010,1410,['SCD2 join по [valid_from, valid_to) на business time. У каждого факта ровно одна версия каждой dimension.','Меры суммируются только в одной валюте. Остаток — отдельный daily snapshot, не сумма остатков за дни.'])

def roadmap():
    ns=[];es=[]
    data=[('m1','M1 | недели 1–2','Discovery / owners / baseline','Gate: scope + источники'),('m2','M2 | недели 3–6','Identity / reference pilot','Gate: safe match + unmerge'),('m3','M3 | недели 5–10','Общий PG DWH / catalog','Gate: full reconciliation'),('m4','M4 | недели 11–12','Cutover отчётности','3 месяца: общий профиль/BI'),('m5','M5 | месяцы 4–6','CRM / cases / consents','Gate: один writer в когорте'),('m6','M6 | месяцы 6–9','Core / Cards / Loans волны','Gate: finance/legal/certification'),('m7','M7 | месяцы 7–10','Lakehouse / data products','Gate: replay / ACL / cost'),('m8','M8 | месяцы 10–12','Stabilize / archive / shutdown','12 месяцев: exit gates')]
    positions=[(40,200),(570,200),(1100,200),(1630,200),(40,640),(570,640),(1100,640),(1630,640)]
    for (key,title,l1,l2),(x,y) in zip(data,positions):ns.append(node(key,x,y,430,190,[title,l1,l2], 'store' if key in ('m4','m8') else 'process'))
    for a,b,x in [('m1','m2',470),('m2','m3',1000),('m3','m4',1530)]:es.append(edge(a,b,[(x,295),(x+100,295)],'gate',(x+22,255)))
    es.extend([edge('m4','m5',[(1845,390),(1845,480),(255,480),(255,640)],'M4 → M5, обслуживание',(600,490)),edge('m5','m6',[(470,735),(570,735)],'gate',(490,695)),edge('m4','m7',[(1950,390),(1950,550),(1315,550),(1315,640)],'M4 → M7, параллельно M6',(1350,560)),edge('m6','m8',[(785,830),(785,1000),(1845,1000),(1845,830)],'M6 и M7 обязательны до M8',(980,1015)),edge('m7','m8',[(1530,735),(1630,735)],'gate',(1550,695))])
    render('Task4','migration-roadmap','Миграция | Волны с бизнес-результатом и exit gates','Относительный план. Связи — зависимости, не автоматический переход по дате. Lakehouse не блокирует M4.',ns,es,2130,1190,['Каждая волна: consistent T0 → history+delta → shadow → DQ/finance → Go/No-Go → fencing/route → observation.','Непереносимый портфель остаётся у одного RB-мастера как открытое исключение; полное отключение не объявляется.'])

if __name__=='__main__':
    logical();context();transition();target();star();roadmap()
