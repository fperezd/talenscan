"use client";

import {
  ArrowRight,
  ClipboardList,
  DoorOpen,
  FileBarChart,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Candidate, CandidateDocument } from "@/types/candidate";
import type { CandidateEvaluation } from "@/types/evaluation";
import type { SearchMandate } from "@/types/search-mandate";
import type { ClientShortlist, DecisionRoomStatus } from "@/types/shortlist";

type Metrics = {
  activeMandates: number;
  cvsAnalyzed: number;
  preselected: number;
  averageScore: number | null;
  totalEvaluations: number;
  recentMandates: SearchMandate[];
  recentEvaluations: Array<CandidateEvaluation & { candidate?: Candidate }>;
  rooms: ClientShortlist[];
};

const INITIAL_METRICS: Metrics = {
  activeMandates: 0,
  cvsAnalyzed: 0,
  preselected: 0,
  averageScore: null,
  totalEvaluations: 0,
  recentMandates: [],
  recentEvaluations: [],
  rooms: [],
};

const ROOM_STATUS_LABEL: Record<DecisionRoomStatus, string> = {
  draft: "Borrador",
  ready_to_share: "Listo",
  invitation_sent: "Invitación enviada",
  viewed: "Visto",
  in_review: "En revisión",
  feedback_received: "Feedback recibido",
  closed: "Cerrado",
  expired: "Expirado",
};

const ROOM_STATUS_TONE: Record<DecisionRoomStatus, string> = {
  draft: "bg-slate-100 text-brand-grayMid",
  ready_to_share: "bg-brand-blueSoft text-brand-blue",
  invitation_sent: "bg-indigo-100 text-indigo-700",
  viewed: "bg-cyan-100 text-cyan-700",
  in_review: "bg-amber-100 text-amber-700",
  feedback_received: "bg-emerald-100 text-emerald-700",
  closed: "bg-slate-200 text-slate-700",
  expired: "bg-rose-100 text-rose-700",
};

function isActiveMandate(status: string | undefined): boolean {
  if (!status) return false;
  const lower = status.toLowerCase();
  return !lower.includes("borrador") && !lower.includes("cerrado");
}

function scoreCategoryTone(category: string | undefined): string {
  const lower = (category || "").toLowerCase();
  if (lower.includes("muy alto")) return "bg-emerald-100 text-emerald-700";
  if (lower.includes("buen")) return "bg-blue-100 text-blue-700";
  if (lower.includes("parcial")) return "bg-amber-100 text-amber-700";
  if (lower.includes("bajo")) return "bg-zinc-200 text-brand-grayMid";
  return "bg-rose-100 text-rose-700";
}

