# -*- coding: utf-8 -*-
"""진열대별 상세 북(다페이지 A4 가로). Chromium 인쇄로 PDF 출력."""
import json, html

D = json.load(open('data/book-data.json', encoding='utf-8'))
M, T, PG = D['modules'], D['totals'], D['packagingGuide']
L = json.load(open('data/kpharmacy-open-final-layout.json', encoding='utf-8'))
S = L['store']

e = lambda s: html.escape(str(s or ''))
def cut(s, n):
    s = str(s or '')
    return e(s if len(s) <= n else s[:n - 1] + '…')

THEME = {
    '피부약·상처 보호': ('#C2410C', '#FFF4ED', '#FDE4D3'),
    '더마·세정·선케어': ('#BE185D', '#FFF1F6', '#FBD9E6'),
    '일반약·여행·생활': ('#0369A1', '#EFF8FE', '#CFE7F7'),
    '영양·건강 선물':   ('#B45309', '#FFFAEB', '#FCECC5'),
    '립·눈·다리·구강':  ('#6D28D9', '#F6F3FF', '#E2DBFB'),
    '추천·상담 안내':   ('#A16207', '#FEFCE8', '#F7EAB8'),
}
ST = {'오픈 진열': ('#047857', '#ECFDF5'), '테마 진열': ('#B45309', '#FFFBEB'),
      '시험 진열': ('#6D28D9', '#F5F3FF'), '안내': ('#475569', '#F1F5F9'),
      '확장 여유': ('#94A3B8', '#F8FAFC')}

PAGES = []
TOC = []
def page(kind, num, ttl, en, right, body, cls=''):
    if cls != 'cover':
        TOC.append((num, kind, ttl))
    PAGES.append(f'''<section class="pg {cls}"><header class="ph">
      <div class="pk">{e(kind)}</div>
      <div class="pt">{e(ttl)}<small>{e(en)}</small></div>
      <div class="pr">{right}</div></header>
      <div class="pb">{body}</div>
      <footer class="pf"><span>K-Pharmacy by ONNURI · 성수 2F · 약국 조닝 &amp; 5단 선반 운영서</span>
      <span>선반 번호 S1 = 최상단 · 페이징 단위 F = 페이싱</span>
      <b>{num:02d}</b></footer></section>''')

# ── 모듈 상세 카드 ───────────────────────────────────────────────
def mod_card(mid, compact=False):
    m = M[mid]
    c, bg, bd = THEME.get(m['theme'], ('#475569', '#F8FAFC', '#E2E8F0'))
    rows = []
    for s in m['shelves']:
        sc, sbg = ST.get(s['status'], ('#475569', '#F1F5F9'))
        if s['items']:
            its = ''.join(
                f'<li><b>{e(i["code"])}</b><i>{i["f"]}F</i>{e(i["name"])}'
                + (f'<u>/ {e(i["spec"])}</u>' if i.get('spec') else '')
                + ('<em>신규</em>' if i.get('new') else '') + '</li>'
                for i in s['items'])
        elif s['status'] == '안내':
            its = '<li class="ph0">진열 없음 — 분류·상담 안내 사인</li>'
        else:
            its = '<li class="ph0">미배정 — 오픈 후 확장 여유</li>'
        rows.append(
            f'<div class="sh"><div class="sl"><b>S{s["level"]}</b>'
            f'<span class="ss" style="color:{sc};background:{sbg}">{e(s["short"])}</span>'
            f'<i>{s["f"] or 0}F</i></div>'
            f'<div class="sn">{e(s["need"] or s["group"])}'
            f'<small>{e(s["group"])}</small></div>'
            f'<ul class="si">{its}</ul></div>')
    bz = m['brandZone']
    tag = (f'<div class="mbz" style="background:{c}">BRAND BLOCK · {e(bz["brand"])}'
           f'<small>{e(bz["claim"])}</small></div>' if bz else '')
    pend = (f'<div class="mpd">추가 배정 {len(m["pending"])}건 포함</div>' if m['pending'] else '')
    return f'''<div class="mc{' cp' if compact else ''}" style="--c:{c};--bg:{bg};--bd:{bd}">
      <div class="mh"><div class="mid">{e(mid)}</div>
        <div class="mn">{e(m["name"])}<small>{e(m["theme"])} · {e(m["role"] or "")}</small></div>
        <div class="mf">{m["skuRows"]}<small>SKU</small></div>
        <div class="mf">{m["facings"]}<small>F</small></div></div>
      {tag}<div class="ms">{''.join(rows)}</div>{pend}</div>'''

# ── 평면도 ───────────────────────────────────────────────────────
def rot_attr(el):
    r = float(el.get('rotation') or 0)
    if not r % 360:
        return ''
    cx, cy = el['x'] + el['w'] / 2, el['y'] + el['h'] / 2
    return f' transform="rotate({r:.0f} {cx:.0f} {cy:.0f})"'

def bbox(el):
    cx, cy = el['x'] + el['w'] / 2, el['y'] + el['h'] / 2
    w, h = el['w'], el['h']
    if round(float(el.get('rotation') or 0)) % 180:
        w, h = h, w
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

