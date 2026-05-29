import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { CandidateCompareClient } from "@/components/comparar/candidate-compare-client";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Comparar candidatos"
        title="Comparativo lado a lado"
        description="Selecciona hasta 5 candidatos del pipeline de este mandato y compáralos dimensión por dimensión."
      />
      <MandatoTabs />
      <CandidateCompareClient mandateId={id} />
    </AppShell>
  );
}
