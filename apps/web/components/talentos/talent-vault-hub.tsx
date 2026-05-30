"use client";

import {
  Ban,
  Loader2,
  Plus,
  Search,
  Sparkles,
  TrendingUp,
  UserCheck,
  Users,
  Vault,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  AVAILABILITY_LABELS,
  TALENT_STATUS_LABELS,
  type AvailabilityStatus,
  type TalentListResponse,
  type TalentProfile,
  type TalentStatus,
  type TalentSummary,
  type TalentVaultMetrics,
} from "@/types/talent";

const STATUS_TONE: Record<TalentStatus, string> = {
  active: "bg-emerald-100 text-emerald-700",
  passive: "bg-amber-100 text-amber-700",
  placed: "bg-brand-blueSoft text-brand-blue",
  archived: "bg-slate-100 text-brand-grayMid",
};

const inputClass =
  "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15";

export function TalentVaultHub() {
  const [data, setData] = useState<TalentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<TalentStatus | "">("");
  const [availabilityFilter, setAvailabilityFilter] = useState<AvailabilityStatus | "">("");
  const [creating, setCreating] = useState(false);

  async function reload() {
    setError(null);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (statusFilter) params.set("estado", statusFilter);
      if (availabilityFilter) params.set("disponibilidad", availabilityFilter);
      const qs = params.toString();
      const body = await apiFetch<TalentListResponse>(`/api/talentos${qs ? `?${qs}` : ""}`);
      setData(body);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible cargar la Bóveda de Talento.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => void reload(), 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, statusFilter, availabilityFilter]);

  const metrics = data?.metrics;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-brand-grayMid">
          Base inteligente de perfiles evaluados y reutilizables.
        </p>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
        >
          <Plus className="h-4 w-4" />
          Nuevo talento
        </button>
      </div>

      {/* Métricas */}
      <MetricsRow metrics={metrics} loading={loading && !data} />

      {/* Buscador + filtros */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[260px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por cargo, empresa, skill, industria o nombre"
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TalentStatus | "")}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
        >
          <option value="">Todo estado</option>
          {(Object.keys(TALENT_STATUS_LABELS) as TalentStatus[]).map((k) => (
            <option key={k} value={k}>
              {TALENT_STATUS_LABELS[k]}
            </option>
          ))}
        </select>
        <select
          value={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.value as AvailabilityStatus | "")}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
        >
          <option value="">Toda disponibilidad</option>
          {(Object.keys(AVAILABILITY_LABELS) as AvailabilityStatus[]).map((k) => (
            <option key={k} value={k}>
              {AVAILABILITY_LABELS[k]}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      ) : loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState />
      ) : (
        <TalentTable items={data.items} />
      )}

      {creating ? (
        <CreateTalentModal
          onClose={() => setCreating(false)}
          onCreated={(p) => {
            setCreating(false);
            window.location.href = `/talentos/${p.id}`;
          }}
        />
      ) : null}
    </div>
  );
}

function MetricsRow({
  metrics,
  loading,
}: {
  metrics: TalentVaultMetrics | undefined;
  loading: boolean;
}) {
  const cards = [
    { label: "Total talentos", value: metrics?.total, icon: Vault },
    { label: "Evaluados", value: metrics?.evaluated, icon: Sparkles },
    { label: "En reserva", value: metrics?.in_reserve, icon: Users },
    { label: "Disponibles", value: metrics?.available, icon: UserCheck, tone: "emerald" as const },
    {
      label: "Score promedio",
      value: metrics?.average_score ?? "—",
      icon: TrendingUp,
    },
    { label: "Actualizados (30d)", value: metrics?.updated_last_30_days, icon: TrendingUp },
  ];
  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map(({ label, value, icon: Icon, tone }) => (
        <div key={label} className="rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-soft">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-brand-grayMid">
            <Icon className={cn("h-3.5 w-3.5", tone === "emerald" ? "text-emerald-600" : "text-brand-blue")} />
            {label}
          </div>
          <p className="mt-1 text-2xl font-bold text-brand-black">
            {loading ? "…" : value ?? 0}
          </p>
        </div>
      ))}
    </section>
  );
}