def plan(codes=True):
    p = [f'<rect x="0" y="0" width="{S["w"]}" height="{S["h"]}" fill="#fff" '
         f'stroke="#233" stroke-width="70"/>']
    for el in L['elements']:
        code, t = el.get('code'), el['type']
        if t == 'zone' or not code:
            continue
        m = M.get(code)
        c = THEME.get(m['theme'], ('#94A3B8',))[0] if m else '#94A3B8'
        bz = m and m['brandZone']
        p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                 f'height="{el["h"]:.0f}" fill="{c}" fill-opacity="{0.92 if bz else 0.5}" '
                 f'stroke="{"#111" if bz else c}" stroke-width="{60 if bz else 22}"'
                 f'{rot_attr(el)}/>')
    for el in L['elements']:
        if el['type'] in ('checkout', 'counter', 'storageRoom', 'fridge', 'wall'):
            p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                     f'height="{el["h"]:.0f}" fill="#CBD5E1" stroke="#94A3B8" '
                     f'stroke-width="30"{rot_attr(el)}/>')
        if el['type'] == 'door':
            p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                     f'height="{el["h"]:.0f}" fill="#0EA5E9"{rot_attr(el)}/>')

    def lab(x, y, t, size=190, fill='#16233A', rot=0):
        tr = f' transform="rotate({rot} {x:.0f} {y:.0f})"' if rot else ''
        p.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" font-weight="800" '
                 f'fill="{fill}" text-anchor="middle"{tr} '
                 f'style="paint-order:stroke;stroke:#fff;stroke-width:70">{html.escape(t)}</text>')

    if codes:
        for el in L['elements']:
            code = el.get('code')
            if not code or el['type'] != 'wallShelf':
                continue
            x0, y0, x1, y1 = bbox(el)
            txt = code.split('-')[-1] if code[0] == 'G' else code
            lab((x0 + x1) / 2, (y0 + y1) / 2 + 60, txt, 150, '#0F172A')
    grp = {}
    for el in L['elements']:
        code = el.get('code')
        if not code or el['type'] not in ('wallShelf', 'endcap'):
            continue
        key = code.split('-')[0] if code[0] == 'G' else code[0]
        x0, y0, x1, y1 = bbox(el)
        b = grp.setdefault(key, [1e9, 1e9, -1e9, -1e9])
        b[0] = min(b[0], x0); b[1] = min(b[1], y0)
        b[2] = max(b[2], x1); b[3] = max(b[3], y1)
    for k, b in grp.items():
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 70
        if k == 'W':
            lab(cx, b[1] - 130, '상단 벽면 W1–W5', 210)
        elif k == 'L':
            lab(b[2] + 320, cy, '좌측 벽면 L1–L4', 210, rot=-90)
        elif k == 'B':
            lab(cx, b[3] + 330, '하단 진입부 B1–B8', 210)
        else:
            lab(cx, cy, k, 340)
    lab(7100, 800, 'POS · 상담 카운터', 210, '#475569')
    lab(9600, 2050, 'RF1 냉장', 175, '#475569')
    lab(7480, 4450, '조제 · 투약대', 210, '#475569')
    lab(751, 10160, '좌 슬라이딩 4m', 175, '#0369A1')
    lab(9767, 10160, '우 슬라이딩 4m', 175, '#0369A1')
    return (f'<svg viewBox="-560 -560 {S["w"]+1120} {S["h"]+1320}" class="plan">'
            + ''.join(p) + '</svg>')

legend = ''.join(f'<div class="lg"><i style="background:{v[0]}"></i>{e(k)}</div>'
                 for k, v in THEME.items())

# ══ P1 표지 ══════════════════════════════════════════════════════
kpi = [('63', '진열 모듈', 'W5 · L4 · B8 · G 36 · 엔드캡 12 · 냉장 1 ※ 본서 수록 63'),
       ('315', '선반 칸(5단)', '모듈당 S1~S5 고정 · S1 = 최상단'),
       ('714', '배치 SKU 행', f'기존 {T["baseSku"]} + 추가 배정 {T["addSku"]}'),
       ('738', '총 페이싱 F', '선반 유효폭 865mm(엔드캡 645mm) 기준'),
       ('9', '브랜드 블록', '엔드캡·양면 곤돌라 단독 구획'),
       ('37', '보류 SKU', '캔디·간식 29 + 식별 불가 8')]
cover = f'''<div class="cv">
  <div class="cv-l">
    <div class="cv-brand">K-Pharmacy <span>by ONNURI</span></div>
    <h1>약국 조닝 &amp; 진열대별<br>5단 선반 운영서</h1>
    <p class="cv-sub">성수 2F · 10,512 × 10,338 mm · 32.9평<br>
      오픈 선정 상품군 배치 확정본 · 브랜드 블록 포함</p>
    <div class="cv-kpi">{''.join(
      f'<div class="kp"><b>{a}</b><span>{e(b)}</span><small>{e(c)}</small></div>'
      for a, b, c in kpi)}</div>
    <div class="cv-toc"><h4>목차</h4><div class="tcs">__TOC__</div></div>
    <div class="cv-note">본서는 <b>kpharmacy.openplan/1.0</b> JSON(<code>kpharmacy-open-final-layout.json</code>)에서
      기계적으로 생성된다. 선반 번호·상태·페이싱은 JSON 원본과 1:1로 일치하며, 수치를 고치려면
      JSON을 고친 뒤 본서를 재생성한다.</div>
  </div>
  <div class="cv-r">{plan(False)}<div class="lgs">{legend}</div></div></div>'''
page('COVER', 1, '표지 · 전체 요약', 'K-PHARMACY / SEONGSU 2F',
     f'<b>{e(D["generatedAt"][:10])}</b><small>생성 기준일</small>', cover, 'cover')

# ══ P2 평면도 ════════════════════════════════════════════════════
bz_rows = ''.join(
    f'<tr><td class="cd">{e(k)}</td><td><b>{e(m["brandZone"]["brand"])}</b></td>'
    f'<td>{e(m["brandZone"]["claim"])}</td>'
    f'<td class="mut">{e(m["brandZone"].get("why") or m["theme"])}</td></tr>'
    for k, m in M.items() if m['brandZone'])
