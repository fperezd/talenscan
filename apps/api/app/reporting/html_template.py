"""Template HTML que replica la pantalla de Evaluación 360.

Se renderiza con Jinja2 y luego se convierte a PDF con WeasyPrint para
obtener fidelidad visual 1:1 con la UI web.
"""

from __future__ import annotations

REPORT_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Evaluación 360 — {{ candidate_name }}</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 22mm 16mm;
    @bottom-center {
      content: "Talenscan · Evaluación 360 · " counter(page) " / " counter(pages);
      font-size: 8pt;
      color: #57575680;
      font-family: 'Helvetica', 'Arial', sans-serif;
    }
  }

  :root {
    --brand-blue: #177FC6;
    --brand-blue-dark: #0F5E94;
    --brand-blue-soft: #E5F1FA;
    --brand-black: #1D1D1B;
    --brand-gray: #575756;
    --brand-gray-mid: #6f6f6e;
    --slate-50: #F8FAFC;
    --slate-100: #F1F5F9;
    --slate-200: #E2E8F0;
    --emerald-50: #ECFDF5;
    --emerald-100: #D1FAE5;
    --emerald-200: #A7F3D0;
    --emerald-700: #047857;
    --rose-50: #FFF1F2;
    --rose-100: #FFE4E6;
    --rose-200: #FECDD3;
    --rose-700: #BE123C;
    --amber-50: #FFFBEB;
    --amber-100: #FEF3C7;
    --amber-200: #FDE68A;
    --amber-700: #B45309;
    --indigo-50: #EEF2FF;
    --indigo-100: #E0E7FF;
    --indigo-200: #C7D2FE;
    --indigo-700: #4338CA;
  }

  * { box-sizing: border-box; }

  body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 10pt;
    color: var(--brand-black);
    line-height: 1.45;
    margin: 0;
    padding: 0;
  }

  .eyebrow {
    color: var(--brand-blue);
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0 0 4px 0;
  }

  h1, h2, h3, h4 { margin: 0; font-weight: 600; color: var(--brand-black); }
  p { margin: 0; }

  /* --- Header --- */
  .hero {
    border-radius: 14px;
    background: white;
    border: 1px solid var(--slate-200);
    padding: 18px;
    display: flex;
    align-items: flex-start;
    gap: 18px;
    margin-bottom: 14px;
    page-break-inside: avoid;
  }

  .score-card {
    flex-shrink: 0;
    width: 92px;
    height: 92px;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--bg-tone, var(--brand-blue-soft));
    border: 3px solid var(--ring-tone, var(--brand-blue));
  }
  .score-card .num { font-size: 32pt; font-weight: 700; color: var(--text-tone, var(--brand-blue)); line-height: 1; }
  .score-card .of { font-size: 7pt; color: var(--brand-gray); margin-top: 2px; text-transform: uppercase; letter-spacing: 1px; }

  .hero-info { flex: 1; }
  .hero-info h1 { font-size: 18pt; margin: 4px 0; }
  .hero-info .recommendation { font-size: 10pt; color: var(--brand-gray); max-width: 480px; }

  .badges { margin-top: 8px; }
  .badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 8pt;
    font-weight: 600;
    margin-right: 4px;
  }
  .badge-cat { background: var(--badge-bg, var(--brand-blue-soft)); color: var(--badge-fg, var(--brand-blue)); }
  .badge-emerald { background: var(--emerald-100); color: var(--emerald-700); }
  .badge-rose { background: var(--rose-100); color: var(--rose-700); }
  .badge-indigo { background: var(--indigo-100); color: var(--indigo-700); }
  .badge-amber { background: var(--amber-100); color: var(--amber-700); }

  /* --- Sections --- */
  .section {
    background: white;
    border-radius: 14px;
    border: 1px solid var(--slate-200);
    padding: 16px 18px;
    margin-bottom: 12px;
    page-break-inside: avoid;
  }
  .section h3 {
    font-size: 11pt;
    margin: 0 0 8px 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .section h3 .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--brand-blue);
    display: inline-block;
  }
  .section .body { font-size: 10pt; color: var(--brand-gray); }
  .section .body p { margin: 0; }

  .thesis-card {
    background: linear-gradient(135deg, var(--brand-blue-soft), white);
    border: 1px solid var(--brand-blue);
  }
  .thesis-card .quote {
    font-size: 12pt;
    font-weight: 600;
    color: var(--brand-black);
    line-height: 1.5;
    margin-top: 4px;
  }
  .diff-card {
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid var(--slate-200);
    background: rgba(255,255,255,0.7);
  }
  .diff-card .label {
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--brand-gray);
    letter-spacing: 1px;
  }
  .diff-card p { margin-top: 3px; color: var(--brand-black); }

  /* --- 3-col grid (Fortalezas / Oportunidades / Brechas) --- */
  .three-col {
    display: table;
    width: 100%;
    border-collapse: separate;
    border-spacing: 8px;
    margin-bottom: 12px;
  }
  .col {
    display: table-cell;
    width: 33.33%;
    border-radius: 14px;
    padding: 14px;
    border: 1px solid;
    vertical-align: top;
  }
  .col h3 { font-size: 10pt; }
  .col.strengths { background: var(--emerald-50); border-color: var(--emerald-200); }
  .col.opportunities { background: var(--indigo-50); border-color: var(--indigo-200); }
  .col.gaps { background: var(--rose-50); border-color: var(--rose-200); }
  .col .item {
    background: white;
    border: 1px solid;
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 6px;
  }
  .col.strengths .item { border-color: var(--emerald-100); }
  .col.opportunities .item { border-color: var(--indigo-100); }
  .col.gaps .item { border-color: var(--rose-100); }
  .col .item .title { font-size: 9pt; font-weight: 600; color: var(--brand-black); }
  .col .item .detail { font-size: 8.5pt; color: var(--brand-gray); margin-top: 2px; }
  .col .item .evidence { font-size: 7.5pt; font-style: italic; color: var(--brand-gray); margin-top: 3px; }
  .col.opportunities .item .evidence { color: var(--indigo-700); }
  .col.strengths .item .evidence { color: var(--emerald-700); }
  .col.gaps .item .evidence { color: var(--brand-gray); }
  .col.gaps .item .impact { font-size: 8pt; color: var(--rose-700); margin-top: 3px; }
  .col.gaps .item .mitigation { font-size: 8pt; color: var(--brand-gray); margin-top: 2px; }

  .opp-skills {
    margin-top: 8px;
    border-top: 1px solid var(--indigo-200);
    padding-top: 8px;
  }
  .opp-skills .label { font-size: 7pt; font-weight: 700; text-transform: uppercase; color: var(--indigo-700); letter-spacing: 1px; }
  .opp-skills .chips { margin-top: 4px; }
  .opp-skills .chip {
    display: inline-block;
    background: white;
    border: 1px solid var(--indigo-200);
    border-radius: 999px;
    padding: 3px 8px;
    font-size: 8pt;
    color: var(--indigo-700);
    margin: 2px 3px 2px 0;
  }

  /* --- Dimension table --- */
  table.dimensions {
    width: 100%;
    border-collapse: collapse;
    margin-top: 6px;
    font-size: 9pt;
  }
  table.dimensions thead th {
    background: var(--slate-50);
    color: var(--brand-gray);
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 6px 8px;
    text-align: left;
    border-bottom: 1px solid var(--slate-200);
  }
  table.dimensions tbody td {
    padding: 6px 8px;
    border-bottom: 1px solid var(--slate-100);
    vertical-align: top;
  }
  table.dimensions .dim-name { font-weight: 600; color: var(--brand-black); }
  table.dimensions .dim-score {
    text-align: center;
    font-weight: 700;
    color: var(--brand-black);
    white-space: nowrap;
  }
  .score-bar { width: 60px; height: 4px; background: var(--slate-200); border-radius: 2px; margin: 3px auto 0; overflow: hidden; }
  .score-bar .fill { height: 100%; border-radius: 2px; }
  .fill-strong { background: #34D399; }
  .fill-good { background: #60A5FA; }
  .fill-mid { background: #FBBF24; }
  .fill-low { background: #FB7185; }
  .ev-badge { padding: 2px 6px; border-radius: 999px; font-size: 7pt; font-weight: 600; }
  .ev-alta { background: var(--emerald-100); color: var(--emerald-700); }
  .ev-media { background: var(--amber-100); color: var(--amber-700); }
  .ev-baja { background: #E2E8F0; color: var(--brand-gray); }
  .rationale { color: var(--brand-gray); font-size: 8pt; }

  /* --- Trajectory grid --- */
  .traj-grid { display: table; width: 100%; border-spacing: 8px; }
  .traj-cell {
    display: table-cell;
    width: 33.33%;
    background: var(--slate-50);
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 10px 12px;
  }
  .traj-cell .label { font-size: 7pt; font-weight: 700; text-transform: uppercase; color: var(--brand-gray); letter-spacing: 1px; }
  .traj-cell .value { font-size: 10pt; font-weight: 600; color: var(--brand-black); margin-top: 2px; }
  .traj-narrative { margin-top: 10px; color: var(--brand-gray); font-size: 9.5pt; line-height: 1.55; }

  /* --- Cultural fit signals --- */
  .signal-card {
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 5px;
    border: 1px solid;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .signal-card .text { flex: 1; font-size: 9pt; color: var(--brand-black); }
  .signal-card .indicator {
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 2px 7px;
    border-radius: 999px;
    background: white;
  }
  .signal-positive { background: var(--emerald-50); border-color: var(--emerald-200); }
  .signal-positive .indicator { color: var(--emerald-700); border: 1px solid var(--emerald-200); }
  .signal-risk { background: var(--rose-50); border-color: var(--rose-200); }
  .signal-risk .indicator { color: var(--rose-700); border: 1px solid var(--rose-200); }
  .signal-neutral { background: var(--slate-50); border-color: var(--slate-200); }
  .signal-neutral .indicator { color: var(--brand-gray); border: 1px solid var(--slate-200); }

  /* --- Lists (weaknesses, risks, red flags, references, onboarding) --- */
  .bullet-list { list-style: none; padding: 0; margin: 0; }
  .bullet-list li {
    padding-left: 16px;
    position: relative;
    margin-bottom: 5px;
    font-size: 9.5pt;
    color: var(--brand-black);
  }
  .bullet-list li::before {
    content: "";
    position: absolute;
    left: 4px;
    top: 7px;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--brand-blue);
  }
  .bullet-list.amber li::before { background: #F59E0B; }
  .bullet-list.rose li::before { background: #F43F5E; }
  .bullet-list.slate li::before { background: #94A3B8; }

  .risk-card {
    background: white;
    border: 1px solid var(--amber-100);
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 9pt;
  }
  .risk-card .validation { font-size: 8pt; color: var(--amber-700); margin-top: 3px; }

  /* --- Interview questions --- */
  .question-item {
    background: var(--slate-50);
    border: 1px solid var(--slate-100);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 6px;
    page-break-inside: avoid;
  }
  .question-item .question-line { display: flex; align-items: flex-start; gap: 8px; }
  .question-item .number {
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--brand-blue-soft);
    color: var(--brand-blue);
    font-size: 9pt;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .question-item .text { flex: 1; font-size: 10pt; color: var(--brand-black); }
  .question-item .meta { margin-top: 5px; font-size: 7.5pt; color: var(--brand-gray); }
  .question-item .meta .label { font-weight: 700; color: var(--brand-black); }
  .question-item .meta .priority-badge {
    margin-left: 6px;
    padding: 2px 7px;
    border-radius: 999px;
    font-weight: 600;
  }
  .priority-alta { background: var(--rose-100); color: var(--rose-700); }
  .priority-media { background: var(--amber-100); color: var(--amber-700); }
  .priority-baja { background: var(--slate-100); color: var(--brand-gray); }

  /* --- Two-col grid --- */
  .two-col { display: table; width: 100%; border-spacing: 8px; margin-bottom: 12px; }
  .two-col > .col-half { display: table-cell; width: 50%; vertical-align: top; }
  .three-grid { display: table; width: 100%; border-spacing: 8px; margin-bottom: 12px; }
  .three-grid > .col-third { display: table-cell; width: 33.33%; vertical-align: top; }

  /* --- Mandate meta table --- */
  .meta-table { width: 100%; border-collapse: collapse; font-size: 9pt; }
  .meta-table td { padding: 4px 6px; border-bottom: 1px solid var(--slate-100); }
  .meta-table .label { width: 30%; color: var(--brand-gray); font-weight: 700; font-size: 8pt; text-transform: uppercase; letter-spacing: 0.6px; }
  .meta-table .value { color: var(--brand-black); }

  /* --- Verdict --- */
  .verdict-card {
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--slate-50);
    border: 1px solid var(--slate-200);
  }
  .verdict-card .label { font-size: 7pt; font-weight: 700; text-transform: uppercase; color: var(--brand-gray); letter-spacing: 1px; }
  .verdict-card p { margin-top: 3px; font-weight: 600; color: var(--brand-black); }

  /* --- Evidence --- */
  .evidence-list li {
    background: var(--slate-50);
    border: 1px solid var(--slate-100);
    border-radius: 8px;
    padding: 6px 10px;
    margin-bottom: 4px;
    font-style: italic;
    font-size: 9pt;
    color: var(--brand-gray);
    list-style: none;
    padding-left: 10px;
  }

  /* --- Footer note --- */
  .traceability {
    margin-top: 16px;
    padding: 10px 12px;
    background: var(--slate-50);
    border-radius: 10px;
    font-size: 7.5pt;
    color: var(--brand-gray);
    line-height: 1.5;
  }
</style>
</head>
<body>

<!-- Hero -->
<div class="hero" style="--bg-tone: {{ tone.bg }}; --ring-tone: {{ tone.ring }}; --text-tone: {{ tone.text }};">
  <div class="score-card">
    <div class="num">{{ score }}</div>
    <div class="of">/ 100</div>
  </div>
  <div class="hero-info">
    <p class="eyebrow">Evaluación 360 Talenscan</p>
    <h1>{{ candidate_name }}</h1>
    <p style="color: var(--brand-gray); font-size: 10pt; margin-top: 2px;">
      {{ target_role }} · {{ client_name }}
    </p>
    <p class="recommendation" style="margin-top: 8px;">{{ recommendation }}</p>
    <div class="badges">
      <span class="badge" style="--badge-bg: {{ tone.badge_bg }}; --badge-fg: {{ tone.badge_fg }};">{{ score_category }}</span>
      {% if critical_gaps_detailed %}
      <span class="badge badge-rose">{{ critical_gaps_detailed|length }} brecha{{ '' if critical_gaps_detailed|length == 1 else 's' }} crítica{{ '' if critical_gaps_detailed|length == 1 else 's' }}</span>
      {% else %}
      <span class="badge badge-emerald">Sin brechas críticas</span>
      {% endif %}
      {% if opportunities %}
      <span class="badge badge-indigo">{{ opportunities|length }} oportunidad{{ '' if opportunities|length == 1 else 'es' }} transferible{{ '' if opportunities|length == 1 else 's' }}</span>
      {% endif %}
    </div>
  </div>
</div>

<!-- Tesis de talento -->
{% if talent_thesis %}
<div class="section thesis-card">
  <p class="eyebrow">Tesis de talento</p>
  <p class="quote">{{ talent_thesis }}</p>
  {% if differentiation %}
  <div class="diff-card">
    <div class="label">Diferenciador</div>
    <p>{{ differentiation }}</p>
  </div>
  {% endif %}
</div>
{% endif %}

<!-- Resumen ejecutivo -->
<div class="section">
  <h3><span class="dot"></span>Resumen ejecutivo</h3>
  <div class="body">
    <p>{{ summary }}</p>
    {% if final_verdict %}
    <div class="verdict-card">
      <div class="label">Veredicto final</div>
      <p>{{ final_verdict }}</p>
    </div>
    {% endif %}
  </div>
</div>

<!-- Mandato meta -->
<div class="section">
  <h3><span class="dot"></span>Información del mandato</h3>
  <table class="meta-table">
    <tr><td class="label">Cliente</td><td class="value">{{ client_name }}</td></tr>
    <tr><td class="label">Mandato</td><td class="value">{{ mandate_title }}</td></tr>
    <tr><td class="label">Cargo objetivo</td><td class="value">{{ target_role }}</td></tr>
    <tr><td class="label">Perfil objetivo</td><td class="value">{{ position_spec_title }}</td></tr>
    {% if candidate_position %}<tr><td class="label">Cargo actual</td><td class="value">{{ candidate_position }}</td></tr>{% endif %}
    {% if candidate_company %}<tr><td class="label">Empresa actual</td><td class="value">{{ candidate_company }}</td></tr>{% endif %}
    {% if candidate_email %}<tr><td class="label">Email</td><td class="value">{{ candidate_email }}</td></tr>{% endif %}
    {% if candidate_phone %}<tr><td class="label">Teléfono</td><td class="value">{{ candidate_phone }}</td></tr>{% endif %}
  </table>
</div>

<!-- 3 columnas: Fortalezas / Oportunidades / Brechas -->
{% if strengths_detailed or opportunities or critical_gaps_detailed %}
<div class="three-col">
  {% if strengths_detailed %}
  <div class="col strengths">
    <h3 style="color: var(--emerald-700);">Fortalezas calzadas <span class="badge badge-emerald" style="margin-left:4px;">{{ strengths_detailed|length }}</span></h3>
    {% for s in strengths_detailed %}
    <div class="item">
      <div class="title">{{ s.title }}</div>
      {% if s.detail %}<div class="detail">{{ s.detail }}</div>{% endif %}
      {% if s.evidence %}<div class="evidence">Evidencia: {{ s.evidence }}</div>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if opportunities %}
  <div class="col opportunities">
    <h3 style="color: var(--indigo-700);">Oportunidades transferibles <span class="badge badge-indigo" style="margin-left:4px;">{{ opportunities|length }}</span></h3>
    <p style="font-size: 7.5pt; color: var(--indigo-700); margin: -4px 0 6px 0;">Fortalezas que el cliente puede no estar valorando.</p>
    {% for o in opportunities %}
    <div class="item">
      <div class="title">{{ o.title }}</div>
      {% if o.detail %}<div class="detail">{{ o.detail }}</div>{% endif %}
      {% if o.evidence %}<div class="evidence">Evidencia: {{ o.evidence }}</div>{% endif %}
    </div>
    {% endfor %}
    {% if transferable_skills %}
    <div class="opp-skills">
      <div class="label">Habilidades transferibles</div>
      <div class="chips">
        {% for t in transferable_skills %}<span class="chip">{{ t }}</span>{% endfor %}
      </div>
    </div>
    {% endif %}
  </div>
  {% endif %}

  {% if critical_gaps_detailed %}
  <div class="col gaps">
    <h3 style="color: var(--rose-700);">Brechas críticas <span class="badge badge-rose" style="margin-left:4px;">{{ critical_gaps_detailed|length }}</span></h3>
    {% for g in critical_gaps_detailed %}
    <div class="item">
      <div class="title">{{ g.requirement or g.reason or 'Brecha' }}</div>
      {% if g.impact %}<div class="impact">Impacto: {{ g.impact }}</div>{% endif %}
      {% if g.mitigation %}<div class="mitigation"><strong>Mitigación:</strong> {{ g.mitigation }}</div>{% endif %}
      {% if g.evidence %}<div class="evidence">{{ g.evidence }}</div>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endif %}

<!-- Trayectoria -->
{% if career_trajectory and (career_trajectory.tenure_stability or career_trajectory.current_phase or career_trajectory.progression or career_trajectory.narrative) %}
<div class="section">
  <h3><span class="dot"></span>Trayectoria de carrera</h3>
  <div class="traj-grid">
    {% if career_trajectory.tenure_stability %}
    <div class="traj-cell">
      <div class="label">Estabilidad</div>
      <div class="value">{{ career_trajectory.tenure_stability }}</div>
    </div>
    {% endif %}
    {% if career_trajectory.current_phase %}
    <div class="traj-cell">
      <div class="label">Fase actual</div>
      <div class="value">{{ career_trajectory.current_phase }}</div>
    </div>
    {% endif %}
    {% if career_trajectory.progression %}
    <div class="traj-cell">
      <div class="label">Progresión</div>
      <div class="value">{{ career_trajectory.progression }}</div>
    </div>
    {% endif %}
  </div>
  {% if career_trajectory.narrative %}
  <p class="traj-narrative">{{ career_trajectory.narrative }}</p>
  {% endif %}
</div>
{% endif %}

<!-- Score por dimensión -->
{% if dimensions %}
<div class="section">
  <h3><span class="dot"></span>Score por dimensión</h3>
  <table class="dimensions">
    <thead>
      <tr>
        <th>Dimensión</th>
        <th style="text-align:center;">Score</th>
        <th>Evidencia</th>
        <th>Justificación</th>
      </tr>
    </thead>
    <tbody>
      {% for dim in dimensions %}
      {% set max = dim.max_score or 10 %}
      {% set ratio = (dim.score or 0) / max if max else 0 %}
      <tr>
        <td class="dim-name">{{ dim.dimension }}</td>
        <td class="dim-score">
          {{ dim.score }} / {{ max }}
          <div class="score-bar">
            <div class="fill {% if ratio >= 0.85 %}fill-strong{% elif ratio >= 0.6 %}fill-good{% elif ratio >= 0.4 %}fill-mid{% else %}fill-low{% endif %}" style="width: {{ (ratio * 100)|round(0) }}%;"></div>
          </div>
        </td>
        <td>
          {% set ev = (dim.evidence_level or '').lower() %}
          <span class="ev-badge {% if 'alta' in ev %}ev-alta{% elif 'media' in ev %}ev-media{% else %}ev-baja{% endif %}">{{ dim.evidence_level or 'No evidenciado' }}</span>
        </td>
        <td class="rationale">{{ dim.rationale }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

<!-- Cultural fit / Debilidades / Riesgos / Red flags -->
<div class="two-col">
  {% if cultural_fit_signals %}
  <div class="col-half">
    <div class="section">
      <h3><span class="dot"></span>Señales de cultural fit</h3>
      {% for s in cultural_fit_signals %}
      {% set ind = (s.indicator or 'Neutral').lower() %}
      <div class="signal-card {% if 'positive' in ind %}signal-positive{% elif 'risk' in ind %}signal-risk{% else %}signal-neutral{% endif %}">
        <span class="text">{{ s.signal }}</span>
        <span class="indicator">{{ s.indicator or 'Neutral' }}</span>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if weaknesses %}
  <div class="col-half">
    <div class="section">
      <h3><span class="dot"></span>Debilidades manejables</h3>
      <ul class="bullet-list slate">
        {% for w in weaknesses %}<li>{{ w }}</li>{% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}
</div>

<div class="two-col">
  {% if risks_detailed %}
  <div class="col-half">
    <div class="section" style="border-color: var(--amber-200); background: var(--amber-50);">
      <h3 style="color: var(--amber-700);">Riesgos a validar</h3>
      {% for r in risks_detailed %}
      <div class="risk-card">
        <div>{{ r.risk }}</div>
        {% if r.validation %}<div class="validation"><strong>Cómo validar:</strong> {{ r.validation }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if red_flags %}
  <div class="col-half">
    <div class="section" style="border-color: var(--rose-200); background: var(--rose-50);">
      <h3 style="color: var(--rose-700);">Red flags</h3>
      <ul class="bullet-list rose">
        {% for f in red_flags %}<li>{{ f }}</li>{% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}
</div>

<!-- Preguntas de entrevista -->
{% if interview_questions_detailed %}
<div class="section">
  <h3><span class="dot"></span>Preguntas sugeridas para entrevista <span class="badge badge-cat" style="margin-left:4px; --badge-bg: var(--slate-100); --badge-fg: var(--brand-gray);">{{ interview_questions_detailed|length }}</span></h3>
  {% for q in interview_questions_detailed %}
  <div class="question-item">
    <div class="question-line">
      <div class="number">{{ loop.index }}</div>
      <div class="text">{{ q.question }}</div>
    </div>
    <div class="meta">
      {% if q.objective %}<span class="label">Objetivo:</span> {{ q.objective }}{% endif %}
      {% if q.priority %}
      {% set pri = (q.priority or 'media').lower() %}
      <span class="priority-badge {% if 'alta' in pri %}priority-alta{% elif 'media' in pri %}priority-media{% else %}priority-baja{% endif %}">Prioridad {{ q.priority }}</span>
      {% endif %}
    </div>
  </div>
  {% endfor %}
</div>
{% endif %}

<!-- Reference check + Onboarding + Compensación -->
<div class="three-grid">
  {% if reference_check_focus %}
  <div class="col-third">
    <div class="section">
      <h3><span class="dot"></span>Foco en referencias</h3>
      <ul class="bullet-list">
        {% for r in reference_check_focus %}<li>{{ r }}</li>{% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}

  {% if onboarding_considerations %}
  <div class="col-third">
    <div class="section">
      <h3><span class="dot"></span>Onboarding</h3>
      <ul class="bullet-list">
        {% for o in onboarding_considerations %}<li>{{ o }}</li>{% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}

  {% if compensation_signals %}
  <div class="col-third">
    <div class="section">
      <h3><span class="dot"></span>Compensación</h3>
      <p style="font-size: 9.5pt; color: var(--brand-gray); line-height: 1.5;">{{ compensation_signals }}</p>
    </div>
  </div>
  {% endif %}
</div>

<!-- Evidencia citada -->
{% if evidence %}
<div class="section">
  <h3><span class="dot"></span>Evidencia citada del perfil</h3>
  <ul class="evidence-list">
    {% for e in evidence %}<li>&ldquo;{{ e }}&rdquo;</li>{% endfor %}
  </ul>
</div>
{% endif %}

<div class="traceability">
  <strong style="color: var(--brand-gray); text-transform: uppercase; font-size: 7pt; letter-spacing: 0.8px;">Nota de trazabilidad</strong><br/>
  {{ traceability_note }}<br/>
  <span style="font-size: 7pt;">Modelo: {{ model_version }} · Prompt: {{ prompt_version }}</span>
</div>

</body>
</html>
"""
