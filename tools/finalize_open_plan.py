# -*- coding: utf-8 -*-
"""최종 산출물 생성: 브랜드존 갱신 · 슬라이딩 도어 · 포장 치수 가이드 · 통합 JSON."""
import json, openpyxl, collections, datetime

XLSX = 'data/Pharmacy_Full_Zoning_Shelf_Operations_v2.xlsx'
wb = openpyxl.load_workbook(XLSX, data_only=True)
sh = [r for r in list(wb['02_선반315'].iter_rows(values_only=True))[6:] if r[0]]
zo = {r[0]: r for r in [x for x in list(wb['01_전체조닝63'].iter_rows(values_only=True))[6:]
                        if x[0] and x[0] != '합계']}
A = json.load(open('data/open-selection-assignment.json', encoding='utf-8'))
layout = json.load(open('data/uploaded-integrated-layout-v2.json', encoding='utf-8'))

# ── ① 브랜드존 (아크로패스 제외 · 닥터리쥬올 편입) ──────────────────────
BRAND_ZONES = {
    "G5-ER": dict(brand="닥터리쥬올", maker="Dr.Reju-All",
                  claim="PDRN 재생 스킨케어",
                  why="이 엔드의 역할이 'PDRN 제품 구분'. 자사 전용 모듈 G5-D-1과 인접해 "
                      "G5에 브랜드 코너를 형성한다. 국내 약 5,000개 약국 유통·약국 채널 대표 PDRN 브랜드.",
                  evidence="공식몰 및 유통 자료(2026-09 확인) · 약국 채널 중심", ch=3, pt=3),
    "G1-EL": dict(brand="리쥬비(-넥스·-에스)", maker="파마리서치",
                  claim="PDRN 의약품·화장품 구분",
                  why="여드름 상태 선택 엔드에서 '여드름 후 흉터·재생' 상담으로 연결. "
                      "의약품 리쥬비넥스(W1)와 화장품 리쥬비-에스를 같은 브랜드로 대조 설명 가능.",
                  evidence="파마리서치 제품 구분 자료(원본 07_실행기준 인용)", ch=3, pt=3),
    "G5-EL": dict(brand="프로캄", maker="한미사이언스", claim="EGF·멜라·아크페어",
                  why="11개 모듈에 걸친 다축 배치. 고민 길찾기 엔드와 정합.",
                  evidence="한미사이언스 공식 라인(원본 04 인용)", ch=3, pt=3),
    "G2-ER": dict(brand="케어리브", maker="일동제약(니치반 브랜드)", claim="습윤 밴드·하이드로콜로이드",
                  why="선정 SKU 18건으로 최다. G2-ER에 이미 본진.",
                  evidence="일동제약 유통 · 약국 상처 밴드 카테고리 대표(2026-09 확인)", ch=3, pt=3),
    "G2-EL": dict(brand="이지덤", maker="대웅제약", claim="습윤 드레싱",
                  why="케어리브와 소재·부위 비교 구도.", evidence="대웅제약 공식", ch=3, pt=3),
    "G4-ER": dict(brand="고려은단", maker="고려은단", claim="약국 비타민",
                  why="G4-ER에 이미 본진. 약국 채널 비타민 대표.", evidence="원본 04", ch=3, pt=2),
    "G4-EL": dict(brand="에버콜라겐", maker="뉴트리", claim="먹는 콜라겐",
                  why="이너뷰티 단일 축.", evidence="원본 04", ch=2, pt=3),
    "G3-EL": dict(brand="마데카파마시아", maker="동국제약", claim="센텔라·재생",
                  why="G3-D-3 선케어와 연결.", evidence="동국제약 제조사 공식(원본 04)", ch=3, pt=3),
    "G6-ER": dict(brand="신신", maker="신신제약", claim="파스·외용",
                  why="L3·G6-U-1 본진과 연결.", evidence="원본 04", ch=3, pt=3),
    "G3-ER": dict(brand=None, claim="", maker="", ch=0, pt=0,
                  why="두피·휴식 테마. 르디퍼가 두피·헤어 라인을 함께 공급하면 1순위 후보. "
                      "현재 선정된 르디퍼 4건은 전부 RX 스킨케어라 G5-D-3으로 배정했다.",
                  evidence="르디퍼 약국 전용 RX 라인 및 두피·헤어 라인 운영(2026-09 확인)"),
    "G1-ER": dict(brand=None, claim="", maker="", ch=0, pt=0,
                  why="엠디스픽이 9건 배치되어 있으나 제조·채널 미확인. 확인 후 재검토.", evidence=""),
    "G6-EL": dict(brand=None, claim="", maker="", ch=0, pt=0,
                  why="립·눈 테마 전용 전문 채널 브랜드 후보 없음.", evidence=""),
}
EXCLUDED = {"아크로패스": "사용자 지정 제외. 선정 SKU 4건은 G1-D-2·B1 본진 배치를 유지한다."}

