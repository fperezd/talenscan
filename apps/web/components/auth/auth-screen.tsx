"use client";

import { Loader2, Lock, Mail } from "lucide-react";
import { useState } from "react";

import { login, register, ssoStartUrl } from "@/lib/auth";

type Mode = "login" | "register";

const inputClass =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15";

export function AuthScreen({ onAuthed, initialError }: { onAuthed: () => void; initialError?: string | null }) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(initialError || null);

  async function submit() {
    if (!email.trim() || !password) {
      setError("Ingresá tu correo corporativo y contraseña.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password, fullName.trim());
      }
      onAuthed();
    } catch (caught) {
      const msg = caught instanceof Error ? caught.message : "Error de autenticación.";
      setError(humanize(msg));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-soft">
        <div className="text-center">
          <img src="/logo-talenscan.png" alt="Talenscan" className="mx-auto h-16 w-auto" />
          <h1 className="mt-4 text-xl font-semibold text-brand-black">
            {mode === "login" ? "Ingresá a TalenScan" : "Creá tu cuenta"}
          </h1>
          <p className="mt-1 text-sm text-brand-grayMid">
            Acceso solo con <strong>correo corporativo</strong> de tu empresa.
          </p>
        </div>

        {/* SSO */}
        <div className="mt-6 space-y-2">
          <a
            href={ssoStartUrl("google")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-brand-black transition hover:bg-slate-50"
          >
            <GoogleIcon /> Continuar con Google Workspace
          </a>
          <a
            href={ssoStartUrl("microsoft")}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-brand-black transition hover:bg-slate-50"
          >
            <MicrosoftIcon /> Continuar con Microsoft
          </a>
        </div>

        <div className="my-5 flex items-center gap-3 text-[11px] uppercase tracking-wider text-brand-grayMid">
          <span className="h-px flex-1 bg-slate-200" /> o con email <span className="h-px flex-1 bg-slate-200" />
        </div>

        {/* Email + password */}
        <div className="space-y-3">
          {mode === "register" ? (
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Nombre completo"
              className={inputClass}
            />
          ) : null}
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@empresa.com"
              className={`${inputClass} pl-9`}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "Contraseña (mínimo 8)" : "Contraseña"}
              className={`${inputClass} pl-9`}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>

          {error ? (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>
          ) : null}

          <button
            type="button"
            onClick={submit}
            disabled={busy}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {mode === "login" ? "Ingresar" : "Crear cuenta"}
          </button>
        </div>

        <p className="mt-4 text-center text-xs text-brand-grayMid">
          {mode === "login" ? "¿No tenés cuenta?" : "¿Ya tenés cuenta?"}{" "}
          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
            className="font-semibold text-brand-blue hover:underline"
          >
            {mode === "login" ? "Registrate" : "Ingresá"}
          </button>
        </p>
      </div>
    </div>
  );
}

function humanize(msg: string): string {
  const m = msg.toLowerCase();
  if (m.includes("corporativo") || m.includes("empresa")) return msg;
  if (m.includes("409") || m.includes("ya existe")) return "Ya existe una cuenta con ese email.";
  if (m.includes("401") || m.includes("incorrect")) return "Email o contraseña incorrectos.";
  return msg || "No fue posible completar la operación.";
}

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.26 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.3 9.14 5.38 12 5.38Z" />
    </svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 23 23" aria-hidden>
      <path fill="#F25022" d="M1 1h10v10H1z" />
      <path fill="#7FBA00" d="M12 1h10v10H12z" />
      <path fill="#00A4EF" d="M1 12h10v10H1z" />
      <path fill="#FFB900" d="M12 12h10v10H12z" />
    </svg>
  );
}
