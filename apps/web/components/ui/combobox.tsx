"use client";

import { Check, ChevronDown, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type ComboboxProps = {
  value: string;
  onChange: (value: string) => void;
  options: readonly string[];
  placeholder?: string;
  allowCustom?: boolean;
  disabled?: boolean;
  className?: string;
  emptyLabel?: string;
  id?: string;
};

export function Combobox({
  value,
  onChange,
  options,
  placeholder = "Selecciona o escribe...",
  allowCustom = true,
  disabled = false,
  className,
  emptyLabel = "Sin coincidencias. Presiona Enter para usar el valor escrito.",
  id,
}: ComboboxProps) {
  const generatedId = useId();
  const fallbackId = id || generatedId;
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery(value);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [value]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return options;
    return options.filter((option) => option.toLowerCase().includes(normalized));
  }, [options, query]);

  function commit(next: string) {
    onChange(next);
    setQuery(next);
    setOpen(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      if (filtered.length > 0) {
        commit(filtered[0]);
      } else if (allowCustom && query.trim()) {
        commit(query.trim());
      }
    }
    if (event.key === "Escape") {
      setOpen(false);
      setQuery(value);
    }
  }

  function handleClear(event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    commit("");
  }

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div className="relative">
        <input
          id={fallbackId}
          type="text"
          value={query}
          disabled={disabled}
          placeholder={placeholder}
          autoComplete="off"
          onChange={(event) => {
            setQuery(event.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          className={cn(
            "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 pr-16 text-sm text-brand-black",
            "placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15",
            "disabled:cursor-not-allowed disabled:bg-slate-50"
          )}
        />
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center gap-1 pr-2">
          {query ? (
            <button
              type="button"
              onClick={handleClear}
              aria-label="Limpiar"
              className="pointer-events-auto rounded p-1 text-brand-grayMid hover:bg-slate-100 hover:text-brand-black"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          ) : null}
          <ChevronDown
            className={cn("h-4 w-4 text-brand-grayMid transition", open && "rotate-180")}
          />
        </div>
      </div>

      {open && !disabled ? (
        <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-64 overflow-auto rounded-xl border border-slate-200 bg-white p-1 shadow-elevated">
          {filtered.length === 0 ? (
            <p className="px-3 py-2 text-xs text-brand-grayMid">{emptyLabel}</p>
          ) : (
            filtered.map((option) => {
              const selected = option === value;
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => commit(option)}
                  className={cn(
                    "flex w-full items-center justify-between gap-2 rounded-lg px-3 py-1.5 text-left text-sm",
                    selected
                      ? "bg-brand-blueSoft text-brand-blue"
                      : "text-brand-black hover:bg-slate-50"
                  )}
                >
                  <span>{option}</span>
                  {selected ? <Check className="h-3.5 w-3.5" /> : null}
                </button>
              );
            })
          )}
        </div>
      ) : null}
    </div>
  );
}
