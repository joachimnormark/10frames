# =============================================================================
# README
# =============================================================================
# Tenframe-værktøj til addition og subtraktion
#
# Installation og kørsel:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# Testet på: Chrome 124+, Firefox 125+, Safari 17+ (desktop og tablet/touch)
#
# Kendte begrænsninger:
#   - Blå prikker i venstre frame kan ikke trækkes (klik fjerner dem)
#   - Drag blå pool → højre frame er bevidst blokeret
#
# MANUELLE TESTSCENARIER:
#   1. Klik blå pool-prik  → blå i venstre frame; venstre tæller +1
#   2. Klik rød pool-prik  → rød i højre frame; højre tæller +1
#   3. Klik tom venstre celle → blå fra pool; tæller +1
#   4. Klik tom højre celle   → rød fra pool; tæller +1
#   5. Klik besat celle → fjernes; korrekt pool +1
#   6. Drag rød fra højre frame → venstre: rød visuelt; V+1, H-1, pool uændret
#   7. Drag rød fra rød pool   → venstre: rød visuelt; V+1, rød pool -1
#   8. Touch-tap placerer/fjerner prikker
#   9. Touch-drag: ghost følger finger; drop registreres
#  10. Mode-skift: symbol + resultat opdateres straks
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Tenframe-vaerktoej", layout="wide")
st.title("\U0001f522 Tenframe-vaerktoej")

# ── HTML/JS komponent ─────────────────────────────────────────────────────────
# VIGTIGT: plain triple-quoted string – IKKE f-string – for at undgaa konflikter
# mellem Python og JavaScript krøllede parenteser og template literals.
# Ingen Python-vaerdier injiceres; al logik er ren JavaScript.
# ─────────────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<style>
/* ── Reset ──────────────────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
  background:#f0f2f6;
  padding:16px 12px;
  user-select:none;
  -webkit-user-select:none;
}

/* ── Dropdown ───────────────────────────────────────────────────────── */
#controls{margin-bottom:18px;display:flex;align-items:center;gap:10px}
#controls label{font-size:15px;font-weight:600;color:#444}
#mode-select{font-size:15px;padding:6px 14px;border:2px solid #bbb;
  border-radius:8px;cursor:pointer;background:white}

/* ── Hoved-layout ───────────────────────────────────────────────────── */
#main{display:flex;align-items:center;justify-content:center;
  gap:12px;flex-wrap:wrap}

