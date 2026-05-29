import { DecisionRoomBuilder } from "@/components/decision-room/decision-room-builder";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader
        eyebrow="Decision Room"
        title="Shortlist, feedback y decisiones del cliente en un solo lugar."
        description="Construye una sala privada para que el cliente revise candidatos preseleccionados, compare alternativas y deje feedback estructurado sobre la búsqueda."
      />
      <MandatoTabs />
      <DecisionRoomBuilder mandateId={id} />
    </AppShell>
  );
}
