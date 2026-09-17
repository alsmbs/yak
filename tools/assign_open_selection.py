# -*- coding: utf-8 -*-
"""오픈 선정 '예' 미배치 384건 추가 배정 + 브랜드존 갱신.

배정 규칙
  ① 권장 주 진열에 모듈이 있으면 그 모듈로 간다.
  ② 모듈 내에서는 '운영 상품군'이 같은 선반을 우선, 없으면 확장 여유 → 사용폭이 적은 선반.
  ③ 냉장·음료는 RF1로 보낸다.
  ④ '상설 미배정'은 같은 상품군을 이미 취급하는 모듈로 보낸다. 없으면 미배정으로 남긴다.
  ⑤ 초기 페이싱은 1F (07_실행기준: 대체 후보는 채택 시 1F부터).
"""
import openpyxl, json, collections, re, datetime, csv

XLSX = 'data/Pharmacy_Full_Zoning_Shelf_Operations_v2.xlsx'
SEL = '/root/.claude/uploads/4dbaf3ab-ee67-566b-9d6a-eba6866d3a4d/0a6c0203-22.xlsx'
LAYOUT = 'data/uploaded-integrated-layout-v2.json'

wb = openpyxl.load_workbook(XLSX, data_only=True)
c3 = [r for r in list(wb['03_상품분류2526'].iter_rows(values_only=True))[6:] if r[0]]
sh = [r for r in list(wb['02_선반315'].iter_rows(values_only=True))[6:] if r[0]]
pl = [r for r in list(wb['05_상품별배치367'].iter_rows(values_only=True))[6:] if r[0]]
zo = {r[0]: r for r in [x for x in list(wb['01_전체조닝63'].iter_rows(values_only=True))[6:]
                        if x[0] and x[0] != '합계']}
sel = {r[0]: str(r[4]) for r in list(openpyxl.load_workbook(SEL, data_only=True)['Sheet1']
                                     .iter_rows(values_only=True))[1:] if r[0]}

MODRE = re.compile(r'^([WLB]\d|G\d-[UD]-\d|G\d-E[LR])$')
placed = {r[4] for r in pl}
shelf_by_id = {r[0]: r for r in sh}
shelves_of = collections.defaultdict(list)
for r in sh:
    shelves_of[r[1]].append(r)

EFF = lambda mod: 645 if mod.endswith(('-EL', '-ER')) else 865
FACE = 70                       # 평균 페이싱 폭 가정(§가이드)
used = collections.Counter()    # 선반별 사용폭
for r in pl:
    used[r[1]] += int(r[10] or 0) * FACE

# 상품군 → 그 상품군을 취급하는 모듈
group_mod = collections.defaultdict(collections.Counter)
for r in sh:
    if r[6]:
        for g in str(r[6]).split('/'):
            group_mod[g.strip()][r[1]] += 1

def pick_shelf(mod, group):
    """모듈 안에서 배정할 선반 선택. S1은 개구 100mm라 제외."""
    cand = [s for s in shelves_of.get(mod, []) if int(s[3]) != 1]
    if not cand:
        return None
    same = [s for s in cand if s[6] and group and group.strip() in str(s[6])]
    pool = same or [s for s in cand if s[10] == '확장 여유'] or cand
    return min(pool, key=lambda s: (used[s[0]], int(s[3])))

