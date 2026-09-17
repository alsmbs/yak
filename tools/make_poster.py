# -*- coding: utf-8 -*-
"""한 장짜리 조닝 개요 포스터(HTML). Chromium 인쇄로 PDF·PNG 출력."""
import json, html

D = json.load(open('data/book-data.json', encoding='utf-8'))
M, T = D['modules'], D['totals']
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
ICON = {'피부약·상처 보호': '🩹', '더마·세정·선케어': '🧴', '일반약·여행·생활': '💊',
        '영양·건강 선물': '🎁', '립·눈·다리·구강': '👁', '추천·상담 안내': '⭐'}

def lv_rows(mod, maxc=15, show_brand=True):
    """5단 행. 브랜드존은 배지로 표시."""
    out = []
    for s in mod['shelves']:
        it = s['items']
        if it:
            lead = it[0]['name']
            more = f" 외 {len(it)-1}" if len(it) > 1 else ""
            sub = cut(lead, maxc) + e(more)
            cls = 'new' if all(i.get('new') for i in it) else ''
        elif s['status'] == '안내':
            sub, cls = '<span class="mut">분류·상담 안내</span>', 'gd'
        else:
            sub, cls = '<span class="mut">확장 여유</span>', 'rs'
        out.append(
            f'<div class="lv {cls}"><b>{s["level"]}</b>'
            f'<span class="nd">{cut(s["need"] or s["group"], maxc)}</span>'
            f'<span class="pr">{sub}</span>'
            f'<i>{s["f"] or ""}</i></div>')
    return ''.join(out)

def card(mid, maxc=15):
    m = M[mid]
    c, bg, bd = THEME.get(m['theme'], ('#475569', '#F8FAFC', '#E2E8F0'))
    bz = m['brandZone']
    badge = (f'<div class="bz" style="background:{c}">BRAND · {e(bz["brand"])}</div>' if bz else '')
    pend = (f'<div class="pd">추가 배정 {len(m["pending"])}건</div>' if m['pending'] else '')
    return f'''<div class="card" style="--c:{c};--bg:{bg};--bd:{bd}">
      <div class="hd"><div><div class="cd">{e(mid)}</div>
        <div class="nm">{cut(m["name"],18)}</div>
        <div class="rl">{cut(m["role"] or m["theme"],20)}</div></div>
        <div class="ic">{ICON.get(m["theme"],"")}</div></div>
      <div class="lvs">{lv_rows(m, maxc)}</div>
      <div class="ft">{badge}{pend}<span class="f">{m["skuRows"]} SKU · {m["facings"]}F</span></div>
    </div>'''

