import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { TalentVaultHub } from "@/components/talentos/talent-vault-hub";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Bóveda de Talento"
        title="Bóveda de Talento"
        description="Base inteligente de perfiles evaluados y reutilizables: consolida CVs, evaluaciones, procesos y notas en un Perfil Maestro de Talento por persona."
      />
      <TalentVaultHub />
    </AppShell>
  );
}
