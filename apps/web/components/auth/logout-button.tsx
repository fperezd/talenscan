"use client";

import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";

import { AUTH_ENABLED, decodeToken, getToken, logout } from "@/lib/auth";

/** Botón de salir + email del usuario. Solo visible si la auth está activa y hay sesión. */
export function LogoutButton() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!AUTH_ENABLED) return;
    const payload = decodeToken(getToken());
    setEmail((payload?.email as string) || null);
  }, []);

  if (!AUTH_ENABLED || !email) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-xs text-brand-grayMid sm:inline">{email}</span>
      <button
        type="button"
        onClick={logout}
        title="Cerrar sesión"
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-rose-200 hover:text-rose-700"
      >
        <LogOut className="h-3.5 w-3.5" />
        Salir
      </button>
    </div>
  );
}
