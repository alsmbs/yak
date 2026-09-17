# -*- coding: utf-8 -*-
"""오픈 배정 리포트 PDF. 기존 K-PHARMACY 조닝 문서의 편집 형식을 따른다."""
import json, openpyxl, collections, datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors

pdfmetrics.registerFont(UnicodeCIDFont('HYGothic-Medium'))
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
B, R = 'HYGothic-Medium', 'HYSMyeongJo-Medium'

W, H = landscape(A4)
M = 34
INK   = colors.HexColor('#16233A')
MUTED = colors.HexColor('#6B7C90')
LINE  = colors.HexColor('#D9E1E9')
BRAND = colors.HexColor('#B4453C')     # 첨부 렌더의 테라코타 톤
SOFT  = colors.HexColor('#FBF3F1')
OK    = colors.HexColor('#0F7B5F')
WARN  = colors.HexColor('#B4651B')

A  = json.load(open('data/open-selection-assignment.json', encoding='utf-8'))
P  = json.load(open('data/open-plan-summary.json', encoding='utf-8'))
wb = openpyxl.load_workbook('data/Pharmacy_Full_Zoning_Shelf_Operations_v2.xlsx', data_only=True)
sh = [r for r in list(wb['02_선반315'].iter_rows(values_only=True))[6:] if r[0]]
zo = {r[0]: r for r in [x for x in list(wb['01_전체조닝63'].iter_rows(values_only=True))[6:]
                        if x[0] and x[0] != '합계']}
TODAY = datetime.date.today().isoformat()
page = [0]