body2 = f'''<div class="p2">
  <div class="p2a">{plan(True)}</div>
  <div class="p2b">
    <h3>테마 6분류</h3><div class="lgs v">{legend}</div>
    <h3>브랜드 블록 9개</h3>
    <table class="tb sm"><tbody>{bz_rows}</tbody></table>
    <h3>동선 전제</h3>
    <ul class="bl">
      <li>하단 좌·우 <b>각 4m 슬라이딩 도어</b> — 문짝이 벽을 따라 이동하므로 전후 여닫이 여유 불필요.
        개구를 물리적으로 막는 집기만 간섭으로 본다.</li>
      <li>진입 직후 <b>B1–B8</b>가 첫 접점(탐색·신제품), 좌측 <b>L1–L4</b>가 일반약 목적 구매,
        상단 <b>W1–W5</b>가 상담·선물 마감 동선.</li>
      <li>중앙 <b>G1–G6</b>는 양면 곤돌라. <b>D면 = 입구 방향</b>, <b>U면 = POS 방향</b>으로
        같은 테마를 앞뒤로 마주 세워 교차 노출을 만든다.</li>
      <li>기둥 없음. 후방 POS·조제·투약대와 RF1 냉장은 판매 진열에서 제외.</li>
    </ul></div></div>'''
page('01', 2, '전체 매장 위치도', 'FLOOR MAP & ZONE INDEX',
     '<b>10,512 × 10,338</b><small>mm · 32.9평</small>', body2)

# ══ P3 집기 제원 · 포장 가이드 ═══════════════════════════════════
cls_rows = ''.join(
    f'<tr><td class="cd">{e(c["id"])}</td><td><b>{e(c["label"])}</b></td>'
    f'<td>{e(c["widthMm"])} mm</td><td>{e(c["perShelf865"])}</td>'
    f'<td>{e(c["perShelf645"])}</td><td class="mut">{e(c["examples"])}</td></tr>'
    for c in PG['classes'])
hl = PG['heightLimits']
hl_rows = ''.join(f'<tr><td class="cd">{e(k)}</td><td>{e(v)}{" mm" if isinstance(v,int) else ""}</td></tr>'
                  for k, v in hl.items() if k != 'note')
body3 = f'''<div class="p3">
  <div>
    <h3>포장 폭 구간 가이드 — 실측 대체</h3>
    <p class="lead">{e(PG["basis"])}</p>
    <table class="tb"><thead><tr><th>구간</th><th>구분</th><th>포장 폭</th>
      <th>일반 모듈(865mm)</th><th>엔드캡(645mm)</th><th>대표 예시</th></tr></thead>
      <tbody>{cls_rows}</tbody></table>
    <div class="cal"><b>배정 규칙</b> {e(PG["targetRule"])}</div>
    <h3>모든 칸을 채우지 않는다</h3>
    <ul class="bl">
      <li>315칸 전부를 실제 진열로 채우는 것은 오픈 시점에 불가능하다. 본서는
        <b>오픈 진열 · 테마 진열 · 시험 진열</b>만 상품을 박고,
        <b>안내</b>는 사인·분류 표시, <b>확장 여유</b>는 의도적 공백으로 남긴다.</li>
      <li>현재 총 페이싱 <b>{T["totalF"]}F</b>. 유효폭 기준 이론 수용량 대비 충전율은 낮은 편이며,
        이는 과적이 아니라 <b>의도된 여백</b>이다. 오픈 후 판매 데이터로 확장 여유부터 채운다.</li>
      <li>SKU별 가로·세로·깊이 실측이 확보되면 S/M/L/XL 구간을 실측 값으로 교체하고
        페이싱을 재계산한다. 그 전까지 F 값은 <b>계획치</b>다.</li>
    </ul>
  </div>
  <div>
    <h3>선반 개구 높이 한계</h3>
    <table class="tb sm"><tbody>{hl_rows}</tbody></table>
    <p class="mut sm2">{e(hl.get("note"))}</p>
    <h3>선반 유효폭</h3>
    <table class="tb sm"><tbody>{''.join(
      f'<tr><td class="cd">{e(k)}</td><td>{v} mm</td></tr>'
      for k, v in PG["shelfEffectiveWidthMm"].items())}</tbody></table>
    <h3>모듈 코드 체계</h3>
    <table class="tb sm"><tbody>
      <tr><td class="cd">W1–W5</td><td>상단 벽면 5연</td></tr>
      <tr><td class="cd">L1–L4</td><td>좌측 벽면 4연</td></tr>
      <tr><td class="cd">B1–B8</td><td>하단 진입부 8연</td></tr>
      <tr><td class="cd">G#-D-1~3</td><td>곤돌라 입구 방향 면</td></tr>
      <tr><td class="cd">G#-U-1~3</td><td>곤돌라 POS 방향 면</td></tr>
      <tr><td class="cd">G#-EL / ER</td><td>곤돌라 좌·우 엔드캡</td></tr>
      <tr><td class="cd">RF1</td><td>냉장 쇼케이스</td></tr>
    </tbody></table>
    <div class="cal alt"><b>S1 주의</b> 곤돌라·엔드캡 S1은 개구 80mm로 사실상 진열 불가다.
      본서는 G·E의 S1을 전량 <b>분류·상담 안내</b>로 운영한다.</div>
  </div></div>'''
page('02', 3, '집기 제원 · 포장 가이드', 'FIXTURE SPEC & PACKAGING GUIDE',
     '<b>S / M / L / XL</b><small>4구간 근사</small>', body3)

