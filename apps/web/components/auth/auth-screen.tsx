"use client";

import { ssoStartUrl } from "@/lib/auth";

export function AuthScreen({ initialError }: { onAuthed: () => void; initialError?: string | null }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-soft">
        <div className="text-center">
          <img src="/logo-talenscan.png" alt="TalentScan" className="mx-auto h-16 w-auto" />
          <h1 className="mt-4 text-xl font-semibold text-brand-black">Ingresá a TalentScan</h1>
          <p className="mt-1 text-sm text-brand-grayMid">Acceso con tu cuenta Microsoft 365 corporativa.</p>
        </div>

        <div className="mt-8">
          <a
            href={ssoStartUrl("microsoft")}
            className="flex w-full items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-brand-black shadow-sm transition hover:bg-slate-50 hover:shadow"
          >
            <MicrosoftIcon />
            Continuar con Microsoft 365
          </a>
        </div>

        {initialError ? (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-center text-xs text-rose-700">{initialError}</p>
        ) : null}

        <p className="mt-6 text-center text-xs text-brand-grayMid">Solo cuentas corporativas de empresa.</p>
      </div>
    </div>
  );
}

function MicrosoftIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 23 23" aria-hidden>
      <path fill="#F25022" d="M1 1h10v10H1z" />
      <path fill="#7FBA00" d="M12 1h10v10H12z" />
      <path fill="#00A4EF" d="M1 12h10v10H1z" />
      <path fill="#FFB900" d="M12 12h10v10H12z" />
    </svg>
  );
}
