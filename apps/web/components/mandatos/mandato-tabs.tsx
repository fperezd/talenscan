"use client";

import { ClipboardList, DoorOpen, FileText, GitCompare, KanbanSquare, Map, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";

import { Tabs, type TabItem } from "@/components/ui/tabs";
import { useDynamicId } from "@/lib/use-dynamic-id";

const TAB_ICONS = {
  resumen: ClipboardList,
  "perfil-objetivo": FileText,
  evaluar: Sparkles,
  comparar: GitCompare,
  pipeline: KanbanSquare,
  "decision-room": DoorOpen,
  "talent-market-map": Map,
} as const;

export function MandatoTabs() {
  const mandateId = useDynamicId("mandatos");
  const pathname = usePathname() || "";

  const base = `/mandatos/${mandateId}`;

  const items: TabItem[] = [
    { href: base, label: "Resumen", icon: TAB_ICONS.resumen },
    { href: `${base}/perfil-objetivo`, label: "Perfil objetivo", icon: TAB_ICONS["perfil-objetivo"] },
    { href: `${base}/evaluar`, label: "Evaluar candidatos", icon: TAB_ICONS.evaluar },
    { href: `${base}/comparar`, label: "Comparar candidatos", icon: TAB_ICONS.comparar },
    { href: `${base}/pipeline`, label: "Pipeline", icon: TAB_ICONS.pipeline },
    { href: `${base}/decision-room`, label: "Decision Room", icon: TAB_ICONS["decision-room"] },
    { href: `${base}/talent-market-map`, label: "Market Map", icon: TAB_ICONS["talent-market-map"] },
  ].map((item) => ({
    ...item,
    active:
      item.href === base
        ? pathname === base || pathname === `${base}/`
        : pathname.startsWith(item.href),
  }));

  return <Tabs items={items} className="mb-6" />;
}
