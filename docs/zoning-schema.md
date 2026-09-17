# `kpharmacy.zoning/1.0` — 약국 조닝·진열 교환 형식

`Pharmacy_Full_Zoning_20260912.pdf` + `Pharmacy_Full_Zoning_Shelf_Operations.xlsx` 의
운영 구조(41진열면 · 63모듈 · 315선반 · 2,526품목 · 36브랜드)를 손실 없이 담는 JSON 형식입니다.
시뮬레이터의 `JSON 열기` 로 바로 읽고, `조닝 문서` 로 다시 씁니다.

## 0. 설계 원칙

| 원칙 | 내용 |
| --- | --- |
| **좌표와 의미의 분리** | `geometry` 는 언제든 다시 계산되는 파생값이고, `modules[].shelves[]` 가 원장(原帳)입니다. 실측 전에는 `geometryStatus: "assumed"` 로 표시합니다. |
| **단 번호의 명시** | `meta.levelOrder` 로 S1이 최상단인지 최하단인지 문서 자체가 선언합니다. 관례에 의존하지 않습니다. |
| **미확정의 보존** | `decision: "미선정"`, `confirmedCode: ""` 같은 빈 값을 버리지 않습니다. "아직 정해지지 않았다"는 것도 정보입니다. |
| **근거의 동행** | `evidence`, `compliance`, `references` 로 각 배정의 확실성 수준을 함께 싣습니다. |

## 1. 최상위 구조

```jsonc
{
  "schema": "kpharmacy.zoning/1.0",
  "meta":     { /* 문서 메타 · 단 번호 체계 · 집계 · 출처 · 면책 */ },
  "params":   { /* 배치를 다시 계산하는 입력값 */ },
  "store":    { /* 매장 외곽 · 출입구 · 업무영역 · 조닝영역 */ },
  "taxonomy": { /* 주테마 · 운영상태 · 진열면 정의 */ },
  "fixtures": [ /* 곤돌라 등 물리 집기 */ ],
  "modules":  [ /* 63개 진열 모듈 — 원장 */ ],
  "skus":     [ /* 2,526품목의 운영 분류 (선택) */ ],
  "brands":   [ /* 36개 브랜드 검토군 (선택) */ ],
  "references": [ /* 자료 근거 (선택) */ ],
  "changes":  [ /* 최적화안에만 존재: 기준안 대비 변경 이력 */ ]
}
```

## 2. `meta`

```jsonc
"meta": {
  "project": "K-Pharmacy 전체 매장 조닝",
  "baseDate": "2026-09-12",          // 원본 기준일
  "generatedAt": "2026-09-17",
  "units": "mm",
  "levelOrder": "topDown",           // "topDown" = S1이 최상단 | "bottomUp" = S1이 최하단
  "levelOrderNote": "S1 = 최상단, S5 = 최하단 (원본 문서 표기 기준)",
  "geometryStatus": "assumed",       // "assumed" | "measured"
  "geometryNote": "집기 유효폭·깊이·높이 미실측. params 를 실측치로 교체하면 전체 좌표가 재계산된다.",
  "counts": { "faces": 41, "modules": 63, "shelves": 315, "skus": 2526, "brands": 36 },
  "sources": [ "…" ],
  "disclaimer": "운영 제안 자료. 법정 기준 판정을 대신하지 않는다."
}
```

> **`levelOrder` 가 이 형식에서 가장 중요한 한 줄입니다.** 첨부된 두 문서는 서로 다른 관례를
> 씁니다. `Pharmacy_Full_Zoning_20260912.pdf` 와 선반 ID(`W1/S1`)는 **S1 = 최상단**이고,
> 이전에 공유된 ONNURI 플로어맵 이미지는 **1단 = 최하단**입니다. 형식이 이를 선언하므로
> 두 관례가 한 파일 안에서 섞이지 않습니다. 시뮬레이터는 이 값을 읽어 표기를 전환합니다.

## 3. `params` — 배치 재계산 입력값

실측 전 좌표는 전부 이 값들에서 파생됩니다. 실측 후 여기만 고치면 `geometry` 전체가 다시 계산됩니다.

```jsonc
"params": {
  "storeW": 15400, "storeH": 12200, "ceiling": 2700, "minAisle": 1300,
  "wallDepth": 400,        // 벽면 집기 깊이
  "gondolaDepth": 900,     // 양면 곤돌라 전체 깊이 (면당 450)
  "moduleW": 1300,         // 모듈 1개 폭
  "endW": 450,             // 엔드캡 폭
  "shelfH": 2100, "gondolaH": 1650, "endH": 1500,
  "levels": 5,
  "gondolaPitch": 2300,    // 곤돌라 열 피치 (− gondolaDepth = 통로 1,400)
  "gondolaTop": 2300, "wallGap": 1400
}
```

## 4. `taxonomy`

