"use client";

import { Loader2 } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";

import { AuthScreen } from "@/components/auth/auth-screen";
import { AUTH_ENABLED, getToken } from "@/lib/auth";

/**
 * Portón de autenticación. Opt-in: si NEXT_PUBLIC_AUTH_ENABLED no es "true",
 * es transparente (no rompe el deploy actual sin usuarios). Cuando está activo,
 * exige un token de sesión; si no hay, muestra la pantalla de login/registro.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  // Si la auth está deshabilitada en build, no renderizamos lógica de cliente:
  // mismo árbol en server y cliente → sin hydration mismatch.
  if (!AUTH_ENABLED) return <>{children}</>;
  return <Gated>{children}</Gated>;
}

function Gated({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-brand-bg">
        <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
      </div>
    );
  }
  if (!authed) {
    return <AuthScreen onAuthed={() => setAuthed(true)} />;
  }
  return <>{children}</>;
}