/* ── Pool ───────────────────────────────────────────────────────────── */
.pool-area{display:flex;flex-direction:column;align-items:center;gap:6px}
.pool-label{font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.6px;color:#666}
.pool-box{
  background:white;border:2px solid #ddd;border-radius:10px;padding:8px;
  display:grid;
  grid-template-columns:repeat(2,42px); /* 2 kolonner – aendre her */
  grid-auto-rows:42px;
  gap:6px;width:102px;min-height:210px;align-content:start;
}
/* Prik-stoerrelse i pool: 42×42 – aendre her */
.pool-dot{width:42px;height:42px;border-radius:50%;cursor:grab;
  box-shadow:0 2px 5px rgba(0,0,0,.22);transition:transform .1s,box-shadow .1s}
.pool-dot:hover {transform:scale(1.12);box-shadow:0 4px 8px rgba(0,0,0,.3)}
.pool-dot:active{transform:scale(.93);cursor:grabbing}
.pool-dot.blue{background:#1e88ff} /* ← blaa farve */
.pool-dot.red {background:#e53935} /* ← roed farve */
.pool-count{font-size:20px;font-weight:700;color:#333;
  min-width:24px;text-align:center}

/* ── Tenframe ───────────────────────────────────────────────────────── */
.frame-wrap{display:flex;flex-direction:column;align-items:center;gap:8px}
.tenframe{
  display:grid;
  grid-template-columns:repeat(5,58px); /* celle-bredde */
  grid-template-rows:   repeat(2,58px); /* celle-hoejde */
  border:3px solid #333;border-radius:5px;overflow:hidden;background:#fff;
}
.cell{width:58px;height:58px;border:2px solid #999;display:flex;
  align-items:center;justify-content:center;cursor:pointer;
  position:relative;transition:background .1s}
.cell:hover    {background:#f0f7ff}
.cell.dov      {background:#cce4ff;outline:3px dashed #1e88ff;outline-offset:-2px}
.cell.dov-deny {background:#ffe0e0}

/* Prik-stoerrelse i celle: 46×46 – aendre her */
.dot-cell{width:46px;height:46px;border-radius:50%;pointer-events:none;
  box-shadow:0 2px 5px rgba(0,0,0,.22)}
.dot-cell.blue{background:#1e88ff}
.dot-cell.red {background:#e53935}

/* ── Taeller under frame ─────────────────────────────────────────────── */
.frame-count{font-size:30px;font-weight:700;color:#333;
  min-width:40px;text-align:center}

/* ── Operator ────────────────────────────────────────────────────────── */
.op-sym{font-size:42px;font-weight:700;color:#444;padding:0 2px;align-self:center}

/* ── Resultat-raekke ─────────────────────────────────────────────────── */
#result-row{
  margin:16px auto 0;display:flex;align-items:center;justify-content:center;
  gap:8px;font-size:34px;font-weight:700;color:#222;
  background:white;border-radius:12px;padding:10px 24px;
  box-shadow:0 2px 6px rgba(0,0,0,.09);max-width:420px;
}
#result-row span{display:inline-block;min-width:36px;text-align:center}

/* ── Touch/drag ghost ────────────────────────────────────────────────── */
#drag-ghost{
  position:fixed;width:48px;height:48px;border-radius:50%;
  pointer-events:none;z-index:9999;display:none;
  box-shadow:0 4px 12px rgba(0,0,0,.3);opacity:.82;
  transform:translate(-50%,-50%);
}
</style>
</head>
<body>

<div id="controls">
  <label for="mode-select">Vaelg regneart:</label>
  <select id="mode-select" aria-label="Vaelg addition eller subtraktion">
    <option value="addition">Addition (+)</option>
    <option value="subtraction">Subtraktion (&minus;)</option>
  </select>
</div>

<div id="main">

  <div class="pool-area"
       aria-label="Blaa prikker &ndash; klik for at placere i venstre tenframe">
    <div class="pool-label">Blaa pool</div>
    <div class="pool-box" id="blue-pool-box"
         role="group" aria-label="Blaa pool"></div>
    <div class="pool-count" id="blue-count" aria-live="polite">10</div>
  </div>

  <div class="frame-wrap">
    <div class="tenframe" id="left-frame"
         role="grid" aria-label="Venstre tenframe"></div>
    <div class="frame-count" id="left-count" aria-live="polite">0</div>
  </div>

  <div class="op-sym" id="frame-op" aria-hidden="true">+</div>

  <div class="frame-wrap">
    <div class="tenframe" id="right-frame"
         role="grid" aria-label="Hoejre tenframe"></div>
    <div class="frame-count" id="right-count" aria-live="polite">0</div>
  </div>

  <div class="pool-area"
       aria-label="Roede prikker &ndash; klik for at placere i hoejre tenframe">
    <div class="pool-label">Roed pool</div>
    <div class="pool-box" id="red-pool-box"
         role="group" aria-label="Roed pool"></div>
    <div class="pool-count" id="red-count" aria-live="polite">10</div>
  </div>

</div>

<div id="result-row" aria-live="polite">
  <span id="r-left">0</span>
  <span id="r-op">+</span>
  <span id="r-right">0</span>
  <span>=</span>
  <span id="r-result">0</span>
</div>

<div id="drag-ghost" aria-hidden="true"></div>

<script>
// ================================================================
// TILSTAND
// ================================================================
var state = {
  leftCells:  [null,null,null,null,null,null,null,null,null,null],
  rightCells: [null,null,null,null,null,null,null,null,null,null],
  bluePool: 10,   // startvaerdi – skift her
  redPool:  10,   // startvaerdi – skift her
  mode: 'addition'
};

// Drag-kilde: null | { type: 'blue-pool'|'red-pool'|'right', idx: number|null }
var dragSrc = null;

// Farver – skift her
var COLOR_BLUE = '#1e88ff';
var COLOR_RED  = '#e53935';

// ================================================================
// HJAELPERE
// ================================================================
function el(id) { return document.getElementById(id); }

function countOccupied(cells) {
  var n = 0;
  for (var i = 0; i < cells.length; i++) { if (cells[i] !== null) n++; }
  return n;
}
function firstEmpty(cells) {
  for (var i = 0; i < cells.length; i++) { if (cells[i] === null) return i; }
  return -1;
}

// ================================================================
// RENDER
// ================================================================
function render() {
  var sym = state.mode === 'addition' ? '+' : '\u2212';
  el('frame-op').textContent = sym;
  el('r-op').textContent     = sym;

  renderPool('blue-pool-box', 'blue-count', state.bluePool, 'blue');
  renderPool('red-pool-box',  'red-count',  state.redPool,  'red');
  renderFrame('left-frame',  state.leftCells,  'left');
  renderFrame('right-frame', state.rightCells, 'right');

  var lc = countOccupied(state.leftCells);
  var rc = countOccupied(state.rightCells);
  el('left-count').textContent  = lc;
  el('right-count').textContent = rc;
  el('r-left').textContent      = lc;
  el('r-right').textContent     = rc;
  el('r-result').textContent    = state.mode === 'addition' ? lc + rc : lc - rc;
}

// ── Pool ─────────────────────────────────────────────────────────
function renderPool(boxId, countId, count, color) {
  var box = el(boxId);
  box.innerHTML = '';

  for (var i = 0; i < count; i++) {
    var dot = document.createElement('div');
    dot.className = 'pool-dot ' + color;
    dot.setAttribute('draggable', 'true');
    dot.setAttribute('role', 'button');
    dot.setAttribute('tabindex', '0');
    dot.setAttribute('aria-label', (color === 'blue' ? 'Blaa' : 'Roed') + ' pool-prik');

    // Luk over color med IIFE for korrekt closure i loop
    (function(c) {
      dot.addEventListener('click', function() { placeFromPool(c); });
      dot.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') placeFromPool(c);
      });
      // HTML5 drag – brug string-konkatenation (undgaar escaping-problemer)
      dot.addEventListener('dragstart', function(e) {
        dragSrc = { type: c + '-pool', idx: null };
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', c + '-pool');
      });
      // Touch drag
      dot.addEventListener('touchstart', function(e) {
        dragSrc = { type: c + '-pool', idx: null };
        startTouchDrag(e, c === 'blue' ? COLOR_BLUE : COLOR_RED);
      }, { passive: false });
    })(color);

    box.appendChild(dot);
  }
  el(countId).textContent = count;
}

// ── Frames ───────────────────────────────────────────────────────
function renderFrame(frameId, cells, side) {
  var frame = el(frameId);
  frame.innerHTML = '';

  for (var i = 0; i < 10; i++) {
    var cell = document.createElement('div');
    cell.className = 'cell';
    cell.setAttribute('data-frame', side);
    // Brug String() for eksplicit konvertering – undgaar implicitte coercions
    cell.setAttribute('data-idx', String(i));
    cell.setAttribute('role', 'gridcell');
    cell.setAttribute('aria-label',
      (side === 'left' ? 'Venstre' : 'Hoejre') + ' celle ' + (i + 1) +
      (cells[i] ? ' besat (' + cells[i] + ')' : ' tom')
    );

    if (cells[i] !== null) {
      var dot = document.createElement('div');
      dot.className = 'dot-cell ' + cells[i];

      // Kun roede prikker i hoejre frame kan trækkes (til venstre frame)
      if (cells[i] === 'red' && side === 'right') {
        dot.setAttribute('draggable', 'true');
        (function(idx) {
          dot.addEventListener('dragstart', function(e) {
            dragSrc = { type: 'right', idx: idx };
            e.dataTransfer.effectAllowed = 'move';
            // String-konkatenation for data
            e.dataTransfer.setData('text/plain', 'right-' + idx);
            e.stopPropagation();
          });
          dot.addEventListener('touchstart', function(e) {
            dragSrc = { type: 'right', idx: idx };
            startTouchDrag(e, COLOR_RED);
            e.stopPropagation();
          }, { passive: false });
        })(i);
      }
      cell.appendChild(dot);
    }

    // Klik: tom celle → placer fra pool; besat → fjern
    (function(s, idx) {
      cell.addEventListener('click', function() {
        if (cells[idx] !== null) removeDot(s, idx);
        else                     placeIntoCell(s, idx);
      });
    })(side, i);

    // Drag-over highlighting
    cell.addEventListener('dragover', function(e) {
      if (canDrop(this.getAttribute('data-frame'))) {
        e.preventDefault();
        this.classList.add('dov');
        e.dataTransfer.dropEffect = 'move';
      } else {
        this.classList.add('dov-deny');
      }
    });
    cell.addEventListener('dragleave', function() {
      this.classList.remove('dov', 'dov-deny');
    });
    cell.addEventListener('drop', function(e) {
      e.preventDefault();
      this.classList.remove('dov', 'dov-deny');
      handleDrop(
        this.getAttribute('data-frame'),
        parseInt(this.getAttribute('data-idx'), 10)
      );
    });

    frame.appendChild(cell);
  }
}

// ================================================================
// PLACERING / FJERNELSE
// ================================================================

// Pool-klik → foerste ledige celle i tilsvarende frame
function placeFromPool(color) {
  if (color === 'blue') {
    if (state.bluePool <= 0) return;
    var idx = firstEmpty(state.leftCells);
    if (idx === -1) return;
    state.leftCells[idx] = 'blue';
    state.bluePool--;
  } else {
    if (state.redPool <= 0) return;
    var idx2 = firstEmpty(state.rightCells);
    if (idx2 === -1) return;
    state.rightCells[idx2] = 'red';
    state.redPool--;
  }
  render();
}

// Klik paa tom celle → placer fra tilsvarende pool
function placeIntoCell(side, idx) {
  if (side === 'left') {
    if (state.bluePool <= 0) return;
    state.leftCells[idx] = 'blue';
    state.bluePool--;
  } else {
    if (state.redPool <= 0) return;
    state.rightCells[idx] = 'red';
    state.redPool--;
  }
  render();
}

// Klik paa besat celle → fjern og returner til farve-pool
function removeDot(side, idx) {
  var cells = side === 'left' ? state.leftCells : state.rightCells;
  var color = cells[idx];
  if (!color) return;
  cells[idx] = null;
  if (color === 'blue') state.bluePool++;
  else                  state.redPool++;
  render();
}

// ================================================================
// DRAG & DROP LOGIK
// ================================================================
function canDrop(targetSide) {
  if (!dragSrc) return false;
  if (dragSrc.type === 'blue-pool') return targetSide === 'left';
  if (dragSrc.type === 'red-pool')  return true;               // roed → begge sider
  if (dragSrc.type === 'right')     return targetSide === 'left'; // roed frame → venstre
  return false;
}

function handleDrop(targetSide, targetIdx) {
  if (!dragSrc) return;
  var targetCells = targetSide === 'left' ? state.leftCells : state.rightCells;
  if (targetCells[targetIdx] !== null) { dragSrc = null; return; } // Celle optaget

  if (dragSrc.type === 'blue-pool' && targetSide === 'left') {
    if (state.bluePool <= 0) { dragSrc = null; return; }
    state.leftCells[targetIdx] = 'blue';
    state.bluePool--;

  } else if (dragSrc.type === 'red-pool') {
    if (state.redPool <= 0) { dragSrc = null; return; }
    // Roed visuelt i begge frames; i venstre tæller den som venstre-prik
    if (targetSide === 'left') state.leftCells[targetIdx]  = 'red';
    else                       state.rightCells[targetIdx] = 'red';
    state.redPool--;

  } else if (dragSrc.type === 'right' && targetSide === 'left') {
    var srcIdx = dragSrc.idx;
    if (state.rightCells[srcIdx] === null) { dragSrc = null; return; }
    state.rightCells[srcIdx] = null;
    state.leftCells[targetIdx] = 'red';  // Forbliver roed visuelt; tæller som venstre
    // Ingen pool-aendring; prik flyttes kun
  }

  dragSrc = null;
  render();
}

// Nulstil dragSrc naar musen slippes uden drop-target
document.addEventListener('dragend', function() { dragSrc = null; });

// ================================================================
// MODE-SKIFT
// ================================================================
el('mode-select').addEventListener('change', function(e) {
  state.mode = e.target.value;
  render();
});

// ================================================================
// TOUCH DRAG  (ghost-baseret)
// ================================================================
var ghost = el('drag-ghost');

function startTouchDrag(e, bgColor) {
  e.preventDefault();
  ghost.style.background = bgColor;
  ghost.style.display = 'block';
  var t = e.touches[0];
  ghost.style.left = t.clientX + 'px';
  ghost.style.top  = t.clientY + 'px';
}

document.addEventListener('touchmove', function(e) {
  if (!dragSrc) return;
  e.preventDefault();
  var t = e.touches[0];
  ghost.style.left = t.clientX + 'px';
  ghost.style.top  = t.clientY + 'px';
}, { passive: false });

// Slip: find celle under finger via bounding-box (paalidelig i iframes)
document.addEventListener('touchend', function(e) {
  if (!dragSrc) return;
  ghost.style.display = 'none';

  var t = e.changedTouches[0];
  var allCells = document.querySelectorAll('.cell');
  var hit = null;

  for (var i = 0; i < allCells.length; i++) {
    var r = allCells[i].getBoundingClientRect();
    if (t.clientX >= r.left && t.clientX <= r.right &&
        t.clientY >= r.top  && t.clientY <= r.bottom) {
      hit = allCells[i];
      break;
    }
  }

  if (hit) {
    handleDrop(
      hit.getAttribute('data-frame'),
      parseInt(hit.getAttribute('data-idx'), 10)
    );
  } else {
    dragSrc = null;
  }
}, { passive: false });

document.addEventListener('touchcancel', function() {
  dragSrc = null;
  ghost.style.display = 'none';
});

// ================================================================
// START
// ================================================================
render();
</script>
</body>
</html>"""

# Komponenthoejde: pool (210) + frame (116) + taeller (40) +
# dropdown (50) + resultat (60) + padding ~ 560
components.html(HTML, height=560, scrolling=False)