```jsonc
"taxonomy": {
  "themes": [                                    // 주테마 6종
    { "id": "skin-rx",   "ko": "피부약·상처 보호", "color": "#D92D20" },
    { "id": "derma",     "ko": "더마·세정·선케어", "color": "#E64291" },
    { "id": "otc-life",  "ko": "일반약·여행·생활", "color": "#0098C9" },
    { "id": "nutrition", "ko": "영양·건강 선물",   "color": "#F47A25" },
    { "id": "lip-eye",   "ko": "립·눈·다리·구강",  "color": "#7A3AA8" },
    { "id": "guide",     "ko": "추천·상담 안내",   "color": "#F4CC32" }
  ],
  "statuses": [                                  // 선반 운영 상태 4종
    { "id": "permanent",   "ko": "상설 선택",   "color": "#039855" },
    { "id": "rotating",    "ko": "교체 전시",   "color": "#F79009" },
    { "id": "conditional", "ko": "조건부 확장", "color": "#2E90FA" },
    { "id": "info",        "ko": "안내",       "color": "#98A2B3" }
  ],
  "faces": [                                     // 진열면 7종
    { "id": "wall-top",  "code": "W",    "ko": "상단 벽면" },
    { "id": "wall-left", "code": "L",    "ko": "좌측 벽면" },
    { "id": "entry",     "code": "B",    "ko": "하단·진입" },
    { "id": "gondola-D", "code": "G-D",  "ko": "입구 방향 하면" },
    { "id": "gondola-U", "code": "G-U",  "ko": "POS 방향 상면" },
    { "id": "end-left",  "code": "G-EL", "ko": "도면 왼쪽 엔드" },
    { "id": "end-right", "code": "G-ER", "ko": "도면 오른쪽 엔드" }
  ]
}
```

## 5. `modules[]` — 원장

```jsonc
{
  "id": "G5-D-2",            // G5 곤돌라 · D(입구 방향) 면 · 도면 왼쪽에서 2번째 모듈
  "fixture": "G5",
  "face": "gondola-D",
  "index": 2,
  "name": "E  주름·탄력",
  "theme": "derma",
  "role": "Lines & Firmness",
  "brandOps": "고민별 비교, 단일 브랜드 전면 배정 없음",
  "note": "기존 리쥬란 전용 모듈을 전환. 대표 제형은 G5-D-3 비교 후보로 유지.",
  "geometry": { "x": 9500, "y": 7150, "w": 1300, "d": 450, "h": 1650,
                "rotation": 0, "status": "assumed" },
  "skuCandidates": 118,      // skus[] 에서 이 모듈을 주 진열로 지목한 품목 수
  "shelves": [ /* 아래 */ ]
}
```

### `modules[].shelves[]`

```jsonc
{
  "id": "G5-D-2/S2",
  "level": 2,                       // meta.levelOrder 기준
  "status": "permanent",
  "symptom": "레티놀 계열 세럼 비교",   // 고민·증상 (고객 언어)
  "group": "탄력·주름 스킨케어",        // 대표 상품군 (운영 언어). "A / B" 는 복수 상품군
  "examples": ["네오젠 리얼레티놀세럼"], // 대표 후보 — 전량 입고 목록이 아님
  "supplyCodes": ["pd0000554"],
  "alternates": "지피덤 EGF 크림 또는 레비온: SKU·표시 확인 후 대체",
  "criteria": "현재 자극·레티노이드·시술·임신 관련 사항은 약사가 확인.",
  "evidence": "첨부 원본 후보. 국내 규격·표시·현행 공급 대조 필요",
  "confirmedName": "",              // 확정 전에는 빈 문자열을 유지한다
  "confirmedCode": ""
}
```

## 6. `skus[]` (선택)

```jsonc
{ "code": "pd0000554", "sourceRow": 556, "name": "네오젠 리얼레티놀세럼", "spec": "30mL",
  "category": "스킨케어", "group": "탄력·주름 스킨케어",
  "primary": "G5-D-2",              // 권장 주 진열. "상설 미배정" 등 비(非)모듈 값도 허용
  "shelf": "G5-D-2/S2",
  "decision": "미선정", "confirmed": "",
  "compliance": "화장품 표시·기능성 대조", "issue": "" }
```

`primary` 에는 모듈 코드 외에 `"상설 미배정"`, `"냉장고 또는 상온 음료, 별도 검토"`,
`"G5-U, 목적별 선택"`(면 단위만 확정) 같은 값이 들어갈 수 있습니다. 파서는 정규식
`\b([WLB]\d|G\d-[UD]-\d|G\d-[UD]|G\d-E[LR])\b` 로 모듈을 추출하고, 나머지는
`unplacedSkus` / `faceLevelSkus` 로 분리 집계합니다.

## 7. 파일 구성

| 파일 | 크기 | 용도 |
| --- | --- | --- |
| `kpharmacy-zoning-63.json` | 1.2 MB | 기준안 전체(SKU·브랜드 포함) |
| `kpharmacy-zoning-63.layout.json` | 224 KB | 기준안 배치·선반 전용(SKU 제외) |
| `kpharmacy-zoning-63.optimized.json` | 1.2 MB | 최적화안 전체 + `changes[]` |
| `kpharmacy-zoning-63.optimized.layout.json` | 227 KB | 최적화안 배치·선반 전용 |

## 8. 왕복 변환 (round-trip)

```
엑셀/PDF ──(gen.py)──▶ kpharmacy-zoning-63.json
                            │
                            ├──▶ 시뮬레이터 [JSON 열기]  → 편집 → [조닝 문서] → 같은 형식으로 저장
                            ├──▶ [진열 계획 CSV]        → 매대×단 전개표
                            └──(optimize.py)──▶ …optimized.json
```

시뮬레이터가 다시 쓰는 문서는 `modules[]` 와 `taxonomy` 를 보존하되 `skus[]` 는 포함하지
않습니다. SKU 원장은 엑셀에 남기고, 도면 편집 결과만 왕복시키는 구성입니다.
