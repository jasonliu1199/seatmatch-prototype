// SeatMatch: LG3 pilot-area floor plan, redrawn as SVG from the HKUST Library LG3 floor plan.
// Coordinates use the original floor-plan image's pixel grid (1600 × 851) so seat positions line up with it.
(function () {
  const VB = { x: 428, y: 298, w: 376, h: 150 };

  // 40 pilot seats. A = single desks, B = long tables (6 seats each), C = window counter.
  const seats = [];
  [[585,362],[597,354],[609,346],[621,338],[458,413],[470,413],[500,413],[512,413],[546,413],[560,413]]
    .forEach(([x, y], i) => seats.push({ id: 'A' + (i + 1), zone: 'A', x, y, plug: i % 3 !== 2, quiet: true, single: true }));
  [492, 521, 551].forEach((cx, t) => [[cx - 9, 372], [cx + 9, 372], [cx - 9, 383], [cx + 9, 383], [cx - 9, 395], [cx + 9, 395]]
    .forEach(([x, y], i) => seats.push({ id: 'B' + (t * 6 + i + 1), zone: 'B', table: t, x, y, plug: t < 2, quiet: false, single: false })));
  [448, 459, 470, 481, 492, 503, 514, 525, 536, 547, 558, 569]
    .forEach((x, i) => seats.push({ id: 'C' + (i + 1), zone: 'C', x, y: 349, plug: i % 2 === 0 || i >= 6, quiet: true, single: false }));

  const ENTRY = [792, 412];
  const C = { floor: '#FBF6E6', wall: '#16233B', win: '#8EC3E8', wood: '#C9A27A', woodD: '#A9825A', chair: '#E2DCCD', atrium: '#E9E4DA', terrace: '#E3E6E8', shelf: '#7B4A3A', text: '#46505F' };

  function svg(opts) {
    const o = Object.assign({ labels: true }, opts || {});
    const p = [];
    const r = (x, y, w, h, fill, extra) => p.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" ${extra || ''}/>`);
    const t = (x, y, s, txt, extra) => o.labels && p.push(`<text x="${x}" y="${y}" font-size="${s}" fill="${C.text}" font-family="Noto Sans TC, PingFang TC, sans-serif" ${extra || ''}>${txt}</text>`);
    // outside: terrace and the atrium void
    r(VB.x, VB.y, VB.w, VB.h, '#EEF1EC');
    r(430, 302, 147, 34, C.terrace);
    p.push(`<path d="M637 326 Q 700 290 804 276 L 804 398 L 725 398 L 725 353 L 692 353 L 692 326 Z" fill="${C.atrium}"/>`);
    p.push(`<path d="M637 326 Q 700 290 804 276" fill="none" stroke="${C.win}" stroke-width="2.4"/>`);
    // floor
    p.push(`<path d="M440 336 L 577 336 L 577 357 Q 603 337 637 326 L 692 326 L 692 353 L 725 353 L 725 398 L 804 398 L 804 448 L 428 448 L 428 392 L 440 392 Z" fill="${C.floor}"/>`);
    // walls and windows
    p.push(`<path d="M440 392 L 440 336 L 577 336 L 577 357" fill="none" stroke="${C.wall}" stroke-width="1.6"/>`);
    p.push(`<path d="M442 336 L 575 336" stroke="${C.win}" stroke-width="2.4"/>`);
    p.push(`<path d="M577 357 Q 603 337 637 326" fill="none" stroke="${C.wall}" stroke-width="1.6"/><path d="M579 355 Q 604 337 636 327" fill="none" stroke="${C.win}" stroke-width="2.2"/>`);
    p.push(`<path d="M577 360 L 577 407" stroke="${C.wall}" stroke-width="1.6"/>`);
    p.push(`<path d="M637 326 L 692 326 L 692 353 L 725 353 L 725 398 L 784 398" fill="none" stroke="${C.wall}" stroke-width="1.6"/>`);
    p.push(`<path d="M428 392 L 440 392" stroke="${C.wall}" stroke-width="1.6"/>`);
    // window counter (C)
    r(442, 339, 131, 7, C.wood, 'rx="1"');
    for (let x = 453; x < 573; x += 11) p.push(`<line x1="${x}" y1="339" x2="${x}" y2="346" stroke="${C.woodD}" stroke-width=".6"/>`);
    // long tables (B) plus the end table by the wall
    r(463, 367, 7, 33, C.wood, 'rx="1"');
    [486, 515, 545].forEach(x => r(x, 366, 12, 35, C.wood, 'rx="1.5"'));
    [[474, 372], [474, 383], [474, 395]].forEach(([x, y]) => r(x - 3, y - 3, 6, 6, C.chair, 'rx="1"'));
    // tables near the arc and the atrium edge (outside the pilot)
    r(580, 373, 11, 7, C.wood, 'rx="1"'); r(607, 364, 6, 22, C.wood, 'rx="1"');
    [[630, 354, 12, 31], [660, 354, 12, 31], [690, 356, 11, 29]].forEach(([x, y, w, h]) => r(x, y, w, h, C.wood, 'rx="1.5"'));
    r(637, 328, 55, 6, C.wood, 'rx="1"'); r(662, 348, 30, 5, C.wood, 'rx="1"');
    [[624, 361], [624, 372], [648, 361], [648, 372], [654, 361], [654, 372], [678, 361], [678, 372], [684, 361], [684, 372]].forEach(([x, y]) => r(x - 3, y - 3, 6, 6, C.chair, 'rx="1"'));
    // single desks along the arc and the shelves (A)
    [[585, 362], [597, 354], [609, 346], [621, 338]].forEach(([x, y]) => p.push(`<rect x="${x - 5}" y="${y - 9}" width="10" height="6" fill="${C.wood}" transform="rotate(-30 ${x} ${y - 6})" rx="1"/>`));
    [452, 494, 540].forEach((x, i) => { r(x, 404, 26 + (i === 2 ? 4 : 0), 5, C.wood, 'rx="1"'); });
    [[594, 25], [635, 25], [694, 25], [736, 12]].forEach(([x, w]) => r(x, 403, w, 5, C.wood, 'rx="1"'));
    // bookshelves
    for (let x = 431; x < 800; x += 9.6) r(x, 430, 6, 18, C.shelf, 'rx="1"');
    // stairs = entry
    r(785, 399, 17, 29, '#FFFFFF', `stroke="${C.wall}" stroke-width="1"`);
    for (let y = 402; y < 428; y += 3.2) p.push(`<line x1="786" y1="${y}" x2="801" y2="${y}" stroke="${C.wall}" stroke-width=".5"/>`);
    // labels
    t(503, 324, 9, '戶外平台', 'text-anchor="middle" opacity=".7"');
    t(745, 330, 9, '中庭（挑空）', 'text-anchor="middle" opacity=".7"');
    t(444, 333, 6.5, 'C 窗邊長桌', 'font-weight="700" fill="#16233B"');
    t(453, 425, 6.5, 'A 單人座位', 'font-weight="700" fill="#16233B"');
    t(596, 372, 6.5, 'A', 'font-weight="700" fill="#16233B"');
    t(484, 363.5, 6.5, 'B 長桌（每張 6 位）', 'font-weight="700" fill="#16233B"');
    p.push('<rect x="636" y="434" width="28" height="11" rx="3" fill="#FBF6E6"/>');
    t(650, 442.5, 7, '書架', 'font-weight="700" text-anchor="middle"');
    t(793, 394, 6.5, '樓梯／入口', 'text-anchor="end" font-weight="700" fill="#B8590F"');
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VB.x} ${VB.y} ${VB.w} ${VB.h}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="圖書館 LG3 試點區平面圖（按 HKUST Library 平面圖重畫）">${p.join('')}</svg>`;
  }

  // percent position of a floor-plan coordinate inside the drawing
  const pct = (x, y) => ({ left: (x - VB.x) / VB.w * 100 + '%', top: (y - VB.y) / VB.h * 100 + '%' });
  const dist = (x, y) => Math.round(Math.hypot(x - ENTRY[0], y - ENTRY[1]) / 9);

  // Seats at one long table that count as "sitting together", by position index 0–5
  // (0/2/4 = left side top→bottom, 1/3/5 = right side). Side-by-side blocks come first, then facing pairs.
  const BLOCKS = {
    1: [[0], [1], [2], [3], [4], [5]],
    2: [[0, 2], [2, 4], [1, 3], [3, 5], [0, 1], [2, 3], [4, 5]],
    3: [[0, 2, 4], [1, 3, 5], [0, 1, 2], [0, 1, 3], [2, 3, 4], [2, 3, 5]],
    4: [[0, 1, 2, 3], [2, 3, 4, 5]]
  };
  const tableBlocks = n => BLOCKS[n] || [];

  window.LG3 = { VB, seats, ENTRY, svg, pct, dist, tableBlocks };
})();
