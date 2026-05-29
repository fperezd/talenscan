import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { EvaluationList } from "@/components/evaluaciones/evaluation-list";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Evaluaciones"
        title="Evaluación 360 Talenscan"
        description="Resultados de evaluación explicable: score 360, brechas críticas y recomendación ejecutiva."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <EvaluationList />
      </section>
    </AppShell>
  );
}
