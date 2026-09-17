# 조닝 데이터 파이프라인

```
Pharmacy_Full_Zoning_Shelf_Operations.xlsx
        │
        ├─ gen_zoning.py       → data/kpharmacy-zoning-63.json            (기준안)
        └─ optimize_zoning.py  → data/kpharmacy-zoning-63.optimized.json  (최적화안 + changes[])
```

## 사용

```bash
pip install openpyxl
python3 tools/gen_zoning.py        # SRC 상수를 엑셀 경로로 수정 후 실행
python3 tools/optimize_zoning.py   # 기준안을 읽어 최적화안 생성
```

## 실측치 반영

`gen_zoning.py` 의 `P = dict(...)` 블록이 유일한 치수 입력점입니다.
실측 후 이 값만 교체하면 63모듈 전체 좌표가 다시 계산됩니다.

```python
P = dict(storeW=15400, storeH=12200, ceiling=2700, minAisle=1300,
         wallDepth=400, gondolaDepth=900, moduleW=1300, endW=450,
         shelfH=2100, gondolaH=1650, endH=1500, levels=5,
         gondolaPitch=2300, gondolaTop=2300, wallGap=1400)
```

`optimize_zoning.py` 는 두 가지 안전장치를 둡니다.

- `set_status()` 는 **안내 선반을 상설로 바꾸려 하면 중단**합니다.
  모듈 전체를 다른 테마로 전용할 때만 `repurpose()` 로 선반 역할을 새로 정의합니다.
- 집기 좌표는 건드리지 않습니다. 물리 변경은 실측 이후 과제입니다.
