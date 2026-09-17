# -*- coding: utf-8 -*-
"""조닝 북 렌더링용 통합 데이터. 63모듈 × 5단 + 기존 배치 + 추가 배정 + 브랜드존."""
import openpyxl, json, collections, datetime

wb = openpyxl.load_workbook('data/Pharmacy_Full_Zoning_Shelf_Operations_v2.xlsx', data_only=True)
zo = {r[0]: r for r in [x for x in list(wb['01_전체조닝63'].iter_rows(values_only=True))[6:]
                        if x[0] and x[0] != '합계']}
sh = [r for r in list(wb['02_선반315'].iter_rows(values_only=True))[6:] if r[0]]
pl = [r for r in list(wb['05_상품별배치367'].iter_rows(values_only=True))[6:] if r[0]]
c3 = {r[0]: r for r in [x for x in list(wb['03_상품분류2526'].iter_rows(values_only=True))[6:] if x[0]]}
A = json.load(open('data/open-selection-assignment.json', encoding='utf-8'))
P = json.load(open('data/open-plan-summary.json', encoding='utf-8'))

byshelf = collections.defaultdict(list)
for r in pl:
    byshelf[r[1]].append(r)
add_shelf = collections.defaultdict(list)   # 1차: 선반 지정
add_mod = collections.defaultdict(list)     # 2차: 모듈만 지정
for r in A['assignments']:
    add_shelf[r['shelf']].append(r)
for r in A['pass2']['assignments']:
    add_mod[r['module']].append(r)

STATUS_SHORT = {'오픈 진열': '진열', '테마 진열': '테마', '시험 진열': '시험',
                '안내': '안내', '확장 여유': '여유'}
THEME_COLOR = {
    '피부약·상처 보호': '#C2410C', '더마·세정·선케어': '#BE185D',
    '일반약·여행·생활': '#0369A1', '영양·건강 선물': '#B45309',
    '립·눈·다리·구강': '#6D28D9', '추천·상담 안내': '#A16207',
}
tail = lambda c: str(c)[-4:] if c else ''

modules = {}
for mid, z in zo.items():
    rows = sorted([r for r in sh if r[1] == mid], key=lambda x: int(x[3]))
    bz = P['brandZones'].get(mid) or {}
    shelves = []
    for r in rows:
        sid, lv = r[0], int(r[3])
        base = [dict(code=tail(p[4]), name=str(p[5]), spec=str(p[6] or ''),
                     f=int(p[10] or 0), new=False) for p in byshelf.get(sid, [])]
        extra = [dict(code=tail(x['code']), name=str(x['name']), spec='',
                      f=x['facing'], new=True, cond=x['condition'])
                 for x in add_shelf.get(sid, [])]
        shelves.append(dict(id=sid, level=lv, status=r[10],
                            short=STATUS_SHORT.get(r[10], r[10]),
                            need=str(r[5] or ''), group=str(r[6] or ''),
                            items=base + extra,
                            f=sum(i['f'] for i in base + extra)))
    pending = [dict(code=tail(x['code']), name=str(x['name']), f=x['facing'],
                    cond=x['condition']) for x in add_mod.get(mid, [])]
    modules[mid] = dict(
        id=mid, name=str(z[3] or ''), theme=str(z[2] or ''), role=str(z[4] or ''),
        color=THEME_COLOR.get(str(z[2]), '#475569'),
        face=('EL' if mid.endswith('-EL') else 'ER' if mid.endswith('-ER')
              else 'D' if '-D-' in mid else 'U' if '-U-' in mid else mid[0]),
        brandZone=(dict(brand=bz.get('brand'), maker=bz.get('maker'),
                        claim=bz.get('claim'), why=bz.get('why')) if bz.get('brand') else None),
        shelves=shelves, pending=pending,
        skuRows=sum(len(s['items']) for s in shelves) + len(pending),
        facings=sum(s['f'] for s in shelves) + sum(p['f'] for p in pending),
    )

tot = dict(
    modules=len(modules), shelves=len(sh),
    baseSku=len(pl), baseF=sum(int(r[10] or 0) for r in pl),
    addSku=A['counts']['totalAssigned'],
    hold=A['counts']['hold'],
    totalF=sum(int(r[10] or 0) for r in pl) + A['counts']['totalAssigned'],
    brandZones=sum(1 for m in modules.values() if m['brandZone']),
)
json.dump(dict(generatedAt=datetime.date.today().isoformat(),
               totals=tot, modules=modules,
               packagingGuide=P['packagingGuide'],
               excluded=P['excluded'],
               hold=A['pass2']['hold']),
          open('data/book-data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("totals:", tot)
print("모듈별 SKU행 상위:", collections.Counter(
    {k: v['skuRows'] for k, v in modules.items()}).most_common(6))
