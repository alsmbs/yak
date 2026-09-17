# -*- coding: utf-8 -*-
"""Pharmacy_Full_Zoning 엑셀 → kpharmacy.zoning/1.0 JSON 변환기.
치수는 원본에서 미실측이므로 geometry.status = "assumed" 로 표기하고
params 블록의 값만 바꾸면 전체 배치가 다시 계산되도록 구성한다."""
import openpyxl, collections, re, json, datetime

SRC = 'Pharmacy_Full_Zoning_Shelf_Operations.xlsx'  # 엑셀 경로로 교체
wb = openpyxl.load_workbook(SRC, data_only=True)

THEMES = [
    ("skin-rx",   "피부약·상처 보호",  "#D92D20"),
    ("derma",     "더마·세정·선케어",  "#E64291"),
    ("otc-life",  "일반약·여행·생활",  "#0098C9"),
    ("nutrition", "영양·건강 선물",    "#F47A25"),
    ("lip-eye",   "립·눈·다리·구강",   "#7A3AA8"),
    ("guide",     "추천·상담 안내",    "#F4CC32"),
]
THEME_ID = {ko: i for i, ko, _ in THEMES}
STATUSES = [
    ("permanent",   "상설 선택",   "#039855"),
    ("rotating",    "교체 전시",   "#F79009"),
    ("conditional", "조건부 확장", "#2E90FA"),
    ("info",        "안내",       "#98A2B3"),
]
STATUS_ID = {ko: i for i, ko, _ in STATUSES}
FACES = [
    ("wall-top",  "W", "상단 벽면"),
    ("wall-left", "L", "좌측 벽면"),
    ("entry",     "B", "하단·진입"),
    ("gondola-D", "G-D", "입구 방향 하면"),
    ("gondola-U", "G-U", "POS 방향 상면"),
    ("end-left",  "G-EL", "도면 왼쪽 엔드"),
    ("end-right", "G-ER", "도면 오른쪽 엔드"),
]

def split(v):
    if v is None: return []
    return [s.strip() for s in str(v).split("\n") if s.strip()]

# ---------- 원본 읽기 ----------
zrows = [r for r in list(wb['01_전체조닝63'].iter_rows(values_only=True))[6:]
         if r[0] and r[0] != '합계']
srows = [r for r in list(wb['02_선반315'].iter_rows(values_only=True))[6:] if r[0]]
prows = [r for r in list(wb['03_상품분류2526'].iter_rows(values_only=True))[6:] if r[0]]
brows = [r for r in list(wb['04_브랜드검토'].iter_rows(values_only=True))[6:] if r[0]]

# SKU → 모듈 적재량
MODRE = re.compile(r'\b([WLB]\d|G\d-[UD]-\d|G\d-[UD]|G\d-E[LR])\b')
load, face_load, unplaced = collections.Counter(), collections.Counter(), collections.Counter()
for r in prows:
    m = MODRE.search((r[6] or "").strip())
    if not m: unplaced[(r[6] or "").strip()] += 1
    elif re.fullmatch(r'G\d-[UD]', m.group(1)): face_load[m.group(1)] += 1
    else: load[m.group(1)] += 1

shelves_by_mod = collections.defaultdict(list)
for r in srows: shelves_by_mod[r[1]].append(r)

# ---------- 파라메트릭 배치(가정치) ----------
# 실측 전 기준 치수. 곤돌라 열 간격 · 벽면 이격이 minAisle 을 만족하도록 잡았다.
P = dict(storeW=15400, storeH=12200, ceiling=2700, minAisle=1300,
         wallDepth=400, gondolaDepth=900, moduleW=1300, endW=450,
         shelfH=2100, gondolaH=1650, endH=1500, levels=5,
         gondolaPitch=2300, gondolaTop=2300, wallGap=1400)
SW, SH = P["storeW"], P["storeH"]
WD, GD, MW, EW = P["wallDepth"], P["gondolaDepth"], P["moduleW"], P["endW"]

fixtures, modules = [], []
geo = {}   # module id -> (x, y, w, d, h, rotation)

# 상단 벽면 W1-W5
for i in range(5):
    geo[f"W{i+1}"] = (800 + i * 1640, 200, 1640, WD, P["shelfH"], 0)