def gondola(g):
    mods_d = [f'{g}-D-{i}' for i in (1, 2, 3) if f'{g}-D-{i}' in M]
    mods_u = [f'{g}-U-{i}' for i in (1, 2, 3) if f'{g}-U-{i}' in M]
    th = M[mods_d[0]]['theme']
    c, bg, bd = THEME.get(th, ('#475569', '#F8FAFC', '#E2E8F0'))
    def col(mid):
        m = M[mid]
        bz = m['brandZone']
        rows = ''.join(
            f'<div class="g-lv"><b>{s["level"]}</b><span>'
            f'{cut(s["items"][0]["name"] if s["items"] else (s["need"] or s["group"]), 14)}</span></div>'
            for s in m['shelves'])
        tag = f'<div class="g-bz" style="background:{c}">{e(bz["brand"])}</div>' if bz else ''
        return (f'<div class="g-col"><div class="g-hd">{e(mid.split("-")[-1])} '
                f'<span>{cut(m["name"],15)}</span></div>{rows}{tag}</div>')
    ends = ''.join(
        f'<div class="end" style="--c:{c}">'
        f'<div class="e-hd">{e(s)} {cut(M[f"{g}-{s}"]["name"],13)}</div>'
        + (f'<div class="e-bz" style="background:{c}">BRAND · '
           f'{e(M[f"{g}-{s}"]["brandZone"]["brand"])}</div>'
           if M[f'{g}-{s}']['brandZone'] else
           f'<div class="e-no">{cut(M[f"{g}-{s}"]["shelves"][1]["need"],20)}</div>')
        + '</div>'
        for s in ('EL', 'ER') if f'{g}-{s}' in M)
    title = {'G1': '여드름·피지·세정', 'G2': '흉터·상처·건조', 'G3': '색소·선케어 / 두피·휴식',
             'G4': '비타민·이너뷰티·영양', 'G5': 'PDRN·장벽·수분', 'G6': '립·눈·다리 / 발·걷기'}[g]
    en = {'G1': 'Acne & Pore Care', 'G2': 'Scar & Wound Care', 'G3': 'Tone, Sun & Daily Care',
          'G4': 'Vitamins & Inner Beauty', 'G5': 'PDRN & Barrier Care',
          'G6': 'Lip, Eye & Travel Comfort'}[g]
    return f'''<div class="gon" style="--c:{c};--bg:{bg};--bd:{bd}">
      <div class="g-top"><div><b>{g}</b> {e(title)}<div class="g-en">{e(en)}</div></div>
        <div class="ic">{ICON.get(th,"")}</div></div>
      <div class="g-face"><div class="g-lab">D 입구 방향</div><div class="g-cols">{''.join(col(x) for x in mods_d)}</div></div>
      <div class="g-face"><div class="g-lab u">U · POS 방향</div><div class="g-cols">{''.join(col(x) for x in mods_u)}</div></div>
      <div class="g-ends">{ends}</div></div>'''

# ── 평면도 SVG ────────────────────────────────────────────────────
L = json.load(open('data/kpharmacy-open-final-layout.json', encoding='utf-8'))
S = L['store']
def rot_attr(el):
    """요소 회전을 SVG transform 으로 옮긴다(도면 좌표계 그대로)."""
    r = float(el.get('rotation') or 0)
    if not r % 360:
        return ''
    cx, cy = el['x'] + el['w'] / 2, el['y'] + el['h'] / 2
    return f' transform="rotate({r:.0f} {cx:.0f} {cy:.0f})"'

def bbox(el):
    """회전을 반영한 축정렬 경계(90도 배수 기준)."""
    cx, cy = el['x'] + el['w'] / 2, el['y'] + el['h'] / 2
    w, h = el['w'], el['h']
    if round(float(el.get('rotation') or 0)) % 180:
        w, h = h, w
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

def plan():
    p = [f'<rect x="0" y="0" width="{S["w"]}" height="{S["h"]}" fill="#fff" stroke="#233" stroke-width="70"/>']
    for el in L['elements']:
        code, t = el.get('code'), el['type']
        if t == 'zone' or not code:
            continue
        m = M.get(code)
        c = THEME.get(m['theme'], ('#94A3B8',))[0] if m else '#94A3B8'
        bz = m and m['brandZone']
        p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                 f'height="{el["h"]:.0f}" fill="{c}" fill-opacity="{0.9 if bz else 0.55}" '
                 f'stroke="{"#111" if bz else c}" stroke-width="{60 if bz else 25}"'
                 f'{rot_attr(el)}/>')
    for el in L['elements']:
        if el['type'] in ('checkout', 'counter', 'storageRoom', 'fridge', 'wall'):
            p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                     f'height="{el["h"]:.0f}" fill="#CBD5E1" stroke="#94A3B8" stroke-width="30"'
                     f'{rot_attr(el)}/>')
        if el['type'] == 'door':
            p.append(f'<rect x="{el["x"]:.0f}" y="{el["y"]:.0f}" width="{el["w"]:.0f}" '
                     f'height="{el["h"]:.0f}" fill="#0EA5E9"{rot_attr(el)}/>')

    def lab(x, y, t, size=190, fill='#16233A', w=800, anchor='middle'):
        p.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" font-weight="{w}" '
                 f'fill="{fill}" text-anchor="{anchor}" '
                 f'style="paint-order:stroke;stroke:#fff;stroke-width:60">{html.escape(t)}</text>')

    # 매대 그룹 라벨 — 실제 좌표에서 산출
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
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 + 65
        if k in ('W', 'L', 'B'):
            nm = {'W': 'W1–W5 상단 벽면', 'L': 'L1–L4 좌측 벽면', 'B': 'B1–B8 하단 진입부'}[k]
            if k == 'L':
                p.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="200" font-weight="800" '
                         f'fill="#16233A" text-anchor="middle" transform="rotate(-90 {cx:.0f} {cy:.0f})" '
                         f'style="paint-order:stroke;stroke:#fff;stroke-width:70">{nm}</text>')
            else:
                lab(cx, cy, nm, 200)
        else:
            lab(cx, cy, k, 330)

    # 후방 운영부 라벨
    lab(7100, 800, 'POS · 상담 카운터', 210, '#475569')
    lab(9600, 2050, 'RF1 냉장', 180, '#475569')
    lab(7480, 4450, '조제 · 투약대', 210, '#475569')
    lab(751, 10150, '좌 출입 4m', 170, '#0369A1')
    lab(9767, 10150, '우 출입 4m', 170, '#0369A1')
    return (f'<svg viewBox="-300 -300 {S["w"]+600} {S["h"]+900}" class="plan">' + ''.join(p) + '</svg>')