rows, unresolved = [], []
stat = collections.Counter()
for r in c3:
    code = r[0]
    if sel.get(code) != '예' or code in placed:
        continue
    prim = str(r[6] or '').strip()
    group = str(r[5] or '')
    imp = str(r[12] or '')
    mod = reason = None
    if MODRE.match(prim):
        mod, reason = prim, "권장 주 진열에 지정된 모듈"
    elif '냉장' in prim:
        mod, reason = 'RF1', "냉장·상온 음료 → 오픈 냉장고"
    elif prim in ('G5-D', 'G5-U'):
        cands = [m for m in shelves_of if m.startswith(prim + '-')]
        best = max(((m, group_mod.get(group, {}).get(m, 0)) for m in cands), key=lambda x: x[1])
        mod, reason = best[0], f"면 단위({prim}) → 상품군 일치 하위모듈"
    elif '미배정' in prim:
        c = group_mod.get(group)
        if c:
            mod, reason = c.most_common(1)[0][0], "동일 상품군 취급 모듈로 귀속"
    if not mod:
        unresolved.append(dict(code=code, name=r[2], group=group, primary=prim,
                               importance=imp, why="동일 상품군 취급 모듈 없음"))
        stat['미배정 유지'] += 1
        continue
    if mod == 'RF1':
        sid, lv = 'RF1/S2', 2
    else:
        s = pick_shelf(mod, group)
        if not s:
            unresolved.append(dict(code=code, name=r[2], group=group, primary=prim,
                                   importance=imp, why="배정 가능한 선반 없음"))
            stat['미배정 유지'] += 1
            continue
        sid, lv = s[0], int(s[3])
    used[sid] += FACE
    stat[f'배정 {imp}'] += 1
    rows.append(dict(shelf=sid, module=mod, level=lv, code=code, name=r[2], spec=r[3] or '',
                     group=group, importance=imp, recommend=str(r[8] or ''), facing=1,
                     role="추가 배정", reason=reason,
                     condition=("분류·표시 확인 후 진열" if imp == 'H' else
                                "초도 비권장 판정 재확인" if imp == 'N' else
                                "대체 후보 채택 · 1F 시작")))

print(f"추가 배정 {len(rows)}건 · 미배정 유지 {len(unresolved)}건")
print(" ", dict(stat))
print("\n모듈별 추가 배정 상위 12")
for m, n in collections.Counter(r['module'] for r in rows).most_common(12):
    print(f"  {m:<9}{n:>4}건  {zo.get(m, ['']*4)[3] if m in zo else '오픈 냉장고'}")

# ── 충전율 재계산 ──────────────────────────────────────────────────
tot_w = sum(EFF(r[1]) for r in sh)
before = sum(int(r[16] or 0) for r in sh) * FACE
after = before + len(rows) * FACE
print(f"\n충전율(페이싱 {FACE}mm 가정)  이전 {before/tot_w*100:.0f}%  →  이후 {after/tot_w*100:.0f}%")
print(f"  계획 F {sum(int(r[16] or 0) for r in sh)} → {sum(int(r[16] or 0) for r in sh)+len(rows)}")

json.dump({"schema": "kpharmacy.assignment/1.0",
           "generatedAt": datetime.date.today().isoformat(),
           "basis": "오픈 선정 '예' 695건 중 미배치 384건의 추가 배정",
           "rules": [
               "권장 주 진열에 모듈이 있으면 그 모듈로 배정",
               "모듈 내에서는 동일 운영 상품군 선반 우선, 없으면 확장 여유 → 사용폭 최소 선반",
               "S1은 개구 100mm·상품높이 80mm로 배정 대상에서 제외",
               "냉장·상온 음료는 RF1로 귀속",
               "초기 페이싱은 1F (대체 후보는 채택 시 1F부터)",
           ],
           "counts": {"assigned": len(rows), "unresolved": len(unresolved),
                      "byImportance": dict(collections.Counter(r['importance'] for r in rows))},
           "assignments": rows, "unresolved": unresolved},
          open('data/open-selection-assignment.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

with open('data/open-selection-assignment.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(["선반ID", "모듈", "단", "공급코드", "상품명", "규격", "운영 상품군",
                "중요도", "취급 권장", "페이싱", "배정 근거", "조건"])
    for r in rows:
        w.writerow([r['shelf'], r['module'], f"S{r['level']}", r['code'], r['name'], r['spec'],
                    r['group'], r['importance'], r['recommend'], r['facing'], r['reason'], r['condition']])
print("\n→ data/open-selection-assignment.json · .csv")
