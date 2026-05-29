"use client";

import { cn } from "@/lib/utils";

export type TabItem = {
  href: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  active?: boolean;
};

type TabsProps = {
  items: TabItem[];
  className?: string;
};

export function Tabs({ items, className }: TabsProps) {
  // Anchors plain en vez de next/link porque las rutas pueden ser dinámicas
  // (/mandatos/N/...) y el client router de Next con static export
  // mostraría 404 al no encontrar el id en el manifest.
  return (
    <nav className={cn("flex flex-wrap gap-1 border-b border-slate-200", className)}>
      {items.map(({ href, label, icon: Icon, active }) => (
        <a
          key={href}
          href={href}
          className={cn(
            "inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition -mb-px",
            active
              ? "border-brand-blue text-brand-blue"
              : "border-transparent text-brand-grayMid hover:text-brand-black"
          )}
        >
          {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
          {label}
        </a>
      ))}
    </nav>
  );
}
