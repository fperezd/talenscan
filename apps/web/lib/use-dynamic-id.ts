"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Extrae el id dinámico desde la URL real del navegador.
 *
 * Necesario porque Next.js con `output: 'export'` sólo pre-renderiza
 * `/mandatos/demo` (vía generateStaticParams). El Worker de Cloudflare
 * sirve ese HTML para cualquier /mandatos/<id>, así que `usePathname()`
 * devuelve la ruta del bundle (con "demo") hasta que React hidrata.
 *
 * Para evitar que un click rápido durante la hidratación lleve al usuario
 * a `/mandatos/demo/...`, además de `usePathname()` leemos directamente
 * `window.location.pathname` en `useEffect` y forzamos un re-render.
 *
 * @param segment Nombre del segmento padre (ej. "mandatos", "candidatos").
 * @param fallback Valor si no se puede parsear (por defecto "demo" para SSR).
 */
export function useDynamicId(segment: string, fallback = "demo"): string {
  const pathname = usePathname() || "";
  const [windowPath, setWindowPath] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    function update() {
      setWindowPath(window.location.pathname);
    }
    update();
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  const source = windowPath ?? pathname;
  const pattern = new RegExp(`/${segment}/([^/]+)`);
  const match = source.match(pattern);
  return match ? decodeURIComponent(match[1]) : fallback;
}
