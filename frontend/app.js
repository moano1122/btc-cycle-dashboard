/* =========================================================================
   BTC Indicators — lógica del dashboard
   ========================================================================= */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const state = {
  snapshot: null,
  charts: {},          // metric_id -> instancia de ECharts
  loadedTutorials: {}, // metric_id -> html
  openCards: new Set(),
  filter: 'all',
  onlyTriggered: false,
  saveTimer: null,
};

/* ------------------------------------------------------------------ utils */
const fmt = (v, dec = 2, unit = '') =>
  v === null || v === undefined || Number.isNaN(v)
    ? '—'
    : v.toLocaleString('es-CO', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + unit;

const fmtUsd = (v) =>
  v === null || v === undefined ? '—' : '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 });

function scoreClass(score) {
  if (score === null || score === undefined) return 'none';
  if (score >= 88) return 'best';
  if (score >= 70) return 'good';
  if (score >= 48) return 'mid';
  if (score >= 28) return 'warn';
  return 'hot';
}

function toast(msg, ms = 3200) {
  const el = $('#toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.hidden = true), ms);
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status} en ${path}`);
  return res.json();
}

/* ------------------------------------------------------------------ gauge */
function renderGauge(score) {
  const el = $('#gauge');
  const chart = state.charts._gauge || echarts.init(el, null, { renderer: 'svg' });
  state.charts._gauge = chart;

  chart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 205, endAngle: -25,
      min: 0, max: 100,
      radius: '92%',
      center: ['50%', '62%'],
      progress: { show: false },
      pointer: {
        icon: 'path://M2 0 L-2 0 L0 -62 Z',
        length: '62%', width: 6, offsetCenter: [0, 0],
        itemStyle: { color: '#e6ecf5' },
      },
      anchor: { show: true, size: 11, itemStyle: { color: '#e6ecf5' } },
      axisLine: {
        lineStyle: {
          width: 16,
          color: [
            [0.15, '#f4643c'], [0.28, '#f5a524'], [0.45, '#4f9dff'],
            [0.60, '#2f7f8f'], [0.75, '#0e6b56'], [0.88, '#189c7a'], [1, '#22d3a5'],
          ],
        },
      },
      axisTick: { distance: -16, length: 4, lineStyle: { color: '#0b0e13', width: 1 } },
      splitLine: { distance: -16, length: 16, lineStyle: { color: '#0b0e13', width: 2 } },
      axisLabel: { distance: -42, color: '#64748b', fontSize: 10 },
      detail: { show: false },
      title: { show: false },
      data: [{ value: score ?? 0 }],
    }],
  });
}

/* ------------------------------------------------------------------ hero */
function renderHero(snap) {
  $('#score').textContent = snap.score ?? '—';
  $('#score').className = 'gauge-score t-' + scoreClass(snap.score);
  $('#band').textContent = snap.band_label;
  $('#band').className = 'band t-' + scoreClass(snap.score);
  $('#band-blurb').textContent = snap.band_blurb || '';
  renderGauge(snap.score);

  const cov = snap.coverage_pct ?? 0;
  $('#coverage-pct').textContent = `${cov}% · ${snap.indicators_usable}/${snap.indicators_total}`;
  $('#coverage-bar').style.width = cov + '%';
  $('#coverage-bar').style.background =
    cov >= 80 ? 'var(--signal)' : cov >= 50 ? 'var(--info)' : 'var(--warn)';

  let note;
  if (cov >= 85) note = 'Cobertura alta: el score es representativo del catálogo completo.';
  else if (cov >= 50) note = 'Cobertura parcial. Faltan indicadores con peso; el score está sesgado hacia los disponibles.';
  else note = 'Cobertura baja. El score se calcula con pocos indicadores y no es fiable todavía — configure la API key y actualice.';
  $('#coverage-note').textContent = note;

  const p = snap.price || {};
  $('#price').textContent = fmtUsd(p.spot ?? p.last_close);
  $('#price-sub').textContent = p.last_close_date ? `cierre ${p.last_close_date}` : '';

  // Se muestran TODAS las categorías, incluidas las que no tienen ningún dato:
  // ocultarlas daría la impresión de que el score las tuvo en cuenta.
  $('#cat-strip').innerHTML = snap.categories
    .map((c) => {
      const cov = c.coverage_pct;
      const flaca = cov < 60;
      const titulo = `${c.count}/${c.count_total} indicadores con datos · ${cov}% del peso de la categoría`
        + (flaca ? ' — esta categoría está poco representada en el score' : '');
      const valor = c.score === null
        ? '<b class="t-none">sin datos</b>'
        : `<b class="t-${scoreClass(c.score)}">${c.score}</b>`;
      return `<span class="cat-pill ${flaca ? 'thin' : ''}" title="${titulo}">${c.label}
          ${valor}<i class="cov">${cov}%</i></span>`;
    })
    .join('');

  $('#tg-state').textContent = snap.telegram_enabled
    ? 'y se envía a Telegram.'
    : '. Telegram no está configurado: rellene TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el archivo .env.';
}

/* ------------------------------------------------------------------ cards */
function cardHTML(r) {
  const cls = scoreClass(r.score);
  const open = state.openCards.has(r.id);

  let valHtml, gapHtml, scoreHtml;
  if (r.available) {
    const staleTag = r.stale ? ` <span class="tag" title="El dato tiene ${r.age_days} días">rancio</span>` : '';
    valHtml = `<div class="val-now">${fmt(r.value, r.decimals, r.unit)}</div>
               <div class="val-meta">${r.as_of}${staleTag}</div>`;

    const dirWord = r.trigger_dir === 'below' ? '≤' : '≥';
    if (r.triggered) {
      gapHtml = `<div class="gap-label">umbral</div>
                 <div class="gap-line t-best">cruzado ✓</div>`;
    } else {
      const pct = r.gap_pct === null || r.gap_pct === undefined ? null : Math.abs(r.gap_pct);
      gapHtml = `<div class="gap-label">falta para ${dirWord} ${fmt(r.trigger, r.decimals, r.unit)}</div>
                 <div class="gap-line">${pct === null ? fmt(Math.abs(r.gap), r.decimals) : fmt(pct, 1) + '%'}</div>`;
    }

    scoreHtml = `<div class="mini-bar"><div class="mini-fill s-${cls}" style="width:${r.score}%"></div></div>
                 <div class="score-row"><span>score</span><b>${r.score}</b></div>`;
  } else {
    valHtml = `<div class="val-now t-none">sin datos</div>
               <div class="val-meta">${(r.detail || '').slice(0, 34)}</div>`;
    gapHtml = '';
    scoreHtml = `<div class="mini-bar"><div class="mini-fill s-none" style="width:0"></div></div>
                 <div class="score-row"><span>score</span><b>—</b></div>`;
  }

  return `
  <div class="card ${r.triggered ? 'triggered' : ''} ${open ? 'open' : ''}" data-id="${r.id}" data-cat="${r.category}">
    <div class="card-head">
      <div class="pip s-${cls}"></div>
      <div class="card-name">
        <div class="card-title">${r.label}
          <span class="tag">${r.category_label}</span>
          ${r.source === 'derived' ? '<span class="tag" title="Se calcula localmente, no consume cupo de API">local</span>' : ''}
          ${r.ciclos >= 2
            ? `<span class="tag tag-ok" title="Umbral derivado de la mediana de ${r.ciclos} suelos de ciclo reales, con la forma de la escala tomada de toda la historia disponible">${r.ciclos} ciclos</span>`
            : r.ciclos === 1
              ? '<span class="tag tag-mid" title="Solo se conoce el suelo de 2022 para este indicador: el proveedor entrega 4 años de historia en el plan gratuito. Un suelo no es una regularidad.">1 ciclo</span>'
              : '<span class="tag tag-warn" title="Sin ningún suelo de ciclo en los datos disponibles. El umbral viene de literatura publicada y puede estar en otra escala.">sin respaldo</span>'}
        </div>
        <div class="card-sum">${r.summary}</div>
      </div>
      <div class="card-val">${valHtml}</div>
      <div class="card-gap">${gapHtml}</div>
      <div class="card-score">${scoreHtml}</div>
      <div class="chev">›</div>
    </div>
    <div class="card-body">
      <div class="body-grid">
        <div class="chart" id="chart-${r.id}"></div>
        <div>
          <div class="weight-box">
            <h4>Peso en el score</h4>
            <p>Cuánto pesa este indicador frente a los demás. Muévalo y el score se recalcula.</p>
            <div class="weight-row">
              <input type="range" min="0" max="20" value="${r.weight}" data-weight="${r.id}">
              <span class="weight-num" id="wnum-${r.id}">${r.weight}</span>
            </div>
          </div>
          <div class="facts">
            <div><span>Umbral de alerta</span><b>${r.trigger_dir === 'below' ? '≤' : '≥'} ${fmt(r.trigger, r.decimals, r.unit)}</b></div>
            <div><span>Respaldo del umbral</span><b class="${r.ciclos >= 2 ? 't-best' : r.ciclos === 1 ? 't-mid' : 't-warn'}">${r.ciclos === 0 ? 'literatura' : r.ciclos + (r.ciclos === 1 ? ' suelo de ciclo' : ' suelos de ciclo')}</b></div>
            ${r.smooth_days ? `<div><span>Suavizado</span><b>${r.smooth_days} días</b></div>` : ''}
            ${r.delta_30d !== null && r.delta_30d !== undefined ? `<div><span>Cambio en 30 días</span><b>${r.delta_30d > 0 ? '+' : ''}${fmt(r.delta_30d, r.decimals)}</b></div>` : ''}
            ${Object.entries(r.historic || {}).map(([k, v]) =>
              `<div><span>${k.startsWith('suelo ') ? 'Suelo de ' + k.split(' ')[1] : k}</span><b>${fmt(v, r.decimals, r.unit)}</b></div>`).join('')}
          </div>
        </div>
      </div>
      <div class="tutorial" id="tut-${r.id}"><p class="empty">Cargando tutorial…</p></div>
    </div>
  </div>`;
}

function renderCards(snap) {
  let rows = [...snap.indicators].sort((a, b) => (b.weight || 0) - (a.weight || 0));
  if (state.filter !== 'all') rows = rows.filter((r) => r.category === state.filter);
  if (state.onlyTriggered) rows = rows.filter((r) => r.triggered);

  $('#cards').innerHTML = rows.length
    ? rows.map(cardHTML).join('')
    : '<p class="empty">Ningún indicador cumple el filtro.</p>';

  // Reabrir y repintar los que ya estaban abiertos.
  state.openCards.forEach((id) => {
    if (rows.some((r) => r.id === id)) loadCardDetail(id);
  });
}

function renderFilters(snap) {
  const cats = [...new Map(snap.indicators.map((r) => [r.category, r.category_label])).entries()];
  $('#filters').innerHTML =
    `<button class="filter ${state.filter === 'all' ? 'on' : ''}" data-cat="all">Todos</button>` +
    cats.map(([k, l]) => `<button class="filter ${state.filter === k ? 'on' : ''}" data-cat="${k}">${l}</button>`).join('');
}

/* ------------------------------------------- gráfica de un indicador */
async function loadCardDetail(id) {
  const meta = state.snapshot.indicators.find((r) => r.id === id);
  if (!meta) return;

  // Tutorial (se cachea: no hace falta volver a pedirlo al reabrir)
  const tutEl = $(`#tut-${id}`);
  if (tutEl) {
    if (state.loadedTutorials[id]) {
      tutEl.innerHTML = state.loadedTutorials[id];
    } else {
      try {
        const t = await api(`/api/tutorial/${id}`);
        const html = t.missing || !t.markdown
          ? '<p class="empty">Todavía no hay tutorial escrito para este indicador.</p>'
          : marked.parse(t.markdown);
        state.loadedTutorials[id] = html;
        tutEl.innerHTML = html;
      } catch {
        tutEl.innerHTML = '<p class="empty">No se pudo cargar el tutorial.</p>';
      }
    }
  }

  // Gráfica
  const chartEl = $(`#chart-${id}`);
  if (!chartEl) return;
  let data;
  try {
    data = await api(`/api/series/${id}?days=2600`);
  } catch {
    chartEl.innerHTML = '<p class="empty">Sin serie histórica todavía.</p>';
    return;
  }
  if (!data.points.length) {
    chartEl.innerHTML = '<p class="empty">Sin datos en caché para este indicador. Pulse «Actualizar datos».</p>';
    return;
  }

  const chart = echarts.init(chartEl, null, { renderer: 'canvas' });
  state.charts[id] = chart;

  const series = data.points.map((p) => [p.d, p.value]);
  const price = (data.price || []).map((p) => [p.d, p.value]);

  // Búsqueda del último valor conocido en o antes de una fecha.
  //
  // Hace falta porque las series tienen granularidades distintas: el RSI
  // mensual tiene un punto al mes y el precio uno al día. ECharts solo incluye
  // en el tooltip las series que tienen un dato EXACTAMENTE en la fecha
  // señalada, así que al pasar el ratón por un día cualquiera aparecía el
  // precio y el indicador no. Con esto siempre se muestran ambos.
  const buscarAntesDe = (arr) => {
    const fechas = arr.map((p) => p[0]);
    return (fecha) => {
      let lo = 0, hi = fechas.length - 1, res = -1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (fechas[mid] <= fecha) { res = mid; lo = mid + 1; } else { hi = mid - 1; }
      }
      return res >= 0 ? arr[res] : null;
    };
  };
  const valorIndicador = buscarAntesDe(series);
  const valorPrecio = buscarAntesDe(price);

  const fmtFecha = (t) => new Date(t).toISOString().slice(0, 10);
  const nf = (v, dec) => v === null || v === undefined
    ? '—'
    : v.toLocaleString('es-CO', { minimumFractionDigits: dec, maximumFractionDigits: dec });

  const vals = data.points.map((p) => p.value);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const zone = data.trigger_dir === 'below'
    ? [{ yAxis: lo - (hi - lo) * 0.08 }, { yAxis: data.trigger }]
    : [{ yAxis: data.trigger }, { yAxis: hi + (hi - lo) * 0.08 }];

  chart.setOption({
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: 54, right: 62, top: 30, bottom: 52 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#2e3a4d' } },
      backgroundColor: '#171e2a',
      borderColor: '#2e3a4d',
      textStyle: { color: '#e6ecf5', fontSize: 12 },
      formatter: (params) => {
        if (!params.length) return '';
        const fecha = fmtFecha(params[0].axisValue);
        const ind = valorIndicador(fecha);
        const pre = valorPrecio(fecha);
        const rezagado = ind && ind[0] !== fecha ? ` <span style="color:#64748b">(dato del ${ind[0]})</span>` : '';
        let html = `<b>${fecha}</b>`;
        html += `<br><span style="color:#f7931a">●</span> ${meta.label}: <b>${nf(ind ? ind[1] : null, meta.decimals)}${meta.unit}</b>${rezagado}`;
        if (pre) html += `<br><span style="color:#37445c">●</span> Precio BTC: <b>$${nf(pre[1], 0)}</b>`;
        return html;
      },
    },
    legend: {
      data: [meta.label, 'Precio BTC'],
      textStyle: { color: '#9aa8bd', fontSize: 11 },
      top: 0, right: 0,
    },
    // Rueda del ratón para acercar, arrastre del control inferior para
    // seleccionar un tramo. Sin esto no se podía mirar un periodo concreto.
    dataZoom: [
      { type: 'inside', zoomOnMouseWheel: true, moveOnMouseMove: true },
      {
        type: 'slider', height: 18, bottom: 8,
        borderColor: '#232c3b', backgroundColor: '#0d1219',
        fillerColor: 'rgba(247,147,26,.10)',
        handleStyle: { color: '#3b4a61' },
        dataBackground: { lineStyle: { color: '#2e3a4d' }, areaStyle: { color: '#171e2a' } },
        textStyle: { color: '#64748b', fontSize: 9 },
      },
    ],
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#2e3a4d' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: 'value', scale: true,
        axisLabel: { color: '#64748b', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1a2230' } },
      },
      {
        type: 'log', scale: true, position: 'right',
        axisLabel: { color: '#3f4d63', fontSize: 10, formatter: (v) => '$' + (v >= 1000 ? (v / 1000) + 'k' : v) },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Precio BTC',
        type: 'line', yAxisIndex: 1, data: price,
        showSymbol: false, lineStyle: { color: '#37445c', width: 1 },
        itemStyle: { color: '#37445c' },
        z: 1,
      },
      {
        name: meta.label,
        type: 'line', yAxisIndex: 0, data: series,
        showSymbol: false, connectNulls: true,
        lineStyle: { color: '#f7931a', width: 1.8 },
        itemStyle: { color: '#f7931a' },
        z: 3,
        markLine: {
          silent: true, symbol: 'none',
          label: {
            formatter: `umbral ${data.trigger}`, color: '#22d3a5',
            fontSize: 10, position: 'insideEndTop',
          },
          lineStyle: { color: '#22d3a5', type: 'dashed', width: 1.2 },
          data: [{ yAxis: data.trigger }],
        },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(34, 211, 165, 0.08)' },
          data: [zone],
        },
      },
    ],
  });

  new ResizeObserver(() => chart.resize()).observe(chartEl);
}