# 좌측 벽면 L1-L4 (세로 방향 진열면)
for i in range(4):
    geo[f"L{i+1}"] = (200, 2400 + i * 1800, WD, 1800, P["shelfH"], 0)
# 하단 진입 B1-B8 (좌측 4 · 우측 4, 가운데는 진입 동선으로 비움)
BY = P["storeH"] - 700
for i in range(4):
    geo[f"B{i+1}"] = (2400 + i * 1240, BY, 1240, WD, P["shelfH"], 0)
for i in range(4):
    geo[f"B{i+5}"] = (8600 + i * 1240, BY, 1240, WD, P["shelfH"], 0)

# 곤돌라: 왼쪽 4대(G1-G4) · 오른쪽 2대(G5-G6). 열 간격 = gondolaPitch − gondolaDepth = 1,400mm
TOP, PITCH = P["gondolaTop"], P["gondolaPitch"]
GPOS = {"G1": (2400, TOP), "G2": (2400, TOP + PITCH),
        "G3": (2400, TOP + PITCH * 2), "G4": (2400, TOP + PITCH * 3),
        "G5": (8600, TOP + PITCH * 2), "G6": (8600, TOP + PITCH * 3)}
for g, (gx, gy) in GPOS.items():
    nmod = 2 if g == "G4" else 3
    length = nmod * MW
    fixtures.append({"id": g, "type": "gondola", "x": gx, "y": gy,
                     "w": length, "d": GD, "h": P["gondolaH"],
                     "moduleCount": nmod,
                     "faces": [f"{g}-D", f"{g}-U", f"{g}-EL", f"{g}-ER"]})
    for i in range(nmod):
        # D면 = 입구 방향(도면 아래), U면 = POS 방향(도면 위)
        geo[f"{g}-U-{i+1}"] = (gx + i * MW, gy, MW, GD / 2, P["gondolaH"], 0)
        geo[f"{g}-D-{i+1}"] = (gx + i * MW, gy + GD / 2, MW, GD / 2, P["gondolaH"], 0)
    geo[f"{g}-EL"] = (gx - EW, gy, EW, GD, P["endH"], 0)
    geo[f"{g}-ER"] = (gx + length, gy, EW, GD, P["endH"], 0)

def face_of(mid):
    if mid[0] == "W": return "wall-top"
    if mid[0] == "L": return "wall-left"
    if mid[0] == "B": return "entry"
    if mid.endswith("-EL"): return "end-left"
    if mid.endswith("-ER"): return "end-right"
    return "gondola-D" if "-D-" in mid else "gondola-U"

# ---------- 모듈 조립 ----------
for r in zrows:
    mid = r[0]
    x, y, w, d, h, rot = geo[mid]
    face = face_of(mid)
    fixture = mid.split("-")[0] if mid[0] == "G" else mid
    sh = sorted(shelves_by_mod.get(mid, []), key=lambda s: s[3])
    shelves = []
    for s in sh:
        shelves.append({
            "id": s[0], "level": s[3],
            "status": STATUS_ID.get(s[10], "info"),
            "symptom": s[5] or "", "group": s[6] or "",
            "examples": split(s[7]), "supplyCodes": split(s[8]),
            "alternates": s[9] or "", "criteria": s[13] or "",
            "evidence": s[14] or "",
            "confirmedName": s[11] or "", "confirmedCode": s[12] or "",
        })
    modules.append({
        "id": mid, "fixture": fixture, "face": face,
        "index": int(mid.rsplit("-", 1)[1]) if re.search(r'-[UD]-\d$', mid) else None,
        "name": r[3] or "", "theme": THEME_ID.get(r[2], "guide"),
        "role": r[4] or "", "brandOps": r[5] or "", "note": r[16] or "",
        "geometry": {"x": round(x), "y": round(y), "w": round(w), "d": round(d),
                     "h": round(h), "rotation": rot, "status": "assumed"},
        "skuCandidates": load.get(mid, 0),
        "shelves": shelves,
    })

skus = [{"code": r[0], "sourceRow": r[1], "name": r[2], "spec": r[3] or "",
         "category": r[4] or "", "group": r[5] or "", "primary": (r[6] or "").strip(),
         "shelf": r[7] or "", "decision": r[8] or "", "confirmed": r[9] or "",
         "compliance": r[10] or "", "issue": r[11] or ""} for r in prows]
