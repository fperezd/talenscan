"""Template HTML del informe comparativo de candidatos (landscape A4).

Diseñado para ser entregado a un cliente/Partner: portada con tesis y
shortlist, score comparativo lado a lado con el mejor por dimensión
resaltado, matriz de calce, trayectoria y preguntas clave por candidato.
"""

from __future__ import annotations

COMPARISON_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Comparativo de candidatos — {{ mandate_title }}</title>
<style>
  @page {
    size: A4 landscape;
    margin: 14mm 12mm 18mm 12mm;
    @bottom-center {
      content: "TalentScan · Comparativo de candidatos · " counter(page) " / " counter(pages);
      font-size: 7.5pt;
      color: #57575680;
      font-family: 'Helvetica', 'Arial', sans-serif;
    }
    @top-right {
      content: "{{ client_name }} · {{ target_role }}";
      font-size: 7pt;
      color: #57575690;
      font-family: 'Helvetica', 'Arial', sans-serif;
    }
  }

  :root {
    --brand-blue: #177FC6;
    --brand-blue-dark: #0F5E94;
    --brand-blue-soft: #E5F1FA;
    --brand-black: #1D1D1B;
    --brand-gray: #575756;
    --slate-50: #F8FAFC;
    --slate-100: #F1F5F9;
    --slate-200: #E2E8F0;
    --emerald-50: #ECFDF5;
    --emerald-100: #D1FAE5;
    --emerald-200: #A7F3D0;
    --emerald-600: #059669;
    --emerald-700: #047857;
    --rose-50: #FFF1F2;
    --rose-100: #FFE4E6;
    --rose-200: #FECDD3;
    --rose-700: #BE123C;
    --amber-50: #FFFBEB;
    --amber-100: #FEF3C7;
    --amber-700: #B45309;
    --indigo-50: #EEF2FF;
    --indigo-100: #E0E7FF;
    --indigo-200: #C7D2FE;
    --indigo-700: #4338CA;
  }

  * { box-sizing: border-box; }

  body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 9pt;
    color: var(--brand-black);
    line-height: 1.4;
    margin: 0;
    padding: 0;
  }

  h1, h2, h3, h4 { margin: 0; font-weight: 600; color: var(--brand-black); }
  p { margin: 0; }

  /* --- Header / Hero --- */
  .hero {
    border-radius: 12px;
    background: white;
    border: 1px solid var(--slate-200);
    padding: 14px 16px;
    margin-bottom: 10px;
    page-break-inside: avoid;
  }
  .hero-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
  }
  .hero-top .left { flex: 1; }
  .eyebrow {
    color: var(--brand-blue);
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0 0 4px 0;
  }
  .hero h1 { font-size: 19pt; margin: 2px 0 4px 0; }
  .hero .meta { color: var(--brand-gray); font-size: 9pt; }
  .hero .meta strong { color: var(--brand-black); }

  .stat-row { display: flex; gap: 12px; margin-top: 10px; }
  .stat {
    flex: 1;
    background: var(--slate-50);
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 8px 10px;
  }
  .stat .label { font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: var(--brand-gray); }
  .stat .value { font-size: 13pt; font-weight: 700; color: var(--brand-black); margin-top: 2px; }
  .stat .sub { font-size: 8pt; color: var(--brand-gray); margin-top: 1px; }
  .stat.highlight { background: var(--emerald-50); border-color: var(--emerald-200); }
  .stat.highlight .value { color: var(--emerald-700); }

  /* --- Section title --- */
  .section-title {
    font-size: 10pt;
    font-weight: 700;
    color: var(--brand-black);
    margin: 14px 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--slate-200);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .section-title .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--brand-blue);
    display: inline-block;
  }

  /* --- Tesis / recomendación ejecutiva --- */
  .thesis-card {
    background: linear-gradient(135deg, var(--brand-blue-soft), white);
    border: 1px solid var(--brand-blue);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 10px;
    page-break-inside: avoid;
  }
  .thesis-card .label {
    color: var(--brand-blue);
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
  }
  .thesis-card h2 { font-size: 11pt; margin-top: 4px; }
  .thesis-card .recommendation { margin-top: 6px; color: var(--brand-black); font-size: 10pt; line-height: 1.5; }
  .thesis-card .note { margin-top: 4px; color: var(--brand-gray); font-size: 8.5pt; }

  /* --- Candidate header strip --- */
  .candidate-strip {
    display: table;
    width: 100%;
    border-spacing: 6px;
    margin-bottom: 8px;
  }
  .candidate-card {
    display: table-cell;
    background: white;
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 10px;
    vertical-align: top;
    position: relative;
  }
  .candidate-card.top {
    border-color: var(--emerald-300, #6EE7B7);
    background: var(--emerald-50);
  }
  .candidate-card .top-badge {
    position: absolute;
    top: -6px;
    left: 8px;
    background: var(--emerald-600);
    color: white;
    font-size: 6.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 2px 7px;
    border-radius: 999px;
  }
  .candidate-card .name { font-size: 11pt; font-weight: 700; color: var(--brand-black); }
  .candidate-card .role { font-size: 8pt; color: var(--brand-gray); margin-top: 1px; }
  .candidate-card .company { font-size: 8pt; color: var(--brand-gray); }
  .candidate-card .score-line {
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .candidate-card .score-num {
    font-size: 17pt;
    font-weight: 800;
    color: var(--score-tone, var(--brand-blue));
    line-height: 1;
  }
  .candidate-card .score-of {
    font-size: 7pt;
    color: var(--brand-gray);
  }
  .candidate-card .badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 999px;
    font-size: 7pt;
    font-weight: 600;
    background: var(--badge-bg);
    color: var(--badge-fg);
  }

  /* --- Comparison table --- */
  table.compare {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    table-layout: fixed;
  }
  table.compare thead th {
    background: var(--slate-50);
    color: var(--brand-gray);
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    padding: 6px 8px;
    text-align: center;
    border-bottom: 1px solid var(--slate-200);
  }
  table.compare thead th.dim-col { text-align: left; }
  table.compare tbody td {
    padding: 6px 8px;
    border-bottom: 1px solid var(--slate-100);
    vertical-align: middle;
    text-align: center;
  }
  table.compare tbody td.dim-name {
    text-align: left;
    font-weight: 600;
    color: var(--brand-black);
    font-size: 8.5pt;
  }
  table.compare tr.total-row td { background: var(--slate-50); font-weight: 700; }
  table.compare td.best {
    background: var(--emerald-50);
    color: var(--emerald-700);
    font-weight: 700;
  }
  table.compare .score-cell {
    font-weight: 600;
    font-size: 9pt;
    color: var(--brand-black);
  }
  table.compare .bar { width: 50px; height: 3px; background: var(--slate-200); border-radius: 2px; margin: 2px auto 0; overflow: hidden; }
  table.compare .bar .fill { height: 100%; border-radius: 2px; }
  .fill-strong { background: #34D399; }
  .fill-good { background: #60A5FA; }
  .fill-mid { background: #FBBF24; }
  .fill-low { background: #FB7185; }

  .pill {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 999px;
    font-size: 7.5pt;
    font-weight: 600;
  }
  .pill-emerald { background: var(--emerald-100); color: var(--emerald-700); }
  .pill-rose { background: var(--rose-100); color: var(--rose-700); }
  .pill-indigo { background: var(--indigo-100); color: var(--indigo-700); }
  .pill-amber { background: var(--amber-100); color: var(--amber-700); }
  .pill-slate { background: var(--slate-100); color: var(--brand-gray); }

  /* --- 360 matrix --- */
  .matrix {
    display: table;
    width: 100%;
    border-spacing: 6px;
    margin-top: 4px;
  }
  .matrix .col {
    display: table-cell;
    vertical-align: top;
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    background: white;
    padding: 8px;
  }
  .matrix .col h4 {
    font-size: 8.5pt;
    margin: 0 0 4px 0;
    padding-bottom: 3px;
    border-bottom: 1px solid var(--slate-100);
  }
  .matrix .col .row {
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px dotted var(--slate-100);
  }
  .matrix .col .row:last-child { border-bottom: none; }
  .matrix .col .row-label { font-size: 7pt; font-weight: 700; text-transform: uppercase; color: var(--brand-gray); letter-spacing: 0.6px; margin-bottom: 2px; }
  .matrix .col .item {
    font-size: 8pt;
    color: var(--brand-black);
    margin-bottom: 2px;
    padding-left: 8px;
    position: relative;
  }
  .matrix .col .item::before {
    content: "";
    position: absolute;
    left: 0;
    top: 5px;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--brand-blue);
  }
  .matrix .col .item.strength::before { background: var(--emerald-600); }
  .matrix .col .item.gap::before { background: #F43F5E; }
  .matrix .col .item.opp::before { background: var(--indigo-700); }

  /* --- Per-candidate detail block --- */
  .detail-block {
    background: white;
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
    page-break-inside: avoid;
  }
  .detail-block .head {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--slate-100);
    margin-bottom: 6px;
  }
  .detail-block .head .score {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: var(--brand-blue-soft);
    color: var(--brand-blue);
    font-weight: 700;
    font-size: 11pt;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .detail-block .head .name { font-size: 11pt; font-weight: 700; }
  .detail-block .head .role { font-size: 8pt; color: var(--brand-gray); }
  .detail-block .thesis { font-size: 8.5pt; color: var(--brand-gray); font-style: italic; margin-bottom: 6px; }
  .detail-block .grid { display: table; width: 100%; border-spacing: 4px; }
  .detail-block .grid > div {
    display: table-cell;
    vertical-align: top;
    padding: 6px 8px;
    border-radius: 8px;
    font-size: 7.5pt;
  }
  .detail-block .grid .qcol { background: var(--slate-50); }
  .detail-block .grid .scol { background: var(--emerald-50); }
  .detail-block .grid .gcol { background: var(--rose-50); }
  .detail-block .grid .ocol { background: var(--indigo-50); }
  .detail-block .grid h5 {
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--brand-gray);
    letter-spacing: 0.6px;
    margin-bottom: 3px;
  }

  .traceability {
    margin-top: 14px;
    padding: 8px 10px;
    background: var(--slate-50);
    border-radius: 10px;
    font-size: 7pt;
    color: var(--brand-gray);
    line-height: 1.5;
  }
  .traceability strong { color: var(--brand-gray); text-transform: uppercase; font-size: 6.5pt; letter-spacing: 0.8px; }
</style>
</head>
<body>

<!-- Hero -->
<div class="hero">
  <div class="hero-top">
    <div class="left">
      <p class="eyebrow">Comparativo TalentScan · {{ candidates_count }} candidato{{ '' if candidates_count == 1 else 's' }}</p>
      <h1>{{ mandate_title }}</h1>
      <p class="meta">
        <strong>{{ client_name }}</strong> · {{ target_role }} · {{ industry }} · {{ city }}, {{ country }}
      </p>
    </div>
  </div>
  <div class="stat-row">
    <div class="stat highlight">
      <div class="label">Top score</div>
      <div class="value">{{ top_scorer.name }}</div>
      <div class="sub">{{ top_scorer.score }} / 100 · {{ top_scorer.category }}</div>
    </div>
    <div class="stat">
      <div class="label">Score promedio</div>
      <div class="value">{{ avg_score }}</div>
      <div class="sub">/ 100 entre {{ candidates_count }} candidatos</div>
    </div>
    <div class="stat">
      <div class="label">Sin brechas críticas</div>
      <div class="value">{{ candidates_without_gaps_count }}</div>
      <div class="sub">de {{ candidates_count }} candidatos</div>
    </div>
    <div class="stat">
      <div class="label">Industria objetivo</div>
      <div class="value">{{ candidates_with_industry_count }}</div>
      <div class="sub">de {{ candidates_count }} candidatos</div>
    </div>
  </div>
</div>

<!-- Tesis comparativa -->
<div class="thesis-card">
  <p class="label">Shortlist recomendado</p>
  <h2>{{ shortlist_headline }}</h2>
  <p class="recommendation">{{ shortlist_rationale }}</p>
  {% if shortlist_note %}
  <p class="note">{{ shortlist_note }}</p>
  {% endif %}
</div>

<!-- Candidate header strip -->
<p class="section-title"><span class="dot"></span>Candidatos en comparación</p>
<div class="candidate-strip">
  {% for c in candidates %}
  <div class="candidate-card {% if c.is_top %}top{% endif %}" style="--score-tone: {{ c.tone.text }}; --badge-bg: {{ c.tone.badge_bg }}; --badge-fg: {{ c.tone.badge_fg }};">
    {% if c.is_top %}<span class="top-badge">Top score</span>{% endif %}
    <div class="name">{{ c.name }}</div>
    <div class="role">{{ c.current_position }}</div>
    <div class="company">{{ c.current_company }}</div>
    <div class="score-line">
      <span class="score-num">{{ c.score }}</span>
      <span class="score-of">/ 100</span>
      <span class="badge">{{ c.score_category }}</span>
    </div>
  </div>
  {% endfor %}
</div>

<!-- Score comparativo -->
<p class="section-title"><span class="dot"></span>Score por dimensión</p>
<table class="compare">
  <thead>
    <tr>
      <th class="dim-col" style="width: 22%;">Dimensión</th>
      {% for c in candidates %}
      <th>{{ c.short_name }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
    <tr class="total-row">
      <td class="dim-name">Score total</td>
      {% for c in candidates %}
      <td class="{% if c.is_top %}best{% endif %} score-cell">{{ c.score }} / 100</td>
      {% endfor %}
    </tr>
    {% for row in dimension_rows %}
    <tr>
      <td class="dim-name">{{ row.name }}</td>
      {% for cell in row.cells %}
      <td class="{% if cell.is_best %}best{% endif %}">
        {% if cell.score is none %}
        <span style="color: var(--brand-gray); font-size: 8pt;">—</span>
        {% else %}
        <div class="score-cell">{{ cell.score }} / {{ row.max }}</div>
        <div class="bar"><div class="fill {% if cell.ratio >= 0.85 %}fill-strong{% elif cell.ratio >= 0.6 %}fill-good{% elif cell.ratio >= 0.4 %}fill-mid{% else %}fill-low{% endif %}" style="width: {{ (cell.ratio * 100)|round(0) }}%;"></div></div>
        {% endif %}
      </td>
      {% endfor %}
    </tr>
    {% endfor %}
    <tr>
      <td class="dim-name">Brechas críticas</td>
      {% for c in candidates %}
      <td>
        {% if c.gaps_count == 0 %}
        <span class="pill pill-emerald">Sin brechas</span>
        {% else %}
        <span class="pill pill-rose">{{ c.gaps_count }}</span>
        {% endif %}
      </td>
      {% endfor %}
    </tr>
    <tr>
      <td class="dim-name">Fortalezas calzadas</td>
      {% for c in candidates %}
      <td><span class="pill pill-emerald">{{ c.strengths_count }}</span></td>
      {% endfor %}
    </tr>
    <tr>
      <td class="dim-name">Oportunidades transferibles</td>
      {% for c in candidates %}
      <td><span class="pill pill-indigo">{{ c.opportunities_count }}</span></td>
      {% endfor %}
    </tr>
    <tr>
      <td class="dim-name">Fase de carrera</td>
      {% for c in candidates %}
      <td style="font-size: 7.5pt; color: var(--brand-black);">{{ c.current_phase }}</td>
      {% endfor %}
    </tr>
    <tr>
      <td class="dim-name">Estabilidad</td>
      {% for c in candidates %}
      <td><span class="pill {% if c.tenure_stability_tone == 'positive' %}pill-emerald{% elif c.tenure_stability_tone == 'risk' %}pill-rose{% else %}pill-slate{% endif %}">{{ c.tenure_stability }}</span></td>
      {% endfor %}
    </tr>
    <tr>
      <td class="dim-name">Recomendación</td>
      {% for c in candidates %}
      <td style="font-size: 7.5pt; color: var(--brand-black);">{{ c.recommendation }}</td>
      {% endfor %}
    </tr>
  </tbody>
</table>

<!-- Matriz 360 (top 3 por candidato) -->
<p class="section-title"><span class="dot"></span>Calce 360 — Top 3 por candidato</p>
<div class="matrix">
  {% for c in candidates %}
  <div class="col">
    <h4>{{ c.name }}</h4>
    <div class="row">
      <div class="row-label">Fortalezas</div>
      {% if c.top_strengths %}
        {% for s in c.top_strengths %}<div class="item strength">{{ s }}</div>{% endfor %}
      {% else %}
        <div class="item" style="color: var(--brand-gray); font-style: italic;">Sin fortalezas destacadas</div>
      {% endif %}
    </div>
    <div class="row">
      <div class="row-label">Brechas</div>
      {% if c.top_gaps %}
        {% for g in c.top_gaps %}<div class="item gap">{{ g }}</div>{% endfor %}
      {% else %}
        <div class="item" style="color: var(--brand-gray); font-style: italic;">Sin brechas críticas</div>
      {% endif %}
    </div>
    <div class="row">
      <div class="row-label">Oportunidades</div>
      {% if c.top_opportunities %}
        {% for o in c.top_opportunities %}<div class="item opp">{{ o }}</div>{% endfor %}
      {% else %}
        <div class="item" style="color: var(--brand-gray); font-style: italic;">No identificadas</div>
      {% endif %}
    </div>
  </div>
  {% endfor %}
</div>

<!-- Detalle por candidato -->
<p class="section-title"><span class="dot"></span>Detalle individual y preguntas clave para entrevista</p>
{% for c in candidates %}
<div class="detail-block">
  <div class="head">
    <div class="score">{{ c.score }}</div>
    <div>
      <div class="name">{{ c.name }}</div>
      <div class="role">{{ c.current_position }} · {{ c.current_company }}</div>
    </div>
  </div>
  {% if c.talent_thesis %}
  <p class="thesis">{{ c.talent_thesis }}</p>
  {% endif %}
  <div class="grid">
    <div class="qcol">
      <h5>Preguntas prioritarias (Alta)</h5>
      {% if c.priority_questions %}
        {% for q in c.priority_questions %}
          <div style="margin-bottom: 3px;">· {{ q }}</div>
        {% endfor %}
      {% else %}
        <div style="color: var(--brand-gray); font-style: italic;">No definidas.</div>
      {% endif %}
    </div>
    <div class="scol">
      <h5>Foco en referencias</h5>
      {% if c.reference_check_focus %}
        {% for r in c.reference_check_focus %}
          <div style="margin-bottom: 3px;">· {{ r }}</div>
        {% endfor %}
      {% else %}
        <div style="color: var(--brand-gray); font-style: italic;">No definido.</div>
      {% endif %}
    </div>
    <div class="ocol">
      <h5>Onboarding</h5>
      {% if c.onboarding_considerations %}
        {% for o in c.onboarding_considerations %}
          <div style="margin-bottom: 3px;">· {{ o }}</div>
        {% endfor %}
      {% else %}
        <div style="color: var(--brand-gray); font-style: italic;">Plan estándar.</div>
      {% endif %}
    </div>
  </div>
</div>
{% endfor %}

<div class="traceability">
  <strong>Nota de trazabilidad</strong><br/>
  Informe comparativo generado por TalentScan a partir del perfil objetivo del cargo y las Evaluaciones 360 individuales de cada candidato. Debe ser revisado por el consultor responsable antes de ser compartido con el cliente. La conclusión ejecutiva del shortlist refleja el ranking algorítmico (score total + brechas críticas) y debe ser validada por el partner del mandato.
</div>

</body>
</html>
"""
