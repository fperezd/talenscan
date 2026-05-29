import { ArrowRight, Plus } from "lucide-react";
import Link from "next/link";

export function Topbar() {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-3 backdrop-blur">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">Panel ejecutivo</p>
        <p className="text-sm font-medium text-brand-black">
          Gestión profesional de mandatos y candidatos
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Link
          href="/pipeline"
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-slate-300 hover:bg-slate-50 hover:text-brand-black"
        >
          Ver pipeline
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
        <Link
          href="/mandatos/nuevo"
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
        >
          <Plus className="h-3.5 w-3.5" />
          Crear mandato
        </Link>
      </div>
    </header>
  );
}
