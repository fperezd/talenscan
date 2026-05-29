"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoForm } from "@/components/mandatos/mandato-form";
import { apiFetch } from "@/lib/api";
import type { SearchMandate, SearchMandateInput } from "@/types/search-mandate";

export default function Page() {
  async function handleCreate(payload: SearchMandateInput) {
    const created = await apiFetch<SearchMandate>("/api/mandatos", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // Hard navigation: las rutas dinámicas no están en el manifest estático
    // de Next y router.push devolvería 404. window.location pasa por el
    // Worker de Cloudflare que reescribe a /mandatos/demo.
    window.location.href = `/mandatos/${created.id}`;
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Mandatos"
        title="Nuevo mandato de búsqueda"
        description="Completa el levantamiento consultivo del cliente: contexto, cargo, requisitos y mercado objetivo."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <MandatoForm submitLabel="Crear mandato" onSubmit={handleCreate} />
      </section>
    </AppShell>
  );
}