/* ------------------------------------------- gráfica del score histórico */
async function renderScoreHistory() {
  const el = $('#score-history');
  let data;
  try {
    data = await api('/api/score-history?days=3600');
  } catch {
    el.innerHTML = '<p class="empty">No se pudo cargar el histórico.</p>';
    return;
  }
  if (!data.score.length) {
    el.innerHTML = '<p class="empty">Aún no hay suficiente historia en caché. Pulse «Actualizar datos» y vuelva.</p>';
    return;
  }

  const chart = echarts.init(el, null, { renderer: 'canvas' });
  state.charts._history = chart;

  chart.setOption({
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: 46, right: 64, top: 34, bottom: 34 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#171e2a', borderColor: '#2e3a4d',
      textStyle: { color: '#e6ecf5', fontSize: 12 },
    },
    legend: {
      data: ['Score de suelo', 'Precio BTC', 'Cobertura'],
      textStyle: { color: '#9aa8bd', fontSize: 11 }, top: 0, right: 0,
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#2e3a4d' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: [
      {
        type: 'value', min: 0, max: 100, name: 'score',
        nameTextStyle: { color: '#64748b', fontSize: 10 },
        axisLabel: { color: '#64748b', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1a2230' } },
      },
      {
        type: 'log', position: 'right', scale: true,
        axisLabel: { color: '#3f4d63', fontSize: 10, formatter: (v) => '$' + (v >= 1000 ? v / 1000 + 'k' : v) },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 4, borderColor: '#232c3b', textStyle: { color: '#64748b', fontSize: 9 } }],
    series: [
      {
        name: 'Precio BTC', type: 'line', yAxisIndex: 1,
        data: data.price.map((p) => [p.d, p.value]),
        showSymbol: false, lineStyle: { color: '#37445c', width: 1 }, z: 1,
      },
      {
        name: 'Score de suelo', type: 'line', yAxisIndex: 0,
        data: data.score.map((p) => [p.d, p.score]),
        showSymbol: false, lineStyle: { color: '#22d3a5', width: 2 }, z: 3,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,211,165,0.28)' },
            { offset: 1, color: 'rgba(34,211,165,0.01)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: '#0e6b56', type: 'dashed', width: 1 },
          label: { color: '#4ec9a8', fontSize: 10, formatter: '{b}' },
          data: [
            { yAxis: 75, name: 'suelo probable' },
            { yAxis: 60, name: 'acumulación' },
          ],
        },
      },
      {
        name: 'Cobertura', type: 'line', yAxisIndex: 0,
        data: data.score.map((p) => [p.d, p.coverage]),
        showSymbol: false, lineStyle: { color: '#4f9dff', width: 1, type: 'dotted' },
        z: 2,
      },
    ],
  });
  new ResizeObserver(() => chart.resize()).observe(el);
}