els = {e.get("code"): e for e in layout["elements"] if e.get("code")}
applied = 0
for mod, b in BRAND_ZONES.items():
    e = els.get(mod)
    if not e:
        continue
    z = e.setdefault("zoning", {})
    if not b["brand"]:
        z.pop("brandZone", None)
        continue
    z["brandZone"] = {k: b[k] for k in ("brand", "maker", "claim", "why", "evidence")}
    z["brandZone"]["channelTier"] = b["ch"]
    z["brandZone"]["pointTier"] = b["pt"]
    z["brandZone"]["levels"] = [2, 3, 4, 5]
    z["brandZone"]["status"] = "제안 · 거래조건 미확인"
    for i in range(1, 5):                       # levelDetails[0]=S1(안내) 제외
        if i < len(e.get("levelDetails", [])):
            d = e["levelDetails"][i]
            d["brandZone"] = b["brand"]
            d["note"] = f"[브랜드존] {b['brand']} · {b['claim']} | " + str(d.get("note", ""))
            applied += 1
    e["note"] = f"[브랜드존] {b['brand']} ({b['maker']}) · {b['claim']}\n" + str(e.get("note", ""))

# ── ② 슬라이딩 도어 (간섭 없음) ─────────────────────────────────────
S = layout["store"]
layout["elements"] = [e for e in layout["elements"] if e.get("code") not in ("DR-L", "DR-R")]
for cid, name, x in (("DR-L", "좌측 슬라이딩 도어 4m", 0), ("DR-R", "우측 슬라이딩 도어 4m", S["w"] - 4000)):
    layout["elements"].append(dict(
        id=f"door_{cid}", type="door", name=name, code=cid, x=x, y=S["h"] - 120,
        w=4000, h=120, zHeight=2400, bays=1, levels=1, zone="공용동선",
        category="출입구", categoryZone="공용동선", opacity=1, rotation=0,
        locked=False, hidden=False, levelDetails=[],
        note="하단 좌·우 각 4,000mm 슬라이딩 도어. 미닫이 방식이라 B열 진열과 간섭 없음(사용자 확인)."))

# ── ③ 추가 배정 반영 ────────────────────────────────────────────────
add_by_mod = collections.defaultdict(list)
for r in A["assignments"]:
    add_by_mod[r["module"]].append(r)
for r in A["pass2"]["assignments"]:
    add_by_mod[r["module"]].append(r)
for mod, items in add_by_mod.items():
    e = els.get(mod)
    if not e:
        continue
    z = e.setdefault("zoning", {})
    z["additionalAssignments"] = [
        dict(code=i["code"], name=i["name"], group=i.get("group", ""),
             importance=i["importance"], facing=i["facing"],
             reason=i["reason"], condition=i["condition"]) for i in items]
    z["openingSkuCountAfter"] = (z.get("openingSkuCount") or 0) + len(items)

