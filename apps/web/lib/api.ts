export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const headers: HeadersInit = isFormData
    ? { ...(init?.headers || {}) }
    : {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Error de comunicacion con Talenscan API");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
