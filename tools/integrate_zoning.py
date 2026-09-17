# -*- coding: utf-8 -*-
"""통합안 생성기.

기준(base)   : 업로드된 도면 기반 모델 (실측 치수·평면도·315선반 원본 보존)
보강(overlay): 카탈로그 2,526품목의 모듈별 배정 수와 운영상태 1급 필드화

원칙
  ① 도면에서 읽은 치수는 건드리지 않는다. 951·1000mm 통로도 넓히지 않는다.
  ② 안내 70칸·조건부 70칸의 빈 category 를 채우지 않는다(상품 타일 방지).
  ③ 원본 선반 정보(sourceShelves)는 한 필드도 버리지 않는다.
"""
import json, collections, re, datetime

UPLOAD = 'data/uploaded-drawing-model.json'
CATALOG = 'data/kpharmacy-zoning-63.json'
OUT = 'data/kpharmacy-zoning-63.integrated.json'

up = json.load(open(UPLOAD, encoding='utf-8'))
cat = json.load(open(CATALOG, encoding='utf-8'))

sku_by_module = {m["id"]: m["skuCandidates"] for m in cat["modules"]}
THEME_KO = {t["ko"]: t["id"] for t in cat["taxonomy"]["themes"]}
STATUS_ID = {"상설 선택": "permanent", "교체 전시": "rotating",
             "조건부 확장": "conditional", "안내": "info"}
FACING = {"더마·세정·선케어": 85, "피부약·상처 보호": 55, "일반약·여행·생활": 60,
          "영양·건강 선물": 75, "립·눈·다리·구강": 45, "추천·상담 안내": 85}
PANEL = 60

