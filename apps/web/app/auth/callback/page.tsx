"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { setToken } from "@/lib/auth";

const ERROR_LABELS: Record<string, string> = {
  dominio_de_consumo: "Usá un correo corporativo (no gmail/outlook/etc.).",
  google_sin_workspace: "La cuenta de Google debe ser de Google Workspace (empresa).",
  microsoft_cuenta_personal: "La cuenta de Microsoft debe ser corporativa, no personal.",
  cuenta_no_empresarial: "Solo se permiten cuentas de empresa.",
};

export default function AuthCallbackPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    const params = new URLSearchParams(hash);
    const token = params.get("token");
    const err = params.get("error");
    if (token) {
      setToken(token);
      window.location.replace("/");
      return;
    }
    setError(err ? ERROR_LABELS[err] || `No se pudo iniciar sesión (${err}).` : "No se recibió token de sesión.");
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4">
      {error ? (
        <div className="w-full max-w-md rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-soft">
          <p className="text-sm text-rose-700">{error}</p>
          <a href="/" className="mt-4 inline-block text-sm font-semibold text-brand-blue hover:underline">
            Volver al inicio
          </a>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-brand-grayMid">
          <Loader2 className="h-5 w-5 animate-spin text-brand-blue" />
          Validando tu acceso…
        </div>
      )}
    </div>
  );
}
