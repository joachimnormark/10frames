# app.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Tenframes (Addition/Subtraktion)", layout="wide")
st.title("Tenframes — visuelt værktøj til addition og subtraktion")

mode = st.selectbox("Vælg operation", options=["Addition (+)", "Subtraktion (−)"])

# HTML/CSS/JS komponent
# Bemærk: komponenten håndterer al interaktion i browseren (klik + drag/drop).
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {{
    --svg-w: 760px;
    --svg-h: 220px;
    --cell-size: 36; /* px */
    --gap: 18;       /* mellem tenframes */
    --pool-gap: 24;  /* afstand fra frame til pool */
  }}
  body {{
    margin: 0;
    padding: 8px 12px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f6f7fb;
    color: #222;
  }}
  .container {{
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:12px;
  }}
  .top-row {{
    display:flex;
    align-items:center;
    gap:12px;
  }}
  .canvas-wrap {{
    display:flex;
    align-items:center;
    gap:12px;
    background: white;
    padding:14px;
    border-radius:10px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
  }}
  svg {{
    width: calc(var(--cell-size) * 10 + 2px);
    height: calc(var(--cell-size) * 2 + 2px);
    overflow: visible;
    touch-action: none;
  }}
  .frame-border {{
    fill: none;
    stroke: #cfcfe6;
    stroke-width: 2;
    rx: 6;
    ry: 6;
  }}
  .cell {{
    fill: white;
    stroke: #bdbddf;
    stroke-width: 2;
    rx: 6;
    ry: 6;
  }}
  .grid-line {{
    stroke: #bdbddf;
    stroke-width: 2;
  }}
  .dot-blue {{
    fill: #1e88ff;
    stroke: #ffffff;
    stroke-width: 2;
  }}
  .dot-red {{
    fill: #e53935;
    stroke: #ffffff;
    stroke-width: 2;
  }}
  .pool {{
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:8px;
    min-width:120px;
  }}
  .pool-dots {{
    display:flex;
    gap:8px;
    flex-wrap:wrap;
    justify-content:center;
    max-width:120px;
  }}
  .pool-dot {{
    width:28px;
    height:28px;
    border-radius:50%;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    display:inline-block;
    cursor:grab;
  }}
  .pool-dot:active {{ cursor:grabbing; }}
  .pool-label {{
    font-weight:600;
    color:#333;
  }}
  .counts-row {{
    display:flex;
    align-items:center;
    gap:18px;
    margin-top:8px;
    font-size:18px;
    font-weight:700;
  }}
  .count-box {{
    min-width:80px;
    text-align:center;
  }}
  .symbol {{
    font-size:22px;
    font-weight:800;
  }}
  /* Responsive */
  @media (max-width:900px) {{
    .canvas-wrap {{ flex-direction:column; gap:18px; }}
    .pool {{ flex-direction:row; gap:18px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="canvas-wrap">
    <!-- Blue pool (left) -->
    <div class="pool" id="bluePool">
      <div class="pool-label">Blå prikker</div>
      <div class="pool-dots" id="bluePoolDots"></div>
      <div id="bluePoolCount" style="font-weight:600;"></div>
    </div>

    <!-- Left tenframe SVG -->
    <svg id="leftFrame" viewBox="0 0 360 72" xmlns="http://www.w3.org/2000/svg">
      <!-- background border -->
      <rect x="0" y="0" width="360" height="72" class="frame-border"></rect>
      <!-- cells 2x5 -->
      <!-- We'll create cells via JS -->
    </svg>

    <!-- Symbol between frames -->
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
      <div style="font-size:28px;font-weight:800;">{ '+' if 'Addition' in mode else '−' }</div>
    </div>

    <!-- Right tenframe SVG -->
    <svg id="rightFrame" viewBox="0 0 360 72" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="360" height="72" class="frame-border"></rect>
    </svg>

    <!-- Red pool (right) -->
    <div class="pool" id="redPool">
      <div class="pool-label">Røde prikker</div>
      <div class="pool-dots" id="redPoolDots"></div>
      <div id="redPoolCount" style="font-weight:600;"></div>
    </div>
  </div>

  <!-- Counts under frames -->
  <div class="counts-row">
    <div class="count-box"><span id="leftCount">0</span></div>
    <div class="symbol">{ '+' if 'Addition' in mode else '−' }</div>
    <div class="count-box"><span id="rightCount">0</span></div>
  </div>
</div>

<script>
(function() {{
  const CELL_W = 36;
  const CELL_H = 36;
  const COLS = 5;
  const ROWS = 2;
  const CAPACITY = COLS * ROWS; // 10
  // Pools initial counts (max 10 each)
  let bluePool = CAPACITY;
  let redPool = CAPACITY;

  // Frame state arrays: null | 'blue' | 'red'
  const leftState = Array(CAPACITY).fill(null);
  const rightState = Array(CAPACITY).fill(null);

  // Helper: create cells in an SVG
  function createFrame(svgEl, stateArray, frameName) {{
    // Clear existing children except border (first child)
    while (svgEl.childNodes.length > 1) svgEl.removeChild(svgEl.lastChild);

    for (let r = 0; r < ROWS; r++) {{
      for (let c = 0; c < COLS; c++) {{
        const idx = r * COLS + c;
        const x = c * (CELL_W + 8) + 8;
        const y = r * (CELL_H + 8) + 8;

        // cell rect
        const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', CELL_W);
        rect.setAttribute('height', CELL_H);
        rect.setAttribute('rx', 6);
        rect.setAttribute('ry', 6);
        rect.setAttribute('class', 'cell');
        rect.setAttribute('data-idx', idx);
        rect.setAttribute('data-frame', frameName);
        rect.style.cursor = 'pointer';

        // click handler: toggle placement/removal
        rect.addEventListener('click', (ev) => {{
          const i = parseInt(rect.getAttribute('data-idx'));
          const f = rect.getAttribute('data-frame');
          if (f === 'left') {{
            // clicking left frame: place blue if empty and bluePool>0, else remove
            if (!leftState[i]) {{
              if (bluePool <= 0) return;
              leftState[i] = 'blue';
              bluePool--;
            }} else {{
              // remove and return to appropriate pool (if red removed from left, it returns to red pool)
              const color = leftState[i];
              leftState[i] = null;
              if (color === 'blue') bluePool++;
              else if (color === 'red') redPool++;
            }}
          }} else {{
            // right frame: place red if empty and redPool>0, else remove
            if (!rightState[i]) {{
              if (redPool <= 0) return;
              rightState[i] = 'red';
              redPool--;
            }} else {{
              const color = rightState[i];
              rightState[i] = null;
              if (color === 'red') redPool++;
              else if (color === 'blue') bluePool++;
            }}
          }}
          renderAll();
        }});

        // allow drop on cells
        rect.addEventListener('dragover', (e) => {{
          e.preventDefault();
        }});
        rect.addEventListener('drop', (e) => {{
          e.preventDefault();
          const data = e.dataTransfer.getData('text/plain');
          // data format: color|source (e.g., "red|pool" or "red|right:3")
          if (!data) return;
          const parts = data.split('|');
          const color = parts[0];
          const source = parts[1] || '';
          const i = parseInt(rect.getAttribute('data-idx'));
          const f = rect.getAttribute('data-frame');

          // Only allow dropping if target cell empty
          if (f === 'left') {{
            if (leftState[i]) return;
            // If dragging red into left: it remains red but counts as left occupancy
            if (color === 'red') {{
              leftState[i] = 'red';
              // remove from source
              if (source.startsWith('right:')) {{
                const idxSrc = parseInt(source.split(':')[1]);
                rightState[idxSrc] = null;
              }} else if (source === 'redPool') {{
                redPool = Math.max(0, redPool - 1);
              }}
            }} else if (color === 'blue') {{
              // blue dragged into left (from blue pool) -> place blue
              leftState[i] = 'blue';
              if (source === 'bluePool') bluePool = Math.max(0, bluePool - 1);
            }}
          }} else {{
            // dropping into right frame
            if (rightState[i]) return;
            if (color === 'red') {{
              rightState[i] = 'red';
              if (source.startsWith('right:')) {{
                const idxSrc = parseInt(source.split(':')[1]);
                rightState[idxSrc] = null;
              }} else if (source === 'redPool') {{
                redPool = Math.max(0, redPool - 1);
              }} else if (source.startsWith('left:')) {{
                const idxSrc = parseInt(source.split(':')[1]);
                leftState[idxSrc] = null;
              }}
            }} else if (color === 'blue') {{
              // allow blue into right? We'll allow but it will count as right occupancy
              rightState[i] = 'blue';
              if (source === 'bluePool') bluePool = Math.max(0, bluePool - 1);
            }}
          }}
          renderAll();
        }});

        svgEl.appendChild(rect);

        // if occupied, draw dot
        const dot = document.createElementNS('http://www.w3.org/2000/svg','circle');
        dot.setAttribute('cx', x + CELL_W/2);
        dot.setAttribute('cy', y + CELL_H/2);
        dot.setAttribute('r', 12);
        dot.setAttribute('data-idx', idx);
        dot.setAttribute('data-frame', frameName);
        dot.style.pointerEvents = 'none'; // clicks handled by rect
        svgEl.appendChild(dot);
      }}
    }}
  }}

  // Pools rendering
  function renderPools() {{
    const bluePoolDots = document.getElementById('bluePoolDots');
    const redPoolDots = document.getElementById('redPoolDots');
    bluePoolDots.innerHTML = '';
    redPoolDots.innerHTML = '';

    // show up to CAPACITY small draggable dots (visual)
    for (let i = 0; i < bluePool; i++) {{
      const d = document.createElement('div');
      d.className = 'pool-dot';
      d.style.background = '#1e88ff';
      d.setAttribute('draggable', 'true');
      d.setAttribute('data-color', 'blue');
      d.addEventListener('dragstart', (e) => {{
        e.dataTransfer.setData('text/plain', 'blue|bluePool');
      }});
      bluePoolDots.appendChild(d);
    }}
    for (let i = 0; i < redPool; i++) {{
      const d = document.createElement('div');
      d.className = 'pool-dot';
      d.style.background = '#e53935';
      d.setAttribute('draggable', 'true');
      d.setAttribute('data-color', 'red');
      d.addEventListener('dragstart', (e) => {{
        e.dataTransfer.setData('text/plain', 'red|redPool');
      }});
      redPoolDots.appendChild(d);
    }}

    document.getElementById('bluePoolCount').innerText = `${{bluePool}}`;
    document.getElementById('redPoolCount').innerText = `${{redPool}}`;
  }}

  // Render frames and dots based on state arrays
  function renderFrames() {{
    const leftSvg = document.getElementById('leftFrame');
    const rightSvg = document.getElementById('rightFrame');

    // ensure cells exist
    createFrame(leftSvg, leftState, 'left');
    createFrame(rightSvg, rightState, 'right');

    // Now set dot visibility/colors
    // left
    for (let i = 0; i < CAPACITY; i++) {{
      const dot = leftSvg.querySelector(`circle[data-idx='{i}']`);
      const rect = leftSvg.querySelector(`rect[data-idx='{i}']`);
      if (!dot || !rect) continue;
      const val = leftState[i];
      if (val) {{
        dot.style.display = 'block';
        dot.setAttribute('class', val === 'blue' ? 'dot-blue' : 'dot-red');
        dot.style.pointerEvents = 'auto';
        // make dot draggable from left frame (so red can be moved back)
        dot.setAttribute('draggable', 'true');
        dot.addEventListener('dragstart', (e) => {{
          // source left:i
          e.dataTransfer.setData('text/plain', `${{val}}|left:${{i}}`);
        }});
      }} else {{
        dot.style.display = 'none';
        dot.removeAttribute('draggable');
      }}
    }}

    // right
    for (let i = 0; i < CAPACITY; i++) {{
      const dot = rightSvg.querySelector(`circle[data-idx='{i}']`);
      const rect = rightSvg.querySelector(`rect[data-idx='{i}']`);
      if (!dot || !rect) continue;
      const val = rightState[i];
      if (val) {{
        dot.style.display = 'block';
        dot.setAttribute('class', val === 'blue' ? 'dot-blue' : 'dot-red');
        dot.style.pointerEvents = 'auto';
        dot.setAttribute('draggable', 'true');
        dot.addEventListener('dragstart', (e) => {{
          e.dataTransfer.setData('text/plain', `${{val}}|right:${{i}}`);
        }});
      }} else {{
        dot.style.display = 'none';
        dot.removeAttribute('draggable');
      }}
    }}
  }}

  // Update counts under frames
  function updateCounts() {{
    const leftCount = leftState.filter(x => x !== null).length;
    const rightCount = rightState.filter(x => x !== null).length;
    document.getElementById('leftCount').innerText = leftCount;
    document.getElementById('rightCount').innerText = rightCount;
  }}

  // Render everything
  function renderAll() {{
    renderPools();
    renderFrames();
    updateCounts();
  }}

  // Initial render
  renderAll();

  // Make pools clickable as alternative to drag: clicking a pool dot will place into first empty cell
  document.getElementById('bluePoolDots').addEventListener('click', (e) => {{
    if (bluePool <= 0) return;
    // place into first empty left cell
    const idx = leftState.findIndex(x => x === null);
    if (idx === -1) return;
    leftState[idx] = 'blue';
    bluePool--;
    renderAll();
  }});
  document.getElementById('redPoolDots').addEventListener('click', (e) => {{
    if (redPool <= 0) return;
    const idx = rightState.findIndex(x => x === null);
    if (idx === -1) return;
    rightState[idx] = 'red';
    redPool--;
    renderAll();
  }});

  // Also allow clicking on dots in frames to remove them (return to pool)
  // We already handle clicks on rects to toggle; but for touch devices, ensure taps on dots also toggle:
  document.addEventListener('click', (e) => {{
    // if clicked inside an svg circle, find its frame and idx
    const target = e.target;
    if (target.tagName === 'circle' && target.hasAttribute('data-idx')) {{
      const idx = parseInt(target.getAttribute('data-idx'));
      const frame = target.getAttribute('data-frame');
      if (frame === 'left') {{
        const color = leftState[idx];
        if (!color) return;
        leftState[idx] = null;
        if (color === 'blue') bluePool++;
        else if (color === 'red') redPool++;
      }} else if (frame === 'right') {{
        const color = rightState[idx];
        if (!color) return;
        rightState[idx] = null;
        if (color === 'red') redPool++;
        else if (color === 'blue') bluePool++;
      }}
      renderAll();
    }}
  }});

  // Prevent default drag behavior on document
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());

}})();
</script>
</body>
</html>
"""

# Embed the component; set height to allow interaction
components.html(html, height=420, scrolling=True)
