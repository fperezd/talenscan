"use client";

import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { MandatoForm } from "@/components/mandatos/mandato-form";
import { useToast } from "@/components/ui/toast";
import { apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import type { SearchMandate, SearchMandateInput } from "@/types/search-mandate";

type MandatoDetailClientProps = {
  mandateId?: string;
};

export function MandatoDetailClient({ mandateId: propId }: MandatoDetailClientProps = {}) {
  const pathId = useDynamicId("mandatos");
  const mandateId = pathId && pathId !== "demo" ? pathId : propId || pathId;
  const toast = useToast();
  const [mandate, setMandate] = useState<SearchMandate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch<SearchMandate>(`/api/mandatos/${mandateId}`);
        setMandate(data);
      } catch (fetchError) {
        console.error(fetchError);
        setError("No se encontro el mandato solicitado.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [mandateId]);

  async function handleUpdate(payload: SearchMandateInput) {
    const updated = await apiFetch<SearchMandate>(`/api/mandatos/${mandateId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    setMandate(updated);
    setSavedMessage("Mandato actualizado correctamente.");
    toast.push({
      kind: "success",
      title: "Mandato actualizado",
      description: "Los cambios fueron guardados en el servidor.",
    });
  }

  if (loading) {
    return <p className="text-sm text-brand-grayMid">Cargando mandato...</p>;
  }

  if (error || !mandate) {
    return (
      <div className="space-y-3">
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error || "Mandato no encontrado"}</p>
        <Link href="/mandatos" className="inline-flex rounded-lg border border-slate-200 px-3 py-2 text-sm text-brand-grayMid hover:bg-slate-50 hover:text-brand-black">Volver a mandatos</Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {savedMessage ? (
        <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{savedMessage}</span>
        </div>
      ) : null}
      <MandatoForm
        initialValue={{
          client_name: mandate.client_name,
          search_title: mandate.search_title,
          target_role: mandate.target_role,
          industry: mandate.industry,
          country: mandate.country,
          city: mandate.city,
          work_mode: mandate.work_mode,
          seniority_level: mandate.seniority_level,
          reports_to: mandate.reports_to,
          business_context: mandate.business_context,
          role_objective: mandate.role_objective,
          key_challenges: mandate.key_challenges,
          main_responsibilities: mandate.main_responsibilities,
          expected_results: mandate.expected_results,
          must_have_requirements: mandate.must_have_requirements,
          nice_to_have_requirements: mandate.nice_to_have_requirements,
          target_companies: mandate.target_companies,
          target_industries: mandate.target_industries,
          equivalent_roles: mandate.equivalent_roles,
          compensation_context: mandate.compensation_context,
          urgency: mandate.urgency,
          target_hire_date: mandate.target_hire_date,
          comments: mandate.comments,
          status: mandate.status,
        }}
        submitLabel="Guardar cambios"
        onSubmit={handleUpdate}
      />
    </div>
  );
}