# ══ P4 운영 상태 정의 ════════════════════════════════════════════
st_cnt = {}
for m in M.values():
    for s in m['shelves']:
        st_cnt[s['status']] = st_cnt.get(s['status'], 0) + 1
st_rows = ''.join(
    f'<tr><td><span class="ss" style="color:{ST[k][0]};background:{ST[k][1]}">{e(k)}</span></td>'
    f'<td class="num">{v}</td><td class="num">{v*100//315}%</td><td>{e(d)}</td></tr>'
    for k, v, d in [(k, st_cnt.get(k, 0), d) for k, d in [
        ('오픈 진열', '오픈 첫날부터 상품이 박히는 칸. 선정 리스트의 본진.'),
        ('테마 진열', '월별·시즌 테마로 교체 운영하는 칸. 고정 SKU를 두지 않는다.'),
        ('시험 진열', '신규 브랜드 도입 테스트 칸. 판매 데이터 확보용.'),
        ('안내', '상품 대신 분류 사인·상담 안내를 두는 칸. G·E의 S1 포함.'),
        ('확장 여유', '의도적 공백. 오픈 후 실판매로 우선 채운다.')]] if True)
face_rows = ''
for f, nm in [('W', '상단 벽면'), ('L', '좌측 벽면'), ('B', '하단 진입부'),
              ('G', '중앙 곤돌라'), ('E', '엔드캡')]:
    ms = [m for m in M.values() if m['face'] == f]
    if not ms:
        ms = [m for k, m in M.items() if (k.startswith('G') and '-E' in k) == (f == 'E')
              and k[0] == 'G' and (f in ('G', 'E'))]
    if not ms:
        continue
    face_rows += (f'<tr><td><b>{f}</b> {e(nm)}</td><td class="num">{len(ms)}</td>'
                  f'<td class="num">{sum(x["skuRows"] for x in ms)}</td>'
                  f'<td class="num">{sum(x["facings"] for x in ms)}</td>'
                  f'<td class="num">{sum(1 for x in ms if x["brandZone"])}</td></tr>')
body4 = f'''<div class="p3">
  <div>
    <h3>선반 운영 상태 5구분 — 315칸</h3>
    <table class="tb"><thead><tr><th>상태</th><th>칸</th><th>비중</th><th>정의</th></tr></thead>
      <tbody>{st_rows}</tbody></table>
    <h3>배치 결정 순서</h3>
    <ol class="bl num">
      <li><b>선정 리스트 본진 배치</b> — 오픈 선정 상품군을 테마·상담 맥락에 맞는 모듈에 먼저 꽂는다.</li>
      <li><b>약국 다빈도 브랜드 상위 노출</b> — 리쥬비넥스·프로캄·닥터리쥬올·르디퍼 등은
        시선 높이(골든존 850–1500mm)인 S2·S3를 우선 점유한다.</li>
      <li><b>추가 전환분 재배정</b> — 오픈 운영 '예'로 전환된 항목 {T["addSku"]}건을
        키워드 라우팅으로 2패스 배정. 위치 판단이 필요한 {T["hold"]}건은 보류.</li>
      <li><b>남는 선반에 브랜드 블록</b> — 1단만이라도 단독 구획을 주되,
        일반 뷰티샵이 아닌 <b>피부과·약국 중심 유통</b>이면서 약국 소구점이 분명한 브랜드를 우선한다.</li>
    </ol>
    <div class="cal alt"><b>제외</b> {''.join(f'{e(k)} — {e(v)}' for k, v in D["excluded"].items())}</div>
  </div>
  <div>
    <h3>면별 집계</h3>
    <table class="tb"><thead><tr><th>면</th><th>모듈</th><th>SKU 행</th><th>페이싱</th>
      <th>브랜드</th></tr></thead><tbody>{face_rows}</tbody></table>
    <h3>브랜드 블록 선정 기준</h3>
    <ul class="bl">
      <li><b>1순위 — 유통 채널</b>: 피부과·약국을 주 채널로 공급되는 브랜드.
        올리브영·일반 뷰티샵 중심 브랜드는 후순위로 둔다.</li>
      <li><b>2순위 — 소구점 명확성</b>: PDRN·EGF·시카·흉터·습윤 등 약사가
        한 문장으로 설명 가능한 기능 축을 가진 브랜드.</li>
      <li><b>3순위 — 인지도</b>: 동일 조건이면 자체 인지도가 높은 쪽.</li>
      <li>브랜드 블록은 <b>엔드캡 우선</b>. 엔드캡은 양방향 동선에서 먼저 보이고
        구획 경계가 뚜렷해 브랜드 단독 노출에 적합하다.</li>
    </ul>
    <h3>본서 읽는 법</h3>
    <ul class="bl">
      <li>각 모듈 카드는 <b>S1(최상단) → S5(최하단)</b> 순으로 5행이다.</li>
      <li>행 왼쪽 = 선반 번호 · 운영 상태 · 해당 칸 총 페이싱.</li>
      <li>행 오른쪽 = <b>공급처 코드 4자리 · 페이싱 · 상품명 / 규격</b>.
        <em>신규</em> 표시는 추가 전환분이다.</li>
    </ul>
  </div></div>'''
page('03', 4, '운영 상태 정의 · 배치 원칙', 'OPERATING STATUS & ASSORTMENT LOGIC',
     f'<b>{T["addSku"]}</b><small>추가 배정 건</small>', body4)

# ══ P5~ 모듈 상세 ════════════════════════════════════════════════
def mod_page(num, kind, ttl, en, right, ids, cols):
    body = (f'<div class="mg c{cols}">'
            + ''.join(mod_card(i) for i in ids if i in M) + '</div>')
    page(kind, num, ttl, en, right, body)