/* ------------------------------------------------------------------ alertas */
async function renderAlerts() {
  const { events } = await api('/api/alerts?limit=40');
  const el = $('#alerts');
  if (!events.length) {
    el.innerHTML = '<p class="empty">Todavía no se ha disparado ninguna alerta.</p>';
    return;
  }
  el.innerHTML = events
    .map((e) => {
      const color = e.severity === 'signal' ? 'var(--signal)' : 'var(--line-2)';
      const when = (e.ts_utc || '').replace('T', ' ').slice(0, 16);
      const delivered = e.delivered ? '' : ' · no enviado a Telegram';
      return `<div class="alert">
          <div class="pipe" style="background:${color}"></div>
          <time>${when}${delivered}</time>
          <div>
            <div class="alert-title">${e.title}</div>
            <div class="alert-msg">${(e.message || '').split('\n')[0]}</div>
          </div>
        </div>`;
    })
    .join('');
}

/* ------------------------------------------------------------------ pesos */
function scheduleWeightSave() {
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(async () => {
    const weights = {};
    $$('input[data-weight]').forEach((i) => (weights[i.dataset.weight] = +i.value));
    // Conservar los pesos de los indicadores filtrados fuera de la vista.
    Object.entries(state.snapshot.weights).forEach(([k, v]) => {
      if (!(k in weights)) weights[k] = v;
    });
    const res = await api('/api/weights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weights }),
    });
    state.snapshot = res.snapshot;
    renderHero(res.snapshot);
    renderScoreHistory();
    toast('Pesos guardados. Score recalculado.');
  }, 500);
}

