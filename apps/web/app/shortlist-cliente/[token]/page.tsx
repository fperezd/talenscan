import { ClientShortlistPublicView } from "@/components/shortlist-cliente/client-shortlist-public-view";

export function generateStaticParams() {
  return [{ token: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <ClientShortlistPublicView token={token} />;
}