n = 5
mod_page(n, '04', '상단 벽면 W1–W5', 'TOP WALL',
         '<b>피부·더마 2 + 추천 1 + 영양·선물 2</b><small>상담 마감 동선</small>',
         ['W1', 'W2', 'W3', 'W4', 'W5'], 5); n += 1
mod_page(n, '05', '좌측 벽면 L1–L4', 'LEFT WALL',
         '<b>일반약 목적 구매</b><small>여행 중 필요 약</small>',
         ['L1', 'L2', 'L3', 'L4'], 4); n += 1
mod_page(n, '06', '하단 진입부 B1–B4', 'ENTRANCE DISCOVERY 1/2',
         '<b>좌측 진입 접점</b><small>증상 탐색</small>',
         ['B1', 'B2', 'B3', 'B4'], 4); n += 1
mod_page(n, '07', '하단 진입부 B5–B8', 'ENTRANCE DISCOVERY 2/2',
         '<b>우측 진입 접점</b><small>더마·신제품</small>',
         ['B5', 'B6', 'B7', 'B8'], 4); n += 1

GT = {'G1': ('여드름·피지·세정', 'Acne & Pore Care'),
      'G2': ('흉터·상처·건조', 'Scar & Wound Care'),
      'G3': ('색소·선케어 / 두피·휴식', 'Tone, Sun & Daily Care'),
      'G4': ('비타민·이너뷰티·영양', 'Vitamins & Inner Beauty'),
      'G5': ('PDRN·장벽·수분', 'PDRN & Barrier Care'),
      'G6': ('립·눈·다리 / 발·걷기', 'Lip, Eye & Travel Comfort')}
for i, g in enumerate(['G1', 'G2', 'G3', 'G4', 'G5', 'G6']):
    d = [f'{g}-D-{k}' for k in (1, 2, 3) if f'{g}-D-{k}' in M]
    u = [f'{g}-U-{k}' for k in (1, 2, 3) if f'{g}-U-{k}' in M]
    ee = [f'{g}-{k}' for k in ('EL', 'ER') if f'{g}-{k}' in M]
    sku = sum(M[x]['skuRows'] for x in d + u)
    fac = sum(M[x]['facings'] for x in d + u)
    ec = ' · 엔드캡 ' + '/'.join(x.split('-')[-1] for x in ee) if ee else ''
    body = (f'<div class="gsec"><div class="glab">D면 · 입구 방향</div>'
            f'<div class="mg c{len(d)}">{"".join(mod_card(x) for x in d)}</div></div>'
            f'<div class="gsec"><div class="glab u">U면 · POS 방향</div>'
            f'<div class="mg c{len(u)}">{"".join(mod_card(x) for x in u)}</div></div>')
    page(f'{8+i:02d}', n, f'중앙 곤돌라 {g} — {GT[g][0]}', f'CENTRAL GONDOLA {g} · {GT[g][1]}',
         f'<b>{sku} SKU · {fac}F</b><small>양면 {len(d)+len(u)}개 면{e(ec)} 별면</small>', body, 'gpg')
    n += 1

# 엔드캡 2개 면 — 브랜드 블록의 주 무대
for half, gs in ((1, ['G1', 'G2', 'G3']), (2, ['G4', 'G5', 'G6'])):
    ids = [f'{g}-{k}' for g in gs for k in ('EL', 'ER') if f'{g}-{k}' in M]
    nb = sum(1 for x in ids if M[x]['brandZone'])
    body = (f'<div class="mg c3 ecp">{"".join(mod_card(x) for x in ids)}</div>'
            '<div class="cal alt"><b>엔드캡 운영 원칙</b> 엔드캡은 양방향 동선에서 먼저 보이고 '
            '구획 경계가 뚜렷해 브랜드 단독 노출에 가장 적합하다. 브랜드 블록이 붙지 않은 엔드캡은 '
            '해당 곤돌라의 <b>진입 안내면</b>으로 두어, 뒤이어 나오는 D면 테마를 한 줄로 예고한다. '
            'S1은 개구 80mm로 진열 불가이므로 전량 분류 사인이다.</div>')
    page(f'{13+half:02d}', n, f'엔드캡 {gs[0]}–{gs[-1]}',
         f'GONDOLA ENDCAPS {gs[0]}–{gs[-1]}',
         f'<b>{len(ids)}면 · 브랜드 {nb}</b><small>단독 구획</small>', body, 'ecpg')
    n += 1

# ══ 마지막 — 보류·실행 ══════════════════════════════════════════
hold = D['hold']
grp = {}
for h in hold:
    grp.setdefault(h['group'], []).append(h)
hold_rows = ''.join(
    f'<tr><td class="cd">{e(h["code"])}</td><td>{cut(h["name"],28)}</td>'
    f'<td>{e(h["group"])}</td><td class="mut">{e(h["why"])}</td></tr>'
    for h in hold[:30])
more = (f'<p class="mut sm2">외 {len(hold)-30}건 — 전량 '
        f'<code>data/open-plan-summary.json</code> 의 <code>hold[]</code> 참조.</p>'
        if len(hold) > 30 else '')
grp_rows = ''.join(f'<tr><td>{e(k)}</td><td class="num">{len(v)}</td></tr>'
                   for k, v in sorted(grp.items(), key=lambda x: -len(x[1])))
