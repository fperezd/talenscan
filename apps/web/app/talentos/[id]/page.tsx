import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { TalentProfileDetail } from "@/components/talentos/talent-profile-detail";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader
        eyebrow="Perfil Maestro de Talento"
        title="Ficha de talento"
        description="Historial consolidado de experiencia, evaluaciones, procesos, notas y trazabilidad del talento."
      />
      <TalentProfileDetail talentId={id} />
    </AppShell>
  );
}
