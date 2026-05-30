import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { TalentMarketMap } from "@/components/talent-market-map/talent-market-map";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader
        eyebrow="Talent Market Map"
        title="Mapa estratégico del mercado de talento."
        description="Segmenta el mercado objetivo en industrias, empresas y cargos equivalentes, mide la cobertura de la búsqueda, detecta brechas repetidas y recibe recomendaciones para recalibrar el perfil."
      />
      <MandatoTabs />
      <TalentMarketMap mandateId={id} />
    </AppShell>
  );
}
