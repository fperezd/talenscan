import { Plus } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoList } from "@/components/mandatos/mandato-list";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Mandatos"
        title="Mandatos de búsqueda"
        description="Gestiona mandatos activos, genera perfiles objetivo y evalúa candidatos."
        actions={
          <Link
            href="/mandatos/nuevo"
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            <Plus className="h-3.5 w-3.5" />
            Crear mandato de búsqueda
          </Link>
        }
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <MandatoList />
      </section>
    </AppShell>
  );
}
