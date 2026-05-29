"use client";

import {
  DndContext,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  AlertCircle,
  Check,
  ChevronDown,
  Clock,
  Copy,
  Edit3,
  Eye,
  GripVertical,
  KeyRound,
  Loader2,
  Lock,
  Mail,
  Pin,
  PinOff,
  Plus,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch, API_BASE_URL } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CandidateEvaluation } from "@/types/evaluation";
import type { SearchMandate } from "@/types/search-mandate";
import {
  CLIENT_DECISION_LABELS,
  RECOMMENDATION_LABELS,
  type ClientShortlist,
  type ConsultantRecommendation,
  type DecisionRoomStatus,
  type EvidenceLevel,
  type ShortlistItem,
} from "@/types/shortlist";

const STATUS_LABEL: Record<DecisionRoomStatus, string> = {
  draft: "Borrador",
  ready_to_share: "Listo para compartir",
  invitation_sent: "Invitación enviada",
  viewed: "Visto por cliente",
  in_review: "En revisión",
  feedback_received: "Feedback recibido",
  closed: "Cerrado",
  expired: "Expirado",
};

const STATUS_TONE: Record<DecisionRoomStatus, string> = {
  draft: "bg-slate-100 text-brand-grayMid",
  ready_to_share: "bg-brand-blueSoft text-brand-blue",
  invitation_sent: "bg-indigo-100 text-indigo-700",
  viewed: "bg-cyan-100 text-cyan-700",
  in_review: "bg-amber-100 text-amber-700",
  feedback_received: "bg-emerald-100 text-emerald-700",
  closed: "bg-slate-200 text-slate-700",
  expired: "bg-rose-100 text-rose-700",
};

const TTL_OPTIONS = [
  { hours: 24, label: "24 horas" },
  { hours: 72, label: "3 días" },
  { hours: 168, label: "7 días (recomendado)" },
  { hours: 336, label: "14 días" },
  { hours: 720, label: "30 días" },
] as const;

const CLIENT_BASE_URL =
  typeof window !== "undefined" ? window.location.origin : "https://talenscan-web.tooxs-fperez.workers.dev";

type Props = { mandateId: string };

