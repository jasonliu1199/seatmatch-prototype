"""Automated checks for the SeatMatch web slides and app (webapp-testing style).

usage: python3 test_deck.py <slides index.html> <app index.html>
"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

slides_path, app_path = (pathlib.Path(p).resolve().as_uri() for p in sys.argv[1:3])
fails, notes = [], []

def check(cond, msg):
    (notes if cond else fails).append(('PASS ' if cond else 'FAIL ') + msg)

LAYOUT_JS = r"""
() => {
  const slide = document.querySelector('.slide.active');
  const sr = slide.getBoundingClientRect();
  const foot = slide.querySelector('.foot');
  const fr = foot ? foot.getBoundingClientRect() : null;
  const out = [], intoFoot = [], lowContrast = [];
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return [.2126 * f(m[0]) + .7152 * f(m[1]) + .0722 * f(m[2]), m[3] === undefined ? 1 : m[3]]; };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const b = getComputedStyle(e).backgroundColor; const m = b.match(/[\d.]+/g); if (m && (m.length < 4 || +m[3] > .5)) return b; } return 'rgb(255,255,255)'; };
  slide.querySelectorAll('*').forEach(el => {
    if (el.closest('.foot') || el.closest('svg') && el.tagName !== 'svg') return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const name = (el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '')) + ' "' + (el.textContent || '').trim().slice(0, 18) + '"';
    if (r.right > sr.right + 2 || r.bottom > sr.bottom + 2 || r.left < sr.left - 2 || r.top < sr.top - 2) out.push(name);
    else if (fr && r.bottom > fr.top - 4 && r.top < fr.bottom && el.children.length === 0 && el.textContent.trim()) intoFoot.push(name);
    // text contrast (own text nodes only)
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own) {
      const cs = getComputedStyle(el);
      const [l1, a] = lum(cs.color), [l2] = lum(bgOf(el));
      const ratio = (Math.max(l1, l2) + .05) / (Math.min(l1, l2) + .05);
      const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
      const need = size >= 32 || (size >= 24 && bold) ? 3 : 4.5;
      if (a > .5 && ratio < need) lowContrast.push(name + ' ' + ratio.toFixed(2) + '<' + need);
    }
  });
  return { out: [...new Set(out)].slice(0, 6), intoFoot: [...new Set(intoFoot)].slice(0, 6), lowContrast: [...new Set(lowContrast)].slice(0, 6) };
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')
    # ---------- slides ----------
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.goto(slides_path + '#1')
    page.wait_for_timeout(800)
    n = page.evaluate("document.querySelectorAll('.slide').length")
    for i in range(1, n + 1):
        if i > 1:
            page.keyboard.press('ArrowRight')
        page.wait_for_timeout(2600)
        cur = page.evaluate("[...document.querySelectorAll('.slide')].findIndex(s => s.classList.contains('active')) + 1")
        check(cur == i, f'slide {i}: arrow key navigation lands on slide {i} (got {cur})')
        res = page.evaluate(LAYOUT_JS)
        check(not res['out'], f'slide {i}: nothing spills outside the slide {res["out"]}')
        check(not res['intoFoot'], f'slide {i}: nothing runs into the footer {res["intoFoot"]}')
        check(not res['lowContrast'], f'slide {i}: text contrast meets WCAG AA {res["lowContrast"]}')
        notes_txt = page.evaluate("document.querySelector('.slide.active').dataset.notes || ''")
        check(len(notes_txt) > 0, f'slide {i}: has speaker notes')
    # interactions
    page.goto(slides_path + '#6'); page.reload(); page.wait_for_timeout(600)
    for state, label in (('taken', '有人'), ('away', '暫離'), ('free', '空位')):
        page.click(f'.slide.active .demo-btn[data-state="{state}"]')
        got = page.text_content('#ph-txt')
        check(got == label, f'sensor demo: "{state}" button shows {label} (got {got})')
    page.goto(slides_path + '#7'); page.reload(); page.wait_for_timeout(600)
    total = page.evaluate("['n-free','n-away','n-taken'].reduce((a,id)=>a+ +document.getElementById(id).textContent,0)")
    check(total == 40, f'live map: free + away + taken = 40 (got {total})')
    page.click('#f-match'); page.wait_for_timeout(200)
    m = page.evaluate("document.querySelectorAll('.ldot.match').length")
    check(m >= 2 and m % 2 == 0, f'live map: "2 人＋插座" highlights seats in pairs (got {m})')
    adj = page.evaluate("""() => { const ok = new Set(LG3.tableBlocks(2).map(b => b.join(','))); const by = {};
      [...document.querySelectorAll('.ldot.match')].forEach(d => { const k = [...document.querySelectorAll('.ldot')].indexOf(d); const s = LG3.seats[k]; if (s.zone === 'B') (by[s.table] = by[s.table] || []).push((+s.id.slice(1) - 1) % 6); });
      return Object.values(by).every(v => ok.has(v.sort((a, b) => a - b).join(','))); }""")
    check(adj, 'live map: matched long-table seats sit side by side or face each other')
    page.goto(slides_path + '#8'); page.reload(); page.wait_for_timeout(1500)
    ready = page.evaluate("document.getElementById('appvid').readyState")
    check(ready >= 2, f'app video: slide 8 video loads (readyState {ready})')
    page.click('#vplay'); page.wait_for_timeout(1200)
    playing = page.evaluate("(v => !v.paused && v.currentTime > 0.3)(document.getElementById('appvid'))")
    check(playing, 'app video: the play button starts the video')
    check(page.evaluate("!document.fullscreenElement && getComputedStyle(document.getElementById('vplay')).display === 'none'"), 'app video: plays inside the slide, button hidden while playing')
    page.keyboard.press('ArrowRight'); page.wait_for_timeout(300)
    check(page.evaluate("document.getElementById('appvid').paused"), 'app video: leaving the slide pauses the video')
    page.keyboard.press('n')
    check(page.is_visible('#notes'), 'N key opens the speaker notes')
    rm = browser.new_page(viewport={'width': 1920, 'height': 1080}, reduced_motion='reduce')
    rm.goto(slides_path + '#3'); rm.wait_for_timeout(300)
    anim = rm.evaluate("getComputedStyle(document.querySelector('.slide.active .a-rise')).animationName")
    check(anim == 'none', f'prefers-reduced-motion turns entrance animations off (got {anim})')
    check(not errors, f'no console / page errors {errors[:3]}')

    # ---------- app ----------
    app = browser.new_page(viewport={'width': 375, 'height': 812})
    aerr = []
    app.on('pageerror', lambda e: aerr.append(str(e)))
    app.goto(app_path); app.wait_for_timeout(500)
    check(app.evaluate("document.querySelectorAll('.mdot').length") == 40, 'app: 40 seat dots on the LG3 plan')
    app.click('#n-1'); app.click('#f-single'); app.wait_for_timeout(100)
    zones = app.evaluate("[...document.querySelectorAll('#results .zone')].map(z=>z.textContent)")
    check(zones and all(z == '單人座位' for z in zones), f'app: 1 person + 單人座位 only returns single seats {zones}')
    app.click('#n-1'); app.click('#f-single'); app.click('#f-plug')
    for n in (2, 3, 4):
        app.click(f'#n-{n}'); app.wait_for_timeout(80)
        bad = app.evaluate("""n => { const ok = new Set(LG3.tableBlocks(n).map(b => b.join(',')));
          return [...document.querySelectorAll('#results .ids')].map(e => e.textContent).filter(t => t.startsWith('B')).filter(t => {
            const idx = t.split('、').map(id => (+id.slice(1) - 1) % 6).sort((a, b) => a - b); return !ok.has(idx.join(',')); }); }""", n)
        check(not bad, f'app: {n} people at a long table are seated together {bad}')
    app.click('#f-plug')
    app.click('#n-4'); app.wait_for_timeout(100)
    check(app.is_disabled('#f-single'), 'app: 單人座位 is disabled for 4 people')
    app.click('#show-0'); app.wait_for_timeout(300)
    check(app.is_visible('#v-map'), 'app: "在平面圖顯示" opens the map tab')
    picked = app.evaluate("document.querySelectorAll('.mdot.pick').length")
    check(picked == 4, f'app: picked group of 4 is outlined on the plan (got {picked})')
    app.click('#dot-C4'); app.wait_for_timeout(100)
    check(app.is_visible('#sheet'), 'app: tapping a dot opens the seat sheet')
    small = app.evaluate("[...document.querySelectorAll('button')].filter(b=>{const r=b.getBoundingClientRect();return r.width&&r.height&&(r.height<24||r.width<24)}).length")
    notes.append(f'INFO app: {small} buttons smaller than 24px (map dots are dense by design)')
    check(not aerr, f'app: no page errors {aerr[:3]}')
    browser.close()

print('\n'.join(notes))
print('\n'.join(fails))
print(f'\n{len(notes) - sum(1 for x in notes if x.startswith("INFO"))} passed, {len(fails)} failed')