body_l = f'''<div class="p3">
  <div>
    <h3>보류 {len(hold)}건 — 자동 배정하지 않은 항목</h3>
    <p class="lead">아래 항목은 키워드 라우팅으로 위치를 단정할 수 없어 <b>의도적으로 보류</b>했다.
      임의 배치가 오히려 매장 포지셔닝을 훼손한다고 판단한 건이다.</p>
    <table class="tb sm"><thead><tr><th>코드</th><th>상품</th><th>분류</th><th>보류 사유</th>
      </tr></thead><tbody>{hold_rows}</tbody></table>{more}
  </div>
  <div>
    <h3>분류별 보류 집계</h3>
    <table class="tb sm"><thead><tr><th>분류</th><th>건</th></tr></thead>
      <tbody>{grp_rows}</tbody></table>
    <h3>오픈 전 확인 사항</h3>
    <ol class="bl num">
      <li><b>캔디·간식 29건의 포지셔닝 결정</b> — 관광객 객단가 보조로 계산대 옆에 둘지,
        약국 정체성을 지키기 위해 취급하지 않을지는 경영 판단이다. 본서는 자리를 비워 두었다.</li>
      <li><b>식별 불가 8건의 원장 정합</b> — 공급처 코드와 상품명이 매칭되지 않는다.
        원본 상품 마스터에서 코드를 확정한 뒤 배정한다.</li>
      <li><b>포장 실측</b> — S/M/L/XL 근사를 실측으로 교체하면 페이싱이 바뀐다.
        특히 XL(선물세트·홍삼)이 몰린 W5·B5를 재검토한다.</li>
      <li><b>브랜드 블록 계약 확인</b> — 단독 구획은 공급 조건·판촉물 지원과 함께 협의한다.
        미확정 브랜드는 해당 칸을 <b>시험 진열</b>로 되돌린다.</li>
      <li><b>S1 사인 제작</b> — G·E의 S1 60칸은 개구 80mm로 진열 불가. 분류 사인 발주가 선행되어야
        상단 라인이 비어 보이지 않는다.</li>
    </ol>
    <h3>산출물</h3>
    <table class="tb sm"><tbody>
      <tr><td class="cd">JSON</td><td>kpharmacy-open-final-layout.json — 시뮬레이터 로드용 원본</td></tr>
      <tr><td class="cd">JSON</td><td>open-plan-summary.json — 배정·보류·브랜드 블록 요약</td></tr>
      <tr><td class="cd">PDF</td><td>본서 — 진열대별 5단 선반 상세</td></tr>
      <tr><td class="cd">PNG</td><td>1장 포스터 — 현장 부착용</td></tr>
      <tr><td class="cd">HTML</td><td>pharmacy-layout-studio.html — 3D·평면 시뮬레이터</td></tr>
    </tbody></table>
    <div class="cal alt"><b>정확도 고지</b> 페이싱·포장 구간은 실측이 아닌 <b>계획 추정치</b>다.
      브랜드의 유통 채널 성격은 공개 정보 기준이며, 최종 취급·마진·독점 조건은
      실사와 거래 확인이 필요하다.</div>
  </div></div>'''
page('16', n, '보류 항목 · 오픈 전 확인', 'HOLDS & PRE-OPENING CHECKLIST',
     f'<b>{len(hold)}</b><small>보류 건</small>', body_l)

TOTAL = len(PAGES)
toc_html = ''.join(
    f'<div class="tc"><b>{n:02d}</b><span>{e(t)}</span></div>' for n, k, t in TOC)
PAGES[0] = PAGES[0].replace('__TOC__', toc_html)
HTML = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>K-Pharmacy 진열대별 선반 운영서</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#525659;color:#16233A;
 font-family:'Noto Sans KR',-apple-system,'Malgun Gothic',sans-serif;
 -webkit-font-smoothing:antialiased}}
.pg{{width:1400px;height:990px;background:#fff;margin:0 auto 14px;padding:26px 30px 0;
 display:flex;flex-direction:column;position:relative;overflow:hidden;page-break-after:always}}
.pg:last-child{{page-break-after:auto}}
.ph{{display:flex;align-items:flex-end;gap:14px;border-bottom:2.2px solid #16233A;padding-bottom:9px;
 flex:0 0 auto}}
.pk{{background:#16233A;color:#fff;font-size:11px;font-weight:800;padding:4px 8px;border-radius:4px;
 letter-spacing:.5px}}