# ── ④ 포장 치수 가이드 (실측 대체) ───────────────────────────────────
GUIDE = {
    "basis": "포장 실측이 어려운 상황에서 페이싱 수를 정하기 위한 폭 구간 가이드. "
             "SKU별 입력 대신 이 4개 구간 중 하나를 고르면 된다.",
    "shelfEffectiveWidthMm": {"일반 모듈": 865, "엔드캡": 645},
    "classes": [
        dict(id="S", label="소형", examples="스틱·앰플·립·소형 튜브", widthMm="20~35",
             perShelf865="24~43F", perShelf645="18~32F"),
        dict(id="M", label="중형", examples="크림 30~50ml·연고·정제 박스", widthMm="40~60",
             perShelf865="14~21F", perShelf645="10~16F"),
        dict(id="L", label="대형", examples="로션 100~200ml·세럼 박스·밴드 대용량", widthMm="70~100",
             perShelf865="8~12F", perShelf645="6~9F"),
        dict(id="XL", label="특대", examples="선물세트·대용량 홍삼·기기", widthMm="120~180",
             perShelf865="4~7F", perShelf645="3~5F"),
    ],
    "targetFillRate": 0.70,
    "targetRule": "선반 목표 충전율 70% 기준 → 일반 모듈 605mm, 엔드캡 450mm를 채우는 F를 배정한다.",
    "heightLimits": {"W-S1": 440, "W-S2~S4": 270, "W-S5": 310,
                     "G·E-S1": 80, "G·E-S2~S5": 200,
                     "note": "06_집기치수20의 개구 높이에서 여유 20mm를 뺀 값. "
                             "S1(곤돌라·엔드)은 80mm라 대부분의 상품이 들어가지 않는다."},
    "practicalNote": "모든 칸을 실제 진열처럼 채우는 것은 초도에 현실적이지 않다. "
                     "S2·S3를 70%로 먼저 채우고, S4·S5는 40~50%에서 시작해 2주 후 조정하는 것을 권한다.",
}

doc = layout["project"].setdefault("zoningDocumentation", {})
doc["revision2"] = dict(
    date=datetime.date.today().isoformat(),
    resolved=[
        "하단 좌·우 4,000mm는 슬라이딩 도어로 확인 — B열 진열과 간섭 없음.",
        "X5 기둥 없음 — 중앙 1,000mm는 통로.",
        "오픈 선정 '예' 695건 중 미배치 384건을 추가 검토해 347건 배정.",
        "브랜드존에서 아크로패스를 제외하고 닥터리쥬올을 G5-ER에 편입.",
    ],
    packagingGuide=GUIDE,
    brandZoneExcluded=EXCLUDED,
    hold=dict(count=len(A["pass2"]["hold"]),
              reason="캔디·간식 29건은 약국 포지셔닝 판단 필요, 8건은 상품명으로 용도 판별 불가."),
)
layout["project"]["name"] = "관광형 약국 · 전체 조닝 · 오픈 배정본"
json.dump(layout, open('data/kpharmacy-open-final-layout.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print(f"브랜드존 {sum(1 for b in BRAND_ZONES.values() if b['brand'])}개 엔드캡 · {applied}칸 표기")
print(f"추가 배정 반영 모듈 {len(add_by_mod)}개 · 총 {sum(len(v) for v in add_by_mod.values())}건")
print(f"슬라이딩 도어 2개 · 포장 가이드 {len(GUIDE['classes'])}구간")
print("→ data/kpharmacy-open-final-layout.json")
json.dump(dict(schema="kpharmacy.openplan/1.0", generatedAt=datetime.date.today().isoformat(),
               brandZones={k: v for k, v in BRAND_ZONES.items()},
               excluded=EXCLUDED, packagingGuide=GUIDE,
               assignment=dict(counts=A["counts"], hold=A["pass2"]["hold"])),
          open('data/open-plan-summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("→ data/open-plan-summary.json")
