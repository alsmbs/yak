# -*- coding: utf-8 -*-
"""기준안(63모듈) → 최적화안 변환.
원칙: ① 집기는 이동하지 않는다(실측 전) ② '안내' 선반은 상설로 바꾸지 않는다
      ③ 저활용 피부약 모듈을 통합해 확보한 자리만 더마 고민축으로 넘긴다."""
import json, copy, collections

SRC = 'data/kpharmacy-zoning-63.json'
d = json.load(open(SRC, encoding='utf-8'))
mods = {m["id"]: m for m in d["modules"]}
THEME = {t["id"]: t["ko"] for t in d["taxonomy"]["themes"]}
CAP = 14

def perm(m): return sum(1 for s in m["shelves"] if s["status"] == "permanent")
def summarize(doc, label):
    t = collections.defaultdict(lambda: dict(perm=0, sku=0, mod=0))
    for m in doc["modules"]:
        v = t[m["theme"]]; v["perm"] += perm(m); v["sku"] += m["skuCandidates"]; v["mod"] += 1
    print(f"\n[{label}]")
    print(f"{'주테마':<14}{'모듈':>4}{'상설':>5}{'SKU':>6}{'수용':>6}{'충족률':>8}")
    for k, v in sorted(t.items(), key=lambda x: -x[1]["sku"]):
        cap = v["perm"] * CAP
        print(f"{THEME[k]:<14}{v['mod']:>4}{v['perm']:>5}{v['sku']:>6}{cap:>6}"
              f"{(cap/v['sku']*100 if v['sku'] else 0):>7.0f}%")
    return t

summarize(d, "기준안 AS-IS")
o = copy.deepcopy(d)
om = {m["id"]: m for m in o["modules"]}
changes = []

def set_status(mid, level, status, why):
    s = next(x for x in om[mid]["shelves"] if x["level"] == level)
    if s["status"] == "info":
        raise SystemExit(f"안내 선반은 전환 금지: {mid}/S{level}")
    old = s["status"]; s["status"] = status
    changes.append({"module": mid, "shelf": f"S{level}", "from": old, "to": status, "why": why})

def retheme(mid, theme, name, role, note):
    m = om[mid]
    changes.append({"module": mid, "from": f"{THEME[m['theme']]} · {m['name']}",
                    "to": f"{THEME[theme]} · {name}", "why": note})
    m["theme"] = theme; m["name"] = name; m["role"] = role
    m["note"] = note

# ── ① 저활용 피부약 모듈 통합 → 더마 고민축 확장분 확보 ──────────────
# 모듈 전체를 다른 테마로 전용하는 경우에는 선반 역할도 새로 정의한다.
# 기준안의 설계 언어를 따라 S1은 선택 안내, S2-S5는 상설로 둔다.
def repurpose(mid, theme, name, role, note, pattern):
    m = om[mid]
    changes.append({"module": mid,
                    "from": f"{THEME[m['theme']]} · {m['name']} (상설 {perm(m)}단)",
                    "to": f"{THEME[theme]} · {name} (상설 {pattern.count('permanent')}단)",
                    "why": note})
    m["theme"] = theme; m["name"] = name; m["role"] = role; m["note"] = note
    for s, st in zip(sorted(m["shelves"], key=lambda x: x["level"]), pattern):
        s["status"] = st

PATTERN = ["info"] + ["permanent"] * 4
repurpose("G2-D-2", "derma", "A  피지·모공 확장", "Pores & Sebum (ext.)",
          "실리콘 흉터관리는 G2-D-1로 통합. 확보한 모듈을 G1-D-3(A축) 위성으로 전환.", PATTERN)
repurpose("G2-U-3", "derma", "B  잡티·피부 톤 확장", "Spots & Tone (ext.)",
          "습윤·상처 세정은 G2-U-1로 통합. 확보한 모듈을 G3-D-2(B축) 위성으로 전환.", PATTERN)
# 통합 수용처에 상설 1단씩 보강(조건부 → 상설)
set_status("G2-D-1", 5, "permanent", "실리콘 겔 통합 수용")
set_status("G2-U-1", 4, "permanent", "습윤·소독 통합 수용")

# ── ② 과적 더마·영양 모듈의 '조건부 확장' → '상설 선택' ───────────────
for mid, lvs, why in [
    ("G5-D-2", [4, 5], "E 주름·탄력 4.2배 과적 해소"),
    ("G5-U-2", [4, 5], "D 민감·진정 2.9배 과적 해소"),
    ("G3-D-2", [4], "B 잡티·톤 3.1배 과적 해소"),
    ("G3-D-3", [4, 5], "선케어 2.1배 과적 해소"),
    ("G1-U-1", [5], "세안 2.1배 과적 해소"),
    ("G5-U-3", [5], "수분·전신 보습 2.0배 과적 해소"),
    ("G4-U-1", [5], "콜라겐·단백 1.5배 과적 해소"),
]:
    for lv in lvs:
        set_status(mid, lv, "permanent", why)

# ── ③ 브랜드존 축소: 닥터리쥬올 3단 → 2단, 1단은 E축 인접 확장 ────────
changes.append({"module": "G5-D-1", "from": "상설 3단(브랜드 전용)", "to": "상설 2단",
                "why": "배정 3품목 대비 과다. S3를 조건부로 내려 E축 확장 여지 확보."})
next(x for x in om["G5-D-1"]["shelves"] if x["level"] == 3)["status"] = "conditional"

o["meta"]["project"] = "K-Pharmacy 전체 매장 조닝 · 최적화안"
o["meta"]["variant"] = "optimized"
o["meta"]["basedOn"] = "kpharmacy-zoning-63.json (2026-09-12 기준안)"
o["meta"]["optimizationRules"] = [
    "집기 위치·수량은 변경하지 않는다(실물 치수 미실측).",
    "'안내' 선반은 상설로 전환하지 않는다(분류·상담 안내 기능 보존).",
    "저활용 피부약 모듈을 통합해 확보한 자리만 더마 고민축으로 이관한다.",
    "SKU 개별 선정은 포함하지 않는다. 약사 검토 대상이다.",
]
o["changes"] = changes
json.dump(o, open('data/kpharmacy-zoning-63.optimized.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
summarize(o, "최적화안 TO-BE")
print(f"\n변경 건수: {len(changes)}")
st = collections.Counter(s["status"] for m in o["modules"] for s in m["shelves"])
st0 = collections.Counter(s["status"] for m in d["modules"] for s in m["shelves"])
print("운영상태  AS-IS →", dict(st0))
print("          TO-BE →", dict(st))
