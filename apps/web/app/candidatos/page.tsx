import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { CandidateHub } from "@/components/candidatos/candidate-hub";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Candidatos"
        title="Candidatos"
        description="Consulta candidatos, perfiles estructurados y evaluaciones 360 Talenscan."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <CandidateHub />
      </section>
    </AppShell>
  );
}
