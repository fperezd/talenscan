"use client";

import {
  Ban,
  Briefcase,
  Building2,
  Check,
  Clock,
  Linkedin,
  Loader2,
  Mail,
  MapPin,
  Plus,
  Sparkles,
  Tag as TagIcon,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import {
  AVAILABILITY_LABELS,
  NOTE_TYPE_LABELS,
  TALENT_STATUS_LABELS,
  type AvailabilityStatus,
  type NoteType,
  type TalentProfile,
  type TalentStatus,
} from "@/types/talent";

type TabId = "resumen" | "experiencia" | "evaluaciones" | "procesos" | "notas" | "versiones";

const TABS: Array<[TabId, string]> = [
  ["resumen", "Resumen"],
  ["experiencia", "Experiencia y skills"],
  ["evaluaciones", "Evaluaciones"],
  ["procesos", "Procesos"],
  ["notas", "Notas"],
  ["versiones", "Versiones"],
];

const selectClass =
  "rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-brand-black focus:border-brand-blue focus:outline-none";

export function TalentProfileDetail({ talentId: propId }: { talentId?: string }) {
  const pathId = useDynamicId("talentos");
  // Preferir el id real de la URL (window.location); el prop del page estático
  // siempre es "demo" por el rewrite del Worker.
  const talentId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [profile, setProfile] = useState<TalentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("resumen");

  async function reload() {
    setError(null);
    if (talentId === "demo") {
      setProfile(null);
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<TalentProfile>(`/api/talentos/${talentId}`);
      setProfile(data);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible cargar el perfil de talento.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [talentId]);

  async function patch(body: Record<string, unknown>) {
    const updated = await apiFetch<TalentProfile>(`/api/talentos/${talentId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
    setProfile(updated);
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
      </div>
    );
  }
  if (error || !profile) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
        {error || "Perfil no encontrado."}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Header profile={profile} onPatch={patch} talentId={talentId} onReload={reload} />

      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={cn(
              "border-b-2 px-3 py-2 text-sm font-medium transition",
              activeTab === id
                ? "border-brand-blue text-brand-blue"
                : "border-transparent text-brand-grayMid hover:text-brand-black"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === "resumen" ? <ResumenTab profile={profile} /> : null}
      {activeTab === "experiencia" ? <ExperienciaTab profile={profile} /> : null}
      {activeTab === "evaluaciones" ? <EvaluacionesTab profile={profile} /> : null}
      {activeTab === "procesos" ? <ProcesosTab profile={profile} /> : null}
      {activeTab === "notas" ? (
        <NotasTab profile={profile} talentId={talentId} onReload={reload} />
      ) : null}
      {activeTab === "versiones" ? <VersionesTab profile={profile} /> : null}
    </div>
  );
}

function Header({
  profile,
  onPatch,
  talentId,
  onReload,
}: {
  profile: TalentProfile;
  onPatch: (body: Record<string, unknown>) => Promise<void>;
  talentId: string;
  onReload: () => Promise<void>;
}) {
  const [tagInput, setTagInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function addTag() {
    if (!tagInput.trim()) return;
    setBusy(true);
    try {
      await apiFetch<TalentProfile>(`/api/talentos/${talentId}/tags`, {
        method: "POST",
        body: JSON.stringify({ name: tagInput.trim() }),
      });
      setTagInput("");
      await onReload();
    } finally {
      setBusy(false);
    }
  }

  async function removeTag(tagId: number) {
    await apiFetch<TalentProfile>(`/api/talentos/${talentId}/tags/${tagId}`, { method: "DELETE" });
    await onReload();
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-blueSoft/30 via-white to-white p-6 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-semibold", STATUS_TONE(profile.status))}>
              {TALENT_STATUS_LABELS[profile.status]}
            </span>
            {profile.do_not_contact ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2.5 py-0.5 text-[11px] font-semibold text-rose-700">
                <Ban className="h-3 w-3" />
                No contactar
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-brand-black">{profile.full_name}</h2>
          <p className="mt-1 text-sm text-brand-grayMid">
            {[profile.current_position, profile.current_company].filter(Boolean).join(" · ") || "Sin cargo registrado"}
            {profile.inferred_seniority ? ` · ${profile.inferred_seniority}` : ""}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-brand-grayMid">
            {profile.primary_email ? (
              <span className="inline-flex items-center gap-1"><Mail className="h-3 w-3" />{profile.primary_email}</span>
            ) : null}
            {profile.linkedin_url ? (
              <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-brand-blue">
                <Linkedin className="h-3 w-3" />LinkedIn
              </a>
            ) : null}
            {profile.city || profile.country ? (
              <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{[profile.city, profile.country].filter(Boolean).join(", ")}</span>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">Estado</label>
            <select
              value={profile.status}
              onChange={(e) => onPatch({ status: e.target.value })}
              className={selectClass}
            >
              {(Object.keys(TALENT_STATUS_LABELS) as TalentStatus[]).map((k) => (
                <option key={k} value={k}>{TALENT_STATUS_LABELS[k]}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">Disponibilidad</label>
            <select
              value={profile.availability_status}
              onChange={(e) => onPatch({ availability_status: e.target.value })}
              className={selectClass}
            >
              {(Object.keys(AVAILABILITY_LABELS) as AvailabilityStatus[]).map((k) => (
                <option key={k} value={k}>{AVAILABILITY_LABELS[k]}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-xs text-brand-grayMid">
            <input
              type="checkbox"
              checked={profile.do_not_contact}
              onChange={(e) => onPatch({ do_not_contact: e.target.checked })}
              className="h-3.5 w-3.5 rounded border-slate-300 text-brand-blue focus:ring-brand-blue/30"
            />
            Marcar “no contactar”
          </label>
        </div>
      </div>

      {/* Tags */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <TagIcon className="h-3.5 w-3.5 text-brand-grayMid" />
        {profile.tags.map((tag) => (
          <span key={tag.id} className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-medium text-brand-blue">
            {tag.name}
            <button type="button" onClick={() => removeTag(tag.id)} className="hover:text-rose-600" aria-label="Quitar tag">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        ))}
        <div className="inline-flex items-center gap-1">
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addTag()}
            placeholder="Agregar tag…"
            className="w-28 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] text-brand-black focus:border-brand-blue focus:outline-none"
          />
          <button type="button" onClick={addTag} disabled={busy || !tagInput.trim()} className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-brand-blue text-white disabled:opacity-50">
            {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
          </button>
        </div>
      </div>
    </section>
  );
}

function STATUS_TONE(status: TalentStatus): string {
  return {
    active: "bg-emerald-100 text-emerald-700",
    passive: "bg-amber-100 text-amber-700",
    placed: "bg-brand-blueSoft text-brand-blue",
    archived: "bg-slate-100 text-brand-grayMid",
  }[status];
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <h3 className="text-sm font-semibold text-brand-black">{title}</h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function Chips({ items, empty }: { items: string[]; empty: string }) {
  if (!items || items.length === 0) return <p className="text-xs text-brand-grayMid">{empty}</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((s) => (
        <span key={s} className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-brand-black">{s}</span>
      ))}
    </div>
  );
}

function ResumenTab({ profile }: { profile: TalentProfile }) {
  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <Card title="Resumen de talento">
        {profile.summary ? (
          <p className="text-sm leading-relaxed text-brand-black">{profile.summary}</p>
        ) : (
          <p className="text-xs text-brand-grayMid">Sin resumen consolidado todavía.</p>
        )}
      </Card>
      <Card title="Industrias">
        <Chips items={profile.industries} empty="Sin industrias registradas." />
      </Card>
    </div>
  );
}

function ExperienciaTab({ profile }: { profile: TalentProfile }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card title="Skills"><Chips items={profile.skills} empty="Sin skills registradas." /></Card>
      <Card title="Herramientas"><Chips items={profile.tools} empty="Sin herramientas registradas." /></Card>
      <Card title="Idiomas"><Chips items={profile.languages} empty="Sin idiomas registrados." /></Card>
      <Card title="Certificaciones"><Chips items={profile.certifications} empty="Sin certificaciones." /></Card>
    </div>
  );
}

function EvaluacionesTab({ profile }: { profile: TalentProfile }) {
  if (profile.evaluations.length === 0) {
    return <EmptyBlock text="Sin evaluaciones 360 históricas asociadas a este talento." />;
  }
  return (
    <ul className="space-y-3">
      {profile.evaluations.map((ev) => (
        <li key={ev.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-brand-black">
                {ev.target_role || "Evaluación"} {ev.client_name ? `· ${ev.client_name}` : ""}
              </p>
              <p className="text-xs text-brand-grayMid">
                {new Date(ev.created_at).toLocaleDateString("es-ES")}
                {ev.result_stage ? ` · ${ev.result_stage}` : ""}
              </p>
            </div>
            {ev.total_score !== null ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2.5 py-0.5 text-xs font-semibold text-brand-blue">
                <Sparkles className="h-3 w-3" />
                {ev.total_score}/100 {ev.score_category ? `· ${ev.score_category}` : ""}
              </span>
            ) : null}
          </div>
          {ev.recommendation ? <p className="mt-1 text-xs text-brand-grayMid">{ev.recommendation}</p> : null}
        </li>
      ))}
    </ul>
  );
}

function ProcesosTab({ profile }: { profile: TalentProfile }) {
  if (profile.process_history.length === 0) {
    return <EmptyBlock text="Sin historial de procesos. Cuando el talento participe en mandatos, aparecerá aquí." />;
  }
  return (
    <ul className="space-y-3">
      {profile.process_history.map((proc) => (
        <li key={proc.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-brand-blue" />
            <span className="text-sm font-semibold text-brand-black">
              {proc.target_role || "Proceso"} {proc.client_name ? `· ${proc.client_name}` : ""}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-brand-grayMid">
            {proc.pipeline_stage ? <span><Building2 className="mr-1 inline h-3 w-3" />{proc.pipeline_stage}</span> : null}
            {proc.final_result ? <span>Resultado: {proc.final_result}</span> : null}
          </div>
          {proc.consultant_notes ? <p className="mt-1 text-xs text-brand-grayMid">{proc.consultant_notes}</p> : null}
        </li>
      ))}
    </ul>
  );
}

function NotasTab({
  profile,
  talentId,
  onReload,
}: {
  profile: TalentProfile;
  talentId: string;
  onReload: () => Promise<void>;
}) {
  const [noteType, setNoteType] = useState<NoteType>("general");
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);

  async function addNote() {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await apiFetch(`/api/talentos/${talentId}/notas`, {
        method: "POST",
        body: JSON.stringify({ note_type: noteType, note_text: text.trim() }),
      });
      setText("");
      await onReload();
    } finally {
      setSaving(false);
    }
  }

  async function removeNote(noteId: number) {
    await apiFetch(`/api/talentos/${talentId}/notas/${noteId}`, { method: "DELETE" });
    await onReload();
  }

  return (
    <div className="space-y-4">
      <Card title="Agregar nota interna">
        <div className="flex flex-wrap items-start gap-2">
          <select value={noteType} onChange={(e) => setNoteType(e.target.value as NoteType)} className={selectClass}>
            {(Object.keys(NOTE_TYPE_LABELS) as NoteType[]).map((k) => (
              <option key={k} value={k}>{NOTE_TYPE_LABELS[k]}</option>
            ))}
          </select>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            placeholder="Escribe una nota (hallazgos, feedback, contexto)…"
            className="min-w-[260px] flex-1 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
          />
          <button
            type="button"
            onClick={addNote}
            disabled={saving || !text.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-2 text-sm font-semibold text-white transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Guardar
          </button>
        </div>
      </Card>

      {profile.notes.length === 0 ? (
        <EmptyBlock text="Sin notas todavía." />
      ) : (
        <ul className="space-y-2">
          {profile.notes.map((note) => (
            <li key={note.id} className="rounded-xl border border-slate-200 bg-white p-3 shadow-soft">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-brand-grayMid">
                    {NOTE_TYPE_LABELS[note.note_type]}
                  </span>
                  <p className="mt-1 text-sm text-brand-black">{note.note_text}</p>
                  <p className="mt-0.5 inline-flex items-center gap-1 text-[11px] text-brand-grayMid">
                    <Clock className="h-3 w-3" />
                    {new Date(note.created_at).toLocaleString("es-ES")}
                    {note.created_by ? ` · ${note.created_by}` : ""}
                  </p>
                </div>
                <button type="button" onClick={() => removeNote(note.id)} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-brand-grayMid hover:bg-rose-50 hover:text-rose-700" aria-label="Eliminar nota">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function VersionesTab({ profile }: { profile: TalentProfile }) {
  if (profile.versions.length === 0) {
    return <EmptyBlock text="Sin versiones registradas." />;
  }
  return (
    <ol className="space-y-2">
      {profile.versions.map((v) => (
        <li key={v.id} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-soft">
          <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-blueSoft text-[11px] font-bold text-brand-blue">
            v{v.version_number}
          </span>
          <div>
            <p className="text-sm text-brand-black">{v.change_reason || "Actualización"}</p>
            <p className="text-[11px] text-brand-grayMid">
              {new Date(v.created_at).toLocaleString("es-ES")}
              {v.source ? ` · ${v.source}` : ""}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function EmptyBlock({ text }: { text: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-10 text-center text-sm text-brand-grayMid shadow-soft">
      {text}
    </p>
  );
}