def header(c, num, en, ko, lead):
    c.setFillColor(BRAND); c.rect(0, H - 76, W, 76, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont(B, 9)
    c.drawString(M, H - 26, "K-PHARMACY")
    c.setFont(B, 7); c.setFillColor(colors.HexColor('#F0C9C4'))
    c.drawString(M, H - 38, en)
    c.setFont(B, 16); c.setFillColor(colors.white)
    c.drawString(M, H - 60, ko)
    c.setFont(R, 8); c.setFillColor(colors.HexColor('#F5DAD6'))
    c.drawRightString(W - M, H - 26, f"{num}  {TODAY}")
    c.drawRightString(W - M, H - 38, lead[:92])
    return H - 100

def footer(c):
    page[0] += 1
    c.setStrokeColor(LINE); c.setLineWidth(.6)
    c.line(M, 30, W - M, 30)
    c.setFont(R, 7); c.setFillColor(MUTED)
    c.drawString(M, 20, "운영 제안 자료 · 매입·공급가·허가 분류·실측 미확정 · 법정 기준 판정을 대신하지 않음")
    c.drawRightString(W - M, 20, f"{page[0]:02d}")
    c.showPage()

def kpis(c, y, items):
    n = len(items); gap = 8
    bw = (W - M * 2 - gap * (n - 1)) / n
    for i, (lab, val, sub) in enumerate(items):
        x = M + i * (bw + gap)
        c.setFillColor(SOFT); c.setStrokeColor(LINE); c.setLineWidth(.7)
        c.roundRect(x, y - 52, bw, 52, 5, fill=1, stroke=1)
        c.setFont(R, 7.5); c.setFillColor(MUTED); c.drawString(x + 10, y - 16, lab)
        c.setFont(B, 17); c.setFillColor(INK);  c.drawString(x + 10, y - 36, str(val))
        c.setFont(R, 6.8); c.setFillColor(MUTED); c.drawString(x + 10, y - 46, sub[:46])
    return y - 66

def table(c, y, cols, widths, rows, fs=7.6, rh=15, note=None):
    x0 = M
    c.setFillColor(colors.HexColor('#F2F5F8')); c.rect(x0, y - rh, sum(widths), rh, fill=1, stroke=0)
    c.setFont(B, fs); c.setFillColor(INK)
    x = x0
    for col, wd in zip(cols, widths):
        c.drawString(x + 5, y - rh + 4.5, col); x += wd
    y -= rh
    for r in rows:
        if y < 56:
            return y, False
        c.setStrokeColor(LINE); c.setLineWidth(.4); c.line(x0, y, x0 + sum(widths), y)
        x = x0
        for i, (v, wd) in enumerate(zip(r, widths)):
            txt = str(v)
            c.setFont(B if i == 0 else R, fs)
            c.setFillColor(INK if i == 0 else colors.HexColor('#2F3E52'))
            maxc = int(wd / (fs * 0.56))
            c.drawString(x + 5, y - rh + 4.5, txt if len(txt) <= maxc else txt[:maxc - 1] + '…')
            x += wd
        y -= rh
    c.setStrokeColor(LINE); c.line(x0, y, x0 + sum(widths), y)
    if note:
        y -= 12; c.setFont(R, 7); c.setFillColor(MUTED); c.drawString(x0, y, note)
    return y, True

def para(c, y, lines, fs=8.4, lh=13):
    for t in lines:
        if y < 52: break
        bold = t.startswith('**')
        c.setFont(B if bold else R, fs)
        c.setFillColor(INK if bold else colors.HexColor('#33455C'))
        c.drawString(M, y, t.replace('**', ''))
        y -= lh
    return y

c = canvas.Canvas('data/KPharmacy_Open_Assignment_Report.pdf', pagesize=landscape(A4))
c.setTitle("K-Pharmacy 오픈 배정 리포트")

# ── 01 요약 ──────────────────────────────────────────────────────
y = header(c, "01", "OPENING ASSIGNMENT SUMMARY", "오픈 배정 결과 요약",
           "오픈 선정 695건 · 추가 배정 347건 · 브랜드존 9개 엔드캡")
tot = A['counts']['totalAssigned']
y = kpis(c, y, [
    ("오픈 선정 '예'", "695건", "03 시트 기준"),
    ("기존 배치", "311건", "05 상품별배치367"),
    ("추가 배정", f"{tot}건", "1차 292 + 2차 55"),
    ("배정 합계", f"{311+tot}건", "보류 37건 제외"),
    ("계획 페이싱", f"391 → {391+tot}F", "초기 1F 기준"),
    ("진열 충전율", "11% → 20%", "페이싱 70mm 가정"),
])
y = para(c, y - 4, [
    "**배정 원칙**",
    "① 권장 주 진열에 모듈이 지정돼 있으면 그 모듈로 보낸다.",
    "② 모듈 안에서는 운영 상품군이 같은 선반을 우선하고, 없으면 확장 여유 → 사용폭이 가장 적은 선반으로 간다.",
    "③ S1(곤돌라·엔드)은 개구 100mm·상품높이 상한 80mm라 배정 대상에서 제외한다.",
    "④ 냉장·상온 음료는 RF1 오픈 냉장고로 귀속한다.",
    "⑤ 초기 페이싱은 1F에서 시작한다(대체 후보는 채택 시 1F부터).",
    "",
    "**중요도별 추가 배정** — 대체 후보 C 267건 · 확인 후 검토 H 38건 · 초도 비권장 N 42건",
    "H와 N은 배정하되 조건을 함께 기록했다. H는 분류·표시 확인 후 진열, N은 초도 비권장 판정 재확인이 전제다.",
])
top = collections.Counter(r['module'] for r in A['assignments'])
for r in A['pass2']['assignments']:
    top[r['module']] += 1
rows = [[m, zo[m][3] if m in zo else '오픈 냉장고', zo[m][2] if m in zo else '—', f"{n}건"]
        for m, n in top.most_common(10)]
y -= 6
table(c, y, ["모듈", "매대명", "주테마", "추가 배정"], [70, 190, 150, 70], rows,
      note="상위 10개 모듈. 전체 41개 모듈에 분산 배정.")
footer(c)

# ── 02 브랜드존 ──────────────────────────────────────────────────
y = header(c, "02", "BRAND ZONES", "브랜드존 배정 — 엔드캡 9개",
           "전문 채널 · 소구점 명확성 기준. 거래조건 미확인")
y = para(c, y, [
    "**선정 기준** ① 피부과·약국 등 전문 채널 중심 공급 ② 약국 판매 소구점이 한 문장으로 설명되는가 ③ 브랜드 인지도(병행)",
    "인지도는 별도 점수를 매기지 않았다. 매출·거래 근거가 없어 원본 07_실행기준의 '순위 점수 부여 안함' 방침을 따랐다.",
    "",
])
rows = []
for mid, b in P['brandZones'].items():
    if not b['brand']:
        continue
    z = zo.get(mid)
    rows.append([mid, z[3] if z else '', b['brand'], b['maker'], b['claim'],
                 f"채널 {b['ch']} · 소구 {b['pt']}"])
y, _ = table(c, y, ["엔드캡", "매대명", "브랜드", "제조·공급", "소구점", "등급"],
             [56, 128, 110, 122, 150, 96], rows, rh=16)
y = para(c, y - 14, [
    "**변경 사항** 아크로패스를 제외하고 닥터리쥬올을 G5-ER에 편입했다(사용자 지정).",
    "  · 닥터리쥬올 G5-ER — 'PDRN 제품 구분' 엔드이며 자사 전용 모듈 G5-D-1과 인접해 G5에 브랜드 코너를 형성한다.",
    "  · 리쥬비(파마리서치) G1-EL — 여드름 상태 선택 엔드에서 '여드름 후 흉터·재생' 상담으로 연결된다.",
    "  · 아크로패스 선정 4건은 G1-D-2·B1 본진 배치를 그대로 유지한다.",
    "",
    "**보류 3개** G3-ER(두피·휴식) · G1-ER(피지·바디) · G6-EL(립·눈)",
    "  · G3-ER은 르디퍼가 두피·헤어 라인을 함께 공급하면 1순위 후보. 현재 선정된 르디퍼 4건은 전부 RX 스킨케어라 G5-D-3으로 배정했다.",
    "  · 모듈 내 확장 여유 16칸은 채우지 않았다. 충전율이 낮은 상태에서는 페이싱 확대 여지를 남기는 편이 낫다.",
])
footer(c)

# ── 03 포장 치수 가이드 ────────────────────────────────────────────
g = P['packagingGuide']
y = header(c, "03", "PACKAGING SIZE GUIDE", "포장 치수 가이드 — 실측 대체",
           "SKU별 입력 대신 4개 폭 구간으로 페이싱을 정한다")
y = para(c, y, [
    "**전제** 선반 유효폭은 일반 모듈 865mm, 엔드캡 645mm다. 포장 실측이 어려우므로 아래 네 구간 중 하나를 고르면 페이싱 수가 정해진다.",
    "",
])
rows = [[x['id'], x['label'], x['examples'], f"{x['widthMm']} mm",
         x['perShelf865'], x['perShelf645']] for x in g['classes']]
y, _ = table(c, y, ["구분", "명칭", "예시", "포장 폭", "865mm 선반", "645mm 엔드캡"],
             [46, 60, 240, 90, 96, 96], rows, rh=16)
y = para(c, y - 14, [
    "**목표 충전율 70%** 일반 모듈 605mm, 엔드캡 450mm를 채우는 F를 배정한다.",
    "  예) 중형(50mm) 선반 → 605 ÷ 50 ≈ 12F. SKU 3종이면 종당 4F.",
    "",
    "**높이 제약** 06_집기치수20의 개구 높이에서 여유 20mm를 뺀 값이다.",
    "  벽장 S1 440mm · S2~S4 270mm · S5 310mm   |   곤돌라·엔드 S1 80mm · S2~S5 200mm",
    "  곤돌라·엔드의 S1은 80mm라 대부분의 상품이 들어가지 않는다. 안내 유지를 권한다.",
    "",
    "**실행 권고** 모든 칸을 실제 진열처럼 채우는 것은 초도에 현실적이지 않다.",
    "  S2·S3를 70%로 먼저 채우고 S4·S5는 40~50%에서 시작해 2주 후 회전을 보고 조정한다.",
    "  빈 폭을 같은 SKU 반복으로 채우지 않는다는 원본 원칙은 유지한다.",
])
footer(c)

# ── 04 보류·확인 ─────────────────────────────────────────────────
y = header(c, "04", "HOLD AND VERIFICATION", "보류 항목과 확인 사항",
           "자동 배정하지 않은 37건 · 오픈 전 확정 항목")
hold = A['pass2']['hold']
byg = collections.Counter(h['group'] for h in hold)
y = kpis(c, y, [
    ("보류", f"{len(hold)}건", "자동 배정하지 않음"),
    ("포지셔닝 판단", "29건", "캔디·간식"),
    ("용도 판별 불가", "8건", "상품명으로 분류 불가"),
    ("확인 후 검토 H", f"{A['counts']['byImportance'].get('H',0)+36}건", "분류·표시 확인 전제"),
])
rows = [[k, f"{v}건", "약국 포지셔닝 판단 필요" if k == '캔디·간식' else "상품명으로 용도 판별 불가"]
        for k, v in byg.most_common()]
y, _ = table(c, y - 4, ["운영 상품군", "건수", "보류 사유"], [220, 70, 300], rows)
y = para(c, y - 14, [
    "**캔디·간식 29건** CJ 다시다·팝콘·비비고 김 등이 포함돼 있다. 약국 포지셔닝과 인접 뷰티 매장 중복을 고려해",
    "  자동 배정하지 않았다. 취급 여부는 경영 판단 항목이다.",
    "",
    "**오픈 전 확정할 것**",
    "① 포장 폭 구간(S/M/L/XL) 지정 — SKU별 실측 대신 구간만 정하면 페이싱이 산출된다.",
    "② 확인 후 검토(H) 품목의 분류·표시 확정 — 르디퍼 RX 3건 포함. 확정 전에는 조건부 진열이다.",
    "③ 초도 비권장(N) 판정 재확인 — 배정했으나 원본 판정과 상충한다.",
    "④ 브랜드 거래 조건 — 04_브랜드검토의 36개 브랜드가 전부 '미검토'다. 브랜드존은 제안 단계다.",
    "⑤ 전면 입면도 확인 — 슬라이딩 도어 4,000mm의 정확한 위치·폭. 평면 모델에서는 실제 개방 구간에 배치했다.",
])
footer(c)

# ── 05 근거·범위 ─────────────────────────────────────────────────
y = header(c, "05", "SOURCES AND BOUNDARIES", "자료 근거와 적용 범위",
           "운영 제안 자료. 실측·거래·허가 확정이 아님")
rows = [
    ["도면", "해당 층 건축 평면도", "X1~X7 · 31,650mm · 5,400mm 반복 그리드. 약국 내부 10,512 × 10,338mm"],
    ["집기", "06_집기치수20", "선반판 885 / 유효폭 865 · 엔드 679 / 645 · 진열깊이 270~330"],
    ["상품", "03_상품분류2526", "원본 2,526행. 오픈 선정 '예' 695건"],
    ["배치", "05_상품별배치367", "본진 326 + 추가 진열 41 · 계획 F 391"],
    ["기준", "07_실행기준", "A 106 / B 208 / T 12 · 상설 138 / 교체 37 / 조건부 70 / 안내 70"],
    ["브랜드", "04_브랜드검토", "36개 검토군. 취급 결정은 전부 '미검토'"],
    ["확인", "사용자 확인 사항", "X5 기둥 없음 · 하단 좌·우 4,000mm 슬라이딩 도어"],
]
y, _ = table(c, y, ["구분", "자료", "내용·범위"], [70, 180, 430], rows, rh=16)
y = para(c, y - 14, [
    "**가정값** 평균 페이싱 폭 70mm는 충전율 산출을 위한 가정이다. 포장 폭이 확정되면 다시 계산해야 한다.",
    "  채널 등급은 제조사 성격에 대한 판단이며 거래 조건으로 확인해야 한다.",
    "",
    "**하지 않은 것** 매출·공급가·마진·재고 회전·관광객 구매 데이터를 반영하지 않았다. 브랜드 순위 점수를 매기지 않았다.",
    "  상품명에 포함된 시술·재생·효능 표현을 매장 자체 효과 주장으로 확대하지 않는다는 원본 원칙을 따른다.",
    "",
    "**기준일** " + TODAY + " · 재고·공급가·국내 판매규격·독점 범위·실물 치수는 미확정",
])
footer(c)
c.save()
import os
print(f"PDF {os.path.getsize('data/KPharmacy_Open_Assignment_Report.pdf')/1024:.0f} KB · {page[0]}쪽")