def capacity(width, theme):
    return max(1, int(max(120, width - PANEL) // FACING.get(theme, 75)))

modules, fixtures = [], {}
for e in up["elements"]:
    z = e.get("zoning")
    if not z:
        continue
    code = e.get("code") or z.get("moduleId")
    theme = z.get("theme", "")
    shelves = []
    for s in (z.get("sourceShelves") or []):
        shelves.append({
            "id": s.get("sourceId"),
            "level": s.get("sourceTopDownShelf"),
            "simulatorLevel": s.get("simulatorBottomUpLevel"),
            "status": STATUS_ID.get(str(s.get("status", "")).strip(), "info"),
            "statusKo": s.get("status"),
            "symptom": s.get("need") or "",
            "group": s.get("productGroup") or "",
            "examples": [v.strip() for v in re.split(r"[\n,]", s.get("representativeCandidates") or "") if v.strip()],
            "supplyCodes": [v.strip() for v in re.split(r"[\n,]", s.get("sourceSupplierCodes") or "") if v.strip()],
            "alternates": s.get("alternativeCandidates") or "",
            "criteria": s.get("selectionNotes") or "",
            "evidence": s.get("sourceEvidence") or "",
            "mappedCategory": s.get("mappedCategory") or "",
            "mappedZone": s.get("mappedZone") or "",
        })
    perm = sum(1 for s in shelves if s["status"] == "permanent")
    per = capacity(max(e["w"], e["h"]), theme)
    sku = sku_by_module.get(code, 0)
    fx = z.get("physicalFixtureId")
    if fx and fx not in fixtures:
        fixtures[fx] = {"id": fx, "type": "gondola" if fx.startswith("G") else "wall",
                        "modules": []}
    if fx:
        fixtures[fx]["modules"].append(code)
    modules.append({
        "id": code,
        "fixture": fx,
        "bay": z.get("physicalBay"),
        "face": z.get("face"),
        "name": e.get("name"),
        "title": z.get("fixtureTitle"),
        "theme": THEME_KO.get(theme, "guide"),
        "themeKo": theme,
        "brandOps": z.get("brandOperation") or "",
        "geometry": {
            "x": e["x"], "y": e["y"], "w": e["w"], "d": e["h"],
            "h": e["zHeight"], "rotation": e.get("rotation", 0),
            "status": "drawing-derived" if fx else "assumed",
            "heightBasis": z.get("heightBasis") or "",
        },
        "capacity": {
            "permanentShelves": perm,
            "perShelf": per,
            "total": perm * per,
            "facingWidthMm": FACING.get(theme, 75),
            "basis": f"유효폭 {max(120, max(e['w'], e['h']) - PANEL)}mm ÷ 페이싱 {FACING.get(theme, 75)}mm",
        },
        "skuCandidates": sku,
        "loadRatio": round(sku / (perm * per), 2) if perm * per else None,
        "shelves": shelves,
    })

th = collections.defaultdict(lambda: dict(mod=0, perm=0, cap=0, sku=0))
for m in modules:
    v = th[m["themeKo"]]
    v["mod"] += 1; v["perm"] += m["capacity"]["permanentShelves"]
    v["cap"] += m["capacity"]["total"]; v["sku"] += m["skuCandidates"]

doc = {
    "schema": "kpharmacy.zoning/1.1",
    "meta": {
        "project": "K-Pharmacy 전체 매장 조닝 · 통합안",
        "variant": "integrated",
        "baseDate": "2026-09-12",
        "generatedAt": datetime.date.today().isoformat(),
        "units": "mm",
        "levelOrder": "topDown",
        "levelOrderNote": "shelves[].level 은 원안 S1(최상단) 기준. simulatorLevel 은 앱의 하단기준 표기.",
        "geometryStatus": "drawing-derived",
        "geometryNote": "좌표·폭은 제공 평면도 치수열에서 산출. 깊이·높이는 미실측 가정치.",
        "composition": {
            "base": "업로드 도면 기반 모델 — 실측 치수 · 평면도 배경 · 315선반 원본",
            "overlay": "카탈로그 2,526품목의 모듈별 배정 수 · 운영상태 1급 필드 · 페이싱 기반 수용력",
        },
        "counts": {
            "modules": len([m for m in modules if m["id"] != "RF1"]),
            "shelves": sum(len(m["shelves"]) for m in modules if m["id"] != "RF1"),
            "refrigeratorModules": 1,
            "skus": len(cat.get("skus", [])),
        },
        "capacityModel": {
            "sidePanelMm": PANEL,
            "facingWidthMm": FACING,
            "note": "전부 가정치. 실물 집기 유효폭과 실제 포장 폭 확인 후 교체할 것.",
        },
        "disclaimer": cat["meta"]["disclaimer"],
    },
    "store": up["store"] | {"backgroundImage": "생략(업로드 원본에 포함)"},
    "floorContext": {
        "source": "해당 층 전체 건축도면 (2026-09-17 제공)",
        "floor": "2F (도면 집기 태그 P-2F-xx 기준)",
        "buildingGrid": {
            "axes": ["X1", "X2", "X3", "X4", "X5", "X6", "X7"],
            "totalWidthMm": 31650,
            "baySpacingMm": [5050, 5400, 5400, 5400, 5400, 5000],
            "note": "5,400mm 반복 = 표준 기둥 그리드. 약국은 X4~X6 2베이를 점유하는 것으로 읽힘(미확인).",
        },
        "tenancy": {
            "assumedSpan": "X4 ~ X6",
            "gridSpanMm": 10800,
            "interiorWidthMm": 10512,
            "wallAllowanceMm": 288,
            "perSideMm": 144,
            "confidence": "arithmetic-fit / 도면 대조 필요",
        },
        "adjacency": {
            "front(하단)": "하부 OPEN 아트리움 보이드. 좌·우 개방 진입 2개소(1,502 / 1,490mm)",
            "right(우측)": "화장실(남) · 승강기 · MIRROR · AV — 상시 통행 코어",
            "left(좌측)": "인접 테넌트(자체 진열 그리드 1,320×1,400) · 에스컬레이터/계단 코어(UP·DN)",
            "rear(상단)": "조제실 · POS 4대 · 후방 업무",
        },
        "verifyOnDrawing": [
            {
                "id": "V1",
                "item": "중앙 1,000mm 간격의 X5 기둥 유무",
                "finding": "X5 그리드선이 중앙 간격(x 4,756~5,756)의 정중앙에 떨어짐(편차 0mm).",
                "impact": "기둥이면 좌우 횡단 불가. 통로가 아니라 기둥 이격으로 보아야 하며 동선 모델이 바뀐다.",
                "ifColumn": {"400mm": "잔여 300+300", "500mm": "잔여 250+250", "600mm": "잔여 200+200"},
            },
            {
                "id": "V2",
                "item": "P-2F-01 ~ P-2F-08 집기 타입 코드",
                "finding": "도면에 집기 타입 태그가 있으나 조닝 코드(W/L/B/G)와 연결되지 않음.",
                "impact": "발주 수량·사양 산출 시 타입별 집계가 필요.",
            },
            {
                "id": "V3",
                "item": "가로 치수열 6mm 불일치",
                "finding": "상·하단 치수열 합이 약 6mm 다름. 하단 10,512mm를 기준으로 채택.",
                "impact": "우측 이격이 1,360(도면) vs 1,366(모델)으로 갈림. 실측 시 확정.",
            },
        ],
    },
    "drawingDimensions": up["project"]["zoningDocumentation"].get("confirmedDrawingDimensionsMm"),
    "derivedDimensions": up["project"]["zoningDocumentation"].get("derivedDimensionsMm"),
    "assumedDimensions": up["project"]["zoningDocumentation"].get("assumedDimensionsMm"),
    "geometryLimits": up["project"]["zoningDocumentation"].get("geometryLimits"),
    "taxonomy": cat["taxonomy"],
    "fixtures": list(fixtures.values()),
    "modules": modules,
    "themeSummary": {k: dict(v, fill=round(v["cap"] / v["sku"], 3) if v["sku"] else None)
                     for k, v in th.items()},
    "unplacedSkus": cat.get("unplacedSkus", {}),
    "faceLevelSkus": cat.get("faceLevelSkus", {}),
    "brands": cat.get("brands", []),
    "references": cat.get("references", []),
}
doc["store"].pop("bg", None)
json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print(f"조닝 모듈 {len(modules)}개 · 선반 {sum(len(m['shelves']) for m in modules)}칸 "
      f"(냉장 RF1 5칸은 원안 315칸에 미포함)")
print(f"\n{'주테마':<14}{'모듈':>4}{'상설':>5}{'수용':>6}{'SKU':>6}{'충족률':>8}")
for k, v in sorted(th.items(), key=lambda x: -x[1]["sku"]):
    print(f"{k:<14}{v['mod']:>4}{v['perm']:>5}{v['cap']:>6}{v['sku']:>6}"
          f"{(v['cap']/v['sku']*100 if v['sku'] else 0):>7.0f}%")
tc = sum(v["cap"] for v in th.values()); ts = sum(v["sku"] for v in th.values())
print(f"{'합계':<14}{sum(v['mod'] for v in th.values()):>4}"
      f"{sum(v['perm'] for v in th.values()):>5}{tc:>6}{ts:>6}{tc/ts*100:>7.0f}%")

# ── 시뮬레이터에 바로 올라가는 레이아웃본 ──────────────────────────────
# 업로드 모델을 그대로 두고 zoning.skuCandidates 만 주입한다.
# 앱의 hydrateZoning() 이 이를 읽어 적재 진단과 운영상태 표시를 켠다.
layout = json.load(open(UPLOAD, encoding='utf-8'))
injected = 0
for e in layout["elements"]:
    z = e.get("zoning")
    if not z:
        continue
    code = e.get("code") or z.get("moduleId")
    if code in sku_by_module:
        z["skuCandidates"] = sku_by_module[code]
        injected += 1
layout["project"]["name"] = "관광형 약국 · 전체 조닝 · 통합안"
layout["project"]["zoningDocumentation"]["integration"] = {
    "base": "업로드 도면 기반 모델(실측 치수·평면도·315선반 원본)",
    "added": "카탈로그 2,526품목의 모듈별 배정 수(zoning.skuCandidates)",
    "effect": "앱의 운영상태 표시·적재 과부하 진단이 이 파일에서 동작한다.",
    "capacityModel": {"sidePanelMm": PANEL, "facingWidthMm": FACING,
                      "note": "모듈 실폭 − 측판 ÷ 포장별 페이싱 폭. 전부 가정치."},
    "unchanged": ["좌표", "치수", "안내·조건부 칸의 빈 category", "sourceShelves 원본"],
}
json.dump(layout, open('data/kpharmacy-integrated-layout.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"\n레이아웃본: zoning.skuCandidates 주입 {injected}개 모듈 → data/kpharmacy-integrated-layout.json")
