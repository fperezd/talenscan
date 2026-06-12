// Auth self-hosted (TalentScan API). Guarda el JWT de sesión en localStorage y
// expone helpers de login/registro/logout. Opt-in vía NEXT_PUBLIC_AUTH_ENABLED.

import { API_BASE_URL, apiFetch } from "@/lib/api";

export const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";
const TOKEN_KEY = "talenscan:token";

export type SessionUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  organization_id: number | null;
};

export type AuthResult = {
  token: string;
  user: SessionUser;
  organization: { id: number; name: string; primary_domain: string | null } | null;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function decodeToken(token: string | null): Record<string, unknown> | null {
  if (!token || token.split(".").length !== 3) return null;
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(payload + "=".repeat((4 - (payload.length % 4)) % 4)));
  } catch {
    return null;
  }
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const res = await apiFetch<AuthResult>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(res.token);
  return res;
}

export async function register(
  email: string,
  password: string,
  fullName: string
): Promise<AuthResult> {
  const res = await apiFetch<AuthResult>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName || null }),
  });
  setToken(res.token);
  return res;
}

export function logout(): void {
  clearToken();
  window.location.href = "/";
}

export function ssoStartUrl(provider: "google" | "microsoft"): string {
  return `${API_BASE_URL}/api/auth/oauth/${provider}/start`;
}
