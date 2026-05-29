"use client";

import { ArrowRight, Briefcase, Building2, Linkedin, Search, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { SkeletonList } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import type { Candidate } from "@/types/candidate";

export function CandidateHub() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return candidates;
    return candidates.filter((candidate) => {
      const haystack = [
        candidate.full_name,
        candidate.current_position,
        candidate.current_company,
        candidate.country,
        candidate.email,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [candidates, search]);

  useEffect(() => {
    async function loadCandidates() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch<Candidate[]>("/api/candidatos");
        setCandidates(data);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar candidatos.");
      } finally {
        setLoading(false);
      }
    }

    void loadCandidates();
  }, []);

  if (loading) {
    return <SkeletonList rows={4} />;
  }

  if (error) {
    return (
      <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {error}
      </p>
    );
  }

  if (!candidates.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-10 text-center">
        <Users className="mx-auto h-7 w-7 text-brand-grayMid" />
        <p className="mt-3 text-sm font-semibold text-brand-black">Aún no hay candidatos cargados</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Sube CVs desde un mandato en la pestaña "Evaluar candidatos".
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar por nombre, cargo, empresa o país..."
          className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-8 text-center text-sm text-brand-grayMid">
          Sin candidatos que coincidan con "{search}".
        </div>
      ) : null}

      {filtered.map((candidate) => {
        const initials = candidate.full_name
          .split(/\s+/)
          .map((p) => p[0])
          .filter(Boolean)
          .slice(0, 2)
          .join("")
          .toUpperCase();
        return (
          <a
            key={candidate.id}
            href={`/candidatos/${candidate.id}`}
            className="group flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand-blue/40 hover:shadow-soft"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-blueSoft text-base font-semibold text-brand-blue">
              {initials || "—"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-brand-black">{candidate.full_name}</p>
                {candidate.linkedin_url ? (
                  <span
                    title="Perfil de LinkedIn"
                    className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-1.5 py-0.5 text-[10px] font-medium text-brand-blue"
                  >
                    <Linkedin className="h-2.5 w-2.5" />
                    LinkedIn
                  </span>
                ) : null}
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-brand-grayMid">
                {candidate.current_position ? (
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    {candidate.current_position}
                  </span>
                ) : null}
                {candidate.current_company ? (
                  <span className="inline-flex items-center gap-1">
                    <Building2 className="h-3 w-3" />
                    {candidate.current_company}
                  </span>
                ) : null}
                {candidate.country ? <span>{candidate.country}</span> : null}
              </div>
            </div>
            <ArrowRight className="h-4 w-4 shrink-0 text-brand-grayMid transition group-hover:translate-x-0.5 group-hover:text-brand-blue" />
          </a>
        );
      })}
    </div>
  );
}