.pt{{font-size:19px;font-weight:800;line-height:1.15}}
.pt small{{display:block;font-size:10px;font-weight:700;color:#93A1B2;letter-spacing:.9px;margin-top:2px}}
.pr{{margin-left:auto;text-align:right}}
.pr b{{font-size:15px;font-weight:800}}
.pr small{{display:block;font-size:9.5px;color:#93A1B2;font-weight:700}}
.pb{{flex:1 1 auto;min-height:0;padding:13px 0 0;display:flex;flex-direction:column;gap:9px}}
.pf{{flex:0 0 auto;display:flex;align-items:center;gap:14px;border-top:1px solid #E2E8F0;
 padding:7px 0 9px;font-size:9px;color:#93A1B2;font-weight:600}}
.pf b{{margin-left:auto;font-size:13px;color:#16233A;font-weight:800}}
h3{{font-size:12.5px;font-weight:800;margin:11px 0 6px;padding-left:7px;border-left:3px solid #16233A}}
h3:first-child{{margin-top:0}}
.lead{{font-size:10.5px;color:#475569;line-height:1.55;margin-bottom:7px}}
.mut{{color:#8894A5}} .sm2{{font-size:9.5px;line-height:1.5;margin-top:5px}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:.92em;background:#F1F5F9;padding:1px 4px;
 border-radius:3px}}
/* 표 */
.tb{{width:100%;border-collapse:collapse;font-size:10px}}
.tb th{{text-align:left;font-size:9px;font-weight:800;color:#64748B;letter-spacing:.4px;
 border-bottom:1.5px solid #CBD5E1;padding:5px 6px}}
.tb td{{padding:4.5px 6px;border-bottom:1px solid #EEF2F6;line-height:1.35;vertical-align:top}}
.tb.sm td,.tb.sm th{{padding:3.5px 5px;font-size:9.5px}}
.tb td.cd{{font-weight:800;white-space:nowrap;color:#0F172A}}
.tb td.num{{text-align:right;font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}}
.ss{{font-size:8.5px;font-weight:800;padding:1.5px 5px;border-radius:9px;white-space:nowrap}}
.bl{{font-size:10.2px;color:#334155;line-height:1.6;padding-left:15px}}
.bl li{{margin-bottom:4.5px}}
.bl.num{{list-style:decimal}}
.cal{{background:#F1F5F9;border-left:3px solid #16233A;padding:8px 10px;font-size:10px;
 line-height:1.55;margin-top:9px;border-radius:0 5px 5px 0}}
.cal.alt{{background:#FFF7ED;border-color:#C2410C}}
.cal b{{font-weight:800;margin-right:5px}}
/* 표지 */
.cover .pb{{padding-top:16px}}
.cv{{display:grid;grid-template-columns:1fr 640px;gap:30px;height:100%}}
.cv-brand{{font-size:27px;font-weight:900;letter-spacing:-1px}}
.cv-brand span{{font-size:12px;font-weight:600;color:#93A1B2;letter-spacing:0}}
.cv h1{{font-size:40px;font-weight:900;line-height:1.18;letter-spacing:-1.6px;margin:16px 0 12px}}
.cv-sub{{font-size:12px;color:#64748B;line-height:1.65;font-weight:600}}
.cv-kpi{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:22px}}
.kp{{border:1px solid #E2E8F0;border-radius:7px;padding:9px 11px;background:#F8FAFC}}
.kp b{{font-size:24px;font-weight:900;letter-spacing:-1px;line-height:1}}
.kp span{{font-size:10.5px;font-weight:800;color:#334155;margin-left:5px}}
.kp small{{display:block;font-size:8.8px;color:#93A1B2;margin-top:3px;line-height:1.35}}
.cv-toc{{margin-top:20px;border-top:1px solid #E2E8F0;padding-top:11px}}
.cv-toc h4{{font-size:10px;font-weight:800;color:#64748B;letter-spacing:.5px;margin-bottom:7px}}
.tcs{{display:grid;grid-template-columns:1fr 1fr;gap:1px 18px}}
.tc{{display:flex;gap:8px;align-items:baseline;font-size:9.8px;padding:2.5px 0;
 border-bottom:1px dotted #EDF1F6}}
.tc b{{font-weight:800;color:#93A1B2;font-variant-numeric:tabular-nums;font-size:9px}}
.tc span{{font-weight:600;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.cv-note{{margin-top:16px;font-size:9.5px;color:#64748B;line-height:1.6;
 border-top:1px solid #E2E8F0;padding-top:10px}}
.cv-r{{display:flex;flex-direction:column;min-height:0;justify-content:center}}
.cover .plan{{flex:0 1 auto;max-height:100%}}
/* 평면도 */
.plan{{width:100%;flex:1 1 auto;min-height:0;background:#F8FAFC;border:1px solid #E2E8F0;
 border-radius:7px}}
.lgs{{display:grid;grid-template-columns:1fr 1fr;gap:3px 12px;margin-top:8px;flex:0 0 auto}}
.lgs.v{{grid-template-columns:1fr}}
.lg{{font-size:9.8px;color:#475569;display:flex;align-items:center;gap:5px;font-weight:600}}
.lg i{{width:9px;height:9px;border-radius:2.5px;flex:0 0 auto}}
.p2{{display:grid;grid-template-columns:1fr 430px;gap:24px;height:100%;min-height:0}}
.p2a{{display:flex;min-height:0}}
.p2b{{overflow:hidden}}
.p3{{display:grid;grid-template-columns:1fr 1fr;gap:26px;height:100%;min-height:0}}
/* 모듈 카드 */
.mg{{display:grid;gap:8px;flex:1 1 auto;min-height:0}}
.mg.c5{{grid-template-columns:repeat(5,1fr)}}
.mg.c4{{grid-template-columns:repeat(4,1fr)}}
.mg.c3{{grid-template-columns:repeat(3,1fr)}}
.mg.c2{{grid-template-columns:repeat(2,1fr)}}
.mg.c1{{grid-template-columns:1fr}}
.mg.end{{grid-template-columns:repeat(2,1fr)}}
/* 카드 내부 타이포는 전부 em — .mc 의 font-size 하나로 균일 축소된다(자동 맞춤용) */
.mc{{border:1px solid var(--bd);border-radius:7px;background:#fff;display:flex;
 flex-direction:column;overflow:hidden;min-height:0;font-size:10px}}
.mh{{display:flex;align-items:center;gap:.7em;background:var(--bg);padding:.7em .9em;
 border-bottom:1px solid var(--bd)}}
.mid{{font-size:1.3em;font-weight:900;color:var(--c);letter-spacing:-.4px;white-space:nowrap}}
.mn{{font-size:1.05em;font-weight:800;line-height:1.2;min-width:0;flex:1 1 auto}}
.mn small{{display:block;font-size:.79em;font-weight:600;color:#8894A5;margin-top:.15em;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.mf{{font-size:1.2em;font-weight:900;color:#334155;text-align:right;line-height:1;white-space:nowrap}}
.mf small{{display:block;font-size:.625em;font-weight:700;color:#93A1B2;margin-top:.2em}}
.mbz{{color:#fff;font-size:.9em;font-weight:800;padding:.45em 1em;letter-spacing:.3px}}
.mbz small{{display:block;font-size:.889em;font-weight:600;opacity:.88;margin-top:.1em}}
.ms{{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}}
.sh{{flex:1 1 auto;min-height:0;border-bottom:1px solid #F1F5F9;padding:.5em .8em;display:flex;
 flex-direction:column;gap:.25em;overflow:hidden}}
.sh:last-child{{border-bottom:0}}
.sl{{display:flex;align-items:center;gap:.5em}}
.sl b{{font-size:1em;font-weight:900;color:var(--c);width:1.9em}}
.sl i{{margin-left:auto;font-size:.88em;font-weight:800;color:#94A3B8;font-style:normal}}
.ss{{font-size:.85em}}
.sn{{font-size:.93em;font-weight:800;color:#1E293B;line-height:1.25}}
.sn small{{display:block;font-size:.839em;font-weight:600;color:#A3AEBD;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.si{{list-style:none;font-size:.88em;line-height:1.4}}
.si li{{display:flex;gap:.45em;align-items:baseline;color:#334155;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.si li b{{font-weight:800;color:#94A3B8;font-size:.909em;font-variant-numeric:tabular-nums}}
.si li i{{font-style:normal;font-weight:800;color:var(--c);font-size:.909em}}
.si li u{{text-decoration:none;color:#A3AEBD}}
.si li em{{font-style:normal;font-size:.83em;font-weight:800;color:#0369A1;background:#EFF8FE;
 padding:0 .35em;border-radius:6px;margin-left:.2em}}
.si li.ph0{{color:#B8C2CE;font-style:italic}}
.si li.more{{color:#0369A1;font-weight:800;font-size:.9em}}
.mpd{{font-size:.83em;font-weight:700;color:#0369A1;background:#EFF8FE;padding:.35em .9em}}
/* 곤돌라 페이지 */
.gpg .pb{{gap:5px;padding-top:9px}}
.gpg .glab{{padding:1.5px 8px}}
.gpg .mg{{gap:7px}}
.gpg .mc{{font-size:9.6px}}
.gpg .si{{line-height:1.32}}
.gsec{{display:flex;flex-direction:column;gap:4px;flex:1 1 0;min-height:0}}
.ecpg .mg{{flex:0 0 auto;grid-auto-rows:minmax(0,auto)}}
.ecpg .pb{{gap:12px}}
.glab{{font-size:9px;font-weight:800;color:#fff;background:#16233A;padding:2.5px 8px;
 border-radius:3px;align-self:flex-start;letter-spacing:.5px}}
.glab.u{{background:#475569}} .glab.e{{background:#C2410C}}
@media print{{body{{background:#fff}}.pg{{margin:0}}}}
</style></head><body>
{''.join(PAGES)}
<script>
/* 자동 맞춤 — 카드 내용이 잘리면 해당 카드의 본문 글자만 단계적으로 줄인다.
   .mc 내부 타이포가 전부 em 이므로 font-size 하나로 균일 축소된다. */
(function () {{
  var MIN = 8.2;
  function clipped(mc) {{
    if (mc.scrollHeight > mc.clientHeight + 1) return true;
    var sh = mc.querySelectorAll('.sh');
    for (var i = 0; i < sh.length; i++)
      if (sh[i].scrollHeight > sh[i].clientHeight + 1) return true;
    return false;
  }}
  document.querySelectorAll('.mc').forEach(function (mc) {{
    var f = parseFloat(getComputedStyle(mc).fontSize);
    var guard = 0;
    while (clipped(mc) && f > MIN && guard++ < 60) {{
      f -= 0.15;
      mc.style.fontSize = f.toFixed(2) + 'px';
    }}
    /* 최소 글자 크기에서도 넘치면, 가장 긴 목록부터 줄이고 남은 건수를 명시한다.
       임의로 감추지 않기 위해 '외 n건'을 남기고 전량은 JSON 에 있다. */
    var guard2 = 0;
    while (clipped(mc) && guard2++ < 200) {{
      var worst = null, worstD = 0;
      mc.querySelectorAll('.sh').forEach(function (sh) {{
        var d = sh.scrollHeight - sh.clientHeight;
        var ul = sh.querySelector('.si');
        var n = ul ? ul.querySelectorAll('li:not(.more):not(.ph0)').length : 0;
        if (n > 1 && d >= worstD) {{ worstD = d; worst = ul; }}
      }});
      if (!worst) break;
      var lis = worst.querySelectorAll('li:not(.more):not(.ph0)');
      lis[lis.length - 1].remove();
      var more = worst.querySelector('li.more');
      var cnt = (more ? parseInt(more.getAttribute('data-n'), 10) : 0) + 1;
      if (!more) {{
        more = document.createElement('li');
        more.className = 'more';
        worst.appendChild(more);
      }}
      more.setAttribute('data-n', cnt);
      more.textContent = '외 ' + cnt + '건 — JSON 참조';
    }}
    if (clipped(mc)) mc.setAttribute('data-clip', '1');
  }});
  document.documentElement.setAttribute('data-fit', 'done');
}})();
</script>
</body></html>'''

# 페이지 수 반영
HTML = HTML.replace('__TOTAL__', str(TOTAL))
open('data/book.html', 'w', encoding='utf-8').write(HTML)
print(f'book.html {len(HTML)//1024} KB · {TOTAL} pages')
