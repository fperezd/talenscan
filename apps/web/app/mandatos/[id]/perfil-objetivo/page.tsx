import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { PositionSpecClient } from "@/components/position-spec/position-spec-client";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Perfil objetivo"
        title="Perfil objetivo del cargo"
        description="Estructura evaluable del cargo: requisitos, competencias, criterios y matriz de scoring."
      />
      <MandatoTabs />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <PositionSpecClient mandateId={id} />
      </section>
    </AppShell>
  );
}
