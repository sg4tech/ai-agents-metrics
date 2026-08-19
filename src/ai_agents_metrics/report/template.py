"""Self-contained HTML template for the AI Agents Metrics report.

The template is a single string with four substitution placeholders:
- ``{DATA_JSON}``        — serialised report data dict (JSON)
- ``{GENERATED_AT}``    — human-readable generation timestamp
- ``{GRANULARITY_LABEL}`` — e.g. "Daily buckets"
- ``{GRAN_NOUN}``        — e.g. "day" or "week"

All chart rendering happens in the browser via embedded vanilla JS / Canvas 2D.
No external requests are made at generation time or at view time.
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Agents Metrics Report</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f8fafc;
    color: #1e293b;
    padding: 32px 24px;
    min-height: 100vh;
  }
  header { margin-bottom: 20px; }
  header h1 {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
  }
  header p { font-size: 13px; color: #64748b; }
  .report-controls { display:flex; align-items:end; gap:10px; flex-wrap:wrap; margin:16px 0 20px; }
  .report-field { display:flex; flex-direction:column; gap:4px; }
  .report-field label { font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase; }
  .report-field select, .report-field input {
    height:36px; border:1px solid #cbd5e1; border-radius:7px;
    background:#fff; color:#1e293b; padding:0 10px; font:inherit; font-size:13px;
  }
  .report-field input:disabled { opacity:.5; background:#f1f5f9; }

  /* charts grid */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(480px, 100%), 1fr));
    gap: 24px;
  }
  .card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
    padding: 24px;
  }
  .card h2 {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 4px;
  }
  .card .subtitle {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 16px;
  }
  canvas { display: block; width: 100%; }
  .legend {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-top: 12px;
    font-size: 12px;
    color: #475569;
  }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
  .legend-item[data-toggleable] { cursor: pointer; user-select: none; transition: opacity .15s; }
  .legend-item[data-toggleable]:hover { opacity: .75; }
  .legend-item[data-toggleable].off { opacity: .35; text-decoration: line-through; }

  /* section dividers */
  .section-header {
    margin: 32px 0 16px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid #e2e8f0;
    display: flex;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
  }
  .section-header h3 {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin: 0;
  }
  .section-header p {
    font-size: 12px;
    color: #94a3b8;
    margin: 0;
  }
  .src-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
    padding: 2px 7px;
    border-radius: 4px;
  }
  .src-badge.history { background: #f0fdf4; color: #15803d; }

  /* warehouse-state callout */
  .callout {
    margin: 0 0 18px;
    padding: 10px 14px;
    background: #fef3c7;
    border-left: 3px solid #f59e0b;
    border-radius: 4px;
    font-size: 12px;
    color: #78350f;
    line-height: 1.5;
  }
  .callout strong { font-weight: 600; }
  .callout code {
    background: #fde68a;
    padding: 2px 7px;
    border-radius: 3px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-weight: 600;
    color: #78350f;
  }
  .callout:empty { display: none; }
</style>
</head>
<body>
<header>
  <h1>AI Agents Metrics</h1>
  <p>Generated {GENERATED_AT} &nbsp;·&nbsp; {GRANULARITY_LABEL}</p>
</header>

<div class="report-controls" aria-label="Report filters">
  <div class="report-field"><label for="project-select">Project</label><select id="project-select"></select></div>
  <div class="report-field"><label for="period-preset">Trend period</label>
    <select id="period-preset"><option value="all">All time</option>
      <option value="30">Last 30 days</option><option value="90">Last 90 days</option>
      <option value="365">Last year</option><option value="custom">Custom dates</option></select></div>
  <div class="report-field"><label for="period-from">From</label><input id="period-from" type="date" disabled></div>
  <div class="report-field"><label for="period-to">To</label><input id="period-to" type="date" disabled></div>
</div>

<div id="sh-activity" class="section-header"></div>
<div class="grid">

  <div class="card">
    <h2>Session Activity</h2>
    <p class="subtitle">AI-agent threads per {GRAN_NOUN} · source: warehouse</p>
    <canvas id="c1" height="240"></canvas>
    <div class="legend" id="c1-legend"></div>
  </div>

</div>

<div id="sh-history" class="section-header"></div>
<div class="callout" id="warehouse-callout"></div>
<div class="grid">

  <div class="card">
    <h2>Sessions per Thread</h2>
    <p class="subtitle" id="c2-subtitle"></p>
    <canvas id="c2" height="240"></canvas>
    <div class="legend" id="c2-legend"></div>
  </div>

  <div class="card">
    <h2 id="c3-title">Tokens Spent</h2>
    <p class="subtitle" id="c3-subtitle"></p>
    <canvas id="c3" height="240"></canvas>
    <div class="legend" id="c3-legend"></div>
  </div>

</div>

<div id="sh-practice" class="section-header"></div>
<div class="grid" id="grid-practice">

  <div class="card" id="c5-card" style="grid-column: 1 / -1;">
    <h2>Practice Events by Name</h2>
    <p class="subtitle" id="c5-subtitle"></p>
    <canvas id="c5" height="280"></canvas>
    <div class="legend" id="c5-legend"></div>
  </div>

</div>

<script>
const FULL_DATA = {DATA_JSON};
const PROJECT_REPORTS = FULL_DATA.project_reports || { current: FULL_DATA };
let PROJECT_DATA = PROJECT_REPORTS[FULL_DATA.selected_project] || FULL_DATA;
let DATA = PROJECT_DATA;

function shiftedDate(dateText, days) {
  const date = new Date(dateText + 'T00:00:00Z');
  date.setUTCDate(date.getUTCDate() + days); return date.toISOString().slice(0, 10);
}

function filteredReportData(from, to) {
  const source = PROJECT_DATA.daily_filter_data || PROJECT_DATA;
  const indices = [];
  for (let i = 0; i < (source.buckets || []).length; i++) {
    const bucket = source.buckets[i];
    if ((!from || bucket >= from) && (!to || bucket <= to)) indices.push(i);
  }
  const select = values => indices.map(i => values[i]);
  const data = Object.assign({}, source, {
    buckets: select(source.buckets || []),
    chart1_threads: select(source.chart1_threads || []),
    chart2_bar: select(source.chart2_bar || []),
    chart2_line: select(source.chart2_line || []),
    chart3_series: (source.chart3_series || []).map(series =>
      Object.assign({}, series, { values: select(series.values || []) })),
  });
  data.history_date_from = data.buckets.length ? data.buckets[0] : null;
  data.history_date_to = data.buckets.length ? data.buckets[data.buckets.length - 1] : null;
  if (PROJECT_DATA.summary) data.summary = Object.assign({}, PROJECT_DATA.summary, {
    total_threads: data.chart1_threads.reduce((sum, value) => sum + value, 0),
    total_sessions: data.chart2_bar.reduce((sum, value) => sum + value, 0),
    date_from: data.history_date_from, date_to: data.history_date_to,
  });
  return data;
}

function applyPeriodFilter() {
  const preset = document.getElementById('period-preset');
  const fromInput = document.getElementById('period-from');
  const toInput = document.getElementById('period-to');
  if (!preset || !fromInput || !toInput) return;
  const custom = preset.value === 'custom'; fromInput.disabled = !custom; toInput.disabled = !custom;
  if (preset.value === 'all') { DATA = PROJECT_DATA; render(); return; }
  let from = custom ? fromInput.value : ''; let to = custom ? toInput.value : '';
  if (!custom && PROJECT_DATA.history_date_to) {
    to = PROJECT_DATA.history_date_to; from = shiftedDate(to, -(Number(preset.value) - 1));
  }
  DATA = filteredReportData(from, to); render();
}

function applyProjectSelection() {
  const project = document.getElementById('project-select');
  if (!project || !PROJECT_REPORTS[project.value]) return;
  PROJECT_DATA = PROJECT_REPORTS[project.value];
  document.getElementById('period-preset').value = 'all';
  document.getElementById('period-from').value = PROJECT_DATA.history_date_from || '';
  document.getElementById('period-to').value = PROJECT_DATA.history_date_to || '';
  applyPeriodFilter();
}

function initializeReportControls() {
  const project = document.getElementById('project-select');
  for (const path of Object.keys(PROJECT_REPORTS)) {
    const option = document.createElement('option'); option.value = path;
    option.textContent = path === '__all_projects__' ? 'All projects' : path;
    option.selected = path === FULL_DATA.selected_project; project.appendChild(option);
  }
  project.addEventListener('change', applyProjectSelection);
  document.getElementById('period-from').value = PROJECT_DATA.history_date_from || '';
  document.getElementById('period-to').value = PROJECT_DATA.history_date_to || '';
  document.getElementById('period-preset').addEventListener('change', applyPeriodFilter);
  document.getElementById('period-from').addEventListener('change', applyPeriodFilter);
  document.getElementById('period-to').addEventListener('change', applyPeriodFilter);
}

// ── series toggle state ───────────────────────────────────────────────────────

// Chart 3's series count depends on how many distinct models appear in the
// data, so c3 toggles are initialized dynamically in render().
const seriesToggles = { c1: [true], c3: [] };

function toggleSeries(chartId, idx) {
  const t = seriesToggles[chartId];
  // Keep at least one series visible.
  if (t.filter(Boolean).length === 1 && t[idx]) return;
  t[idx] = !t[idx];
  redrawStackedChart(chartId);
}

function redrawStackedChart(chartId) {
  const d = DATA;
  if (chartId === 'c1') {
    renderC1Legend();
    drawStackedBar('c1', d.buckets, [d.chart1_threads],
      ['#22c55e'], false, '', seriesToggles.c1);
  } else if (chartId === 'c3') {
    renderC3Legend();
    const pfx = d.chart3_mode === 'cost' ? '$' : '';
    const sArr = (d.chart3_series || []).map(s => s.values);
    const cArr = (d.chart3_series || []).map(s => s.color);
    drawStackedBar('c3', d.buckets, sArr, cArr, true, pfx, seriesToggles.c3);
  }
}

function makeLegendItem(color, label, chartId, idx) {
  const on = seriesToggles[chartId][idx];
  return '<div class="legend-item' + (on ? '' : ' off') + '" data-toggleable="1" ' +
    'data-chart="' + chartId + '" data-idx="' + idx + '" ' +
    'onclick="toggleSeries(this.dataset.chart, +this.dataset.idx)">' +
    '<div class="legend-dot" style="background:' + color + '"></div>' + label + '</div>';
}

// ── utilities ────────────────────────────────────────────────────────────────

function fmt(n) {
  if (n === null || n === undefined) return '';
  const abs = Math.abs(n);
  if (abs >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (abs >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (abs >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  if (abs < 1 && abs > 0) return n.toFixed(3);
  return n % 1 === 0 ? n.toString() : n.toFixed(2);
}

function niceMax(v) {
  if (v <= 0) return 1;
  const magnitude = Math.pow(10, Math.floor(Math.log10(v)));
  const steps = [1, 2, 2.5, 5, 10];
  for (const s of steps) {
    if (magnitude * s >= v) return magnitude * s;
  }
  return magnitude * 10;
}

// Returns { max, clipped, threshold } — clips Y axis when outliers skew scale.
// Uses median as the baseline: if max > 4× median, the top values are outliers.
// The cap is floored at rawMax/5 so that on skewed distributions (a low
// median with a very large rawMax) the cap never ends up >5× below rawMax —
// that failure mode produced severely off-scale bars on real cost data,
// rendering every non-outlier bar indistinguishable.
function smartMax(values) {
  const valid = values.filter(v => v != null).sort((a, b) => a - b);
  if (!valid.length) return { max: 1, clipped: false };
  const rawMax = valid[valid.length - 1];
  if (valid.length <= 2) return { max: niceMax(rawMax), clipped: false };
  const mid = Math.floor(valid.length / 2);
  const median = valid.length % 2 ? valid[mid] : (valid[mid - 1] + valid[mid]) / 2;
  if (median > 0 && rawMax > 4 * median) {
    const cap = niceMax(Math.max(median * 2.5, rawMax / 5));
    return { max: cap, clipped: true, threshold: cap };
  }
  return { max: niceMax(rawMax), clipped: false };
}

function setupCanvas(id) {
  const el = document.getElementById(id);
  const dpr = window.devicePixelRatio || 1;
  const rect = el.parentElement.getBoundingClientRect();
  const w = rect.width - 48;
  // Cache the intended height: setting el.height reflects back to the attribute,
  // so reading getAttribute on a re-draw would see the inflated dpr-multiplied value.
  if (!el.dataset.intendedHeight) el.dataset.intendedHeight = el.getAttribute('height');
  const h = parseInt(el.dataset.intendedHeight);
  el.width = w * dpr;
  el.height = h * dpr;
  el.style.width = w + 'px';
  el.style.height = h + 'px';
  const ctx = el.getContext('2d');
  ctx.scale(dpr, dpr);
  return { ctx, w, h };
}

function drawEmpty(ctx, w, h) {
  ctx.fillStyle = '#94a3b8';
  ctx.font = '13px system-ui';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('No data available', w / 2, h / 2);
}

function drawAxes(ctx, ML, MT, cw, ch) {
  ctx.strokeStyle = '#e2e8f0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(ML, MT);
  ctx.lineTo(ML, MT + ch);
  ctx.lineTo(ML + cw, MT + ch);
  ctx.stroke();
}

function drawYGrid(ctx, ML, MT, cw, ch, maxVal, steps, yPrefix) {
  for (let i = 0; i <= steps; i++) {
    const y = MT + ch - (i / steps) * ch;
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(ML, y);
    ctx.lineTo(ML + cw, y);
    ctx.stroke();
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText((yPrefix || '') + fmt((i / steps) * maxVal), ML - 6, y);
  }
}

function drawXLabels(ctx, labels, ML, MT, cw, ch, step) {
  const n = labels.length;
  const gap = cw / n;
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'top';
  for (let i = 0; i < n; i += step) {
    const x = ML + i * gap + gap / 2;
    ctx.save();
    ctx.translate(x, MT + ch + 6);
    ctx.rotate(-Math.PI / 4);
    ctx.fillText(labels[i], 0, 0);
    ctx.restore();
  }
}

// ── chart 1: stacked bar by goal type ────────────────────────────────────────

function drawStackedBar(id, labels, series, colors, useSmartMax, labelPrefix, toggles) {
  const { ctx, w, h } = setupCanvas(id);
  const activeSeries = series.map((s, i) => (!toggles || toggles[i]) ? s : s.map(() => 0));
  const totals = labels.map((_, i) => activeSeries.reduce((s, ser) => s + (ser[i] || 0), 0));
  if (!labels.length || Math.max(...totals) === 0) { drawEmpty(ctx, w, h); return; }

  const ML = 52, MR = 16, MT = 20, MB = 68;
  const cw = w - ML - MR, ch = h - MT - MB;
  const { max: maxVal, clipped } = useSmartMax ? smartMax(totals) : { max: niceMax(Math.max(...totals)), clipped: false };
  const n = labels.length;
  const gap = cw / n;
  const barW = Math.max(3, gap * 0.65);
  const step = Math.max(1, Math.ceil(n / 12));

  drawYGrid(ctx, ML, MT, cw, ch, maxVal, 4, labelPrefix);
  drawAxes(ctx, ML, MT, cw, ch);

  if (clipped) {
    ctx.strokeStyle = '#fca5a5';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(ML, MT);
    ctx.lineTo(ML + cw, MT);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#fca5a5';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText('clipped', ML + 4, MT - 2);
  }

  for (let i = 0; i < n; i++) {
    let base = 0;
    const total = totals[i];
    const isOutlier = clipped && total > maxVal;
    for (let s = 0; s < activeSeries.length; s++) {
      const v = activeSeries[s][i] || 0;
      if (v === 0) { base += v; continue; }
      const x = ML + i * gap + (gap - barW) / 2;
      const clampedBase = Math.min(base, maxVal);
      const clampedTop = Math.min(base + v, maxVal);
      const segH = (clampedTop - clampedBase) / maxVal * ch;
      if (segH <= 0) { base += v; continue; }
      const y = MT + ch - clampedTop / maxVal * ch;
      const isTop = (s === activeSeries.length - 1) || activeSeries.slice(s + 1).every(ser => !ser[i]);
      ctx.fillStyle = isOutlier ? colors[s] + 'aa' : colors[s];
      ctx.beginPath();
      ctx.roundRect(x, y, barW, segH, [isTop && !isOutlier ? 3 : 0, isTop && !isOutlier ? 3 : 0, 0, 0]);
      ctx.fill();
      base += v;
    }
    // Total label — always use fmt() for readability
    if (total > 0) {
      const labelY = isOutlier ? MT + 2 : MT + ch - Math.min(total, maxVal) / maxVal * ch;
      if (!isOutlier && labelY < MT + 4) continue;
      ctx.fillStyle = isOutlier ? '#dc2626' : '#475569';
      ctx.font = 'bold 10px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = isOutlier ? 'top' : 'bottom';
      ctx.fillText((labelPrefix || '') + fmt(total), ML + i * gap + gap / 2, labelY + (isOutlier ? 2 : -2));
    }
  }

  drawXLabels(ctx, labels, ML, MT, cw, ch, step);
}

// ── chart 2: combo bar + line ────────────────────────────────────────────────

function drawCombo(id, labels, barValues, lineValues, barColor, lineColor) {
  const { ctx, w, h } = setupCanvas(id);
  // Only treat an empty-label or no-non-null-line case as "No data available".
  // An all-zero session signal is valid warehouse data and must still render.
  const lineHasData = lineValues.some(v => v !== null);
  if (!labels.length || !lineHasData) { drawEmpty(ctx, w, h); return; }

  const ML = 48, MR = 48, MT = 12, MB = 68;
  const cw = w - ML - MR, ch = h - MT - MB;
  const n = labels.length;
  const gap = cw / n;
  const barW = Math.max(3, gap * 0.55);
  const step = Math.max(1, Math.ceil(n / 12));

  const maxBar = niceMax(Math.max(...barValues, 1));
  const lineFiltered = lineValues.filter(v => v !== null);
  const maxLine = niceMax(lineFiltered.length ? Math.max(...lineFiltered) : 1);

  drawYGrid(ctx, ML, MT, cw, ch, maxBar, 4);
  drawAxes(ctx, ML, MT, cw, ch);

  // Right Y labels (line axis)
  for (let i = 0; i <= 4; i++) {
    const y = MT + ch - (i / 4) * ch;
    ctx.fillStyle = lineColor;
    ctx.font = '10px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    const val = (i / 4) * maxLine;
    ctx.fillText(fmt(val), ML + cw + 6, y);
  }

  // Bars
  for (let i = 0; i < n; i++) {
    const v = barValues[i] || 0;
    if (v === 0) continue;
    const x = ML + i * gap + (gap - barW) / 2;
    const barH = (v / maxBar) * ch;
    const y = MT + ch - barH;
    ctx.fillStyle = barColor;
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]);
    ctx.fill();
    ctx.globalAlpha = 1;
    if (barH > 18) {
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(v, x + barW / 2, y + 5);
    }
  }

  // Line
  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  let started = false;
  for (let i = 0; i < n; i++) {
    const v = lineValues[i];
    if (v === null) { started = false; continue; }
    const x = ML + i * gap + gap / 2;
    const y = MT + ch - (v / maxLine) * ch;
    if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Dots
  for (let i = 0; i < n; i++) {
    const v = lineValues[i];
    if (v === null) continue;
    const x = ML + i * gap + gap / 2;
    const y = MT + ch - (v / maxLine) * ch;
    ctx.fillStyle = lineColor;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  drawXLabels(ctx, labels, ML, MT, cw, ch, step);

}


// ── section headers ──────────────────────────────────────────────────────────

function renderSectionHeaders() {
  const d = DATA;

  function dateRange(from, to) {
    if (!from) return 'no data';
    return from === to ? from : from + ' \u2192 ' + to;
  }

  const activityEl = document.getElementById('sh-activity');
  if (activityEl) {
    const range = dateRange(d.history_date_from, d.history_date_to);
    const count = d.summary ? ' \u00b7 ' + d.summary.total_threads + ' threads' : '';
    activityEl.innerHTML =
      '<h3>Agent Activity</h3>' +
      '<span class="src-badge history">warehouse</span>' +
      '<p>' + range + count + '</p>';
  }

  const historyEl = document.getElementById('sh-history');
  if (historyEl) {
    const range = dateRange(d.history_date_from, d.history_date_to);
    const badge = '<span class="src-badge history">warehouse</span>';
    historyEl.innerHTML =
      '<h3>Session History</h3>' + badge + '<p>' + range + '</p>';
  }

  const practiceEl = document.getElementById('sh-practice');
  const practiceCard = document.getElementById('c5-card');
  const practiceGrid = document.getElementById('grid-practice');
  const c5 = d.chart5 || {};
  if (practiceEl) {
    if (c5.source === 'warehouse' && (c5.labels || []).length) {
      const shown = c5.shown_events || 0;
      const total = c5.total_events || 0;
      const omitted = Math.max(0, total - shown);
      const omittedNote = omitted > 0
        ? ' \u00b7 ' + omitted + ' events in ' + ((c5.labels || []).length >= 15 ? 'long tail' : 'other names') + ' not shown'
        : '';
      practiceEl.innerHTML =
        '<h3>Practice Events</h3>' +
        '<span class="src-badge history">warehouse</span>' +
        '<p>' + total + ' events across ' + (c5.labels || []).length + ' names' + omittedNote + '</p>';
      if (practiceCard) practiceCard.style.display = '';
      if (practiceGrid) practiceGrid.style.display = '';
    } else {
      // Hide the whole section when there are no practice events to show.
      practiceEl.innerHTML = '';
      if (practiceCard) practiceCard.style.display = 'none';
      if (practiceGrid) practiceGrid.style.display = 'none';
    }
  }
}

// ── render all ───────────────────────────────────────────────────────────────

function renderC1Legend() {
  const leg = document.getElementById('c1-legend');
  if (!leg) return;
  leg.innerHTML = [
    makeLegendItem('#22c55e', 'Threads', 'c1', 0),
  ].join('');
}

function renderC3Legend() {
  const series = DATA.chart3_series || [];
  const leg = document.getElementById('c3-legend');
  if (leg) leg.innerHTML = series.map((s, i) => makeLegendItem(s.color, s.name, 'c3', i)).join('');
}

function renderChart3Meta() {
  const cost = DATA.chart3_mode === 'cost';
  const gran = DATA.granularity === 'day' ? 'day' : 'week';
  const title = document.getElementById('c3-title');
  const sub = document.getElementById('c3-subtitle');
  if (title) title.textContent = cost ? 'Cost by Model' : 'Tokens by Model';
  if (sub) sub.textContent = (cost ? 'USD per ' + gran : 'Tokens per ' + gran) +
    ' \u00b7 stacked by model \u00b7 source: history';
  renderC3Legend();
}

// Chart 5 palette — agent/skill/other. Green for Agent (subagent spawn),
// blue for Skill (scripted workflow), slate for the "other" bucket.
const C5_COLORS = ['#22c55e', '#3b82f6', '#94a3b8'];
const C5_LABELS = ['Agent', 'Skill', 'Other'];

function renderChart5() {
  const c5 = DATA.chart5 || {};
  const labels = c5.labels || [];
  if (!labels.length) return;

  const sub = document.getElementById('c5-subtitle');
  if (sub) {
    sub.textContent = 'Top ' + labels.length + ' practice names by count \u00b7 stacked by kind \u00b7 source: history';
  }

  const leg = document.getElementById('c5-legend');
  if (leg) {
    // Only show legend items for kinds that actually have data so the legend
    // doesn't mislead on a Skill-only or Agent-only dataset.
    const totals = [
      (c5.agent || []).reduce((a, b) => a + b, 0),
      (c5.skill || []).reduce((a, b) => a + b, 0),
      (c5.other || []).reduce((a, b) => a + b, 0),
    ];
    const items = [];
    for (let i = 0; i < C5_LABELS.length; i++) {
      if (totals[i] > 0) {
        items.push('<div class="legend-item"><div class="legend-dot" style="background:' +
          C5_COLORS[i] + '"></div>' + C5_LABELS[i] + ' (' + totals[i] + ')</div>');
      }
    }
    leg.innerHTML = items.join('');
  }

  const series = [c5.agent || [], c5.skill || [], c5.other || []];
  // Chart 5 is not toggleable — pass a tri-state "all visible" array to keep
  // drawStackedBar's toggle-aware path happy.
  drawStackedBar('c5', labels, series, C5_COLORS, false, '', [true, true, true]);
}

function renderWarehouseCallout() {
  const el = document.getElementById('warehouse-callout');
  if (!el) return;
  const state = DATA.warehouse_state || { status: 'ok' };
  const messages = {
    missing_file: {
      title: 'No history warehouse yet.',
      body: 'Session History and Practice Events are missing until you extract agent history.',
    },
    schema_outdated: {
      title: 'Warehouse schema is outdated.',
      body: 'Re-deriving the history pipeline will refresh tables and surface missing charts.',
    },
    empty_for_cwd: {
      title: 'Warehouse has no data for this project yet.',
      body: 'Session History and Practice Events are unavailable for the selected project.',
    },
  };
  const m = messages[state.status];
  if (!m) { el.innerHTML = ''; return; }
  el.innerHTML =
    '<strong>\u26a0 ' + m.title + '</strong> ' + m.body +
    ' &nbsp;Run: <code>ai-agents-metrics history-update</code>';
}

function renderChart2Meta() {
  const sub = document.getElementById('c2-subtitle');
  const leg = document.getElementById('c2-legend');
  if (sub) sub.textContent = 'Sessions (bars) \u00b7 average sessions per thread (line) \u00b7 source: history';
  if (leg) leg.innerHTML =
    '<div class="legend-item"><div class="legend-dot" style="background:#f97316"></div>Sessions</div>' +
    '<div class="legend-item"><div class="legend-dot" style="background:#ef4444;border-radius:50%"></div>Sessions per thread (line)</div>';
}

function render() {
  const d = DATA;
  // Initialize c3 toggles once to match the number of model series; preserve
  // user toggles on window-resize re-renders.
  const c3Len = (d.chart3_series || []).length;
  if (seriesToggles.c3.length !== c3Len) {
    seriesToggles.c3 = new Array(c3Len).fill(true);
  }
  renderSectionHeaders();
  renderWarehouseCallout();
  renderChart2Meta();
  renderChart3Meta();
  renderC1Legend();
  drawStackedBar('c1', d.buckets, [d.chart1_threads], ['#22c55e'], false, '', seriesToggles.c1);
  const whStatus = (d.warehouse_state && d.warehouse_state.status) || 'ok';
  drawCombo('c2', d.buckets, d.chart2_bar, d.chart2_line, '#f97316', '#ef4444');
  const c3Prefix = d.chart3_mode === 'cost' ? '$' : '';
  const c3Values = (d.chart3_series || []).map(s => s.values);
  const c3Colors = (d.chart3_series || []).map(s => s.color);
  drawStackedBar('c3', d.buckets, c3Values, c3Colors, true, c3Prefix, seriesToggles.c3);
  renderChart5();
}

window.addEventListener('load', () => { initializeReportControls(); render(); });
window.addEventListener('resize', render);
</script>
</body>
</html>
"""
