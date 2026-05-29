import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { EvaluarCandidatosClient } from "@/components/evaluaciones/evaluar-candidatos-client";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Evaluar candidatos"
        title="Carga de CVs y Evaluación 360"
        description="Sube CVs, genera el perfil estructurado del candidato y obtén la Evaluación 360 Talenscan."
      />
      <MandatoTabs />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <EvaluarCandidatosClient mandateId={id} />
      </section>
    </AppShell>
  );
}