# 04 시트 후반부는 브랜드가 아니라 '자료 근거' 표이므로 분리한다(브랜드 36 + 근거 9).
cut = next((i for i, r in enumerate(brows) if r[1] == "자료명"), len(brows))
brands = [{"brand": r[0], "role": r[1], "lineup": r[2] or "", "placement": r[3] or "",
           "checks": r[4] or "", "evidence": r[5] or "", "photo": r[6] or "",
           "decision": r[7] or "", "url": r[8] or ""} for r in brows[:cut]]
references = [{"kind": r[0], "title": r[1], "detail": r[2] or "", "caveat": r[3] or "",
               "url": r[8] or ""} for r in brows[cut + 1:]]

doc = {
    "schema": "kpharmacy.zoning/1.0",
    "meta": {
        "project": "K-Pharmacy 전체 매장 조닝",
        "baseDate": "2026-09-12",
        "generatedAt": datetime.date.today().isoformat(),
        "units": "mm",
        "levelOrder": "topDown",
        "levelOrderNote": "S1 = 최상단, S5 = 최하단 (원본 문서 표기 기준)",
        "geometryStatus": "assumed",
        "geometryNote": "원본에서 집기 유효폭·깊이·높이는 미실측. params 값을 실측치로 교체하면 전체 좌표가 재계산된다.",
        "counts": {"faces": 41, "modules": len(modules),
                   "shelves": sum(len(m["shelves"]) for m in modules),
                   "skus": len(skus), "brands": len(brands), "references": len(references)},
        "sources": [
            "Pharmacy_Full_Zoning_20260912.pdf (20p)",
            "Pharmacy_Full_Zoning_Shelf_Operations.xlsx (4시트)",
            "무신사뷰티 초기 취급검토 품목 전체 리스트.xls (원본 2,526행)",
        ],
        "disclaimer": "운영 제안 자료. 재고·공급가·국내 판매규격·허가 분류·실물 치수는 미확정이며 법정 기준 판정을 대신하지 않는다.",
    },
    "params": P,
    "store": {"w": SW, "h": SH, "ceiling": P["ceiling"], "minAisle": P["minAisle"],
              "entrances": [{"id": "ENT-L", "name": "좌측 진입", "x": 600, "y": SH - 220, "w": 1200, "d": 220},
                            {"id": "ENT-R", "name": "우측 진입", "x": 13800, "y": SH - 220, "w": 1400, "d": 220}],
              "backOffice": [
                  {"id": "BOH-RX", "name": "조제실", "x": 9800, "y": 200, "w": 5400, "d": 1900, "h": 2400},
                  {"id": "BOH-POS", "name": "POS · 결제 · TAX REFUND", "x": 9800, "y": 3100, "w": 3200, "d": 800, "h": 1050},
                  {"id": "BOH-FRIDGE", "name": "냉장고", "x": 14300, "y": 3100, "w": 1000, "d": 800, "h": 1900},
              ],
              "zones": [
                  {"id": "Z-BOH", "name": "조제·BOH", "zone": "조제·BOH",
                   "x": 9600, "y": 100, "w": 5700, "d": 4000,
                   "note": "조제·결제·환급·냉장 보관. 315구획에 포함하지 않는 보조 공간."},
                  {"id": "Z-ENTRY", "name": "진입 탐색", "zone": "공용동선",
                   "x": 300, "y": SH - 900, "w": SW - 600, "d": 800,
                   "note": "좌·우 진입 고객의 탐색 구간(B1-B8). 중앙은 통행로."},
              ]},
    "taxonomy": {
        "themes": [{"id": i, "ko": ko, "color": c} for i, ko, c in THEMES],
        "statuses": [{"id": i, "ko": ko, "color": c} for i, ko, c in STATUSES],
        "faces": [{"id": i, "code": c, "ko": ko} for i, c, ko in FACES],
    },
    "fixtures": fixtures,
    "modules": modules,
    "faceLevelSkus": dict(face_load),
    "unplacedSkus": dict(unplaced),
    "skus": skus,
    "brands": brands,
    "references": references,
}
json.dump(doc, open('data/kpharmacy-zoning-63.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("modules:", len(modules), "shelves:", doc["meta"]["counts"]["shelves"],
      "skus:", len(skus), "brands:", len(brands), "refs:", len(references))
print("면단위 미지정:", face_load, "| 모듈외:", sum(unplaced.values()))
