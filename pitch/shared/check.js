// Layout check for a deck, run by render.py (loads the deck with ?check and reads #layout-report).
// It reports three things per slide:
//   outside  - an element that leaves the 1456 x 819 slide
//   overflow - an element whose content is larger than its box (text spilling out of a card)
//   overlap  - two separate text blocks whose boxes intersect (wrap an intended overlay in data-allow-overlap)
// Does nothing when the deck is opened or printed normally.
(function () {
  if (!/[?&]check\b/.test(location.search)) return;

  function describe(el) {
    const cls = (el.getAttribute('class') || '').trim();
    const txt = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 48);
    return '<' + el.tagName.toLowerCase() + (cls ? ' .' + cls.split(/\s+/).join('.') : '') + '> "' + txt + '"';
  }
  function ownText(el) {
    for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) return true;
    return false;
  }
  function textBox(el) {
    // tight box around the element's own text (not its padding)
    const range = document.createRange();
    range.selectNodeContents(el);
    const rects = Array.from(range.getClientRects()).filter(r => r.width > 0 && r.height > 0);
    if (!rects.length) return null;
    return {
      left: Math.min(...rects.map(r => r.left)), top: Math.min(...rects.map(r => r.top)),
      right: Math.max(...rects.map(r => r.right)), bottom: Math.max(...rects.map(r => r.bottom)),
    };
  }

  function run() {
    const issues = [];
    document.querySelectorAll('.slide').forEach((s, si) => {
      const n = si + 1;
      const sr = s.getBoundingClientRect();
      const all = Array.from(s.querySelectorAll('*'));
      for (const el of all) {
        if (el.closest('[data-allow-overflow]')) continue;
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;
        const t = 1.5;
        if (r.left < sr.left - t || r.top < sr.top - t || r.right > sr.right + t || r.bottom > sr.bottom + t) {
          issues.push({ slide: n, kind: 'outside', el: describe(el),
            box: [r.left - sr.left, r.top - sr.top, r.right - sr.left, r.bottom - sr.top].map(Math.round) });
        }
        const cs = getComputedStyle(el);
        if (cs.display !== 'inline' && !(el instanceof SVGElement) && el.tagName !== 'IMG') {
          const dx = el.scrollWidth - el.clientWidth, dy = el.scrollHeight - el.clientHeight;
          // large type with a tight line-height pokes a few px out of its line box; that is not a defect
          const tolY = Math.max(3, 0.35 * parseFloat(cs.fontSize || '16'));
          if ((dx > 2 || dy > tolY) && el.clientWidth > 0 && el.clientHeight > 0) {
            issues.push({ slide: n, kind: 'overflow', el: describe(el), by: [dx, dy] });
          }
        }
      }
      // overlap between separate text blocks
      const texts = all.filter(el => ownText(el) && !(el instanceof SVGElement) && !el.closest('svg'))
        .map(el => ({ el, b: textBox(el) })).filter(x => x.b);
      for (let i = 0; i < texts.length; i++) {
        for (let j = i + 1; j < texts.length; j++) {
          const A = texts[i], B = texts[j];
          if (A.el.contains(B.el) || B.el.contains(A.el)) continue;
          if (A.el.closest('[data-allow-overlap]') || B.el.closest('[data-allow-overlap]')) continue;
          const w = Math.min(A.b.right, B.b.right) - Math.max(A.b.left, B.b.left);
          const h = Math.min(A.b.bottom, B.b.bottom) - Math.max(A.b.top, B.b.top);
          if (w > 2 && h > 2) issues.push({ slide: n, kind: 'overlap', a: describe(A.el), b: describe(B.el), by: [Math.round(w), Math.round(h)] });
        }
      }
      // missing images
      s.querySelectorAll('img').forEach(img => {
        if (!img.complete || img.naturalWidth === 0) issues.push({ slide: n, kind: 'broken-image', el: img.getAttribute('src') });
      });
    });
    const pre = document.createElement('pre');
    pre.id = 'layout-report';
    pre.textContent = JSON.stringify({ slides: document.querySelectorAll('.slide').length, issues });
    document.body.appendChild(pre);
  }

  window.addEventListener('load', () => {
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => setTimeout(run, 50));
  });
})();
