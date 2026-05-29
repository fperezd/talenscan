import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoDetailClient } from "@/components/mandatos/mandato-detail-client";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Mandato"
        title="Detalle del mandato"
        description="Resumen consultivo del mandato, requisitos y mercado objetivo."
      />
      <MandatoTabs />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <MandatoDetailClient mandateId={id} />
      </section>
    </AppShell>
  );
}