/* ------------------------------------------------------------------ estado */
async function showStatus() {
  const s = await api('/api/status');
  const b = s.budget;
  const rows = Object.entries(s.metric_states)
    .sort()
    .map(([k, v]) => {
      const cls = v.status === 'ok' ? 'ok' : v.status === 'error' ? 'bad' : 'meh';
      return `<div class="row"><span>${k}</span>
        <span class="${cls}">${v.status}</span>
        <span class="meh">${v.last_data_point || ''} ${(v.detail || '').slice(0, 40)}</span></div>`;
    })
    .join('');

  $('#status-body').innerHTML = `
    <div class="status-grid">
      <div><span>API key configurada</span><b class="${b.has_key ? 'ok' : 'bad'}">${b.has_key ? 'sí' : 'NO'}</b></div>
      <div><span>Telegram</span><b class="${s.telegram_enabled ? 'ok' : 'bad'}">${s.telegram_enabled ? 'activo' : 'sin configurar'}</b></div>
      <div><span>Cupo última hora</span><b>${b.used_hour} / ${b.limit_hour}</b></div>
      <div><span>Cupo últimas 24h</span><b>${b.used_day} / ${b.limit_day}</b></div>
      <div><span>Indicadores en catálogo</span><b>${s.catalog_size}</b></div>
      <div><span>Sin datos todavía</span><b class="${s.missing.length ? 'bad' : 'ok'}">${s.missing.length}</b></div>
    </div>
    ${!b.has_key ? `<div class="disclaimer" style="margin-top:16px">
      Sin API key el cupo es de ${b.limit_hour} peticiones por hora y ${b.limit_day} al día, que no alcanza
      para los 22 indicadores on-chain. Registre una key gratuita en
      <code>bitcoin-data.com</code> y póngala en el archivo <code>.env</code>.
    </div>` : ''}
    <div class="status-list">${rows}</div>`;
  $('#modal-status').hidden = false;
}