function TalentTable({ items }: { items: TalentSummary[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-soft">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wider text-brand-grayMid">
            <th className="px-4 py-3 font-semibold">Nombre / cargo</th>
            <th className="px-4 py-3 font-semibold">Empresa</th>
            <th className="px-4 py-3 font-semibold">Industrias</th>
            <th className="px-4 py-3 font-semibold">Score</th>
            <th className="px-4 py-3 font-semibold">Estado</th>
            <th className="px-4 py-3 font-semibold">Disponibilidad</th>
            <th className="px-4 py-3 font-semibold">Tags</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr
              key={t.id}
              onClick={() => (window.location.href = `/talentos/${t.id}`)}
              className="cursor-pointer border-b border-slate-100 transition last:border-0 hover:bg-slate-50/60"
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-brand-black">{t.full_name}</span>
                  {t.do_not_contact ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-1.5 py-0.5 text-[10px] font-semibold text-rose-700">
                      <Ban className="h-2.5 w-2.5" />
                      No contactar
                    </span>
                  ) : null}
                </div>
                {t.current_position ? (
                  <p className="text-xs text-brand-grayMid">{t.current_position}</p>
                ) : null}
              </td>
              <td className="px-4 py-3 text-xs text-brand-grayMid">{t.current_company || "—"}</td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {(t.industries || []).slice(0, 2).map((ind) => (
                    <span key={ind} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-brand-grayMid">
                      {ind}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">
                {t.last_score !== null ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-semibold text-brand-blue">
                    <Sparkles className="h-2.5 w-2.5" />
                    {t.last_score}
                  </span>
                ) : (
                  <span className="text-xs text-brand-grayMid">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", STATUS_TONE[t.status])}>
                  {TALENT_STATUS_LABELS[t.status]}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-brand-grayMid">
                {AVAILABILITY_LABELS[t.availability_status]}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {t.tags.slice(0, 3).map((tag) => (
                    <span key={tag.id} className="rounded-full bg-brand-blueSoft/60 px-2 py-0.5 text-[10px] text-brand-blue">
                      {tag.name}
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-soft">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-blueSoft">
        <Vault className="h-5 w-5 text-brand-blue" />
      </div>
      <h3 className="mt-3 text-lg font-semibold text-brand-black">
        Aún no tienes talentos en la Bóveda
      </h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-brand-grayMid">
        Carga un CV o reutiliza candidatos evaluados para comenzar a construir tu base
        inteligente de talento.
      </p>
    </div>
  );
}

function CreateTalentModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (p: TalentProfile) => void;
}) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [position, setPosition] = useState("");
  const [company, setCompany] = useState("");
  const [saving, setSaving] = useState(false);
  const [dupes, setDupes] = useState<{ id: number; full_name: string; reasons: string[] }[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function checkDuplicates() {
    try {
      const body = await apiFetch<{
        has_potential_duplicates: boolean;
        matches: { talent_profile_id: number; full_name: string; match_reasons: string[] }[];
      }>("/api/talentos/detectar-duplicados", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName || null,
          primary_email: email || null,
          linkedin_url: linkedin || null,
          current_company: company || null,
        }),
      });
      setDupes(
        body.matches.map((m) => ({
          id: m.talent_profile_id,
          full_name: m.full_name,
          reasons: m.match_reasons,
        }))
      );
    } catch {
      // silencioso: la detección es un apoyo, no bloquea
    }
  }

  async function submit() {
    if (!fullName.trim()) {
      setError("El nombre es obligatorio.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const p = await apiFetch<TalentProfile>("/api/talentos", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          primary_email: email || null,
          linkedin_url: linkedin || null,
          current_position: position || null,
          current_company: company || null,
        }),
      });
      onCreated(p);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible crear el talento.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Nuevo talento
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">
              Crear Perfil Maestro de Talento
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid hover:bg-slate-100"
            aria-label="Cerrar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-3">
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            onBlur={checkDuplicates}
            placeholder="Nombre completo *"
            className={inputClass}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <input value={email} onChange={(e) => setEmail(e.target.value)} onBlur={checkDuplicates} placeholder="Email" className={inputClass} />
            <input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} onBlur={checkDuplicates} placeholder="LinkedIn URL" className={inputClass} />
            <input value={position} onChange={(e) => setPosition(e.target.value)} placeholder="Cargo actual" className={inputClass} />
            <input value={company} onChange={(e) => setCompany(e.target.value)} onBlur={checkDuplicates} placeholder="Empresa actual" className={inputClass} />
          </div>

          {dupes.length > 0 ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              <p className="font-semibold">Posible(s) duplicado(s) encontrado(s):</p>
              <ul className="mt-1 space-y-0.5">
                {dupes.slice(0, 3).map((d) => (
                  <li key={d.id}>
                    <a href={`/talentos/${d.id}`} className="underline" target="_blank" rel="noreferrer">
                      {d.full_name}
                    </a>{" "}
                    ({d.reasons.join(", ")})
                  </li>
                ))}
              </ul>
              <p className="mt-1">Revisa si corresponde actualizar uno existente antes de crear uno nuevo.</p>
            </div>
          ) : null}

          {error ? <p className="text-xs text-rose-700">{error}</p> : null}
        </div>

        <div className="mt-5 flex items-center justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={saving || !fullName.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Crear talento
          </button>
        </div>
      </div>
    </div>
  );
}
