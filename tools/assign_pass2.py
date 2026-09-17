# -*- coding: utf-8 -*-
"""2차 배정: 상품군이 '확인 대기'라 1차에서 남은 92건을 상품명 기준으로 라우팅."""
import json, re, collections, csv, datetime

A = json.load(open('data/open-selection-assignment.json', encoding='utf-8'))
un = A['unresolved']

# 상품명 키워드 → 모듈. 위에서부터 먼저 맞는 규칙을 적용한다.
RULES = [
    (r'부스터|톡스|시너지|PDRN|피디알엔|리쥬|인퓨전', 'G5-D-3', 'PDRN·부스터 제형 비교'),
    (r'아토|장벽|멀티크림|에멀젼|로션|수딩크림', 'G5-U-1', '장벽·건조'),
    (r'진정|시카|카밍|어성초', 'G5-U-2', '민감·진정'),
    (r'수분|하이드|모이스', 'G5-U-3', '수분·전신 보습'),
    (r'토너|패드', 'G5-U-3', '토너·패드'),
    (r'톤|화이트|브라이트|멜라', 'G3-D-2', '잡티·피부 톤'),
    (r'선크림|자외선|선스틱|썬', 'G3-D-3', '선케어'),
    (r'세럼|앰플|크림|밤', 'G5-D-2', '주름·탄력'),
    (r'숙취|컨디션|알디콤|RU21|웨이크업|헛개', 'G4-U-2', '숙취·일상 영양'),
    (r'다이어트|가르시니아|체중|콜레우스|오일케어|브이케어', 'G4-U-2', '체중관리 경구'),
    (r'비타|홍정|도담도담|액티핏', 'W4', '경구 영양'),
    (r'스프레이액|인후|목', 'L1', '목·기침'),
    (r'정$|캡슐|액$', 'L2', '경구 상담약'),
    (r'패치', 'G6-D-3', '기능 표방 패치'),
    (r'인퓨저|기기', 'G1-ER', '미용기기'),
]
# 포지셔닝 판단이 필요해 자동 배정하지 않는 군
HOLD_GROUPS = {'캔디·간식'}

rows, hold = [], []
for u in un:
    if u['group'] in HOLD_GROUPS:
        u['why'] = "약국 포지셔닝 판단 필요 — 자동 배정하지 않음"
        hold.append(u)
        continue
    hit = next(((m, w) for p, m, w in RULES if re.search(p, u['name'])), None)
    if not hit:
        u['why'] = "상품명으로 용도를 판별할 수 없음"
        hold.append(u)
        continue
    mod, why = hit
    rows.append(dict(module=mod, code=u['code'], name=u['name'], group=u['group'],
                     importance=u['importance'], facing=1, role="2차 배정",
                     reason=f"상품명 기준 라우팅 · {why}",
                     condition=("분류·표시 확인 후 진열" if u['importance'] == 'H' else
                                "초도 비권장 판정 재확인" if u['importance'] == 'N' else
                                "대체 후보 채택 · 1F 시작")))

print(f"2차 배정 {len(rows)}건 · 보류 {len(hold)}건")
print("  중요도:", dict(collections.Counter(r['importance'] for r in rows)))
print("\n모듈별:")
for m, n in collections.Counter(r['module'] for r in rows).most_common():
    print(f"  {m:<9}{n:>3}건")
print(f"\n보류 {len(hold)}건 사유:")
for k, n in collections.Counter(h['why'] for h in hold).items():
    print(f"  {k}: {n}건")
print("\n르디퍼 처리:")
for r in rows:
    if '디퍼' in r['name']:
        print(f"  {r['code']} {r['name'][:36]:<38}→ {r['module']} ({r['reason']})")

A['pass2'] = {"assignments": rows, "hold": hold,
              "rules": [f"{p} → {m} ({w})" for p, m, w in RULES],
              "holdPolicy": "캔디·간식 등 약국 포지셔닝 판단이 필요한 군은 자동 배정하지 않는다."}
A['counts']['pass2Assigned'] = len(rows)
A['counts']['hold'] = len(hold)
A['counts']['totalAssigned'] = A['counts']['assigned'] + len(rows)
json.dump(A, open('data/open-selection-assignment.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

with open('data/open-selection-assignment.csv', 'a', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(["(2차)", r['module'], "", r['code'], r['name'], "", r['group'],
                    r['importance'], "", r['facing'], r['reason'], r['condition']])
tot = A['counts']['totalAssigned']
print(f"\n총 추가 배정 {tot}건 (1차 {A['counts']['assigned']} + 2차 {len(rows)}) · 보류 {len(hold)}건")
print(f"계획 F 391 → {391+tot} · 충전율 11% → {(391+tot)*70/259275*100:.0f}%")
