"use client";

import {
  ChevronsLeft,
  ChevronsRight,
  ClipboardList,
  FileBarChart,
  Home,
  KanbanSquare,
  Settings,
  Sparkles,
  Users,
  Vault,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Inicio", icon: Home },
  { href: "/mandatos", label: "Mandatos", icon: ClipboardList },
  { href: "/pipeline", label: "Pipeline", icon: KanbanSquare },
  { href: "/candidatos", label: "Candidatos", icon: Users },
  { href: "/talentos", label: "Bóveda de Talento", icon: Vault },
  { href: "/evaluaciones", label: "Evaluaciones", icon: Sparkles },
  { href: "/reportes", label: "Reportes", icon: FileBarChart },
  { href: "/configuracion", label: "Configuración", icon: Settings },
] as const;

const STORAGE_KEY = "talenscan:sidebar-collapsed";

function isActive(currentPath: string, href: string): boolean {
  if (href === "/") return currentPath === "/";
  return currentPath === href || currentPath.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname() || "/";
  const [collapsed, setCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "1") setCollapsed(true);
    } catch {
      // ignore localStorage failures
    }
    setHydrated(true);
  }, []);

  function toggle() {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {
        // ignore
      }
      return next;
    });
  }

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r border-slate-200 bg-white transition-[width] duration-200 md:flex",
        collapsed ? "w-[68px]" : "w-52",
        !hydrated && "opacity-0"
      )}
    >
      <div className="relative flex flex-col items-center bg-white px-3 pt-6 pb-5">
        <Link
          href="/"
          aria-label="Ir al inicio de TalentScan"
          title="Ir al inicio"
          className={cn(
            "flex w-full items-center justify-center rounded-lg py-2 transition hover:bg-slate-50",
            collapsed && "px-0"
          )}
        >
          <img
            src={collapsed ? "/favicon.png" : "/logo-talenscan.png"}
            alt="TalentScan"
            className={cn(
              "w-auto transition-all duration-200",
              collapsed ? "h-8" : "h-12"
            )}
          />
        </Link>
        <button
          type="button"
          onClick={toggle}
          aria-label={collapsed ? "Expandir menú lateral" : "Colapsar menú lateral"}
          className="absolute -right-3 top-20 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 bg-white text-brand-grayMid shadow-soft transition hover:border-brand-blue hover:text-brand-blue"
        >
          {collapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
        </button>
      </div>

      <nav className="flex-1 space-y-0.5 px-2 pb-6 pt-2">
        {items.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition",
                collapsed && "justify-center px-0",
                active
                  ? "bg-brand-blueSoft text-brand-blue"
                  : "text-brand-grayMid hover:bg-slate-50 hover:text-brand-black"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0",
                  active ? "text-brand-blue" : "text-brand-grayMid group-hover:text-brand-black"
                )}
              />
              {!collapsed ? <span>{label}</span> : null}
            </Link>
          );
        })}
      </nav>

      {!collapsed ? (
        <div className="border-t border-slate-100 px-4 py-3">
          <p className="text-[10px] uppercase tracking-wider text-brand-grayMid">TalentScan</p>
          <p className="mt-0.5 text-[11px] text-brand-grayMid">MVP · v0.1</p>
        </div>
      ) : null}
    </aside>
  );
}
