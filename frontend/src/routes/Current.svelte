<script>
  import { onMount } from "svelte";

  let weights = [];
  let canvas;
  let ctx;
  let canvasWidth = 0;
  let canvasHeight = 0;

  const padding = { top: 30, right: 30, bottom: 50, left: 60 };

  // View state
  let offsetX = 0;
  let scale = 1;

  // Drag
  let isDragging = false;
  let dragStartX = 0;
  let dragStartOffset = 0;

  // Momentum
  let velocityX = 0;
  let lastDragX = 0;
  let lastDragTime = 0;
  let animFrameId = null;

  // Hover
  let hoverPoint = null;

  // Gap threshold in days — don't connect points more than this apart
  const GAP_DAYS = 14;

  export let goalWeight = 200;

  onMount(async () => {
    const res = await fetch("http://100.89.197.38:5000/weights");
    weights = await res.json();

    ctx = canvas.getContext("2d");
    resize();

    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("mouseleave", onMouseLeave);
    canvas.addEventListener("wheel", onWheel, { passive: false });

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // Start with a comfortable initial scale so data fills the view
    fitView();
    draw();
  });

  $: goalWeight, draw();

  function resize() {
    canvasWidth = canvas.clientWidth;
    canvasHeight = canvas.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvasWidth * dpr;
    canvas.height = canvasHeight * dpr;
    ctx.scale(dpr, dpr);
    draw();
  }

  function fitView() {
    // Set scale so all points span ~90% of the chart width
    const chartWidth = canvasWidth - padding.left - padding.right;
    const n = weights.length;
    if (n < 2) return;
    // Natural spacing at scale=1 is chartWidth/(n-1)
    // We want total span = chartWidth * scale = chartWidth
    scale = 1;
    offsetX = 0;
  }

  // ---------- interaction ----------

  function onMouseDown(e) {
    cancelMomentum();
    isDragging = true;
    dragStartX = e.clientX;
    dragStartOffset = offsetX;
    lastDragX = e.clientX;
    lastDragTime = performance.now();
    velocityX = 0;
    canvas.style.cursor = "grabbing";
  }

  function onMouseMove(e) {
    if (isDragging) {
      const dx = e.clientX - dragStartX;
      offsetX = dragStartOffset + dx;
      clampOffset();

      const now = performance.now();
      const dt = now - lastDragTime;
      if (dt > 0) velocityX = (e.clientX - lastDragX) / dt;
      lastDragX = e.clientX;
      lastDragTime = now;
      hoverPoint = null;
      draw();
    } else {
      updateHover(e);
      draw();
    }
  }

  function onMouseUp(e) {
    if (!isDragging) return;
    isDragging = false;
    canvas.style.cursor = "grab";
    startMomentum();
  }

  function onMouseLeave() {
    if (isDragging) {
      isDragging = false;
      canvas.style.cursor = "grab";
      startMomentum();
    }
    hoverPoint = null;
    draw();
  }

  function onWheel(e) {
    e.preventDefault();
    cancelMomentum();

    if (e.ctrlKey || e.metaKey) {
      // Pinch-to-zoom
      const factor = e.deltaY > 0 ? 0.92 : 1.08;
      const rect = canvas.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      zoomAt(cursorX, factor);
    } else {
      // Pan (trackpad horizontal scroll or mouse wheel vertical pan)
      const dx = e.shiftKey ? -e.deltaY : -e.deltaX || -e.deltaY;
      offsetX += dx;
      clampOffset();
      draw();
    }
  }

  function zoomAt(cursorX, factor) {
    const oldScale = scale;
    scale = Math.max(0.5, Math.min(scale * factor, 20));
    // Pivot around the data origin (padding + dataPadX) so the point
    // under the cursor stays fixed, matching standard map/image zoom behavior.
    const dataPadX = 30;
    const origin = padding.left + dataPadX;
    const C = cursorX - origin;
    offsetX = C - ((C - offsetX) * scale) / oldScale;
    clampOffset();
    draw();
  }

  function clampOffset() {
    const chartWidth = canvasWidth - padding.left - padding.right;
    const dataPadX = 30;
    const totalWidth = (chartWidth - dataPadX * 2) * scale;
    const minOffset = -(totalWidth - (chartWidth - dataPadX * 2));
    offsetX = Math.max(minOffset, Math.min(0, offsetX));
  }

  function startMomentum() {
    const decay = 0.94;
    function step() {
      if (Math.abs(velocityX) < 0.1) return;
      velocityX *= decay;
      offsetX += velocityX * 16;
      clampOffset();
      draw();
      animFrameId = requestAnimationFrame(step);
    }
    animFrameId = requestAnimationFrame(step);
  }

  function cancelMomentum() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    velocityX = 0;
  }

  // ---------- hover ----------

  function updateHover(e) {
    if (weights.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const pts = getPoints();
    let best = null;
    let bestDist = Infinity;
    for (const p of pts) {
      const d = Math.abs(p.x - mx);
      if (d < bestDist && d < 40) {
        bestDist = d;
        best = p;
      }
    }
    hoverPoint = best;
  }

  // ---------- drawing ----------

  function getPoints() {
    const chartWidth = canvasWidth - padding.left - padding.right;
    const chartHeight = canvasHeight - padding.top - padding.bottom;
    const minW = Math.min(...weights.map((w) => w.weight), goalWeight);
    const maxW = Math.max(...weights.map((w) => w.weight), goalWeight);
    const pad = (maxW - minW) * 0.12 || 2;
    const lo = minW - pad;
    const hi = maxW + pad;
    const range = hi - lo;
    const n = weights.length;
    const dataPadX = 30;
    const spacing = ((chartWidth - dataPadX * 2) * scale) / Math.max(n - 1, 1);

    return weights.map((w, i) => ({
      x: padding.left + dataPadX + i * spacing + offsetX,
      y: padding.top + chartHeight - ((w.weight - lo) / range) * chartHeight,
      weight: w.weight,
      date: w.date,
    }));
  }

  function draw() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // White background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    if (weights.length === 0) return;

    const chartWidth = canvasWidth - padding.left - padding.right;
    const chartHeight = canvasHeight - padding.top - padding.bottom;
    const minW = Math.min(...weights.map((w) => w.weight), goalWeight);
    const maxW = Math.max(...weights.map((w) => w.weight), goalWeight);
    const pad = (maxW - minW) * 0.12 || 2;
    const lo = minW - pad;
    const hi = maxW + pad;
    const range = hi - lo;
    const pts = getPoints();

    // Clip to chart area
    ctx.save();
    ctx.rect(padding.left, padding.top, chartWidth, chartHeight);
    ctx.clip();

    // Draw grid lines
    const gridCount = 5;
    for (let i = 0; i <= gridCount; i++) {
      const y = padding.top + (i / gridCount) * chartHeight;
      ctx.strokeStyle = i === gridCount ? "#ddd" : "#f0f0f0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();
    }

    // Goal weight line
    const goalY =
      padding.top + chartHeight - ((goalWeight - lo) / range) * chartHeight;
    ctx.strokeStyle = "rgba(220, 60, 60, 0.7)";
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, goalY);
    ctx.lineTo(padding.left + chartWidth, goalY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Split into segments across gaps
    const segments = [];
    let seg = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      const daysDiff = daysBetween(weights[i - 1].date, weights[i].date);
      if (daysDiff > GAP_DAYS) {
        segments.push(seg);
        seg = [pts[i]];
      } else {
        seg.push(pts[i]);
      }
    }
    segments.push(seg);

    // Draw smooth line per segment
    ctx.strokeStyle = "#4a90d9";
    ctx.lineWidth = 1.2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const segment of segments) {
      if (segment.length < 2) continue;
      ctx.beginPath();
      drawCatmullRom(ctx, segment);
      ctx.stroke();
    }

    // Draw dots (small, only visible ones)
    for (const p of pts) {
      if (p.x < padding.left - 10 || p.x > padding.left + chartWidth + 10)
        continue;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = "#4a90d9";
      ctx.fill();
    }

    ctx.restore();

    // Y-axis labels
    ctx.textAlign = "right";
    ctx.fillStyle = "#999";
    ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
    for (let i = 0; i <= gridCount; i++) {
      const y = padding.top + (i / gridCount) * chartHeight;
      const val = hi - (i / gridCount) * range;
      ctx.fillText(val.toFixed(1), padding.left - 8, y + 4);
    }

    // X-axis date labels
    drawDateLabels(pts);

    // Hover crosshair + tooltip
    if (
      hoverPoint &&
      hoverPoint.x >= padding.left &&
      hoverPoint.x <= padding.left + chartWidth
    ) {
      drawHover(hoverPoint);
    }
  }

  function drawCatmullRom(ctx, pts) {
    // Catmull-Rom → cubic bezier conversion for ultra-smooth curves
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(i - 1, 0)];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[Math.min(i + 2, pts.length - 1)];

      const tension = 0.5;
      const cp1x = p1.x + ((p2.x - p0.x) * tension) / 3;
      const cp1y = p1.y + ((p2.y - p0.y) * tension) / 3;
      const cp2x = p2.x - ((p3.x - p1.x) * tension) / 3;
      const cp2y = p2.y - ((p3.y - p1.y) * tension) / 3;

      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }
  }

  function drawDateLabels(pts) {
    if (pts.length === 0) return;
    const chartWidth = canvasWidth - padding.left - padding.right;
    const minSpacing = 90; // px between labels
    const maxLabels = Math.floor(chartWidth / minSpacing);
    const step = Math.max(1, Math.ceil(pts.length / maxLabels));

    ctx.fillStyle = "#aaa";
    ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
    ctx.textAlign = "center";

    for (let i = 0; i < pts.length; i += step) {
      const p = pts[i];
      if (p.x < padding.left + 20 || p.x > padding.left + chartWidth - 10)
        continue;
      ctx.fillText(
        formatDate(weights[i].date),
        p.x,
        canvasHeight - padding.bottom + 18,
      );
    }
  }

  function drawHover(p) {
    const chartBottom = canvasHeight - padding.bottom;

    // Vertical line
    ctx.save();
    ctx.strokeStyle = "rgba(100,150,220,0.3)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(p.x, padding.top);
    ctx.lineTo(p.x, chartBottom);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // Highlighted dot
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#4a90d9";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Tooltip
    const label = `${formatDate(p.date)}  ${p.weight.toFixed(1)} lbs`;
    ctx.font = "12px -apple-system, BlinkMacSystemFont, sans-serif";
    const tw = ctx.measureText(label).width;
    const bw = tw + 16;
    const bh = 26;
    let bx = p.x - bw / 2;
    const by = p.y - bh - 12;
    bx = Math.max(
      padding.left + 4,
      Math.min(bx, canvasWidth - padding.right - bw - 4),
    );

    ctx.fillStyle = "rgba(30,40,60,0.85)";
    roundRect(ctx, bx, by, bw, bh, 5);
    ctx.fill();

    ctx.fillStyle = "#fff";
    ctx.textAlign = "center";
    ctx.fillText(label, bx + bw / 2, by + 17);
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.arcTo(x + w, y, x + w, y + r, r);
    ctx.lineTo(x + w, y + h - r);
    ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
    ctx.lineTo(x + r, y + h);
    ctx.arcTo(x, y + h, x, y + h - r, r);
    ctx.lineTo(x, y + r);
    ctx.arcTo(x, y, x + r, y, r);
    ctx.closePath();
  }

  function daysBetween(dateA, dateB) {
    return Math.abs(new Date(dateB) - new Date(dateA)) / 86400000;
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
</script>

<div class="current-box">
  <div class="chart-wrapper">
    <canvas bind:this={canvas} class="chart-canvas" style="cursor: grab;"
    ></canvas>
    <p class="hint">Drag · Scroll to pan · Pinch / Ctrl+scroll to zoom</p>
  </div>
</div>

<style>
  .current-box {
    flex: 1 1 340px;
    min-width: 280px;
    min-height: 60vh;
    border: 1px solid var(--card-border);
    border-radius: 8px;
    background: #ffffff;
    box-shadow: var(--card-shadow);
    overflow: hidden;
  }

  .chart-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 16px;
    box-sizing: border-box;
  }

  .chart-canvas {
    display: block;
    width: 100%;
    height: calc(100% - 24px);
  }

  .hint {
    position: absolute;
    bottom: 6px;
    right: 12px;
    font-size: 10px;
    color: #ccc;
    margin: 0;
    pointer-events: none;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  }
</style>