legend = ''.join(
    f'<div class="lg"><i style="background:{v[0]}"></i>{e(k)}</div>' for k, v in THEME.items())
bz_list = ''.join(
    f'<div class="bzr"><b>{e(k)}</b><span>{e(m["brandZone"]["brand"])}</span>'
    f'<small>{cut(m["brandZone"]["claim"],16)}</small></div>'
    for k, m in M.items() if m['brandZone'])

HTML = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:2000px;background:#fff;color:#16233A;
 font-family:'Noto Sans KR',-apple-system,'Malgun Gothic',sans-serif;padding:26px 30px 20px}}
.top{{display:flex;align-items:flex-end;gap:26px;border-bottom:2.5px solid #16233A;padding-bottom:12px}}
.logo{{font-size:34px;font-weight:900;letter-spacing:-1.2px}}
.logo span{{font-size:13px;font-weight:600;color:#8894A5;letter-spacing:0}}
.ttl{{font-size:20px;font-weight:800}}
.ttl small{{display:block;font-size:11.5px;font-weight:500;color:#7C8A9C;margin-top:3px}}
.chips{{margin-left:auto;display:flex;gap:6px;align-items:center}}
.chip{{font-size:10.5px;font-weight:700;padding:5px 10px;border-radius:20px}}
.rt{{font-size:10px;color:#8894A5;font-weight:700;letter-spacing:.8px;margin-left:12px}}
.sec{{display:flex;align-items:center;gap:8px;margin:16px 0 9px}}
.sn{{background:#16233A;color:#fff;font-size:10.5px;font-weight:800;padding:3px 7px;border-radius:4px}}
.st{{font-size:15px;font-weight:800}}
.se{{font-size:10px;color:#9AA6B6;font-weight:700;letter-spacing:.7px}}
.sr{{margin-left:auto;font-size:10.5px;color:#7C8A9C}}
.grid2{{display:grid;grid-template-columns:660px 1fr;gap:20px}}
.plan{{width:100%;height:auto;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px}}
.lgs{{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin-top:9px}}
.lg{{font-size:10.5px;color:#475569;display:flex;align-items:center;gap:5px}}
.lg i{{width:10px;height:10px;border-radius:3px;display:inline-block}}
.bzs{{margin-top:10px;border-top:1px solid #E2E8F0;padding-top:8px}}
.bzs h4{{font-size:10.5px;color:#64748B;margin-bottom:5px;letter-spacing:.4px}}
.bzr{{display:grid;grid-template-columns:52px 1fr auto;gap:6px;font-size:10px;padding:2.5px 0;
 border-bottom:1px dotted #E8EDF3;align-items:baseline}}
.bzr b{{font-weight:800}} .bzr span{{font-weight:700;color:#0F172A}}
.bzr small{{color:#8894A5;font-size:9px}}
.row5{{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}}
.row4{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}}
.row8{{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}}
.row6{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.card{{border:1px solid var(--bd);border-radius:8px;overflow:hidden;background:#fff}}
.hd{{background:var(--bg);padding:7px 9px;display:flex;justify-content:space-between;
 align-items:flex-start;border-bottom:1px solid var(--bd)}}
.cd{{font-size:15px;font-weight:900;color:var(--c);line-height:1}}
.nm{{font-size:11px;font-weight:800;margin-top:3px}}
.rl{{font-size:9px;color:#8894A5;margin-top:1px}}
.ic{{font-size:14px;opacity:.75}}
.lvs{{padding:3px 5px}}
.lv{{display:grid;grid-template-columns:14px 1fr auto;gap:4px;align-items:baseline;
 padding:3px 3px;border-bottom:1px solid #F1F5F9;font-size:9.5px}}
.lv:last-child{{border:0}}
.lv b{{font-size:9px;font-weight:800;color:var(--c);text-align:center}}
.lv .nd{{font-weight:700;color:#1E293B;line-height:1.25}}
.lv .pr{{display:block;font-size:8.5px;color:#64748B;grid-column:2;line-height:1.2}}
.lv i{{font-style:normal;font-size:8.5px;color:#94A3B8;font-weight:700}}
.lv.gd{{background:#FAFBFC}} .lv.rs{{background:#FDFDFB}}
.lv.new .pr{{color:#0369A1}}
.mut{{color:#A9B4C2}}
.ft{{display:flex;gap:5px;align-items:center;padding:5px 7px;background:#FBFCFD;
 border-top:1px solid #EEF2F6;font-size:8.5px;flex-wrap:wrap}}
.bz{{color:#fff;font-weight:800;padding:2px 6px;border-radius:3px;font-size:8px;letter-spacing:.3px}}
.pd{{color:#0369A1;font-weight:700}}
.ft .f{{margin-left:auto;color:#94A3B8;font-weight:700}}
.gon{{border:1px solid var(--bd);border-radius:9px;overflow:hidden}}
.g-top{{background:var(--bg);padding:8px 10px;display:flex;justify-content:space-between;
 border-bottom:1px solid var(--bd)}}
.g-top b{{font-size:16px;font-weight:900;color:var(--c)}}
.g-top>div:first-child{{font-size:12px;font-weight:800}}
.g-en{{font-size:9px;color:#8894A5;font-weight:600;margin-top:1px}}
.g-face{{padding:5px 6px 2px}}
.g-lab{{font-size:8.5px;font-weight:800;color:#64748B;background:#F1F5F9;
 padding:2px 6px;border-radius:3px;display:inline-block;margin-bottom:4px}}
.g-lab.u{{background:#E8EEF5}}
.g-cols{{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}}
.g-col{{border:1px solid #EDF1F5;border-radius:5px;overflow:hidden}}
.g-hd{{background:#F8FAFC;font-size:8.5px;font-weight:800;padding:3px 5px;color:var(--c);
 border-bottom:1px solid #EDF1F5}}
.g-hd span{{color:#475569;font-weight:700}}
.g-lv{{display:grid;grid-template-columns:11px 1fr;gap:3px;font-size:8.5px;
 padding:2.5px 4px;border-bottom:1px solid #F5F8FA;line-height:1.2}}
.g-lv:last-of-type{{border:0}}
.g-lv b{{color:#94A3B8;font-size:7.5px;text-align:center}}
.g-lv span{{color:#334155}}
.g-bz{{color:#fff;font-size:7.5px;font-weight:800;padding:2px 5px;text-align:center}}
.g-ends{{display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:4px 6px 6px}}
.end{{border:1px solid #EDF1F5;border-radius:5px;padding:4px 6px;background:#FCFDFE}}
.e-hd{{font-size:8.5px;font-weight:800;color:var(--c)}}
.e-bz{{margin-top:3px;color:#fff;font-size:8px;font-weight:800;padding:2px 5px;border-radius:3px;text-align:center}}
.e-no{{margin-top:2px;font-size:8px;color:#94A3B8}}
.foot{{margin-top:14px;padding-top:9px;border-top:1px solid #E2E8F0;display:flex;
 font-size:9.5px;color:#8894A5;gap:18px}}
.foot b{{color:#475569}}
</style></head><body>
<div class="top">
  <div class="logo">K-Pharmacy <span>by ONNURI</span></div>
  <div class="ttl">약국 조닝 &amp; 5단 선반 맵 — 오픈 배정본
    <small>피부 고민부터 여행·영양까지, 위치와 상품군을 한눈에 · 63모듈 315선반 · 우선 진열 {T['baseSku']+T['addSku']}행 / {T['totalF']}F</small></div>
  <div class="chips">
    <span class="chip" style="background:#EFF6FF;color:#1D4ED8">5단 선반</span>
    <span class="chip" style="background:#F0FDF4;color:#15803D">증상별 선택</span>
    <span class="chip" style="background:#FFFBEB;color:#B45309">영양·선물</span>
    <span class="chip" style="background:#FDF2F8;color:#BE185D">브랜드 블록 {T['brandZones']}</span>
    <span class="rt">FLOOR MAP / SHELF THEMES / BRAND ZONES</span>
  </div>
</div>

<div class="grid2">
 <div>
  <div class="sec"><span class="sn">01</span><span class="st">전체 매장 위치도</span>
    <span class="se">FLOOR MAP</span><span class="sr">10,512 × 10,338 mm · 32.9평</span></div>
  {plan()}
  <div class="lgs">{legend}</div>
  <div class="bzs"><h4>브랜드 블록 {T['brandZones']}개 · 엔드캡</h4>{bz_list}</div>
 </div>
 <div>
  <div class="sec"><span class="sn">02</span><span class="st">상단 벽면 W1–W5</span>
    <span class="se">TOP WALL</span><span class="sr">피부·더마 2 + 추천 1 + 영양·선물 2</span></div>
  <div class="row5">{''.join(card(f'W{i}') for i in range(1,6))}</div>
  <div class="sec"><span class="sn">03</span><span class="st">좌측 벽면 L1–L4</span>
    <span class="se">LEFT WALL</span><span class="sr">여행 중 필요한 일반 약국 구색</span></div>
  <div class="row4">{''.join(card(f'L{i}') for i in range(1,5))}</div>
 </div>
</div>

<div class="sec"><span class="sn">04</span><span class="st">중앙 양면 곤돌라 G1–G6</span>
  <span class="se">CENTRAL GONDOLAS</span><span class="sr">D = 입구 방향 / U = POS 방향 · 엔드 12면</span></div>
<div class="row6">{''.join(gondola(f'G{i}') for i in range(1,7))}</div>

<div class="sec"><span class="sn">05</span><span class="st">하단 진입부 B1–B8</span>
  <span class="se">ENTRANCE DISCOVERY</span><span class="sr">좌측 4m · 우측 4m 슬라이딩 도어 · 좌: 증상 탐색 / 우: 더마·신제품</span></div>
<div class="row8">{''.join(card(f'B{i}', 13) for i in range(1,9))}</div>

<div class="foot">
  <span><b>선반 번호</b> S1 = 최상단 → S5 = 최하단</span>
  <span><b>곤돌라·엔드 S1</b> 개구 80mm — 안내 유지</span>
  <span><b>추가 배정</b> {T['addSku']}행 (파란색 표기) · 보류 {T['hold']}행</span>
  <span style="margin-left:auto">대표 상품은 선정 후보이며 최종 취급·페이싱은 실측·거래 확인 후 확정합니다.</span>
</div>
</body></html>'''
open('data/poster.html', 'w', encoding='utf-8').write(HTML)
print("poster.html", len(HTML) // 1024, "KB")