/* ------------------------------------------------------------------ init */
async function load() {
  state.snapshot = await api('/api/snapshot');
  renderHero(state.snapshot);
  renderFilters(state.snapshot);
  renderCards(state.snapshot);
}

function wire() {
  // Expandir / contraer tarjetas
  $('#cards').addEventListener('click', (e) => {
    if (e.target.closest('input, .weight-box')) return;
    const head = e.target.closest('.card-head');
    if (!head) return;
    const card = head.closest('.card');
    const id = card.dataset.id;
    card.classList.toggle('open');
    if (card.classList.contains('open')) {
      state.openCards.add(id);
      loadCardDetail(id);
    } else {
      state.openCards.delete(id);
      state.charts[id]?.dispose();
      delete state.charts[id];
    }
  });

  // Sliders de peso
  $('#cards').addEventListener('input', (e) => {
    const inp = e.target.closest('input[data-weight]');
    if (!inp) return;
    $(`#wnum-${inp.dataset.weight}`).textContent = inp.value;
    scheduleWeightSave();
  });

  // Filtros
  $('#filters').addEventListener('click', (e) => {
    const b = e.target.closest('.filter');
    if (!b) return;
    state.filter = b.dataset.cat;
    renderFilters(state.snapshot);
    renderCards(state.snapshot);
  });

  $('#only-triggered').addEventListener('change', (e) => {
    state.onlyTriggered = e.target.checked;
    renderCards(state.snapshot);
  });

  $('#btn-reset-weights').addEventListener('click', async () => {
    const res = await api('/api/weights/reset', { method: 'POST' });
    state.snapshot = res.snapshot;
    renderHero(res.snapshot);
    renderCards(res.snapshot);
    renderScoreHistory();
    toast('Pesos restaurados a los valores por defecto.');
  });

  $('#btn-refresh').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = 'Actualizando…';
    try {
      const r = await api('/api/refresh', { method: 'POST' });
      const n = r.onchain_fetched.length;
      const blocked = r.onchain_skipped_budget.length;
      toast(`${n} métricas actualizadas${blocked ? `, ${blocked} sin cupo` : ''}.`);
      await load();
      await renderScoreHistory();
      await renderAlerts();
    } catch (err) {
      toast('Falló la actualización: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Actualizar datos';
    }
  });

  $('#btn-status').addEventListener('click', showStatus);
  $('#modal-status').addEventListener('click', (e) => {
    if (e.target.id === 'modal-status' || e.target.dataset.close !== undefined) {
      $('#modal-status').hidden = true;
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') $('#modal-status').hidden = true;
  });

  $('#btn-test-tg').addEventListener('click', async () => {
    const r = await api('/api/alerts/test', { method: 'POST' });
    toast(r.ok ? 'Mensaje enviado a Telegram.' : 'No se pudo enviar: ' + r.detail);
  });

  window.addEventListener('resize', () => {
    Object.values(state.charts).forEach((c) => c?.resize());
  });
}

(async function main() {
  wire();
  await load();
  await renderScoreHistory();
  await renderAlerts();
})();
