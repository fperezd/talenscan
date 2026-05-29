import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { ReportCenter } from "@/components/reportes/report-center";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Reportes"
        title="Informes ejecutivos"
        description="Descarga informes Word y PDF profesionales por evaluación, listos para presentar al cliente."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <ReportCenter />
      </section>
    </AppShell>
  );
}
