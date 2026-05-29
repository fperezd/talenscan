"use client";

import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info" | "warning";

type Toast = {
  id: number;
  kind: ToastKind;
  title: string;
  description?: string;
};

type ToastContextValue = {
  push: (toast: Omit<Toast, "id">) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const STYLES: Record<
  ToastKind,
  { icon: React.ComponentType<{ className?: string }>; bar: string; iconClass: string }
> = {
  success: { icon: CheckCircle2, bar: "border-emerald-200 bg-emerald-50", iconClass: "text-emerald-600" },
  error: { icon: XCircle, bar: "border-rose-200 bg-rose-50", iconClass: "text-rose-600" },
  info: { icon: Info, bar: "border-slate-200 bg-white", iconClass: "text-brand-blue" },
  warning: { icon: AlertTriangle, bar: "border-amber-200 bg-amber-50", iconClass: "text-amber-700" },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((toast: Omit<Toast, "id">) => {
    setToasts((prev) => [...prev, { ...toast, id: Date.now() + Math.random() }]);
  }, []);

  function dismiss(id: number) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  useEffect(() => {
    if (toasts.length === 0) return;
    const timers = toasts.map((toast) =>
      window.setTimeout(() => dismiss(toast.id), toast.kind === "error" ? 6000 : 4000)
    );
    return () => {
      timers.forEach((t) => window.clearTimeout(t));
    };
  }, [toasts]);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => {
          const style = STYLES[toast.kind];
          const Icon = style.icon;
          return (
            <div
              key={toast.id}
              role="status"
              className={cn(
                "flex w-80 items-start gap-3 rounded-xl border px-4 py-3 shadow-elevated",
                style.bar
              )}
            >
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", style.iconClass)} />
              <div className="flex-1">
                <p className="text-sm font-semibold text-brand-black">{toast.title}</p>
                {toast.description ? (
                  <p className="mt-0.5 text-xs text-brand-grayMid">{toast.description}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                aria-label="Cerrar"
                className="rounded p-0.5 text-brand-grayMid transition hover:bg-slate-100 hover:text-brand-black"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Si no hay provider, ignoramos silenciosamente para no romper.
    return { push: () => {} };
  }
  return ctx;
}