export function DecisionRoomBuilder({ mandateId }: Props) {
  const [mandate, setMandate] = useState<SearchMandate | null>(null);
  const [rooms, setRooms] = useState<ClientShortlist[]>([]);
  const [evaluations, setEvaluations] = useState<CandidateEvaluation[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modales
  const [createOpen, setCreateOpen] = useState(false);
  const [invitationOpen, setInvitationOpen] = useState(false);
  const [issuedCode, setIssuedCode] = useState<{
    code: string;
    expiresAt: string;
    publicToken: string;
  } | null>(null);

  async function reload() {
    setError(null);
    try {
      const [mandateData, roomsData, evalsData] = await Promise.all([
        apiFetch<SearchMandate>(`/api/mandatos/${mandateId}`),
        apiFetch<ClientShortlist[]>(`/api/mandatos/${mandateId}/shortlists`),
        apiFetch<CandidateEvaluation[]>(`/api/evaluaciones?mandate_id=${mandateId}`).catch(() =>
          apiFetch<CandidateEvaluation[]>(`/api/evaluaciones`)
        ),
      ]);
      setMandate(mandateData);
      setRooms(roomsData);
      setEvaluations(
        Array.isArray(evalsData)
          ? evalsData.filter((e) =>
              roomsData.length > 0 || e.position_spec_id !== null
            )
          : []
      );
      if (selectedRoomId === null && roomsData.length > 0) {
        setSelectedRoomId(roomsData[0].id);
      }
    } catch (caught) {
      console.error(caught);
      setError("No fue posible cargar los Decision Rooms del mandato.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mandateId]);

  const selectedRoom = useMemo(
    () => rooms.find((r) => r.id === selectedRoomId) || null,
    [rooms, selectedRoomId]
  );

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
        {error}
      </div>
    );
  }

  // Empty state
  if (rooms.length === 0) {
    return (
      <>
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-soft">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-blueSoft">
            <Sparkles className="h-5 w-5 text-brand-blue" />
          </div>
          <h3 className="mt-3 text-lg font-semibold text-brand-black">
            Aún no existe un Decision Room para esta búsqueda
          </h3>
          <p className="mx-auto mt-1 max-w-md text-sm text-brand-grayMid">
            Crea una sala privada para compartir la shortlist, recibir feedback estructurado y ordenar las decisiones del cliente.
          </p>
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            disabled={evaluations.length === 0}
            className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
          >
            <Plus className="h-4 w-4" />
            Crear Decision Room
          </button>
          {evaluations.length === 0 ? (
            <p className="mt-3 text-xs text-brand-grayMid">
              No hay candidatos evaluados disponibles. Carga candidatos o ejecuta una Evaluación 360 antes de construir la shortlist.
            </p>
          ) : null}
        </div>

        {createOpen ? (
          <CreateRoomModal
            mandateId={mandateId}
            evaluations={evaluations}
            existingItems={[]}
            onClose={() => setCreateOpen(false)}
            onCreated={(room) => {
              setRooms((current) => [room, ...current]);
              setSelectedRoomId(room.id);
              setCreateOpen(false);
            }}
          />
        ) : null}
      </>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
            Decision Room
          </label>
          <select
            value={selectedRoomId || ""}
            onChange={(event) => setSelectedRoomId(Number(event.target.value))}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
          >
            {rooms.map((room) => (
              <option key={room.id} value={room.id}>
                {room.title} · {STATUS_LABEL[room.status] || room.status}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
        >
          <Plus className="h-4 w-4" />
          Nuevo Decision Room
        </button>
      </div>

      {selectedRoom ? (
        <RoomWorkspace
          room={selectedRoom}
          mandate={mandate}
          evaluations={evaluations}
          onRefresh={reload}
          onOpenInvitation={() => setInvitationOpen(true)}
          onCodeIssued={setIssuedCode}
        />
      ) : null}

      {createOpen ? (
        <CreateRoomModal
          mandateId={mandateId}
          evaluations={evaluations}
          existingItems={
            selectedRoom?.items.map((item) => item.evaluation_id).filter(Boolean) as number[]
          }
          onClose={() => setCreateOpen(false)}
          onCreated={(room) => {
            setRooms((current) => [room, ...current]);
            setSelectedRoomId(room.id);
            setCreateOpen(false);
          }}
        />
      ) : null}

      {invitationOpen && selectedRoom ? (
        <InvitationModal
          room={selectedRoom}
          mandate={mandate}
          publicUrl={`${CLIENT_BASE_URL}/shortlist-cliente/${selectedRoom.public_token}`}
          accessCode={issuedCode?.code || null}
          codeExpiresAt={issuedCode?.expiresAt || selectedRoom.access_code_expires_at}
          onClose={() => setInvitationOpen(false)}
          onSent={async () => {
            await apiFetch<unknown>(`/api/shortlists/${selectedRoom.id}/invitation-sent`, {
              method: "POST",
            });
            await reload();
            setInvitationOpen(false);
          }}
        />
      ) : null}

      {issuedCode ? (
        <IssuedCodeBanner
          code={issuedCode.code}
          expiresAt={issuedCode.expiresAt}
          publicUrl={`${CLIENT_BASE_URL}/shortlist-cliente/${issuedCode.publicToken}`}
          onClose={() => setIssuedCode(null)}
        />
      ) : null}
    </div>
  );
}

// --- Workspace (header + builder + config) --------------------------------

function RoomWorkspace({
  room,
  mandate,
  evaluations,
  onRefresh,
  onOpenInvitation,
  onCodeIssued,
}: {
  room: ClientShortlist;
  mandate: SearchMandate | null;
  evaluations: CandidateEvaluation[];
  onRefresh: () => Promise<void>;
  onOpenInvitation: () => void;
  onCodeIssued: (info: { code: string; expiresAt: string; publicToken: string }) => void;
}) {
  const [activeTab, setActiveTab] = useState<"builder" | "config" | "events">("builder");

  const publicUrl = `${CLIENT_BASE_URL}/shortlist-cliente/${room.public_token}`;

  return (
    <div className="space-y-4">
      <RoomHeader
        room={room}
        mandate={mandate}
        publicUrl={publicUrl}
        onOpenInvitation={onOpenInvitation}
        onCodeIssued={onCodeIssued}
        onRefresh={onRefresh}
      />

      <div className="flex gap-1 border-b border-slate-200">
        {(
          [
            ["builder", "Room Builder"],
            ["config", "Configuración"],
            ["events", "Actividad"],
          ] as const
        ).map(([id, label]) => (
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

      {activeTab === "builder" ? (
        <RoomBuilderTab room={room} evaluations={evaluations} onRefresh={onRefresh} />
      ) : null}
      {activeTab === "config" ? <RoomConfigTab room={room} onRefresh={onRefresh} /> : null}
      {activeTab === "events" ? <RoomEventsTab room={room} /> : null}
    </div>
  );
}

// --- Header ---------------------------------------------------------------

function RoomHeader({
  room,
  mandate,
  publicUrl,
  onOpenInvitation,
  onCodeIssued,
  onRefresh,
}: {
  room: ClientShortlist;
  mandate: SearchMandate | null;
  publicUrl: string;
  onOpenInvitation: () => void;
  onCodeIssued: (info: { code: string; expiresAt: string; publicToken: string }) => void;
  onRefresh: () => Promise<void>;
}) {
  const [ttlHours, setTtlHours] = useState<number>(168);
  const [busy, setBusy] = useState<string | null>(null);

  async function issueCode() {
    setBusy("code");
    try {
      const body = await apiFetch<{ code: string; code_expires_at: string }>(
        `/api/shortlists/${room.id}/access-code`,
        { method: "POST", body: JSON.stringify({ ttl_hours: ttlHours }) }
      );
      onCodeIssued({
        code: body.code,
        expiresAt: body.code_expires_at,
        publicToken: room.public_token,
      });
      await onRefresh();
    } finally {
      setBusy(null);
    }
  }

  async function regenerate() {
    if (!window.confirm("¿Regenerar el link y el código? El acceso anterior dejará de funcionar.")) {
      return;
    }
    setBusy("regen");
    try {
      const body = await apiFetch<{ public_token: string; code: string; code_expires_at: string }>(
        `/api/shortlists/${room.id}/regenerate-access`,
        { method: "POST", body: JSON.stringify({ ttl_hours: ttlHours }) }
      );
      onCodeIssued({
        code: body.code,
        expiresAt: body.code_expires_at,
        publicToken: body.public_token,
      });
      await onRefresh();
    } finally {
      setBusy(null);
    }
  }

  async function closeRoom() {
    if (!window.confirm("¿Cerrar el Decision Room? El cliente ya no podrá entrar.")) return;
    setBusy("close");
    try {
      await apiFetch<unknown>(`/api/shortlists/${room.id}/close`, { method: "POST" });
      await onRefresh();
    } finally {
      setBusy(null);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(publicUrl);
      window.alert("Link copiado al portapapeles.");
    } catch {
      window.prompt("Copia el link:", publicUrl);
    }
  }

  const statusLabel = STATUS_LABEL[room.status] || room.status;
  const statusTone = STATUS_TONE[room.status] || "bg-slate-100 text-brand-grayMid";

  return (
    <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-blueSoft/30 via-white to-white p-6 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold", statusTone)}>
              {statusLabel}
            </span>
            {room.access_code_required ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-brand-grayMid">
                <Lock className="h-3 w-3" />
                Acceso protegido
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700">
                <AlertCircle className="h-3 w-3" />
                Acceso público sin código
              </span>
            )}
            {room.expires_at ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-0.5 text-[11px] font-semibold text-brand-grayMid">
                <Clock className="h-3 w-3" />
                Acceso hasta {new Date(room.expires_at).toLocaleDateString("es-ES")}
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-brand-black">
            {room.title}
          </h2>
          <p className="mt-1 text-sm text-brand-grayMid">
            {mandate?.target_role || "Cargo"} · {mandate?.client_name || room.client_contact_company || "Cliente"}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-brand-grayMid">
            <span>{room.items.length} candidatos en shortlist</span>
            <span>·</span>
            <span>{room.viewed_count} vistas</span>
            {room.last_invitation_sent_at ? (
              <>
                <span>·</span>
                <span>
                  Invitación enviada{" "}
                  {new Date(room.last_invitation_sent_at).toLocaleDateString("es-ES")}
                </span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={ttlHours}
            onChange={(event) => setTtlHours(Number(event.target.value))}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          >
            {TTL_OPTIONS.map((opt) => (
              <option key={opt.hours} value={opt.hours}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={issueCode}
            disabled={busy === "code"}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {busy === "code" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <KeyRound className="h-3.5 w-3.5" />}
            Generar código
          </button>
          <button
            type="button"
            onClick={onOpenInvitation}
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-blue/30 bg-brand-blueSoft px-3 py-2 text-sm font-semibold text-brand-blue transition hover:bg-brand-blueSoft/80"
          >
            <Mail className="h-3.5 w-3.5" />
            Invitación
          </button>
          <button
            type="button"
            onClick={copyLink}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
          >
            <Copy className="h-3.5 w-3.5" />
            Copiar link
          </button>
          <a
            href={publicUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
          >
            <Eye className="h-3.5 w-3.5" />
            Previsualizar
          </a>
          <button
            type="button"
            onClick={regenerate}
            disabled={busy === "regen"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-60"
          >
            {busy === "regen" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            Regenerar acceso
          </button>
          {room.status !== "closed" ? (
            <button
              type="button"
              onClick={closeRoom}
              disabled={busy === "close"}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
            >
              <X className="h-3.5 w-3.5" />
              Cerrar room
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function IssuedCodeBanner({
  code,
  expiresAt,
  publicUrl,
  onClose,
}: {
  code: string;
  expiresAt: string;
  publicUrl: string;
  onClose: () => void;
}) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
            <ShieldCheck className="h-3.5 w-3.5" />
            Nuevo código generado
          </p>
          <p className="mt-1 text-2xl font-bold tracking-[0.4em] text-emerald-700">{code}</p>
          <p className="mt-1 text-xs text-emerald-700">
            Válido hasta {new Date(expiresAt).toLocaleString("es-ES")}. Compártelo con el cliente junto al link:{" "}
            <a href={publicUrl} className="underline" target="_blank" rel="noreferrer noopener">
              {publicUrl}
            </a>
          </p>
          <p className="mt-1 text-[11px] text-emerald-700">
            Por seguridad, este código no se vuelve a mostrar. Cópialo ahora.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md text-emerald-700 hover:bg-emerald-100"
          aria-label="Cerrar"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

// --- Builder Tab (room items + add from evaluations) -----------------------

function RoomBuilderTab({
  room,
  evaluations,
  onRefresh,
}: {
  room: ClientShortlist;
  evaluations: CandidateEvaluation[];
  onRefresh: () => Promise<void>;
}) {
  const inRoomEvalIds = new Set(room.items.map((i) => i.evaluation_id).filter(Boolean) as number[]);
  const availableEvals = evaluations.filter((e) => !inRoomEvalIds.has(e.id));
  const [busyId, setBusyId] = useState<number | null>(null);

  async function addCandidate(evaluationId: number) {
    setBusyId(evaluationId);
    try {
      await apiFetch<ClientShortlist>(`/api/shortlists/${room.id}/items`, {
        method: "POST",
        body: JSON.stringify({ evaluation_id: evaluationId }),
      });
      await onRefresh();
    } catch (caught) {
      console.error(caught);
      window.alert("No fue posible agregar el candidato. Reintenta más tarde.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_2fr]">
      <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
            Candidatos disponibles
          </p>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-brand-grayMid">
            {availableEvals.length}
          </span>
        </div>
        {availableEvals.length === 0 ? (
          <p className="mt-4 rounded-lg border border-dashed border-slate-200 px-3 py-6 text-center text-xs text-brand-grayMid">
            Todos los candidatos evaluados ya están en el room.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {availableEvals.map((evalItem) => (
              <AvailableCandidate
                key={evalItem.id}
                evaluation={evalItem}
                busy={busyId === evalItem.id}
                onAdd={() => addCandidate(evalItem.id)}
              />
            ))}
          </ul>
        )}
      </aside>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
            Shortlist del Decision Room
          </p>
          <span className="rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-semibold text-brand-blue">
            {room.items.length} candidatos
          </span>
        </div>
        {room.items.length === 0 ? (
          <p className="mt-4 rounded-lg border border-dashed border-slate-200 px-3 py-10 text-center text-xs text-brand-grayMid">
            Esta shortlist aún no tiene candidatos.
          </p>
        ) : (
          <RoomItemList room={room} onRefresh={onRefresh} />
        )}
      </section>
    </div>
  );
}

function AvailableCandidate({
  evaluation,
  onAdd,
  busy,
}: {
  evaluation: CandidateEvaluation;
  onAdd: () => Promise<void>;
  busy: boolean;
}) {
  return (
    <li className="flex items-start justify-between gap-2 rounded-lg border border-slate-200 bg-white p-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-brand-black">
          {(evaluation as CandidateEvaluation & { candidate_name?: string }).candidate_name ||
            `Candidato #${(evaluation as CandidateEvaluation & { candidate_id?: number }).candidate_id ?? evaluation.id}`}
        </p>
        <p className="text-xs text-brand-grayMid">
          Calce {evaluation.total_score}/100 · {evaluation.score_category}
        </p>
      </div>
      <button
        type="button"
        onClick={onAdd}
        disabled={busy}
        className="inline-flex items-center gap-1 rounded-md bg-brand-blue px-2 py-1 text-[11px] font-semibold text-white transition hover:bg-brand-blueDark disabled:opacity-60"
      >
        {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
        Agregar
      </button>
    </li>
  );
}

function RoomItemList({
  room,
  onRefresh,
}: {
  room: ClientShortlist;
  onRefresh: () => Promise<void>;
}) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));
  const [items, setItems] = useState(room.items);
  const [savingOrder, setSavingOrder] = useState(false);

  useEffect(() => {
    setItems(room.items);
  }, [room.items]);

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = items.findIndex((i) => String(i.id) === String(active.id));
    const newIndex = items.findIndex((i) => String(i.id) === String(over.id));
    if (oldIndex === -1 || newIndex === -1) return;
    const next = arrayMove(items, oldIndex, newIndex);
    setItems(next);
    setSavingOrder(true);
    try {
      await apiFetch<unknown>(`/api/shortlists/${room.id}/items/reorder`, {
        method: "PATCH",
        body: JSON.stringify({ ordered_item_ids: next.map((i) => i.id) }),
      });
      await onRefresh();
    } finally {
      setSavingOrder(false);
    }
  }

  return (
    <div className="mt-3">
      {savingOrder ? (
        <p className="mb-2 text-[11px] text-brand-grayMid">Guardando orden…</p>
      ) : null}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map((i) => String(i.id))} strategy={verticalListSortingStrategy}>
          <ul className="space-y-3">
            {items.map((item) => (
              <SortableRoomItem key={item.id} item={item} room={room} onRefresh={onRefresh} />
            ))}
          </ul>
        </SortableContext>
      </DndContext>
    </div>
  );
}

function SortableRoomItem({
  item,
  room,
  onRefresh,
}: {
  item: ShortlistItem;
  room: ClientShortlist;
  onRefresh: () => Promise<void>;
}) {
  const sortable = useSortable({ id: String(item.id) });
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
    opacity: sortable.isDragging ? 0.4 : 1,
  };

  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  async function togglePin() {
    setBusy("pin");
    try {
      await apiFetch<unknown>(
        `/api/shortlists/${room.id}/items/${item.id}/pin`,
        { method: "POST", body: JSON.stringify({ pinned: !item.is_pinned }) }
      );
      await onRefresh();
    } finally {
      setBusy(null);
    }
  }

  async function removeFromRoom() {
    if (!window.confirm(`¿Remover a ${item.candidate_name || `el candidato #${item.candidate_id}`} del Decision Room?`)) return;
    setBusy("remove");
    try {
      await apiFetch<unknown>(`/api/shortlists/${room.id}/items/${item.id}`, {
        method: "DELETE",
      });
      await onRefresh();
    } finally {
      setBusy(null);
    }
  }

  return (
    <li
      ref={sortable.setNodeRef}
      style={style}
      className={cn(
        "rounded-xl border border-slate-200 bg-white shadow-soft",
        item.is_pinned && "ring-1 ring-amber-300"
      )}
    >
      <div className="flex items-start gap-2 p-3">
        <button
          type="button"
          aria-label="Mover"
          className="mt-1 cursor-grab text-slate-300 transition hover:text-brand-grayMid active:cursor-grabbing"
          {...sortable.attributes}
          {...sortable.listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-brand-grayMid">
              #{item.order_index + 1}
            </span>
            {item.is_pinned ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                <Pin className="h-3 w-3" />
                Destacado
              </span>
            ) : null}
            {item.recommendation ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-semibold text-brand-blue">
                <Sparkles className="h-3 w-3" />
                {RECOMMENDATION_LABELS[item.recommendation]}
              </span>
            ) : null}
            {item.client_status ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                <Check className="h-3 w-3" />
                {CLIENT_DECISION_LABELS[item.client_status]}
              </span>
            ) : null}
          </div>
          <p className="mt-1.5 text-sm font-semibold text-brand-black">
            {item.candidate_name || `Candidato #${item.candidate_id}`}
          </p>
          {item.candidate_current_position || item.candidate_current_company ? (
            <p className="mt-0.5 text-xs text-brand-grayMid">
              {[item.candidate_current_position, item.candidate_current_company]
                .filter(Boolean)
                .join(" · ")}
            </p>
          ) : null}
          {item.evaluation_score !== null ? (
            <p className="mt-0.5 inline-flex items-center gap-1 text-[11px] text-brand-grayMid">
              <Sparkles className="h-3 w-3 text-brand-blue" />
              Calce {item.evaluation_score}/100
              {item.evaluation_score_category ? ` · ${item.evaluation_score_category}` : ""}
            </p>
          ) : null}
          {item.consultant_summary ? (
            <p className="mt-1 line-clamp-2 text-xs text-brand-grayMid">{item.consultant_summary}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={togglePin}
            disabled={busy === "pin"}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-slate-100"
            title={item.is_pinned ? "Quitar destacado" : "Destacar"}
          >
            {item.is_pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={() => setEditing((v) => !v)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-slate-100"
            title="Editar presentación"
          >
            <Edit3 className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={removeFromRoom}
            disabled={busy === "remove"}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-60"
            title="Remover del room"
          >
            {busy === "remove" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {editing ? (
        <ItemEditor
          room={room}
          item={item}
          onClose={() => setEditing(false)}
          onSaved={async () => {
            setEditing(false);
            await onRefresh();
          }}
        />
      ) : null}
    </li>
  );
}

function ItemEditor({
  room,
  item,
  onClose,
  onSaved,
}: {
  room: ClientShortlist;
  item: ShortlistItem;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [summary, setSummary] = useState(item.consultant_summary || "");
  const [whyFits, setWhyFits] = useState((item.why_fits || []).join("\n"));
  const [risks, setRisks] = useState((item.risks_or_validations || []).join("\n"));
  const [recommendation, setRecommendation] = useState<ConsultantRecommendation | "">(
    item.recommendation || ""
  );
  const [evidenceLevel, setEvidenceLevel] = useState<EvidenceLevel | "">(
    item.evidence_level || ""
  );
  const [availability, setAvailability] = useState(item.availability || "");
  const [salaryExpectation, setSalaryExpectation] = useState(item.salary_expectation || "");
  const [salaryAuth, setSalaryAuth] = useState(item.salary_share_authorized);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await apiFetch<unknown>(`/api/shortlists/${room.id}/items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          consultant_summary: summary || null,
          why_fits: whyFits.split("\n").map((s) => s.trim()).filter(Boolean),
          risks_or_validations: risks.split("\n").map((s) => s.trim()).filter(Boolean),
          recommendation: recommendation || null,
          evidence_level: evidenceLevel || null,
          availability: availability || null,
          salary_expectation: salaryExpectation || null,
          salary_share_authorized: salaryAuth,
        }),
      });
      await onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-3 border-t border-slate-100 bg-slate-50 p-4">
      <Field label="Resumen visible para el cliente">
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={2}
          className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
        />
      </Field>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Por qué calza (una por línea)">
          <textarea
            value={whyFits}
            onChange={(e) => setWhyFits(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          />
        </Field>
        <Field label="Puntos a validar (una por línea)">
          <textarea
            value={risks}
            onChange={(e) => setRisks(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          />
        </Field>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Recomendación del consultor">
          <select
            value={recommendation}
            onChange={(e) => setRecommendation(e.target.value as ConsultantRecommendation | "")}
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          >
            <option value="">Sin recomendación</option>
            {Object.entries(RECOMMENDATION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Nivel de evidencia">
          <select
            value={evidenceLevel}
            onChange={(e) => setEvidenceLevel(e.target.value as EvidenceLevel | "")}
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          >
            <option value="">—</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
            <option value="low">Baja</option>
          </select>
        </Field>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Disponibilidad">
          <input
            value={availability}
            onChange={(e) => setAvailability(e.target.value)}
            placeholder="Ej. Disponible en 30 días"
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          />
        </Field>
        <Field label="Renta esperada">
          <input
            value={salaryExpectation}
            onChange={(e) => setSalaryExpectation(e.target.value)}
            placeholder="Ej. $80M CLP brutos / año"
            className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black focus:border-brand-blue focus:outline-none"
          />
        </Field>
      </div>
      <label className="flex items-center gap-2 text-xs text-brand-grayMid">
        <input
          type="checkbox"
          checked={salaryAuth}
          onChange={(e) => setSalaryAuth(e.target.checked)}
          className="h-3.5 w-3.5 rounded border-slate-300 text-brand-blue focus:ring-brand-blue/30"
        />
        Autorizar mostrar renta al cliente (requiere también activar el toggle en Configuración)
      </label>
      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className="inline-flex items-center rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="inline-flex items-center gap-1 rounded-md bg-brand-blue px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-blueDark disabled:opacity-60"
        >
          {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
          Guardar
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
        {label}
      </span>
      <span className="mt-1 block">{children}</span>
    </label>
  );
}

// --- Config Tab -----------------------------------------------------------

function RoomConfigTab({
  room,
  onRefresh,
}: {
  room: ClientShortlist;
  onRefresh: () => Promise<void>;
}) {
  const [draft, setDraft] = useState(room);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    try {
      const patch = {
        title: draft.title,
        message_to_client: draft.message_to_client,
        intro_message: draft.intro_message,
        show_scores: draft.show_scores,
        show_availability: draft.show_availability,
        show_salary: draft.show_salary,
        show_risks: draft.show_risks,
        show_comparison: draft.show_comparison,
        allow_comments: draft.allow_comments,
        allow_rating: draft.allow_rating,
        allow_report_download: draft.allow_report_download,
        access_code_required: draft.access_code_required,
        client_contact_name: draft.client_contact_name,
        client_contact_email: draft.client_contact_email,
        client_contact_company: draft.client_contact_company,
      };
      await apiFetch<unknown>(`/api/shortlists/${room.id}/config`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      setSavedAt(new Date().toLocaleTimeString("es-ES"));
      await onRefresh();
    } finally {
      setSaving(false);
    }
  }

  function toggle<K extends keyof ClientShortlist>(key: K, value: ClientShortlist[K]) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <div className="space-y-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-sm font-semibold text-brand-black">Información del Decision Room</h3>
          <div className="mt-3 space-y-3">
            <Field label="Título visible">
              <input
                value={draft.title}
                onChange={(e) => toggle("title", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Mensaje del consultor (visible en el header del room)">
              <textarea
                value={draft.intro_message || ""}
                onChange={(e) => toggle("intro_message", e.target.value)}
                rows={3}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Mensaje adicional (visible en la pestaña Mensaje)">
              <textarea
                value={draft.message_to_client}
                onChange={(e) => toggle("message_to_client", e.target.value)}
                rows={2}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-sm font-semibold text-brand-black">Contacto cliente</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <Field label="Nombre">
              <input
                value={draft.client_contact_name || ""}
                onChange={(e) => toggle("client_contact_name", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Email">
              <input
                value={draft.client_contact_email || ""}
                onChange={(e) => toggle("client_contact_email", e.target.value)}
                placeholder="cliente@empresa.com"
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Empresa">
              <input
                value={draft.client_contact_company || ""}
                onChange={(e) => toggle("client_contact_company", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
          </div>
        </section>
      </div>

      <aside className="space-y-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-sm font-semibold text-brand-black">Visibilidad para el cliente</h3>
          <div className="mt-3 space-y-2">
            <Toggle
              label="Acceso protegido por código"
              checked={draft.access_code_required}
              onChange={(v) => toggle("access_code_required", v)}
            />
            <Toggle label="Mostrar score de calce" checked={draft.show_scores} onChange={(v) => toggle("show_scores", v)} />
            <Toggle label="Mostrar disponibilidad" checked={draft.show_availability} onChange={(v) => toggle("show_availability", v)} />
            <Toggle label="Mostrar renta esperada" checked={draft.show_salary} onChange={(v) => toggle("show_salary", v)} />
            <Toggle label="Mostrar puntos a validar / riesgos" checked={draft.show_risks} onChange={(v) => toggle("show_risks", v)} />
            <Toggle label="Mostrar comparación ejecutiva" checked={draft.show_comparison} onChange={(v) => toggle("show_comparison", v)} />
            <Toggle label="Permitir comentarios" checked={draft.allow_comments} onChange={(v) => toggle("allow_comments", v)} />
            <Toggle label="Permitir valoración 1–5" checked={draft.allow_rating} onChange={(v) => toggle("allow_rating", v)} />
            <Toggle label="Permitir descarga de informe" checked={draft.allow_report_download} onChange={(v) => toggle("allow_report_download", v)} />
          </div>
        </section>

        <div className="flex items-center justify-end gap-3">
          {savedAt ? <span className="text-[11px] text-emerald-700">Guardado a las {savedAt}</span> : null}
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Guardar configuración
          </button>
        </div>
      </aside>
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-xs text-brand-black transition hover:bg-slate-50">
      <span>{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition",
          checked ? "bg-brand-blue" : "bg-slate-300"
        )}
        role="switch"
        aria-checked={checked}
      >
        <span
          className={cn(
            "inline-block h-4 w-4 transform rounded-full bg-white transition",
            checked ? "translate-x-4" : "translate-x-0.5"
          )}
        />
      </button>
    </label>
  );
}

// --- Events Tab -----------------------------------------------------------

type EventItem = {
  id: number;
  event_type: string;
  event_label: string;
  actor_type: "consultant" | "client" | "system";
  actor_name: string | null;
  actor_email: string | null;
  event_metadata: Record<string, unknown>;
  created_at: string;
};

function RoomEventsTab({ room }: { room: ClientShortlist }) {
  const [events, setEvents] = useState<EventItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await apiFetch<EventItem[]>(`/api/shortlists/${room.id}/events`);
        setEvents(data);
      } catch (caught) {
        console.error(caught);
        setError("No fue posible cargar la actividad del room.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [room.id]);

  if (loading) {
    return <Loader2 className="h-5 w-5 animate-spin text-brand-blue" />;
  }
  if (error) return <p className="text-sm text-rose-700">{error}</p>;
  if (!events || events.length === 0) {
    return <p className="text-sm text-brand-grayMid">Sin actividad registrada todavía.</p>;
  }
  return (
    <ol className="space-y-2">
      {events.map((event) => (
        <li
          key={event.id}
          className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-soft"
        >
          <span
            className={cn(
              "mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold uppercase",
              event.actor_type === "client"
                ? "bg-brand-blueSoft text-brand-blue"
                : event.actor_type === "consultant"
                ? "bg-slate-100 text-brand-grayMid"
                : "bg-emerald-50 text-emerald-700"
            )}
          >
            {event.actor_type === "client" ? "C" : event.actor_type === "consultant" ? "T" : "S"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-brand-black">{event.event_label}</p>
            <p className="text-[11px] text-brand-grayMid">
              {new Date(event.created_at).toLocaleString("es-ES")}
              {event.actor_email ? ` · ${event.actor_email}` : ""}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

// --- Create Room modal ----------------------------------------------------

function CreateRoomModal({
  mandateId,
  evaluations,
  existingItems,
  onClose,
  onCreated,
}: {
  mandateId: string;
  evaluations: CandidateEvaluation[];
  existingItems: number[];
  onClose: () => void;
  onCreated: (room: ClientShortlist) => void;
}) {
  const [title, setTitle] = useState("Shortlist Talenscan");
  const [introMessage, setIntroMessage] = useState("");
  const [accessCodeRequired, setAccessCodeRequired] = useState(true);
  const [showScores, setShowScores] = useState(false);
  const [showRisks, setShowRisks] = useState(false);
  const [showAvailability, setShowAvailability] = useState(false);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactCompany, setContactCompany] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const candidates = evaluations.filter((e) => !existingItems.includes(e.id));

  function toggle(id: number) {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function submit() {
    if (selected.size === 0) {
      setError("Selecciona al menos un candidato.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = await apiFetch<ClientShortlist>(
        `/api/mandatos/${mandateId}/shortlists`,
        {
          method: "POST",
          body: JSON.stringify({
            title,
            intro_message: introMessage || null,
            access_code_required: accessCodeRequired,
            show_scores: showScores,
            show_risks: showRisks,
            show_availability: showAvailability,
            client_contact_name: contactName || null,
            client_contact_email: contactEmail || null,
            client_contact_company: contactCompany || null,
            evaluation_ids: Array.from(selected),
          }),
        }
      );
      onCreated(body);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible crear el Decision Room.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Crear Decision Room
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">
              Selecciona candidatos y configura el acceso
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

        <div className="mt-4 space-y-4">
          <Field label="Título visible para el cliente">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
            />
          </Field>
          <Field label="Mensaje del consultor (opcional)">
            <textarea
              value={introMessage}
              onChange={(e) => setIntroMessage(e.target.value)}
              rows={2}
              placeholder="Bienvenido al Decision Room. En este espacio podrá revisar los candidatos preseleccionados…"
              className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
            />
          </Field>

          <div className="grid gap-3 md:grid-cols-3">
            <Field label="Contacto cliente">
              <input
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="Nombre"
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Email">
              <input
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="cliente@empresa.com"
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
            <Field label="Empresa">
              <input
                value={contactCompany}
                onChange={(e) => setContactCompany(e.target.value)}
                placeholder="Empresa"
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
              />
            </Field>
          </div>

          <section className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
              Visibilidad inicial
            </p>
            <div className="mt-2 space-y-1">
              <Toggle label="Acceso protegido por código" checked={accessCodeRequired} onChange={setAccessCodeRequired} />
              <Toggle label="Mostrar score de calce" checked={showScores} onChange={setShowScores} />
              <Toggle label="Mostrar disponibilidad" checked={showAvailability} onChange={setShowAvailability} />
              <Toggle label="Mostrar puntos a validar" checked={showRisks} onChange={setShowRisks} />
            </div>
          </section>

          <section>
            <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
              Candidatos a incluir ({selected.size}/{candidates.length})
            </p>
            {candidates.length === 0 ? (
              <p className="mt-2 rounded-lg border border-dashed border-slate-200 px-3 py-6 text-center text-xs text-brand-grayMid">
                No hay candidatos evaluados disponibles.
              </p>
            ) : (
              <ul className="mt-2 max-h-56 space-y-1.5 overflow-y-auto rounded-lg border border-slate-200 p-2">
                {candidates.map((e) => {
                  const isOn = selected.has(e.id);
                  return (
                    <li key={e.id}>
                      <label className="flex cursor-pointer items-start gap-2 rounded-md px-2 py-1.5 hover:bg-slate-50">
                        <input
                          type="checkbox"
                          checked={isOn}
                          onChange={() => toggle(e.id)}
                          className="mt-0.5 h-3.5 w-3.5 rounded border-slate-300 text-brand-blue focus:ring-brand-blue/30"
                        />
                        <span className="min-w-0 flex-1 text-xs text-brand-black">
                          Evaluación #{e.id} · Score {e.total_score}/100 · {e.score_category}
                        </span>
                      </label>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

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
            disabled={saving || selected.size === 0}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Crear Decision Room
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Invitation modal -----------------------------------------------------

function InvitationModal({
  room,
  mandate,
  publicUrl,
  accessCode,
  codeExpiresAt,
  onClose,
  onSent,
}: {
  room: ClientShortlist;
  mandate: SearchMandate | null;
  publicUrl: string;
  accessCode: string | null;
  codeExpiresAt: string | null;
  onClose: () => void;
  onSent: () => Promise<void>;
}) {
  const subject = `Acceso a Decision Room · Shortlist para ${mandate?.target_role || room.title}`;
  const expiresLine = codeExpiresAt
    ? `Este acceso estará disponible hasta el ${new Date(codeExpiresAt).toLocaleDateString("es-ES")}.`
    : "";
  const codeLine = accessCode
    ? `Código de validación: ${accessCode}`
    : "Código de validación: (genera el código antes de enviar la invitación)";

  const body = `Hola ${room.client_contact_name || "[Cliente]"},

Hemos preparado el Decision Room para la búsqueda de ${mandate?.target_role || room.title}.

En este espacio podrás revisar los candidatos preseleccionados, comparar perfiles y dejar tu feedback para avanzar con entrevistas, pedir más información o descartar candidatos.

Link de acceso:
${publicUrl}

${codeLine}

${expiresLine}

Saludos,
Equipo Talenscan`;

  async function copy(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      window.alert("Copiado al portapapeles.");
    } catch {
      window.prompt("Copia este texto:", value);
    }
  }

  function openMail() {
    const mailto = `mailto:${encodeURIComponent(room.client_contact_email || "")}?subject=${encodeURIComponent(
      subject
    )}&body=${encodeURIComponent(body)}`;
    window.location.href = mailto;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Invitación al cliente
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">
              {room.client_contact_email || "Sin email configurado"}
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
          <Field label="Asunto">
            <input
              value={subject}
              readOnly
              className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-sm text-brand-black"
            />
          </Field>
          <Field label="Cuerpo">
            <textarea
              value={body}
              readOnly
              rows={12}
              className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-brand-black"
            />
          </Field>
          {!accessCode ? (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
              No has generado un código nuevo aún. Cierra este modal y usa <strong>Generar código</strong> en el header del room para producir uno antes de enviar.
            </p>
          ) : null}
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={() => copy(body)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid hover:bg-slate-50"
          >
            <Copy className="h-3.5 w-3.5" />
            Copiar invitación
          </button>
          <button
            type="button"
            onClick={openMail}
            disabled={!room.client_contact_email}
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-blue/30 bg-brand-blueSoft px-3 py-1.5 text-sm font-medium text-brand-blue hover:bg-brand-blueSoft/80 disabled:opacity-60"
          >
            <Mail className="h-3.5 w-3.5" />
            Abrir en correo
          </button>
          <button
            type="button"
            onClick={onSent}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-1.5 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            <Send className="h-3.5 w-3.5" />
            Marcar como enviada
          </button>
        </div>
      </div>
    </div>
  );
}
