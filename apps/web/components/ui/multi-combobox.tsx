"use client";

import { Check, ChevronDown, Plus, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type MultiComboboxProps = {
  value: string[];
  onChange: (value: string[]) => void;
  options: readonly string[];
  placeholder?: string;
  addLabel?: string;
  allowCustom?: boolean;
  className?: string;
  id?: string;
};

export function MultiCombobox({
  value,
  onChange,
  options,
  placeholder = "Agrega o escribe...",
  addLabel = "Agregar",
  allowCustom = true,
  className,
  id,
}: MultiComboboxProps) {
  const generatedId = useId();
  const fallbackId = id || generatedId;
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const remaining = options.filter((option) => !value.includes(option));
    if (!normalized) return remaining;
    return remaining.filter((option) => option.toLowerCase().includes(normalized));
  }, [options, query, value]);

  function add(next: string) {
    const clean = next.trim();
    if (!clean) return;
    if (value.includes(clean)) {
      setQuery("");
      return;
    }
    onChange([...value, clean]);
    setQuery("");
  }

  function remove(item: string) {
    onChange(value.filter((entry) => entry !== item));
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      if (filtered.length > 0) {
        add(filtered[0]);
      } else if (allowCustom && query.trim()) {
        add(query.trim());
      }
    }
    if (event.key === "Backspace" && !query && value.length > 0) {
      remove(value[value.length - 1]);
    }
    if (event.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  }

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div
        className={cn(
          "flex min-h-[42px] flex-wrap items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-1.5",
          "focus-within:border-brand-blue focus-within:ring-2 focus-within:ring-brand-blue/15"
        )}
        onClick={() => {
          const input = containerRef.current?.querySelector("input");
          input?.focus();
        }}
      >
        {value.map((item) => (
          <span
            key={item}
            className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-xs font-medium text-brand-blue"
          >
            {item}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                remove(item);
              }}
              aria-label={`Quitar ${item}`}
              className="rounded-full p-0.5 hover:bg-brand-blue/10"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          id={fallbackId}
          type="text"
          value={query}
          placeholder={value.length === 0 ? placeholder : ""}
          autoComplete="off"
          onChange={(event) => {
            setQuery(event.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          className="flex-1 min-w-[120px] bg-transparent px-1 py-0.5 text-sm text-brand-black placeholder:text-brand-grayMid focus:outline-none"
        />
        <ChevronDown
          className={cn("h-4 w-4 shrink-0 text-brand-grayMid transition", open && "rotate-180")}
        />
      </div>

      {open ? (
        <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-64 overflow-auto rounded-xl border border-slate-200 bg-white p-1 shadow-elevated">
          {filtered.length === 0 ? (
            allowCustom && query.trim() ? (
              <button
                type="button"
                onClick={() => add(query.trim())}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-brand-black hover:bg-slate-50"
              >
                <Plus className="h-3.5 w-3.5 text-brand-blue" />
                {addLabel} <span className="font-semibold">"{query.trim()}"</span>
              </button>
            ) : (
              <p className="px-3 py-2 text-xs text-brand-grayMid">
                {value.length === options.length ? "Todas las opciones agregadas." : "Sin coincidencias."}
              </p>
            )
          ) : (
            filtered.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => add(option)}
                className="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-brand-black hover:bg-slate-50"
              >
                <span>{option}</span>
                <Plus className="h-3.5 w-3.5 text-brand-grayMid" />
              </button>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
