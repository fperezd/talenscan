"use client";

import { Loader2, Plus, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ClientShortlist } from "@/types/shortlist";

type Props = {
  mandateId: string | number;
  evaluationIds: number[];
  /**
   * Etiqueta opcional para el contexto.
   * Ej. "Giorgio Solari", "3 candidatos seleccionados".
   */
  selectionLabel?: string;
  open: boolean;
  onClose: () => void;
  onSuccess?: (room: ClientShortlist) => void;
};

const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  ready_to_share: "Listo",
  invitation_sent: "Invitación enviada",
  viewed: "Visto",
  in_review: "En revisión",
  feedback_received: "Feedback recibido",
  closed: "Cerrado",
  expired: "Expirado",
};

export function AddToRoomModal({
  mandateId,
  evaluationIds,
  selectionLabel,
  open,
  onClose,
  onSuccess,
}: Props) {
  const [rooms, setRooms] = useState<ClientShortlist[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"existing" | "new">("new");
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [newTitle, setNewTitle] = useState("Shortlist TalentScan");
  const [accessCodeRequired, setAccessCodeRequired] = useState(true);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    apiFetch<ClientShortlist[]>(`/api/mandatos/${mandateId}/shortlists`)
      .then((data) => {
        setRooms(data);
        if (data.length > 0) {
          setMode("existing");
          setSelectedRoomId(data[0].id);
        } else {
          setMode("new");
        }
      })
      .catch((caught) => {
        console.error(caught);
        setError("No fue posible cargar los Decision Rooms.");
      })
      .finally(() => setLoading(false));
  }, [mandateId, open]);

  if (!open) return null;

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      if (mode === "existing" && selectedRoomId !== null) {
        // Si solo hay un candidato, llamamos al endpoint add-item.
        // Para varios, iteramos (los endpoints son idempotentes).
        let lastRoom: ClientShortlist | null = null;
        for (const evalId of evaluationIds) {
          lastRoom = await apiFetch<ClientShortlist>(
            `/api/shortlists/${selectedRoomId}/items`,
            {
              method: "POST",
              body: JSON.stringify({ evaluation_id: evalId }),
            }
          );
        }
        onSuccess?.(lastRoom!);
      } else {
        const room = await apiFetch<ClientShortlist>(
          `/api/mandatos/${mandateId}/shortlists`,
          {
            method: "POST",
            body: JSON.stringify({
              title: newTitle || "Shortlist TalentScan",
              access_code_required: accessCodeRequired,
              evaluation_ids: evaluationIds,
            }),
          }
        );
        onSuccess?.(room);
      }
      onClose();
    } catch (caught) {
      console.error(caught);
      setError("No fue posible completar la acción.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center" role="dialog" aria-modal="true">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Decision Room
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">
              {evaluationIds.length > 1
                ? `Crear o ampliar shortlist con ${evaluationIds.length} candidatos`
                : "Agregar candidato a un Decision Room"}
            </h3>
            {selectionLabel ? (
              <p className="mt-1 text-xs text-brand-grayMid">{selectionLabel}</p>
            ) : null}
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

        {loading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-brand-blue" />
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {rooms && rooms.length > 0 ? (
              <div className="rounded-lg border border-slate-200 p-1">
                {(["existing", "new"] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setMode(value)}
                    className={cn(
                      "w-1/2 rounded-md px-3 py-1.5 text-xs font-semibold transition",
                      mode === value
                        ? "bg-brand-blue text-white"
                        : "text-brand-grayMid hover:bg-slate-50"
                    )}
                  >
                    {value === "existing" ? "Usar room existente" : "Crear nuevo"}
                  </button>
                ))}
              </div>
            ) : null}

            {mode === "existing" && rooms && rooms.length > 0 ? (
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Selecciona el Decision Room
                </p>
                <ul className="max-h-56 space-y-1 overflow-y-auto rounded-lg border border-slate-200 p-1">
                  {rooms.map((room) => (
                    <li key={room.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedRoomId(room.id)}
                        className={cn(
                          "flex w-full items-start justify-between gap-3 rounded-md px-3 py-2 text-left text-sm transition",
                          selectedRoomId === room.id
                            ? "bg-brand-blueSoft text-brand-blue"
                            : "text-brand-black hover:bg-slate-50"
                        )}
                      >
                        <div className="min-w-0">
                          <p className="truncate font-semibold">{room.title}</p>
                          <p className="text-[11px] text-brand-grayMid">
                            {room.items.length} candidatos · {STATUS_LABEL[room.status] || room.status}
                          </p>
                        </div>
                        {selectedRoomId === room.id ? (
                          <span className="rounded-full bg-brand-blue px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                            Elegido
                          </span>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {mode === "new" ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    Título del nuevo Decision Room
                  </label>
                  <input
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
                  />
                </div>
                <label className="flex items-center gap-2 text-xs text-brand-grayMid">
                  <input
                    type="checkbox"
                    checked={accessCodeRequired}
                    onChange={(e) => setAccessCodeRequired(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-brand-blue focus:ring-brand-blue/30"
                  />
                  Acceso protegido por código (recomendado)
                </label>
                <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-brand-grayMid">
                  Se incluirá{evaluationIds.length === 1 ? " el candidato seleccionado" : `n ${evaluationIds.length} candidatos`} en este Decision Room.
                </p>
              </div>
            ) : null}

            {error ? <p className="text-xs text-rose-700">{error}</p> : null}
          </div>
        )}

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
            disabled={saving || (mode === "existing" && selectedRoomId === null)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "existing" ? <Plus className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            {mode === "existing" ? "Agregar al room" : "Crear Decision Room"}
          </button>
        </div>
      </div>
    </div>
  );
}