export function DashboardMetrics() {
  const [metrics, setMetrics] = useState<Metrics>(INITIAL_METRICS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [mandates, candidates, evaluations, rooms] = await Promise.all([
          apiFetch<SearchMandate[]>("/api/mandatos").catch(() => []),
          apiFetch<Candidate[]>("/api/candidatos").catch(() => []),
          apiFetch<CandidateEvaluation[]>("/api/evaluaciones").catch(() => []),
          apiFetch<ClientShortlist[]>("/api/shortlists").catch(() => []),
        ]);

        // Documentos no tienen endpoint "list-all" así que asumimos
        // 1 doc por candidato (es lo típico en el MVP).
        const cvsAnalyzed = candidates.length;
        const activeMandates = mandates.filter((m) => isActiveMandate(m.status)).length;
        const preselected = evaluations.filter((e) => e.total_score >= 70).length;
        const averageScore = evaluations.length
          ? Math.round(
              evaluations.reduce((acc, e) => acc + e.total_score, 0) / evaluations.length
            )
          : null;

        const candidateMap = new Map(candidates.map((c) => [c.id, c]));
        const recentEvaluations = evaluations
          .slice()
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 4)
          .map((evaluation) => ({
            ...evaluation,
            candidate: candidateMap.get(evaluation.candidate_id),
          }));

        const recentMandates = mandates
          .slice()
          .sort(
            (a, b) =>
              new Date(b.updated_at || b.created_at).getTime() -
              new Date(a.updated_at || a.created_at).getTime()
          )
          .slice(0, 4);

        setMetrics({
          activeMandates,
          cvsAnalyzed,
          preselected,
          averageScore,
          totalEvaluations: evaluations.length,
          recentMandates,
          recentEvaluations,
          rooms,
        });
      } catch (loadError) {
        console.error(loadError);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const cards = useMemo(
    () => [
      {
        label: "Mandatos activos",
        value: metrics.activeMandates,
        hint: "Excluye borradores y cerrados",
        icon: ClipboardList,
        href: "/mandatos",
      },
      {
        label: "CVs analizados",
        value: metrics.cvsAnalyzed,
        hint: "Candidatos cargados",
        icon: Users,
        href: "/candidatos",
      },
      {
        label: "Candidatos preseleccionados",
        value: metrics.preselected,
        hint: "Score 360 ≥ 70",
        icon: Sparkles,
        href: "/evaluaciones",
      },
      {
        label: "Score 360 promedio",
        value: metrics.averageScore !== null ? metrics.averageScore : "—",
        hint:
          metrics.averageScore === null
            ? "Sin evaluaciones aún"
            : metrics.averageScore >= 70
              ? "Buen calce"
              : metrics.averageScore >= 55
                ? "Calce parcial"
                : "Calce bajo",
        icon: TrendingUp,
        href: "/evaluaciones",
      },
      {
        label: "Evaluaciones generadas",
        value: metrics.totalEvaluations,
        hint: "Total histórico",
        icon: FileBarChart,
        href: "/evaluaciones",
      },
    ],
    [metrics]
  );

  const roomsByStatus = useMemo(() => {
    const map = new Map<DecisionRoomStatus, number>();
    for (const r of metrics.rooms) map.set(r.status, (map.get(r.status) || 0) + 1);
    return map;
  }, [metrics.rooms]);

  const activeRooms = useMemo(
    () =>
      metrics.rooms.filter(
        (r) => r.status !== "closed" && r.status !== "expired" && !r.revoked
      ),
    [metrics.rooms]
  );

  return (
    <div className="space-y-8">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map(({ label, value, hint, icon: Icon, href }) => (
          <a
            key={label}
            href={href}
            className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:border-brand-blue/40 hover:shadow-elevated"
          >
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-blueSoft text-brand-blue transition group-hover:bg-brand-blue group-hover:text-white">
              <Icon className="h-4 w-4" />
            </span>
            <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
              {label}
            </p>
            <p className="mt-2 text-[28px] font-semibold leading-none tracking-tight text-brand-black">
              {loading ? "…" : value}
            </p>
            <p className="mt-2 text-xs text-brand-grayMid">{hint}</p>
          </a>
        ))}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-blueSoft text-brand-blue">
              <DoorOpen className="h-4 w-4" />
            </span>
            <div>
              <h3 className="text-base font-semibold text-brand-black">Decision Rooms activos</h3>
              <p className="text-xs text-brand-grayMid">
                Salas privadas que los clientes pueden revisar en este momento.
              </p>
            </div>
          </div>
          <span className="rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-semibold text-brand-blue">
            {activeRooms.length} activos
          </span>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-4 lg:grid-cols-7">
          {(
            [
              "draft",
              "ready_to_share",
              "invitation_sent",
              "viewed",
              "in_review",
              "feedback_received",
              "closed",
            ] as DecisionRoomStatus[]
          ).map((status) => {
            const count = roomsByStatus.get(status) || 0;
            return (
              <div
                key={status}
                className={cn(
                  "rounded-xl border border-slate-200 bg-white px-3 py-2 text-center",
                  count > 0 && "border-brand-blue/20"
                )}
              >
                <p className="text-xl font-semibold text-brand-black">{count}</p>
                <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-brand-grayMid">
                  {ROOM_STATUS_LABEL[status]}
                </p>
              </div>
            );
          })}
        </div>

        {activeRooms.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {activeRooms.slice(0, 5).map((room) => (
              <li key={room.id}>
                <a
                  href={`/mandatos/${room.mandate_id}/decision-room`}
                  className="flex items-start justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/40 p-3 transition hover:border-brand-blue/40"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-brand-black">{room.title}</p>
                    <p className="text-xs text-brand-grayMid">
                      {room.items.length} candidatos · {room.viewed_count} vistas
                      {room.client_contact_name ? ` · ${room.client_contact_name}` : ""}
                    </p>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold",
                      ROOM_STATUS_TONE[room.status]
                    )}
                  >
                    {ROOM_STATUS_LABEL[room.status]}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 rounded-lg border border-dashed border-slate-200 px-3 py-6 text-center text-xs text-brand-grayMid">
            Aún no hay Decision Rooms activos. Crea uno desde el detalle de un mandato.
          </p>
        )}
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-brand-black">Mandatos recientes</h3>
              <p className="text-xs text-brand-grayMid">Últimos mandatos actualizados.</p>
            </div>
            <a
              href="/mandatos"
              className="inline-flex items-center gap-1 text-xs font-medium text-brand-blue hover:underline"
            >
              Ver todos <ArrowRight className="h-3 w-3" />
            </a>
          </div>
          {loading ? (
            <p className="mt-4 text-sm text-brand-grayMid">Cargando...</p>
          ) : metrics.recentMandates.length === 0 ? (
            <p className="mt-4 text-sm text-brand-grayMid">
              Aún no hay mandatos. Crea el primero para empezar.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {metrics.recentMandates.map((mandate) => (
                <li key={mandate.id}>
                  <a
                    href={`/mandatos/${mandate.id}`}
                    className="flex items-start justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/40 p-3 transition hover:border-brand-blue/40"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-brand-black">
                        {mandate.search_title}
                      </p>
                      <p className="text-xs text-brand-grayMid">
                        {mandate.client_name} · {mandate.target_role}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-brand-grayMid ring-1 ring-slate-200">
                      {mandate.status}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-brand-black">Evaluaciones recientes</h3>
              <p className="text-xs text-brand-grayMid">Últimos candidatos evaluados.</p>
            </div>
            <a
              href="/evaluaciones"
              className="inline-flex items-center gap-1 text-xs font-medium text-brand-blue hover:underline"
            >
              Ver todas <ArrowRight className="h-3 w-3" />
            </a>
          </div>
          {loading ? (
            <p className="mt-4 text-sm text-brand-grayMid">Cargando...</p>
          ) : metrics.recentEvaluations.length === 0 ? (
            <p className="mt-4 text-sm text-brand-grayMid">
              Sin evaluaciones aún. Sube un CV desde un mandato para generar la primera.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {metrics.recentEvaluations.map((evaluation) => (
                <li key={evaluation.id}>
                  <a
                    href={`/evaluaciones/${evaluation.id}`}
                    className="flex items-start justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/40 p-3 transition hover:border-brand-blue/40"
                  >
                    <div className="min-w-0 flex items-start gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-brand-black ring-1 ring-slate-200">
                        {evaluation.total_score}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-brand-black">
                          {evaluation.candidate?.full_name ||
                            `Candidato #${evaluation.candidate_id}`}
                        </p>
                        <p className="text-xs text-brand-grayMid">{evaluation.recommendation}</p>
                      </div>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium",
                        scoreCategoryTone(evaluation.score_category)
                      )}
                    >
                      {evaluation.score_category}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>
    </div>
  );
}
